import pytest

from etl import parse
from etl.genre_map import map_genre

MAINS = """<?xml version='1.0' encoding='ISO-8859-1'?>
<movies>
  <directorfilms>
    <director><dirid>H</dirid><dirname>Hitchcock</dirname></director>
    <films>
      <film><fid>H7</fid><t>The Pleasure Garden</t>
        <year>1925<released>1927</released></year>
        <cats><cat>Dram</cat><cat>susp</cat></cats></film>
      <film><fid>H3</fid><t>Woman to Woman</t><year>1922</year>
        <cats><cat>Dram</cat></cats><error>same(GCt27)</error></film>
      <film><fid>H99</fid><t>No Year</t><year>19x6</year><cats/></film>
    </films>
  </directorfilms>
</movies>
"""

ACTORS = """<?xml version="1.0"?>
<actors>
  <actor><stagename>Bud Abbott</stagename><dob>1895</dob></actor>
  <actor><stagename>Victoria Abril</stagename><dob></dob></actor>
  <actor><stagename></stagename><dob>1950</dob></actor>
</actors>
"""

CASTS = """<?xml version="1.0"?>
<casts>
  <dirfilms><dirid>AA</dirid><filmc>
    <m><f>AA13</f><t>Pygmalion</t><a>Leslie Howard</a></m>
    <m><f>AA13</f><t>Pygmalion</t><a></a></m>
  </filmc></dirfilms>
</casts>
"""


def write(tmp_path, name, body):
    path = tmp_path / name
    path.write_text(body, encoding="utf-8")
    return path


@pytest.mark.parametrize(
    "raw,expected",
    [("1925", 1925), ("1925 ", 1925), ("19x6", None), ("", None), ("196", None), ("2999", None)],
)
def test_parse_year(raw, expected):
    assert parse.parse_year(raw) == expected


def test_mixed_content_year_yields_the_release_year(tmp_path):
    """<year>1925<released>1927</released></year> must yield 1925.

    Two things defend this: reading .text rather than the concatenated text, and parse_year
    truncating to four characters. Either alone is sufficient, so both are asserted directly.
    """
    films = list(parse.iter_films(write(tmp_path, "mains243.xml", MAINS)))
    assert films[0]["year"] == 1925
    assert parse.parse_year("19251927") == 1925


def test_films_inherit_the_director_from_the_enclosing_block(tmp_path):
    films = list(parse.iter_films(write(tmp_path, "mains243.xml", MAINS)))
    assert {f["director"] for f in films} == {"Hitchcock"}


def test_films_expose_the_error_flag_and_genres(tmp_path):
    films = {f["fid"]: f for f in parse.iter_films(write(tmp_path, "mains243.xml", MAINS))}
    assert films["H3"]["flagged"] is True
    assert films["H7"]["flagged"] is False
    assert films["H7"]["genres"] == ["Dram", "susp"]
    assert films["H99"]["year"] is None


def test_iter_actors_reports_missing_values_as_none(tmp_path):
    actors = list(parse.iter_actors(write(tmp_path, "actors63.xml", ACTORS)))
    assert actors[0] == {"name": "Bud Abbott", "birth_year": 1895}
    assert actors[1]["birth_year"] is None
    assert actors[2]["name"] == ""


def test_iter_casts_yields_film_and_actor(tmp_path):
    casts = list(parse.iter_casts(write(tmp_path, "casts124.xml", CASTS)))
    assert casts[0] == {"fid": "AA13", "name": "Leslie Howard"}
    assert casts[1]["name"] == ""


@pytest.mark.parametrize(
    "code,expected",
    [
        ("Dram", "Drama"),
        ("susp", "Thriller"),
        ("SCFI", "Sci-Fi"),
        ("Cart", "Cart"),
        ("", None),
        ("  ", None),
    ],
)
def test_map_genre(code, expected):
    assert map_genre(code) == expected


def test_map_genre_truncates_to_the_column_width():
    assert len(map_genre("x" * 60)) == 32
