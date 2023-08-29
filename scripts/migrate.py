#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""migrates from v1 to v2"""


import json
from warnings import filterwarnings as filter_warnings


def t(data: str) -> str:
    return data[:196] + ("" if len(data) < 196 else " ...")


def main() -> int:
    """entry / main function"""

    with open("a.json", "r") as f:  # old v1 blog
        posts = json.load(f)["blogs"]

    with open("blog.json", "r") as f:
        blog = json.load(f)

    for slug, post in posts.items():
        blog["posts"][slug] = {
            "title": post["title"],
            "description": t(post["content"][:196]),
            "content": post["content"],
            "keywords": post["keywords"].split(),
            "created": post["time"],
        }

    with open("blog.json", "w") as f:
        json.dump(blog, f, indent=4)

    return 0


if __name__ == "__main__":
    assert main.__annotations__.get("return") is int, "main() should return an integer"

    filter_warnings("error", category=Warning)
    raise SystemExit(main())
