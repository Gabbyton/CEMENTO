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
        "-hz",
        "--horizontal-graph",
        help="set whether to make the tree horizontal or stay with the default vertical layout.",
        metavar="is_horizontal",
        type=bool,
        default=False,
    )
    parser.add_argument(
        "-dct",
        "--dont-check-turtle",
        help="set whether to stop evaluating turtle file for potential errors prior to conversion. Computation will be marginally shorter.",
        action="store_false",
    )
    parser.add_argument(
        "-nul",
        "--no-unique-literals",
        help="set whether to to append a unique id to each encountered literal term. Affects labels, definitions and any other literal values.",
        action="store_false",
    )
    parser.set_defaults(_handler=run)


def run(args):
    print(f"converting {args.input} into a drawio diagram at {args.output}...")
    convert_ttl_to_drawio(
        args.input,
        args.output,
        args.horizontal_graph,
        check_ttl_validity=args.dont_check_turtle,
        set_unique_literals=args.no_unique_literals,
    )
