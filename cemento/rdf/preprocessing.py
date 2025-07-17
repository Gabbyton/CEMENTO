import re


def clean_literal_string(literal_term: str) -> str:
    new_literal_term = literal_term.strip().replace('"', "")
    new_literal_term = re.sub(r"@\w+", "", new_literal_term)
    new_literal_term = re.sub(r"\^\^\w+:\w+", "", new_literal_term)
    return new_literal_term


def get_term_aliases(term: str) -> list[str]:
    match = re.search(r"\(([^)]*)\)", term)
    if match:
        alt_term_string = match.group(1)
        alt_term_string = alt_term_string.split(",")
        return [term.strip() for term in alt_term_string]
    return []
