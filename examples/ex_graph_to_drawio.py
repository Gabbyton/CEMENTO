from cemento.draw_io.read_diagram import read_drawio
from cemento.draw_io.write_diagram import draw_tree

INPUT_PATH = ""
OUTPUT_PATH = ""

if __name__ == "__main__":
    graph = read_drawio(INPUT_PATH)
    draw_tree(graph, OUTPUT_PATH, horizontal_tree=False)