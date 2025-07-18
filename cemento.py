import argparse
import os
from pathlib import Path

import requests

from cemento.rdf.constants import DEFAULT_DOWNLOADS
from cemento.rdf.drawio_to_turtle import convert_drawio_to_ttl


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

    parser = argparse.ArgumentParser()
    parser.add_argument("input", help="the path to the input drawio diagram file.")
    parser.add_argument("output", help="the path to the desired output .ttl file.")
    parser.add_argument(
        "-nd",
        "--nodownloads",
        help="turn off automatic downloads to populate ontology references.",
    )
    parser.add_argument(
        "-r",
        "--ontoref",
        help="the path to the folder containing the reference ontologies.",
        default=data_path,
    )
    parser.add_argument(
        "-d",
        "--defaults",
        help="the path to the folder containing the ttl files of the default namespaces.",
        default=defaults_path,
    )
    parser.add_argument(
        "-p",
        "--prefixfile",
        help="the path to the json file containing prefixes.",
        default=prefixes_path,
    )
    args = parser.parse_args()
    if not args.nodownloads:
        make_data_dirs(data_path)
        download_defaults(data_path)

    print(f"converting {args.input} into a ttl file at {args.output}...")
    convert_drawio_to_ttl(
        args.input, args.output, args.ontoref, args.defaults, args.prefixfile
    )
