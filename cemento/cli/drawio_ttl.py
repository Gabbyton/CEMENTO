from cemento.cli.io import (
    get_default_defaults_folder,
    get_default_prefixes_file,
    get_default_references_folder,
)
from cemento.rdf.drawio_to_turtle import convert_drawio_to_ttl


def register(subparsers):
    parser = subparsers.add_parser(
        "drawio_ttl",
        help="subcommand for converting drawio files into rdf triples in the ttl format.",
    )

    parser.add_argument(
        "input", help="the path to the input drawio diagram file.", metavar="file_path"
    )
    parser.add_argument(
        "output", help="the path to the desired output .ttl file.", metavar="file_path"
    )
    parser.add_argument(
        "-r",
        "--ontoref",
        help="the path to the folder containing the reference ontologies.",
        metavar="ref_ontologies_folder_path",
        default=get_default_references_folder(),
    )
    parser.add_argument(
        "-d",
        "--defaults",
        help="the path to the folder containing the ttl files of the default namespaces.",
        default=get_default_defaults_folder(),
        metavar="default_ontologies_folder_path",
    )
    parser.add_argument(
        "-p",
        "--prefixfile",
        help="the path to the json file containing prefixes.",
        default=get_default_prefixes_file(),
        metavar="prefix_file_path",
    )
    parser.set_defaults(_handler=run)


def run(args):
    print(f"converting {args.input} into a ttl file at {args.output}...")
    convert_drawio_to_ttl(
        args.input, args.output, args.ontoref, args.defaults, args.prefixfile
    )
