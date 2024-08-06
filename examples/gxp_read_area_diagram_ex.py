from cemento.draw_io.read_area_diagram import ReadAreaDiagram

# NOTE: please run script from root

if __name__ == "__main__":
    exp = ReadAreaDiagram("test_cases/in/read_area_diagram.drawio")
    # retrieves relationships as usual
    print(exp.get_relationships())
    # retrieve area designations (uses ids of elements)
    print(exp.get_area_designations(parse_values=True))