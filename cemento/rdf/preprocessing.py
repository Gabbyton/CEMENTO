import re

from rdflib import Literal
from rdflib.namespace import split_uri


def clean_literal_string(literal_term: str) -> str:
    new_literal_term = literal_term.strip().replace('"', "")
    new_literal_term = re.sub(r"@\w+", "", new_literal_term)
    new_literal_term = re.sub(r"\^\^\w+:\w+", "", new_literal_term)
    return new_literal_term

# TODO: set supppression key as constant
def remove_suppression_key(term: str) -> str:
    return term.replace("*", "")


def get_term_aliases(term: str) -> list[str]:
    match = re.search(r"\(([^)]*)\)", term)
    if match:
        alt_term_string = match.group(1)
        alt_term_string = alt_term_string.split(",")
        return [term.strip() for term in alt_term_string]
    return []


def format_literal(literal: Literal) -> str:
    literal_str = f'"{literal.value}"'
    lang_str = (
        f"@{literal.language}"
        if hasattr(literal, "language") and literal.language
        else ""
    )

    datatype_str = ""
    if hasattr(literal, "datatype") and literal.datatype:
        datatype = literal.datatype
        _, abbrev = split_uri(datatype)
        datatype_str = f"^^xsd:{abbrev}"

    return f"{literal_str}{lang_str}{datatype_str}"
