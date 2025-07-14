from pathlib import Path

from defusedxml import ElementTree as ET


def parse_elements(file_path: str | Path) -> dict[str, dict[str, any]]:
    # parse elements
    tree = ET.parse(file_path)
    root = tree.getroot()
    root = next(tree.iter("root"))

    elements = dict()
    all_cells = [child for child in root.findall("mxCell")]  # only add base level cells

    for cell in all_cells:
        cell_attrs = dict()
        cell_attrs.update(cell.attrib)

        # add nested position attributes if any
        nested_attrs = dict()
        for subcell in cell.findall("mxGeometry"):
            nested_attrs.update(subcell.attrib)
        cell_attrs.update(nested_attrs)

        # add style attributes as data attributes
        if "style" in cell.attrib:
            style_terms = dict()
            style_tags = []
            for style_attrib_string in cell.attrib["style"].split(";"):
                style_term = style_attrib_string.split("=")
                if len(style_term) > 1:  # for styles with values
                    key, value = style_term
                    style_terms[key] = value
                elif style_term[0]:  # for style tags or names
                    style_tags.append(style_term[0])
            cell_attrs.update(style_terms)
            cell_attrs["tags"] = style_tags
            del cell_attrs["style"]  # remove style to prevent redundancy

        cell_id = cell.attrib["id"]
        del cell_attrs["id"]  # remove id since it is now used as a key
        elements[cell_id] = (
            cell_attrs  # set dictionary of cell key and attribute dictionary
        )

    return elements


def extract_elements(
    elements: dict[str, dict[str, any]],
) -> tuple[set[dict[str, any], set[str]]]:
    # read edges
    term_ids, rel_ids = set(), set()
    for element, data in elements.items():
        # if the vertex attribute is 1 and edgeLabel is not in tags, it is a term (shape)
        if (
            "vertex" in data
            and data["vertex"] == "1"
            and (
                "tags" not in data
                or ("tags" in data and "edgeLabel" not in data["tags"])
            )
        ):
            term_ids.add(element)
        # if an element has an edgeLabel tag, it is a relationship (connection)
        elif "tags" in data and "edgeLabel" in data["tags"]:
            rel_val = data["value"]
            rel_id = data["parent"]
            elements[rel_id]["value"] = rel_val
            rel_ids.add(rel_id)
        # if an element has value, source and target, it is also a relationship (connection)
        elif "value" in data and "source" in data and "target" in data:
            rel_val = data["value"]
            rel_id = element
            rel_ids.add(rel_id)
    return term_ids, rel_ids
