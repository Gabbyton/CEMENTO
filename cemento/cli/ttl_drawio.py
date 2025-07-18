from cemento.rdf.turtle_to_drawio import convert_ttl_to_drawio


def register(subparsers):
    parser = subparsers.add_parser(
        "ttl_drawio",
        help="subcommand for converting rdf triples in the ttl format to drawio diagrams.",
    )

    parser.add_argument(
        "input", help="the path to the input drawio diagram file.", metavar="file_path"
    )
    parser.add_argument(
        "output", help="the path to the desired output .ttl file.", metavar="file_path"
    )
    parser.add_argument(
        "-z",
        "--horizontal",
        help="set whether to make the tree horizontal or stay with the default vertical layout.",
        metavar="folder_path",
        default=None,
    )
    parser.set_defaults(_handler=run)


def run(args):
    print(f"converting {args.input} into a drawio diagram at {args.output}...")
    convert_ttl_to_drawio(args.input, args.output, args.horizontal)
