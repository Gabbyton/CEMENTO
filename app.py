import argparse
from os import path

from cemento.draw_io.read_diagram import ReadDiagram
from cemento.draw_io.write_error_diagram import WriteErrorDiagram
from cemento.rdf.write_array import WriteArray

SEP_WIDTH = 75

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Convert draw.io diagrams into ontologies."
    )
    parser.add_argument(
        "-p",
        "--path",
        dest="file_path",
        required=True,
        help="absolute file path to diagram input. Must be a draw.io file.",
    )
    parser.add_argument(
        "-w",
        "--write_error_diagram",
        dest="should_write_error_diagram",
        default=False,
        action="store_true",
        help="whether or not to draw a separate diagram highlighting user errors.",
    )
    parser.add_argument(
        "-e",
        "--check_errors",
        default=True,
        dest="should_check_errors",
        action="store_true",
        help="whether or not to check for errors and print. True when write_error_diagram is true.",
    )
    parser.add_argument(
        "-d",
        "--do_parse",
        default=False,
        dest="do_parse",
        action="store_true",
        help="whether or not to parse the diagram as if it contained explicit names, definitions, etc.",
    )
    parser.add_argument(
        "-t",
        "--write_triples",
        default=False,
        dest="write_triples",
        action="store_true",
        help="whether or not to write an excel sheet of the triples",
    )
    parser.add_argument(
        "-f",
        "--finalize",
        dest="finalize",
        action="store_true",
        help="whether or not to finalize the diagram and generate a RDF ontology from the file. Only use this when the diagram is ready to be exported.",
    )
    args = parser.parse_args()

    should_check_errors = args.should_check_errors or args.should_write_error_diagram
    read_diagram = ReadDiagram(
        args.file_path, do_check_errors=should_check_errors, parse_terms=args.do_parse
    )

    if args.should_write_error_diagram:
        write_error_diagram = WriteErrorDiagram(read_diagram)
        write_error_diagram.add_error_highlighting()

    if should_check_errors:
        read_diagram.print_errors(sep_width=SEP_WIDTH)

    if args.do_parse:
        print(SEP_WIDTH * "=")
        print("extracted term information:", end=2 * "\n")
        term_info = read_diagram.get_terms_info()
        if term_info.empty:
            print("no term info extracted.")
        else:
            print(term_info)

    if args.write_triples:
        rels_df = read_diagram.get_relationships()
        folder_path, file_name = path.split(read_diagram.get_file_path())
        file_name, _ = file_name.split(".")

        print(SEP_WIDTH * "=")
        print("dataframe preview:", end=2 * "\n")
        if rels_df.empty:
            print("no triples generated from file.")
        else:
            print(rels_df)
            new_file_path = path.join(folder_path, f"{file_name}-triples.csv")
            rels_df.to_csv(new_file_path)
            print(f"saved to -> {new_file_path}")

        if args.do_parse and not term_info.empty:
            term_info_file_path = path.join(folder_path, f"{file_name}-term_info.csv")
            term_info.to_csv(term_info_file_path)

    if args.finalize:
        write_array = WriteArray(read_diagram)
        print(write_array.get_var_array())
        print(write_array.get_rel_array())