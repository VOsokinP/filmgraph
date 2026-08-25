from collections.abc import Iterator
from pathlib import Path

from lxml import etree

MIN_YEAR = 1878
MAX_YEAR = 2030


def _text(element, path: str) -> str:
    found = element.find(path)
    if found is None or found.text is None:
        return ""
    return found.text.strip()


def _stream(path: Path, tag: str):
    context = etree.iterparse(
        str(path),
        tag=tag,
        recover=True,
        resolve_entities=False,
        load_dtd=False,
        no_network=True,
    )
    for _, element in context:
        yield element
        element.clear()
        while element.getprevious() is not None:
            del element.getparent()[0]


def parse_year(raw: str) -> int | None:
    digits = raw.strip()[:4]
    if not digits.isdigit():
        return None
    value = int(digits)
    if not MIN_YEAR <= value <= MAX_YEAR:
        return None
    return value


def iter_films(path: Path) -> Iterator[dict]:
    for block in _stream(path, "directorfilms"):
        director = _text(block, "director/dirname")
        for film in block.iterfind("films/film"):
            year_element = film.find("year")
            raw_year = (year_element.text or "") if year_element is not None else ""
            yield {
                "fid": _text(film, "fid"),
                "title": _text(film, "t"),
                "year": parse_year(raw_year),
                "director": director,
                "genres": [c.text.strip() for c in film.iterfind("cats/cat") if c.text],
                "flagged": film.find("error") is not None,
            }


def iter_actors(path: Path) -> Iterator[dict]:
    for actor in _stream(path, "actor"):
        yield {
            "name": _text(actor, "stagename"),
            "birth_year": parse_year(_text(actor, "dob")),
        }


def iter_casts(path: Path) -> Iterator[dict]:
    for entry in _stream(path, "m"):
        yield {
            "fid": _text(entry, "f"),
            "name": _text(entry, "a"),
        }
