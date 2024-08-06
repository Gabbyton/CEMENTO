from collections import defaultdict

from cemento.draw_io.diagram_ref import DiagramRef
from cemento.draw_io.read_diagram import ReadDiagram


class ReadAreaDiagram(ReadDiagram):

    def __init__(
        self,
        file_path,
        do_check_errors=False,
        diagram_ref=None,
        inverted_rank_arrows=False,
        parse_terms=False,
    ):
        if diagram_ref is None:
            diagram_ref = DiagramRef()

        self.set_file_path(file_path)
        self.set_diagram_ref(diagram_ref)
        self._set_inverted_rank_arrows(inverted_rank_arrows)
        self._set_check_errors(do_check_errors)

        self._elements = self._parse_elements()
        self._edges, self._terms, self._rels = self._read_edges(
            elements=self._get_elements(),
            return_entity_ids=True,
        )
        super().__init__(
            file_path,
            do_check_errors=do_check_errors,
            diagram_ref=diagram_ref,
            inverted_rank_arrows=inverted_rank_arrows,
            parse_terms=parse_terms,
            edges=self._get_edges(),
        )

        self._area_designations = None
        self._area_terms = None

        self._set_area_terms()
        self._set_node_areas()

    def _set_node_areas(self):
        areas = dict()
        terms = set(self._get_terms())
        elements = self._get_elements()

        area_terms = self.get_area_terms().keys()

        for area_term in area_terms:
            x_0, y_0 = int(float(elements[area_term]["x"])), int(
                float(elements[area_term]["y"])
            )
            x_1, y_1 = (
                x_0 + int(float(elements[area_term]["width"])),
                y_0 + int(float(elements[area_term]["height"])),
            )
            areas[area_term] = (x_0, y_0, x_1, y_1)
        # check if node_terms belong to any of the areas
        node_terms = terms - area_terms
        area_designations = defaultdict(set)
        # classify term areas
        for node_term_id in node_terms:
            pos_x, pos_y = (
                int(float(elements[node_term_id].get("x", 0))),
                int(float(elements[node_term_id].get("y", 0))),
            )
            for area_term_id, area in areas.items():
                x_0, y_0, x_1, y_1 = area
                if pos_x > x_0 and pos_x < x_1 and pos_y > y_0 and pos_y < y_1:
                    area_designations[node_term_id].add(area_term_id)
        # classify containing area of areas
        for area_term in area_terms:
            curr_x_0, curr_y_0, curr_x_1, curr_y_1 = areas[area_term]

            for comp_area in area_terms:
                if comp_area == area_term:
                    continue

                comp_x_0, comp_y_0, comp_x_1, comp_y_1 = areas[comp_area]
                if (
                    comp_x_0 < curr_x_0
                    and comp_y_0 < curr_y_0
                    and comp_x_1 > curr_x_1
                    and comp_y_1 > curr_y_1
                ):
                    area_designations[area_term].add(comp_area)

        self._area_designations = area_designations

    def _parse_designations(self, designations):
        elements = self._get_elements()
        parsed_dict = dict()

        for key, values in designations.items():
            new_values = set()
            for value in values:
                new_values.add((value, ReadDiagram.clean_term(elements[value]['value'])))
            new_key = (key, ReadDiagram.clean_term(elements[key]['value']))
            parsed_dict[new_key] = new_values
        return parsed_dict

    def get_area_designations(self, parse_values=False):
        if not parse_values:
            return self._area_designations

        return self._parse_designations(self._area_designations)

    def get_node_designations(self, parse_values=False):
        inverted_dict = defaultdict(set)
        for key, values in self._area_designations.items():
            for value in values:
                inverted_dict[value].add(key)

        if not parse_values:
            return inverted_dict

        return self._parse_designations(inverted_dict)

    def _get_elements(self):
        return self._elements

    def _get_edges(self):
        return self._edges

    def _get_terms(self):
        return self._terms

    def _get_rels(self):
        return self._rels

    def _set_area_terms(self):
        elements = self._get_elements()
        terms = self._get_terms()

        area_terms = {
            term_id: elements[term_id]
            for term_id in terms
            if "~" in elements[term_id]["value"]
        }

        self._area_terms = area_terms

    def get_area_terms(self):
        return self._area_terms
