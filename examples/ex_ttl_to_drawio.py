from cemento.rdf.rdf_to_drawio import convert_rdf_to_drawio

INPUT_PATH = "happy-example.ttl"
OUTPUT_PATH = "sample.drawio"

if __name__ == "__main__":
    convert_rdf_to_drawio(INPUT_PATH, OUTPUT_PATH)
