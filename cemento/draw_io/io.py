import importlib.resources as pkg_resources
import os
from pathlib import Path
from string import Template

from defusedxml import ElementTree as ET


def get_diagram_headers(file_path: str | Path) -> dict[str, str]:
    # retrieve diagram headers
    tree = ET.parse(file_path)
    root = tree.getroot()
    graph_model_tag = next(root.iter("mxGraphModel"))
    diagram_tag = next(root.iter("diagram"))
    diagram_headers = {
        "modify_date": (
            root.attrib["modified"] if "modified" in root.attrib else "July 1, 2024"
        ),
        "diagram_name": diagram_tag.attrib["name"],
        "diagram_id": diagram_tag.attrib["id"],
        "grid_dx": graph_model_tag.attrib["dx"] if "dx" in graph_model_tag else 0,
        "grid_dy": graph_model_tag.attrib["dy"] if "dy" in graph_model_tag else 0,
        "grid_size": int(graph_model_tag.attrib["gridSize"]),
        "page_width": int(graph_model_tag.attrib["pageWidth"]),
        "page_height": int(graph_model_tag.attrib["pageHeight"]),
    }

    return diagram_headers


def get_template_files() -> dict[str, str | Path]:
    current_file_folder = Path(__file__)
    # retrieve the template folder from the grandparent directory
    template_path = current_file_folder.parent.parent.parent / "templates"

    if not template_path.exists():
        template_path = pkg_resources.files("cemento").joinpath("templates")

    template_files = [
        Path(file) for file in os.scandir(template_path) if file.name.endswith(".xml")
    ]
    template_dict = dict()
    for file in template_files:
        with open(file, "r") as f:
            template = Template(f.read())
            template_dict[file.stem] = template
    return template_dict
