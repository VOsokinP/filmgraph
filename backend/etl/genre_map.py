GENRE_CODE_MAP = {
    "actn": "Action",
    "advt": "Adventure",
    "anim": "Animation",
    "biop": "Biography",
    "comd": "Comedy",
    "crim": "Crime",
    "docu": "Documentary",
    "dram": "Drama",
    "faml": "Family",
    "fant": "Fantasy",
    "hist": "History",
    "horr": "Horror",
    "musc": "Musical",
    "myst": "Mystery",
    "noir": "Crime",
    "romt": "Romance",
    "scfi": "Sci-Fi",
    "sptr": "Sport",
    "susp": "Thriller",
    "thlr": "Thriller",
    "war": "War",
    "west": "Western",
}


def map_genre(code: str) -> str | None:
    cleaned = (code or "").strip()
    if not cleaned:
        return None
    mapped = GENRE_CODE_MAP.get(cleaned.lower())
    if mapped:
        return mapped
    return cleaned[:32]
