from cemento.rdf.turtle_to_drawio import convert_ttl_to_drawio

INPUT_PATH = "happy-example.ttl"
OUTPUT_PATH = "sample.drawio"

if __name__ == "__main__":
    convert_ttl_to_drawio(INPUT_PATH, OUTPUT_PATH)
