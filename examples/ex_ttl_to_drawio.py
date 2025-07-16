from cemento.rdf.turtle_to_drawio import convert_ttl_to_drawio

INPUT_PATH = ""
OUTPUT_PATH = ""

if __name__ == "__main__":
    convert_ttl_to_drawio(INPUT_PATH, OUTPUT_PATH, horizontal_tree=False)