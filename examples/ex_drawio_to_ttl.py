from cemento.rdf.drawio_to_turtle import convert_drawio_to_ttl

INPUT_PATH = ""
OUTPUT_PATH = ""
ONTO_PATH = ""  # this path points to the folder containing all the ttl files you want to reference (optional)
PREFIXES_PATH = (
    ""  # this path points to a prefixes file with custom prefix assignments (optional)
)
DEFAULTS_FOLDER = ""  # path to the folder containing default terms. It should come with the cloned repo (optional)

if __name__ == "__main__":
    convert_drawio_to_ttl(
        INPUT_PATH, OUTPUT_PATH, ONTO_PATH, DEFAULTS_FOLDER, PREFIXES_PATH
    )
