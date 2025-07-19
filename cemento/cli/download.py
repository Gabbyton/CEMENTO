import os
from pathlib import Path

import requests

from cemento.cli.constants import DEFAULT_DOWNLOADS


def make_data_dirs(download_path: str | Path) -> Path:
    download_path = Path(download_path)
    if not download_path.exists() or not download_path.is_dir():
        print("creating a download directory for default ontology reference files...")
        os.mkdir(download_path)
    return download_path


def download_default_reference_ontos(data_path: Path) -> list[str]:
    if not data_path.exists() or not data_path.is_dir():
        raise ValueError("The specified download folder does not exist!")

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


def register(subparsers):
    parser = subparsers.add_parser(
        "download",
        help="subcommand for downloading default reference ontologies.",
    )
    parser.add_argument(
        "output",
        help="the path to the desired output folder for downloaded default reference ontologies.",
        metavar="download_folder_path",
    )
    parser.set_defaults(_handler=run)


def run(args):
    print(f"downloading default reference ontologies to folder {args.output}...")
    download_path = make_data_dirs(args.output)
    download_default_reference_ontos(download_path)
