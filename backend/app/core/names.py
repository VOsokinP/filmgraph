def normalize_name(value: str) -> str:
    """Collapse whitespace, and title-case only when the input carries no case information.

    An entirely lower or entirely upper input says nothing about how the person capitalises their
    name, so a convention can be imposed safely. Mixed case is left alone, which keeps McDonald and
    O'Brien intact at the cost of letting BrAdY through: the two are indistinguishable by shape.
    """
    collapsed = " ".join(value.split())
    if collapsed.islower() or collapsed.isupper():
        return collapsed.title()
    return collapsed
