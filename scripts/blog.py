#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""blog manager"""

from __future__ import annotations

import asyncio
import datetime
import hashlib
import json
import os
import re
import shutil
import string
import subprocess
import sys
import tempfile
import time
import typing
import xml.etree.ElementTree as etree
from glob import iglob
from html import escape as html_escape
from threading import Thread
from timeit import default_timer as code_timer
from warnings import filterwarnings as filter_warnings

import mistune
import mistune.core
import mistune.inline_parser
import mistune.plugins
import unidecode
from css_html_js_minify import html_minify  # type: ignore
from css_html_js_minify import process_single_css_file  # type: ignore
from readtime import of_markdown as read_time_of_markdown  # type: ignore

__version__: typing.Final[int] = 2


OK: typing.Final[int] = 0
ER: typing.Final[int] = 1

CONFIG_FILE: typing.Final[str] = "blog.json"
DEFAULT_CONFIG: typing.Dict[str, typing.Any] = {
    "title": "blog",
    "header": "blog",
    "description": "my blog page",
    "posts-dir": "b",
    "assets-dir": "content",
    "rss-file": "rss.xml",
    "blog-keywords": [
        "blog",
        "blog page",
        "blog post",
        "personal",
        "website",
    ],
    "default-keywords": [
        "blog",
        "blog page",
        "blog post",
        "personal",
        "website",
    ],
    "website": "https://example.com",
    "blog": "https://blog.example.com",
    "source": "/git",
    "visitor-count": "/visit",
    "comment": "/c",
    "theme": {
        "primary": "#000",
        "secondary": "#fff",
        "type": "dark",
    },
    "manifest": {
        "icons": [
            {
                "src": "/favicon.ico",
                "sizes": "128x128",
                "type": "image/png",
            },
        ],
    },
    "author": "John Doe",
    "locale": "en_GB",
    "recents": 14,
    "indent": 4,
    "markdown-plugins": [  # good defaults
        "speedup",
        "strikethrough",
        "insert",
        "superscript",
        "subscript",
        "footnotes",
        "abbr",
    ],
    "editor": ["vim", "--", "%s"],
    "context-words": [
        "the",
        "a",
        "about",
        "etc",
        "on",
        "at",
        "in",
        "by",
        "its",
        "i",
        "to",
        "my",
        "of",
        "between",
        "because",
        "of",
        "or",
        "how",
        "to",
        "begin",
        "is",
        "this",
        "person",
        "important",
        "homework",
        "and",
        "cause",
        "how",
        "what",
        "for",
        "with",
        "without",
        "using",
        "im",
    ],
    "wslug-limit": 10,
    "slug-limit": 96,
    "proxy-api": "https://gimmeproxy.com/api/getProxy?post=true&get=true&user-agent=true&supportsHttps=true&protocol=http&minSpeed=20&curl=true",
    "test-proxy": "https://example.com/",
    "test-proxy-timeout": 15,
    "license": "GPL-3.0-or-later",
    "recent-title-trunc": 32,
    "server-host": "127.0.0.1",
    "server-port": 8080,
    "post-preview-size": 196,
    "read-wpm": 150,
    "posts": {},
}

NCI: bool = "CI" not in os.environ
NOCLR: bool = "NOCLR" in os.environ

LOG_CLR: str = "\033[90m"
ERR_CLR: str = "\033[1m\033[31m"
NEW_CLR: str = "\033[1m\033[32m"
IMP_CLR: str = "\033[1m\033[35m"

HTML_BEGIN: typing.Final[
    str
] = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta http-equiv="X-UA-Compatible" content="IE=edge">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta
    name="keywords"
    content="{keywords}"
/>
<meta
    name="robots"
    content="follow, index, max-snippet:-1, max-video-preview:-1, max-image-preview:large"
/>
<meta name="color-scheme" content="{theme_type}" />
<meta name="theme-color" content="{theme_primary}" />
<link rel="manifest" href="/manifest.json" />
<link rel="canonical" href="{blog}/{path}">
<link
    href="/{styles}"
    hreflang="en"
    referrerpolicy="no-referrer"
    rel="stylesheet"
    type="text/css"
/>
<link
    href="/{rss}"
    hreflang="en"
    referrerpolicy="no-referrer"
    title="{blog_title}"
    rel="alternate"
    type="application/rss+xml"
/>
<meta name="author" content="{author}" />
<meta name="generator" content="ari-web blog generator version {version}" />
<meta property="og:locale" content="{locale}" />
<meta name="license" content="{license}">
<link rel="sitemap" href="/sitemap.xml" type="application/xml">"""

POST_TEMPLATE: typing.Final[str] = (
    HTML_BEGIN
    + """
<title>{blog_title} -> {post_title}</title>
<meta name="description" content="{post_title} by {author} at {post_creation_time} GMT -- {post_description}" />
<meta property="article:read_time" content="{post_read_time}" />
<meta property="og:type" content="article" />
</head>

<body>
<main id="blog-content">
   <header role="group">
      <h1 role="heading" aria-level="1">{post_title}</h1>

      <nav id="info-bar" role="menubar">
        <a role="menuitem"
          aria-label="jump to the main content"
          href="#main">skip</a>
        <span role="seperator" aria-hidden="true">|</span>

        <span role="menuitem"><time>{post_creation_time}</time> GMT{post_edit_time}</span>
        <span role="seperator" aria-hidden="true">|</span>

        <span role="menuitem"
           >visitor <img src="{visitor_count}" alt="visitor count"
        /></span>
        <span role="seperator" aria-hidden="true">|</span>

        <span role="menuitem"><time>{post_read_time}</time> read</span>
        <span role="seperator" aria-hidden="true">|</span>

        <a role="menuitem" href="/">home</a>
        <span role="seperator" aria-hidden="true">|</span>

        <a role="menuitem" href="{comment}">comment</a>
        <span role="seperator" aria-hidden="true">|</span>

        <a role="menuitem" href="{website}">website</a>
        <span role="seperator" aria-hidden="true">|</span>

        <a role="menuitem" href="{source}">src</a>
        <span role="seperator" aria-hidden="true">|</span>

        <a role="menuitem" href="/{rss}">rss</a>

        <hr aria-hidden="true" role="seperator" />
      </nav>
   </header>
   <article id="main">{post_content}</article>
</main>
</body>
</html>"""
)

INDEX_TEMPLATE: typing.Final[str] = (
    HTML_BEGIN
    + """
<title>{blog_title}</title>
<meta name="description" content="{blog_description}" />
<meta property="og:type" content="website" />
</head>

<body>
<main id="blog-content">
   <header role="group">
      <h1 role="heading" aria-level="1">{blog_header}</h1>

      <nav id="info-bar" role="menubar">
        <a role="menuitem"
          aria-label="jump to the main content"
          href="#main">skip</a>
        <span role="seperator" aria-hidden="true">|</span>

        <span role="menuitem">latest post : <a href="/{latest_post_path}">{latest_post_title_trunc}</a> at <time>{latest_post_creation_time}</time> GMT</span>
        <span role="seperator" aria-hidden="true">|</span>

        <span role="menuitem"
           >visitor <img src="{visitor_count}" alt="visitor count"
        /></span>
        <span role="seperator" aria-hidden="true">|</span>

        <a role="menuitem" href="{comment}">comment</a>
        <span role="seperator" aria-hidden="true">|</span>

        <a role="menuitem" href="{website}">website</a>
        <span role="seperator" aria-hidden="true">|</span>

        <a role="menuitem" href="{source}">src</a>
        <span role="seperator" aria-hidden="true">|</span>

        <a role="menuitem" href="/{rss}">rss</a>

        <hr aria-hidden="true" role="seperator" />
      </nav>
   </header>
   <article id="main"><ol reversed>{blog_list}</ol></article>
</main>
</body>
</html>"""
)

if NCI:
    import http.server

    import pyfzf  # type: ignore
    import rebelai.ai.alpaca
    import rebelai.ai.gpt
    import rebelai.ai.h2o
    import requests

    AI_MODELS: typing.Tuple[typing.Tuple[typing.Any, bool], ...] = (
        (rebelai.ai.gpt.gpt4, False),
        (rebelai.ai.gpt.gpt3, True),
        (rebelai.ai.h2o.falcon_40b, True),
        (rebelai.ai.alpaca.alpaca_7b, True),
    )
else:
    pyfzf: typing.Any = None
    rebelai: typing.Any = None
    requests: typing.Any = None
    http: typing.Any = None

    AI_MODELS = tuple()  # type: ignore


class Commands:
    def __init__(self) -> None:
        self.commands: dict[
            str, typing.Callable[[typing.Dict[str, typing.Any]], int]
        ] = {}

    def new(
        self, fn: typing.Callable[[typing.Dict[str, typing.Any]], int]
    ) -> typing.Callable[[typing.Dict[str, typing.Any]], int]:
        self.commands[fn.__name__] = fn
        return fn

    def __getitem__(
        self, name: str
    ) -> typing.Callable[[typing.Dict[str, typing.Any]], int]:
        return self.commands[name]


cmds: Commands = Commands()
ecmds: Commands = Commands()


def ctimer() -> float:
    return code_timer() if NCI else 0


def log(msg: str, clr: str = LOG_CLR) -> int:
    if NCI:
        print(
            f"{datetime.datetime.now()} | {msg}"
            if NOCLR
            else f"{clr}{datetime.datetime.now()} | {msg}\033[0m",
            file=sys.stderr,
        )

    return OK


def llog(msg: str) -> int:
    return log(msg, "\033[0m")


def err(msg: str) -> int:
    log(msg, ERR_CLR)
    return ER


def lnew(msg: str) -> int:
    return log(msg, NEW_CLR)


def imp(msg: str) -> int:
    return log(msg, IMP_CLR)


def slugify(
    title: str,
    context_words: typing.Optional[typing.Sequence[str]] = None,
    wslug_limit: int = DEFAULT_CONFIG["wslug-limit"],
    slug_limit: int = DEFAULT_CONFIG["slug-limit"],
) -> str:
    return (
        "-".join(
            [
                w
                for w in "".join(
                    c
                    for c in unidecode.unidecode(title).lower()
                    if c not in string.punctuation
                ).split()
                if w not in (context_words or [])
            ][:wslug_limit]
        )[:slug_limit].strip("-")
        or "post"
    )


def get_proxy(
    api: str,
    test: str,
    timeout: float,
) -> typing.Dict[str, str]:
    while True:
        log("trying to get a proxy")

        proxy: str = requests.get(api).text

        proxies: typing.Dict[str, str] = {
            "http": proxy,
            "http2": proxy,
            "https": proxy,
        }

        try:
            log(f"testing proxy {proxy!r}")
            if not requests.get(
                test,
                timeout=timeout,
                proxies=proxies,
            ):
                raise Exception("proxy failed")
        except Exception:
            err(f"proxy {proxy!r} is bad")
            time.sleep(1)
            continue

        lnew(f"using proxy {proxy!r}")
        return {"proxy": proxy}


def gen_ai(
    prompt: str,
    *args: typing.Any,
    **kwargs: typing.Any,
) -> typing.Optional[str]:
    for model, proxy in AI_MODELS:
        log(
            f"generating text with {model.__name__} ai ( {'' if proxy else 'un'}proxied )"
        )

        for idx in range(1, 4):
            log(f"attempt #{idx}")

            resp: typing.Optional[str] = asyncio.run(
                model(
                    prompt=prompt,
                    request_args=get_proxy(*args, **kwargs) if proxy else None,
                ),
            )

            if resp:
                lnew("text generated")
                return resp.strip()

    err("ai could not generate text")
    return None


def rformat_time(ts: float) -> str:
    return datetime.datetime.utcfromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")


def format_time(ts: float) -> str:
    return f"{rformat_time(ts)} GMT"


def select_multi(options: typing.Sequence[str]) -> typing.List[str]:
    if not options:
        return []

    return pyfzf.FzfPrompt().prompt(
        choices=options,
        fzf_options="-m",
    )


def select_posts(
    posts: typing.Dict[str, typing.Dict[str, typing.Any]]
) -> typing.Tuple[str, ...]:
    return tuple(
        map(
            lambda opt: opt.split("|", maxsplit=1)[0].strip(),
            select_multi(
                tuple(
                    f"{slug} | {post['title']} | {post['description']}"
                    for slug, post in posts.items()
                ),
            ),
        )
    )


if NCI:
    import readline

    def iinput(prompt: str, default_text: str = "", force: bool = True) -> str:
        default_text = default_text.strip()

        if default_text:

            def hook() -> None:
                readline.insert_text(default_text)
                readline.redisplay()

            readline.set_pre_input_hook(hook)

        while not (user_input := input(f"\033[1m{prompt}\033[0m ").strip()) and force:
            pass

        readline.set_pre_input_hook()

        return user_input

else:

    def iinput(prompt: str, default_text: str = "", force: bool = True) -> str:
        raise ValueError(
            f"cannot read user input in CI mode, prompt : {prompt!r}; default text : {default_text!r}; force : {force!r}"
        )


def yn(prompt: str, default: str = "y") -> bool:
    return (iinput(f"{prompt} ? [y/n]", default) + default)[0].lower() == "y"


def get_tmpfile(name: str) -> str:
    return os.path.join(tempfile.gettempdir(), name + ".md")


def open_file(editor: typing.Sequence[str], path: str) -> None:
    log(f"formatting and running {editor!r} with {path!r}")
    subprocess.run([(token.replace("%s", path)) for token in editor])


def trunc(data: str, length: int, end: str = " ...") -> str:
    return data[:length] + (end if len(data) > length else "")


def read_post(path: str) -> str:
    log(f"reading {path!r}")

    try:
        with open(path, "r") as data:
            return data.read().strip()
    except Exception as e:
        err(f"failed to read {path!r} : {e.__class__.__name__} {e}")
        return ""


# markdown

TITLE_LINKS_RE: typing.Final[str] = r"<#:[^>]+?>"


def parse_inline_titlelink(
    _: mistune.inline_parser.InlineParser,
    m: re.Match[str],
    state: mistune.core.InlineState,
) -> int:
    text: str = m.group(0)[3:-1]

    state.append_token(
        {
            "type": "link",
            "children": [{"type": "text", "raw": f"# {text}"}],
            "attrs": {"url": f"#{slugify(text, [], 768, 768)}"},
        }
    )
    return m.end()


def titlelink(md: mistune.Markdown) -> None:
    md.inline.register("titlelink", TITLE_LINKS_RE, parse_inline_titlelink, before="link")  # type: ignore


class BlogRenderer(mistune.HTMLRenderer):
    def heading(self, text: str, level: int, **_: typing.Any) -> str:
        slug: str = slugify(text, [], 768, 768)
        level = max(2, level)

        return f'<h{level} id="{slug}" h><a href="#{slug}">#</a> {text}</h{level}>'


def markdown(md: str, plugins: typing.List[typing.Any]) -> str:
    return mistune.create_markdown(plugins=plugins + [titlelink], renderer=BlogRenderer())(md)  # type: ignore


# edit commands


@ecmds.new
def title(post: typing.Dict[str, typing.Any]) -> int:
    post["title"] = iinput("post title", post["title"])
    return OK


@ecmds.new
def description(post: typing.Dict[str, typing.Any]) -> int:
    post["description"] = iinput("post description", post["description"])
    return OK


@ecmds.new
def content(post: typing.Dict[str, typing.Any]) -> int:
    """edit posts"""

    log("getting post markdown path")
    path: str = get_tmpfile(post["slug"])

    log("writing content")
    with open(path, "w") as p:
        p.write(post["content"])

    open_file(post["editor"], path)

    if not (content := read_post(path)):
        return err("post content cannot be empty")

    post["content"] = content

    return OK


@ecmds.new
def keywords(post: typing.Dict[str, typing.Any]) -> int:
    """edit keywords"""

    post["keywords"] = tuple(
        map(
            lambda k: unidecode.unidecode(k.strip()),
            filter(
                bool,
                set(
                    iinput("post keywords", ", ".join(post["keywords"]), force=False)
                    .lower()
                    .split(",")
                ),
            ),
        )
    )
    return OK


# normal commands


@cmds.new
def help(_: typing.Dict[str, typing.Any]) -> int:
    """print help"""

    return llog(
        "\n\n"
        + "\n".join(
            f"{cmd} -- {fn.__doc__ or 'no help provided'}"
            for cmd, fn in cmds.commands.items()
        )
    )


@cmds.new
def sort(config: typing.Dict[str, typing.Any]) -> int:
    """sort blog posts by creation time"""

    log("sorting posts by creation time")

    config["posts"] = dict(
        map(
            lambda k: (k, config["posts"][k]),
            sorted(
                config["posts"],
                key=lambda k: config["posts"][k]["created"],
                reverse=True,
            ),
        )
    )

    return lnew("sorted blog posts by creation time")


@cmds.new
def new(config: typing.Dict[str, typing.Any]) -> int:
    """create a new blog post"""

    title: str = iinput("post title")

    log("creating a slug from the given title")
    slug: str = slugify(
        title,
        config["context-words"],
        config["wslug-limit"],
        config["slug-limit"],
    )

    if slug in (posts := config["posts"]):
        slug += f"-{sum(map(lambda k: k.startswith(slug), posts))}"

    log("getting post markdown path")
    post_path: str = get_tmpfile(slug)

    open_file(config["editor"], post_path)

    if not (content := read_post(post_path)):
        return err("content cannot be empty")

    keywords: typing.Tuple[str, ...] = tuple(
        map(
            lambda k: unidecode.unidecode(k.strip()),
            filter(
                bool,
                set(
                    iinput("post keywords ( separated by `,` )", force=False)
                    .lower()
                    .split(",")
                ),
            ),
        )
    )

    description: str = ""

    if yn("auto-generate post description", "n"):
        while True:
            description = "  ".join(
                (
                    gen_ai(
                        f"""Write a good, personal, medium to short description for this blog post with the title "{title}" and keywords : \
{', '.join(keywords) or '<none>'}, give just the description, leave some details out as a teaser, the blog post is formatted using Markdown, \
description must be on a singular line and all you should return is the description and nothing else, the description should look as if \
it was written by the author, mimic the writing style of the blog post in the description:

{content}""",
                        api=config["proxy-api"],
                        test=config["test-proxy"],
                        timeout=config["test-proxy-timeout"],
                    )
                    or ""
                ).splitlines()
            )

            if description:
                llog(description)

                if yn("generate new", "n"):
                    continue

                description = iinput("ai post description", description)
                break

            if not yn("failed to generate description, re-generate", "n"):
                break

    if not description:
        description = iinput("manual post description")

    lnew(f"saving blog post {slug!r}")

    posts[slug] = {
        "title": title,
        "description": description.strip(),
        "content": content,
        "keywords": keywords,
        "created": datetime.datetime.utcnow().timestamp(),
    }

    return OK


@cmds.new
def ls(config: typing.Dict[str, typing.Any]) -> int:
    """list all posts"""

    for slug, post in config["posts"].items():
        llog(
            f"""post({slug})

title : {post["title"]!r}
description : {post["description"]!r}
content : {trunc(post["content"], config["post-preview-size"])!r}
keywords : {", ".join(post["keywords"])}
created : {format_time(post["created"])}"""
            + (
                ""
                if (ed := post.get("edited")) is None
                else f"\nedited : {format_time(ed)}"
            )
        )

    return OK


@cmds.new
def ed(config: typing.Dict[str, typing.Any]) -> int:
    """edit posts"""

    fields: typing.List[str] = select_multi(tuple(ecmds.commands.keys()))

    for slug in select_posts(config["posts"]):
        llog(f"editing {slug!r}")

        for field in fields:
            log(f"editing field {field!r}")

            post: typing.Dict[str, typing.Any] = config["posts"][slug]

            post["slug"] = slug
            post["editor"] = config["editor"]

            code: int = ecmds[field](post)

            del post["slug"]
            del post["editor"]

            if code is not OK:
                return code

            post["edited"] = datetime.datetime.utcnow().timestamp()

    return OK


@cmds.new
def rm(config: typing.Dict[str, typing.Any]) -> int:
    """remove posts"""

    for slug in select_posts(config["posts"]):
        imp(f"deleting {slug!r}")
        del config["posts"][slug]

    return OK


@cmds.new
def build(config: typing.Dict[str, typing.Any]) -> int:
    """build blog posts"""

    log("setting up posts directory")

    if os.path.exists(config["posts-dir"]):
        shutil.rmtree(config["posts-dir"])

    os.makedirs(config["posts-dir"], exist_ok=True)

    llog("building blog")

    blog_title: str = html_escape(config["title"])
    author: str = html_escape(config["author"])
    styles: str = os.path.join(config["assets-dir"], "styles.css")

    def build_post(slug: str, post: typing.Dict[str, typing.Any]) -> None:
        ct: float = ctimer()

        post_dir: str = os.path.join(config["posts-dir"], slug)
        os.makedirs(post_dir)

        with open(os.path.join(post_dir, "index.html"), "w") as html:
            html.write(
                html_minify(
                    POST_TEMPLATE.format(
                        keywords=html_escape(
                            ", ".join(
                                set(post["keywords"] + config["default-keywords"])
                            )
                        ),
                        theme_type=config["theme"]["type"],
                        theme_primary=config["theme"]["primary"],
                        styles=styles,
                        rss=config["rss-file"],
                        blog_title=blog_title,
                        post_title=html_escape(post["title"]),
                        author=author,
                        version=__version__,
                        locale=config["locale"],
                        post_creation_time=rformat_time(post["created"]),
                        post_description=html_escape(post["description"]),
                        post_read_time=read_time_of_markdown(
                            post["content"],
                            config["read-wpm"],
                        ).text,
                        post_edit_time=(
                            ""
                            if "edited" not in post
                            else f', edited on <time>{rformat_time(post["edited"])}</time> GMT'
                        ),
                        visitor_count=config["visitor-count"],
                        comment=config["comment"],
                        website=config["website"],
                        source=config["source"],
                        post_content=markdown(
                            post["content"], config["markdown-plugins"]
                        ),
                        blog=config["blog"],
                        path=os.path.join(config["posts-dir"], slug),
                        license=config["license"],
                    )
                )
            )

        lnew(f"built post {post['title']!r} in {ctimer() - ct} s")

    ts: typing.List[Thread] = []

    for slug, post in tuple(config["posts"].items()):
        ts.append(Thread(target=build_post, args=(slug, post), daemon=True))
        ts[-1].start()

    latest_post: typing.Tuple[str, typing.Dict[str, typing.Any]] = tuple(
        config["posts"].items()
    )[0]

    with open("index.html", "w") as index:
        index.write(
            html_minify(
                INDEX_TEMPLATE.format(  # type: ignore
                    keywords=html_escape(", ".join(config["blog-keywords"])),
                    theme_type=config["theme"]["type"],
                    theme_primary=config["theme"]["primary"],
                    blog=config["blog"],
                    path="",
                    styles=styles,
                    rss=config["rss-file"],
                    blog_title=blog_title,
                    author=author,
                    version=__version__,
                    locale=config["locale"],
                    license=config["license"],
                    blog_description=html_escape(config["description"]),
                    blog_header=html_escape(config["header"]),
                    latest_post_path=os.path.join(config["posts-dir"], latest_post[0]),
                    latest_post_title_trunc=html_escape(
                        trunc(latest_post[1]["title"], config["recent-title-trunc"])
                    ),
                    latest_post_creation_time=rformat_time(latest_post[1]["created"]),
                    visitor_count=config["visitor-count"],
                    comment=config["comment"],
                    website=config["website"],
                    source=config["source"],
                    blog_list=" ".join(
                        f'<li><a href="/{os.path.join(config["posts-dir"], slug)}">{html_escape(post["title"])}</a></li>'
                        for slug, post in config["posts"].items()
                    ),
                )
            )
        )

        lnew(f"generated {index.name!r}")

    for t in ts:
        t.join()

    return 0


@cmds.new
def css(config: typing.Dict[str, typing.Any]) -> int:
    """build and minify css"""

    ts: typing.List[Thread] = []

    saved_stdout: typing.Any = sys.stdout
    sys.stdout = open(os.devnull, "w")

    def _thread(c: typing.Callable[..., typing.Any], css: str) -> None:
        def _c() -> None:
            ct: float = ctimer()
            c(css)
            lnew(f"processed {css!r} in {ctimer() - ct} s")

        ts.append(Thread(target=_c, daemon=True))
        ts[-1].start()

    if os.path.isfile(styles := os.path.join(config["assets-dir"], "styles.css")):
        llog(f"minifying {styles!r}")
        _thread(process_single_css_file, styles)  # type: ignore

    if os.path.isdir(fonts := os.path.join(config["assets-dir"], "fonts")):
        log(f"minifying fonts in {fonts!r}")

        for fcss in iglob(os.path.join(fonts, "*.css")):
            if fcss.endswith(".min.css"):
                continue

            _thread(process_single_css_file, fcss)  # type: ignore

    for t in ts:
        t.join()

    sys.stdout.close()
    sys.stdout = saved_stdout

    return OK


@cmds.new
def robots(config: typing.Dict[str, typing.Any]) -> int:
    """generate a robots.txt"""

    llog("generating robots")

    with open("robots.txt", "w") as r:
        r.write(
            f"""User-agent: *
Disallow: /{config["assets-dir"]}/*
Allow: *
Sitemap: {config["blog"]}/sitemap.xml"""
        )

        lnew(f"generated {r.name!r}")

    return OK


@cmds.new
def manifest(config: typing.Dict[str, typing.Any]) -> int:
    """generate a manifest.json"""

    llog("generating a manifest")

    with open("manifest.json", "w") as m:
        json.dump(
            {
                "$schema": "https://json.schemastore.org/web-manifest-combined.json",
                "short_name": config["header"],
                "name": config["title"],
                "description": config["description"],
                "start_url": ".",
                "display": "standalone",
                "theme_color": config["theme"]["primary"],
                "background_color": config["theme"]["secondary"],
                **config["manifest"],
            },
            m,
        )

        lnew(f"generated {m.name!r}")

    return OK


@cmds.new
def sitemap(config: typing.Dict[str, typing.Any]) -> int:
    """generate a sitemap.xml"""

    llog("generating a sitemap")

    now: float = datetime.datetime.utcnow().timestamp()

    root: etree.Element = etree.Element("urlset")
    root.set("xmlns", "http://www.sitemaps.org/schemas/sitemap/0.9")

    for slug, post in (
        ("", config["website"]),
        ("", config["blog"]),
        ("", f"{config['blog']}/{config['rss-file']}"),
    ) + tuple(config["posts"].items()):
        llog(f"adding {slug or post!r} to sitemap")

        url: etree.Element = etree.SubElement(root, "url")

        etree.SubElement(url, "loc").text = (
            f"{config['blog']}/{os.path.join(config['posts-dir'], slug)}"
            if slug
            else post
        )
        etree.SubElement(url, "lastmod").text = datetime.datetime.utcfromtimestamp(
            post.get("edited", post["created"]) if slug else now  # type: ignore
        ).strftime("%Y-%m-%dT%H:%M:%S+00:00")
        etree.SubElement(url, "priority").text = "1.0"

    etree.ElementTree(root).write("sitemap.xml", encoding="UTF-8", xml_declaration=True)
    lnew("generated 'sitemap.xml'")

    return OK


@cmds.new
def rss(config: typing.Dict[str, typing.Any]) -> int:
    """generate an rss feed"""

    llog("generating an rss feed")

    ftime: str = "%a, %d %b %Y %H:%M:%S GMT"
    now: datetime.datetime = datetime.datetime.utcnow()

    root: etree.Element = etree.Element("rss")
    root.set("version", "2.0")

    channel: etree.Element = etree.SubElement(root, "channel")

    etree.SubElement(channel, "title").text = config["title"]
    etree.SubElement(channel, "link").text = config["blog"]
    etree.SubElement(channel, "description").text = config["description"]
    etree.SubElement(channel, "language").text = (
        config["locale"].lower().replace("_", "-")
    )
    etree.SubElement(channel, "lastBuildDate").text = now.strftime(ftime)

    for slug, post in config["posts"].items():
        llog(f"adding {slug!r} to rss")

        item: etree.Element = etree.SubElement(channel, "item")

        etree.SubElement(item, "title").text = post["title"]
        etree.SubElement(item, "link").text = (
            link := f"{config['blog']}/{os.path.join(config['posts-dir'], slug)}"
        )
        etree.SubElement(item, "description").text = post["description"]
        etree.SubElement(item, "pubDate").text = datetime.datetime.utcfromtimestamp(
            post["created"]
        ).strftime(ftime)
        etree.SubElement(item, "guid").text = link

    etree.ElementTree(root).write(
        config["rss-file"], encoding="UTF-8", xml_declaration=True
    )

    lnew(f"generated {config['rss-file']!r}")

    return OK


@cmds.new
def apis(config: typing.Dict[str, typing.Any]) -> int:
    """generate and hash apis"""

    with open("recents.json", "w") as recents:
        json.dump(
            dict(
                map(
                    lambda kv: (
                        kv[0],
                        {
                            "title": kv[1]["title"],
                            "content": trunc(
                                kv[1]["content"], config["post-preview-size"], ""
                            ),
                            "created": kv[1]["created"],
                        },
                    ),
                    tuple(config["posts"].items())[: config["recents"]],
                )
            ),
            recents,
        )
        lnew(f"generated {recents.name!r}")

    for api in recents.name, CONFIG_FILE:
        with open(api, "rb") as content:
            h: str = hashlib.sha256(content.read()).hexdigest()

        with open(f"{api.replace('.', '_')}_hash.txt", "w") as hf:
            hf.write(h)
            lnew(f"generated {hf.name!r}")

    return OK


@cmds.new
def clean(config: typing.Dict[str, typing.Any]) -> int:
    """clean up the site"""

    def remove(file: str) -> None:
        imp(f"removing {file!r}")

        try:
            os.remove(file)
        except IsADirectoryError:
            shutil.rmtree(file)

    for pattern in (
        config["posts-dir"],
        "index.html",
        os.path.join(config["assets-dir"], "*.min.*"),
        "blog_json_hash.txt",
        "manifest.json",
        os.path.join(config["assets-dir"], os.path.join("fonts", "*.min.*")),
        "recents_json_hash.txt",
        "recents.json",
        config["rss-file"],
        "robots.txt",
        "sitemap.xml",
    ):
        if os.path.exists(pattern):
            remove(pattern)
        else:
            for file in iglob(pattern, recursive=True):
                remove(file)

    return OK


@cmds.new
def static(config: typing.Dict[str, typing.Any]) -> int:
    """generate a full static site"""

    ct: float = ctimer()

    for stage in clean, build, css, robots, manifest, sitemap, rss, apis:
        imp(f"running stage {stage.__name__!r} : {stage.__doc__ or stage.__name__!r}")

        st: float = ctimer()

        if (code := stage(config)) is not OK:
            return code

        imp(f"stage finished in {ctimer() - st} s")

    return log(f"site built in {ctimer() - ct} s")


@cmds.new
def serve(config: typing.Dict[str, typing.Any]) -> int:
    """simple server"""

    class RequestHandler(http.server.SimpleHTTPRequestHandler):
        def log_message(self, format: str, *args: typing.Any) -> None:
            llog(format % args)

        def do_GET(self) -> None:
            file_path: str = self.translate_path(self.path)  # type: ignore

            if os.path.isdir(file_path):  # type: ignore
                file_path = os.path.join(file_path, "index.html")  # type: ignore

            try:
                with open(file_path, "rb") as fp:  # type: ignore
                    self.send_response(200)  # type: ignore
                    self.end_headers()  # type: ignore
                    self.wfile.write(fp.read())  # type: ignore
            except Exception as e:
                self.send_response(404)  # type: ignore
                self.end_headers()  # type: ignore
                self.wfile.write(f"{e.__class__.__name__} : {e}".encode())  # type: ignore

    httpd: typing.Any = http.server.HTTPServer(
        (config["server-host"], config["server-port"]), RequestHandler
    )
    httpd.RequestHandlerClass.directory = "."

    try:
        imp(
            f"server running on http://{httpd.server_address[0]}:{httpd.server_address[1]}/ ^C to close it"
        )
        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.server_close()
        imp("server shut down")

    return OK


@cmds.new
def dev(config: typing.Dict[str, typing.Any]) -> int:
    """generate a full static site + serve it"""

    if (code := static(config)) is not OK:
        return code

    return serve(config)


def main() -> int:
    """entry/main function"""

    main_t: float = ctimer()

    log("hello world")

    if len(sys.argv) < 2:
        return err("no arguments provided, see `help`")

    cfg: dict[str, typing.Any] = DEFAULT_CONFIG.copy()

    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as config:
            log(f"using {config.name!r} config")
            cfg.update(json.load(config))
    else:
        lnew("using the default config")

    sort(cfg)

    log(f"looking command {sys.argv[1]!r} up")

    try:
        cmd: typing.Callable[[dict[str, typing.Any]], int] = cmds[sys.argv[1]]
    except KeyError:
        return err(f"command {sys.argv[1]!r} does not exist")

    log("calling and timing the command")
    if NCI:
        print()
        timer: float = ctimer()

    code: int = cmd(cfg)

    if NCI:
        print()
        log(f"command finished in {ctimer() - timer} s")  # type: ignore
        sort(cfg)

    with open(CONFIG_FILE, "w") as config:
        log(f"dumping config to {config.name!r}")
        json.dump(cfg, config, indent=cfg["indent"] if NCI else None)

    log(f"goodbye world, return {code}, total {ctimer() - main_t} s")

    return code


if __name__ == "__main__":
    assert (
        main.__annotations__.get("return") == "int"
    ), "main() should return an integer"

    filter_warnings("error", category=Warning)
    raise SystemExit(main())
