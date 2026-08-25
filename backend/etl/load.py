import argparse
import sys
import time
from collections import Counter
from pathlib import Path

from sqlalchemy import text

from app.db.engine import engine
from etl import parse
from etl.genre_map import GENRE_CODE_MAP, map_genre

BATCH_SIZE = 1000
STAR_ID_PREFIX = "sn"
MAX_ID_LENGTH = 10
MAX_TITLE = 100
MAX_NAME = 100


class Report:
    def __init__(self):
        self.counts = Counter()
        self.samples = {}

    def add(self, key: str, sample: str | None = None, n: int = 1):
        self.counts[key] += n
        if sample and key not in self.samples:
            self.samples[key] = sample

    def render(self) -> str:
        width = max((len(k) for k in self.counts), default=0)
        lines = []
        for key, count in sorted(self.counts.items(), key=lambda kv: -kv[1]):
            sample = self.samples.get(key)
            suffix = f"   e.g. {sample}" if sample else ""
            lines.append(f"  {key:<{width}}  {count:>7,}{suffix}")
        return "\n".join(lines)


def _batched(rows, size=BATCH_SIZE):
    batch = []
    for row in rows:
        batch.append(row)
        if len(batch) >= size:
            yield batch
            batch = []
    if batch:
        yield batch


def _insert(conn, statement: str, rows, dry_run: bool) -> int:
    total = 0
    for batch in _batched(rows):
        if not dry_run:
            conn.execute(text(statement), batch)
        total += len(batch)
    return total


def _existing(conn):
    movie_ids = {r[0] for r in conn.execute(text("SELECT id FROM movies"))}
    movie_keys = {
        (r[0].strip().lower(), r[1], r[2].strip().lower())
        for r in conn.execute(text("SELECT title, year, director FROM movies"))
    }
    stars = {r[1].strip().lower(): r[0] for r in conn.execute(text("SELECT id, name FROM stars"))}
    genres = {r[1].strip().lower(): r[0] for r in conn.execute(text("SELECT id, name FROM genres"))}
    cast_pairs = {
        (r[0], r[1]) for r in conn.execute(text("SELECT starId, movieId FROM stars_in_movies"))
    }
    genre_pairs = {
        (r[0], r[1]) for r in conn.execute(text("SELECT genreId, movieId FROM genres_in_movies"))
    }
    return movie_ids, movie_keys, stars, genres, cast_pairs, genre_pairs


def load(data_dir: Path, dry_run: bool) -> Report:
    report = Report()
    started = time.perf_counter()

    with engine.connect() as conn:
        (
            movie_ids,
            movie_keys,
            star_ids_by_name,
            genre_ids_by_name,
            existing_cast_pairs,
            existing_genre_pairs,
        ) = _existing(conn)
        conn.rollback()
        report.add("existing movies in database", n=len(movie_ids))
        report.add("existing stars in database", n=len(star_ids_by_name))

        new_movies, new_genre_links = [], []
        seen_fids = set()
        pending_genres = {}

        for film in parse.iter_films(data_dir / "mains243.xml"):
            fid, title, year = film["fid"], film["title"], film["year"]
            if not fid:
                report.add("film skipped: no fid")
                continue
            if len(fid) > MAX_ID_LENGTH:
                report.add("film skipped: fid too long", fid)
                continue
            if not title:
                report.add("film skipped: no title", fid)
                continue
            if year is None:
                report.add("film skipped: missing or invalid year", f"{fid} {title!r}")
                continue
            if fid in seen_fids:
                report.add("film skipped: duplicate fid in source", fid)
                continue
            seen_fids.add(fid)
            if fid in movie_ids:
                report.add("film skipped: id already in database", fid)
                continue
            key = (title.strip().lower(), year, film["director"].strip().lower())
            if key in movie_keys:
                report.add("film skipped: same title/year/director already present", title)
                continue
            movie_keys.add(key)

            if film["flagged"]:
                report.add("film loaded despite <error> tag", fid)

            new_movies.append({
                "id": fid,
                "title": title[:MAX_TITLE],
                "year": year,
                "director": (film["director"] or "Unknown")[:MAX_TITLE],
            })
            movie_ids.add(fid)

            for raw in film["genres"]:
                name = map_genre(raw)
                if not name:
                    continue
                if raw.strip().lower() in {"", None}:
                    continue
                if name.lower() not in genre_ids_by_name:
                    pending_genres.setdefault(name.lower(), name)
                new_genre_links.append((fid, name.lower()))
                known = raw.strip().lower() in GENRE_CODE_MAP
                report.add(
                    "genre code mapped" if known else "genre code passed through unmapped",
                    raw,
                )

        report.add("movies to insert", n=len(new_movies))

        with conn.begin():
            _insert(
                conn,
                "INSERT INTO movies (id, title, year, director) "
                "VALUES (:id, :title, :year, :director)",
                new_movies,
                dry_run,
            )

            for offset, (lower, display) in enumerate(pending_genres.items(), start=1):
                if dry_run:
                    genre_ids_by_name[lower] = -offset
                    continue
                result = conn.execute(
                    text("INSERT INTO genres (name) VALUES (:name)"), {"name": display}
                )
                genre_ids_by_name[lower] = result.lastrowid
            report.add("new genres created", n=len(pending_genres))

            genre_rows, seen_pairs = [], set(existing_genre_pairs)
            for fid, lower in new_genre_links:
                genre_id = genre_ids_by_name.get(lower)
                if genre_id is None or (fid, genre_id) in seen_pairs:
                    continue
                seen_pairs.add((fid, genre_id))
                genre_rows.append({"genre_id": genre_id, "movie_id": fid})
            _insert(
                conn,
                "INSERT INTO genres_in_movies (genreId, movieId) VALUES (:genre_id, :movie_id)",
                genre_rows,
                dry_run,
            )
            report.add("genre links inserted", n=len(genre_rows))

        next_star = 1
        new_stars = []

        def allocate(name: str) -> str:
            nonlocal next_star
            star_id = f"{STAR_ID_PREFIX}{next_star:08d}"
            next_star += 1
            star_ids_by_name[name.strip().lower()] = star_id
            return star_id

        for actor in parse.iter_actors(data_dir / "actors63.xml"):
            name = actor["name"]
            if not name:
                report.add("actor skipped: no stagename")
                continue
            key = name.strip().lower()
            if key in star_ids_by_name:
                report.add("actor skipped: name already in database", name)
                continue
            new_stars.append({
                "id": allocate(name),
                "name": name[:MAX_NAME],
                "birth_year": actor["birth_year"],
            })
            if actor["birth_year"] is None:
                report.add("actor loaded with no birth year", name)

        cast_pairs, synthesized = [], []
        seen_cast = set(existing_cast_pairs)
        for entry in parse.iter_casts(data_dir / "casts124.xml"):
            fid, name = entry["fid"], entry["name"]
            if not fid or not name:
                report.add("cast row skipped: missing film or actor")
                continue
            if fid not in movie_ids:
                report.add("cast row skipped: references unknown film", fid)
                continue
            key = name.strip().lower()
            star_id = star_ids_by_name.get(key)
            if star_id is None:
                star_id = allocate(name)
                synthesized.append({"id": star_id, "name": name[:MAX_NAME], "birth_year": None})
                report.add("star synthesized from a cast reference", name)
            if (star_id, fid) in seen_cast:
                report.add(
                    "cast row skipped: link already present"
                    if (star_id, fid) in existing_cast_pairs
                    else "cast row skipped: duplicate pair in source"
                )
                continue
            seen_cast.add((star_id, fid))
            cast_pairs.append({"star_id": star_id, "movie_id": fid})

        with conn.begin():
            _insert(
                conn,
                "INSERT INTO stars (id, name, birthYear) VALUES (:id, :name, :birth_year)",
                new_stars + synthesized,
                dry_run,
            )
            report.add("stars inserted", n=len(new_stars) + len(synthesized))
            _insert(
                conn,
                "INSERT INTO stars_in_movies (starId, movieId) VALUES (:star_id, :movie_id)",
                cast_pairs,
                dry_run,
            )
            report.add("cast links inserted", n=len(cast_pairs))

    elapsed = time.perf_counter() - started
    written = (
        report.counts["movies to insert"]
        + report.counts["stars inserted"]
        + report.counts["cast links inserted"]
        + report.counts["genre links inserted"]
    )
    report.add("_elapsed_ms", n=int(elapsed * 1000))
    report.add("_rows_per_second", n=int(written / elapsed) if elapsed else 0)
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="python -m etl.load")
    parser.add_argument("data_dir", type=Path, help="directory holding the three XML files")
    parser.add_argument("--dry-run", action="store_true", help="parse and report, write nothing")
    args = parser.parse_args(argv)

    required = ["mains243.xml", "actors63.xml", "casts124.xml"]
    missing = [name for name in required if not (args.data_dir / name).exists()]
    if missing:
        print(f"missing input files in {args.data_dir}: {', '.join(missing)}", file=sys.stderr)
        return 2

    report = load(args.data_dir, args.dry_run)
    elapsed_ms = report.counts.pop("_elapsed_ms", 0)
    rate = report.counts.pop("_rows_per_second", 0)

    print(f"\n{'DRY RUN, nothing written' if args.dry_run else 'LOAD COMPLETE'}")
    print(report.render())
    print(f"\n  elapsed {elapsed_ms / 1000:.1f}s   {rate:,} rows/sec")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
