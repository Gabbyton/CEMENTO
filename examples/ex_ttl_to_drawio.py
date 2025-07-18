from cemento.rdf.turtle_to_drawio import convert_ttl_to_drawio

INPUT_PATH = ""
OUTPUT_PATH = ""

if __name__ == "__main__":
    # the horizontal tree parameter controls whether you want the default vertical tree (False) or an inverted horizontal tree (True)
    convert_ttl_to_drawio(INPUT_PATH, OUTPUT_PATH, horizontal_tree=False)
