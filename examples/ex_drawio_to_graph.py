from cemento.draw_io.read_diagram import read_drawio

INPUT_PATH = "happy-example.drawio"

if __name__ == "__main__":
    graph = read_drawio(INPUT_PATH)
    print(graph.edges(data=True))