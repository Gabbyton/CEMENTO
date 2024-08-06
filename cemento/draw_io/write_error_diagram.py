from os import path
from defusedxml import ElementTree as ET

class WriteErrorDiagram:

    def __init__(self, read_diagram, print_id_width=25, separator_width=75):
        self._read_diagram = read_diagram
        self._print_id_width = print_id_width
        self._separator_width = separator_width

    def add_error_highlighting(self):
        tree = ET.parse(self.get_read_diagram().get_file_path())
        root = tree.getroot()

        errors = self.get_read_diagram().get_errors()

        for elem_id, _ in errors.items():
            for element in root.findall(f".//*[@id='{elem_id}']"):
                # read and strip element styles and save as pairs
                styles = list(map(lambda x: x.strip().split('='), element.get('style').strip().split(';')))
                styles = [style for style in styles if style[0]]

                # convert style pairs into dictionary and add/modify strokeColor entry
                style_dict = dict()
                for style in styles:
                    style_dict[style[0]] = '' if len(style) < 2 else  style[1]
                style_dict['strokeColor'] = "#ff0000"
            
                # save the new styles and set to element
                new_style = [f"{key}={value}" if value else f"{key}" for key, value in style_dict.items()]
                new_style = ';'.join(new_style)

                # set new style to the element attribute
                element.set('style', new_style)

        # save the file as a checked version of the original
        file_path, file_name = path.split(self.get_read_diagram().get_file_path())
        file_name, file_ext = file_name.split('.')
        new_file_name = f"{file_name}-errorCheck.{file_ext}"
        tree.write(path.join(file_path, new_file_name))

    def get_read_diagram(self):
        return self._read_diagram

    def _get_print_id_width(self):
        return self._print_id_width

    def _get_separator_width(self):
        return self._separator_width