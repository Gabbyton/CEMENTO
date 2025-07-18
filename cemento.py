import argparse
import os
from pathlib import Path

import requests

import cemento.cli.drawio_ttl as drawio_ttl
import cemento.cli.ttl_drawio as ttl_drawio
from cemento.rdf.constants import DEFAULT_DOWNLOADS


def make_data_dirs(data_path: Path) -> Path:
    if not data_path.exists() or not data_path.is_dir():
        print("creating a data directory for default ontology reference files...")
        os.mkdir(data_path)
    return data_path


# TODO: determine more appropriate way to handle defaults
def download_defaults(data_path: Path) -> list[str]:
    if not data_path.exists() or not data_path.is_dir():
        raise ValueError("The specified folder does not exist!")

    download_files = []
    for key, url in DEFAULT_DOWNLOADS.items():
        default_file = data_path / f"{key}.ttl"
        try:
            if not default_file.exists():
                print(f"attempting to download {default_file.name} from {url}...")
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                default_file.write_bytes(response.content)
                download_files.append(str(default_file))
        except (requests.exceptions.Timeout, requests.exceptions.RequestException):
            print(f"download failed for {default_file.name}....")
    return download_files


if __name__ == "__main__":
    # get the defaults folder path
    defaults_path = Path(__file__).parent / "defaults"
    prefixes_path = Path(__file__).parent / "examples" / "prefixes.json"
    data_path = Path(__file__).parent / "data"

    parser = argparse.ArgumentParser(prog="cemento")

    parser.add_argument(
        "-nd",
        "--nodownloads",
        help="turn off automatic downloads to populate ontology reference folder.",
        metavar="",
    )

    subparsers = parser.add_subparsers(
        dest="cemento", metavar="", title="Available functions"
    )
    subparsers.required = True

    drawio_ttl.register(subparsers)
    ttl_drawio.register(subparsers)

    args = parser.parse_args()

    if hasattr(args, "_handler"):
        args._handler(args)

    if not args.nodownloads:
        make_data_dirs(data_path)
        download_defaults(data_path)
