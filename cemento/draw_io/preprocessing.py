from collections.abc import Iterable

from bs4 import BeautifulSoup

from cemento.draw_io.constants import NxEdge


def remove_predicate_quotes(edges: Iterable[NxEdge]) -> Iterable[NxEdge]:
    return map(lambda edge: (edge.subj, edge.obj, remove_quotes(edge.pred)), edges)


def clean_term(term: str) -> str:
    soup = BeautifulSoup(term, "html.parser")
    term_text = soup.get_text(separator="", strip=True)
    return term_text


def fst(x: tuple[any, any]) -> any:
    return x[0]


def snd(x: tuple[any, any]) -> any:
    return x[1]


def remove_quotes(input_str: str) -> str:
    return input_str.replace('"', "").strip()
