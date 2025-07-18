from cemento.draw_io.read_diagram import read_drawio

INPUT_PATH = ""
ONTO_FOLDER = ""  # this path points to the folder containing all the ttl files you want to reference (optional)
DEFAULTS_FOLDER = ""  # path to the folder containing default terms. It should come with the cloned repo (optional)
PREFIXES_PATH = (
    ""  # this path points to a prefixes file with custom prefix assignments (optional)
)
if __name__ == "__main__":
    graph = read_drawio(INPUT_PATH, ONTO_FOLDER, PREFIXES_PATH, DEFAULTS_FOLDER)
    print(graph.edges(data=True))