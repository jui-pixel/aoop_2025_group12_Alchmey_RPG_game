# src/utils/elements.py
ELEMENTS = [
    "untyped",
    "metal",
    "wood",
    "water",
    "fire",
    "earth",
    "wind",
    "electric",
    "ice",
    "light",
    "dark",
]

WEAKTABLE = [
    ("metal", "wood"),
    ("wood", "water"),
    ("wood", "wind"),
    ("water", "fire"),
    ("fire", "earth"),
    ("fire", "ice"),
    ("earth", "metal"),
    ("earth", "electric"),
    ("wind", "fire"),
    ("electric", "water"),
    ("ice", "wood"),
    ("light", "dark"),
    ("dark", "light"),
]