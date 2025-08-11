from cemento.rdf.rdf_to_turtle import convert_drawio_to_rdf

INPUT_PATH = "happy-example.drawio"
OUTPUT_PATH = "sample.ttl"

if __name__ == "__main__":
    convert_drawio_to_rdf(INPUT_PATH, OUTPUT_PATH)
