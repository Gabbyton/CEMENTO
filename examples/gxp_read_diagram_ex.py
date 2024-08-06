import os
from cemento.draw_io.read_diagram import ReadDiagram

TEST_CASES_FOLDER = "test_cases/in"

if __name__ == "__main__":
    test_files = [file for file in os.scandir(TEST_CASES_FOLDER) if file.name.endswith('.drawio')] 
    for test_file in test_files:
        print(25*"===")
        print(test_file.path)
        read_diagram = ReadDiagram(test_file.path)
        print(read_diagram.get_relationships())
        print(25*'---', '\nerrors:')
        print('\n'.join([e.message for entry in read_diagram.get_errors().values() for e in entry['errors']]))
            