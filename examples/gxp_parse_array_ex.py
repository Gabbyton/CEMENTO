from cemento.rdf.write_array import WriteArray
from cemento.draw_io.read_diagram import ReadDiagram

# NOTE: please run script from root

if __name__ == "__main__":
    onto_path = 'test_cases/in/parse_term_test.drawio'
    read_diagram = ReadDiagram(onto_path, parse_terms=True)
    write_array = WriteArray(read_diagram)
    print(write_array.get_var_array())
    print(write_array.get_rel_array())