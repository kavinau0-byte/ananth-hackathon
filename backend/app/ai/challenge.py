"""Cryptographically random spoken challenge generator for Break-Glass Voice Gate."""

from __future__ import annotations

import secrets

# 220 common, easy-to-pronounce English words (distinct, lowercase).
WORD_LIST: tuple[str, ...] = (
    "acorn", "anchor", "apricot", "archway", "arrow", "aspen", "autumn", "badge",
    "bakery", "balloon", "bamboo", "banjo", "banner", "barley", "barrel", "basket",
    "beacon", "beaver", "beehive", "berry", "bicycle", "birch", "blanket", "blossom",
    "bonfire", "boulder", "branch", "breeze", "bridge", "brook", "bucket", "buffalo",
    "builder", "butter", "button", "cabin", "cactus", "calendar", "camera", "campfire",
    "canal", "candle", "canyon", "captain", "caravan", "carpet", "carrot", "castle",
    "cedar", "cellar", "chalk", "channel", "cherry", "chestnut", "chimney", "cider",
    "cinnamon", "circle", "citadel", "clover", "coastal", "cobbler", "coffee", "collar",
    "comet", "compass", "copper", "coral", "cottage", "cotton", "courtyard", "cradle",
    "crayon", "cricket", "crystal", "cupboard", "curtain", "cushion", "cypress", "dagger",
    "daisy", "dancer", "daybreak", "delta", "desert", "diamond", "dolphin", "domino",
    "donkey", "doorway", "dragon", "drawer", "driftwood", "drizzle", "drumbeat", "eagle",
    "eclipse", "elmwood", "emerald", "engine", "envelope", "evening", "eyebrow", "fabric",
    "falcon", "farmer", "feather", "fennel", "ferry", "festival", "fiddle", "field",
    "figtree", "firefly", "flannel", "flicker", "flower", "flute", "foothill", "forest",
    "fossil", "fountain", "foxglove", "freckle", "frost", "furnace", "galaxy", "gallery",
    "garden", "garland", "gateway", "gazelle", "geyser", "ginger", "glacier", "glider",
    "goblet", "goldfish", "gopher", "granite", "gravel", "greenhouse", "griddle", "griffin",
    "grove", "guitar", "halibut", "hammer", "hammock", "harbor", "harvest", "hatchet",
    "hawthorn", "hazelnut", "heather", "hedgehog", "helmet", "hemlock", "heron", "hickory",
    "highway", "hillside", "hollow", "honey", "horizon", "hornet", "hummingbird", "icicle",
    "iguana", "indigo", "inkwell", "island", "ivory", "jacket", "jasmine", "jigsaw",
    "journal", "journey", "juniper", "kayak", "kennel", "kernel", "kettle", "keyhole",
    "kindling", "kitchen", "kitten", "knapsack", "ladder", "lagoon", "lantern", "larch",
    "larkspur", "lattice", "laurel", "lavender", "leather", "lemon", "leopard", "library",
    "lichen", "lighthouse", "lilac", "limestone", "linden", "linnet", "lizard", "lobster",
    "locket", "locust", "lumber", "magnet", "magpie", "mahogany", "mailbox", "mallard",
    "mango", "mantel", "maple", "marble", "marigold", "marina", "market", "marmot",
)

_DIGIT_WORDS: tuple[str, ...] = (
    "zero", "one", "two", "three", "four",
    "five", "six", "seven", "eight", "nine",
)


def _pick_distinct_words(count: int) -> list[str]:
    """Select `count` distinct words using the secrets CSPRNG."""
    pool = list(WORD_LIST)
    chosen: list[str] = []
    for _ in range(count):
        idx = secrets.randbelow(len(pool))
        chosen.append(pool.pop(idx))
    return chosen


def generate_challenge() -> str:
    """Return a spoken challenge phrase (~4-6s) with 3 distinct words and 2 digits."""
    w1, w2, w3 = _pick_distinct_words(3)
    d1 = secrets.randbelow(10)
    d2 = secrets.randbelow(10)
    return (
        "I am requesting break-glass approval right now. "
        f"My verification words are {w1}, {w2}, and {w3}, "
        f"followed by the digits {d1} ({_DIGIT_WORDS[d1]}) and {d2} ({_DIGIT_WORDS[d2]})."
    )
