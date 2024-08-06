from cemento.draw_io.read_diagram import ReadDiagram

# NOTE: please run script from root

if __name__ == "__main__":
    file_path = "test_cases/in/parse_term_test.drawio" # use test case file found in test_cases dir
    # use ReadDiagram object to read a diagram from a drawio file
        # set parse_terms to True to read term defs.
        # set inverted_rank_arrows to False to read all arrows downward.
    read_diagram = ReadDiagram(file_path, parse_terms=True, inverted_rank_arrows=False)
    # get the df of all relationship triples
    # print(read_diagram.get_relationships())
    # get a dataframe of extracted term info. Only works when parse_terms is True
    terms_info = read_diagram.get_terms_info()