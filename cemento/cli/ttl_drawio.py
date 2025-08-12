from cemento.rdf.rdf_to_drawio import convert_rdf_to_drawio
from cemento.utils.constants import RDFFormat
from cemento.utils.io import (
    get_default_defaults_folder,
    get_default_prefixes_file,
    get_default_references_folder,
)


def register(subparsers):
    parser = subparsers.add_parser(
        "ttl_drawio",
        help="subcommand for converting rdf triples in the turtle format into drawio diagrams.",
    )

    parser.add_argument(
        "input",
        help="the path to the input drawio diagram file.",
        metavar="input_file_path",
    )
    parser.add_argument(
        "output",
        help="the path to the desired output file.",
        metavar="output_file_path",
    )
    parser.add_argument(
        "-f",
        "--format",
        choices=RDFFormat.get_valid_rdf_formats(),
        default=None,
        metavar="file_format",
        help="the format which rdflib will use to parse the file (default: turtle)",
    )
    parser.add_argument(
        "-hz",
        "--horizontal-graph",
        help="set whether to make the tree horizontal or stay with the default vertical layout.",
        action="store_true",
    )
    parser.add_argument(
        "-co",
        "--classes-only",
        help="set whether to just display classes and instances (taxonomy tree).",
        action="store_true",
    )
    parser.add_argument(
        "-db",
        "--demarcate-boxes",
        help="set whether to divide the tree into A-Boxes and T-Boxes.",
        action="store_true",
    )
    parser.add_argument(
        "-r",
        "--onto-ref-folder-path",
        help="the path to the folder containing the reference ontologies.",
        metavar="ref_ontologies_folder_path",
        default=get_default_references_folder(),
    )
    parser.add_argument(
        "-d",
        "--defaults-folder-path",
        help="the path to the folder containing the ttl files of the default namespaces.",
        default=get_default_defaults_folder(),
        metavar="default_ontologies_folder_path",
    )
    parser.add_argument(
        "-p",
        "--prefix-file-path",
        help="the path to the json file containing prefixes.",
        default=get_default_prefixes_file(),
        metavar="prefix_file_path",
    )
    parser.add_argument(
        "-ul",
        "--unique-literals",
        help="set whether to to append a unique id to each encountered literal term. Affects labels, definitions and any other literal values.",
        action="store_true",
    )
    parser.set_defaults(_handler=run)


def run(args):
    print(f"converting {args.input} into a drawio diagram at {args.output}...")
    convert_rdf_to_drawio(
        args.input,
        args.output,
        file_format="turtle",
        horizontal_tree=args.horizontal_graph,
        classes_only=args.classes_only,
        demarcate_boxes=args.demarcate_boxes,
        onto_ref_folder=args.onto_ref_folder_path,
        defaults_folder=args.defaults_folder_path,
        prefixes_path=args.prefix_file_path,
        set_unique_literals=args.unique_literals,
    )
