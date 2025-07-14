from pathlib import Path

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
