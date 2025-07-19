import argparse
import sys

import cemento.cli.download as download
import cemento.cli.drawio_ttl as drawio_ttl
import cemento.cli.ttl_drawio as ttl_drawio
from cemento.cli.constants import header

def main():
    parser = argparse.ArgumentParser(prog="cemento", description=header, formatter_class=argparse.RawDescriptionHelpFormatter)

    subparsers = parser.add_subparsers(
        dest="cemento", metavar="subcommand", title="Available functions", required=True
    )
    subparsers.required = True

    drawio_ttl.register(subparsers)
    ttl_drawio.register(subparsers)
    download.register(subparsers)

    if len(sys.argv) <= 1:
        parser.print_help()
        sys.exit(1)

    args = parser.parse_args()

    if hasattr(args, "_handler"):
        args._handler(args)


if __name__ == "__main__":
    main()
