import re


def fst(x: tuple[any, any]) -> any:
    return x[0]


def snd(x: tuple[any, any]) -> any:
    return x[1]


def remove_term_names(term: str) -> str:
    match = re.search(r"^([^(]*)", term)
    return match.group(1).strip() if match else term


def get_abbrev_term(
    term: str, is_predicate=False, default_prefix="mds"
) -> tuple[str, str]:
    prefix = default_prefix
    abbrev_term = term
    strict_camel_case = False

    term = remove_term_names(term)
    if ":" in term:
        prefix, abbrev_term = term.split(":")

    if is_predicate:
        abbrev_term = abbrev_term.replace("_", " ")
        strict_camel_case = not strict_camel_case

    # if the term is a class, use upper camel case / Pascal case
    abbrev_term = "".join(
        [
            f"{word[0].upper()}{word[1:] if len(word) > 1 else ''}"
            for word in abbrev_term.split()
        ]
    )

    if strict_camel_case and term[0].islower():
        abbrev_term = (
            f"{abbrev_term[0].lower()}{abbrev_term[1:] if len(abbrev_term) > 1 else ''}"
        )

    return prefix, abbrev_term
