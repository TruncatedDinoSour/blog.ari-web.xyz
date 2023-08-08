#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""manage blogs"""

import hashlib
import os
import random
import string
import sys
import xml.etree.ElementTree as etree
from datetime import datetime
from glob import iglob
from html import escape as html_escape
from re import Match as RegexMatch
from shutil import copy as copy_file
from shutil import rmtree
from tempfile import gettempdir
from threading import Thread
from timeit import default_timer as code_timer
from typing import (Any, Callable, Collection, Dict, List, Optional, Set,
                    Tuple, Union)
from urllib.parse import quote as encode_url
from warnings import filterwarnings as filter_warnings

import ujson  # type: ignore
from css_html_js_minify import html_minify  # type: ignore
from css_html_js_minify import process_single_css_file  # type: ignore
from markdown import core as markdown_core  # type: ignore
from markdown import markdown  # type: ignore
from markdown.extensions import Extension  # type: ignore
from markdown.inlinepatterns import InlineProcessor  # type: ignore
from markdown.treeprocessors import Treeprocessor  # type: ignore
from plumbum.commands.processes import ProcessExecutionError  # type: ignore
from pyfzf import FzfPrompt  # type: ignore
from readtime import of_markdown as read_time_of_markdown  # type: ignore

__version__: int = 1

NOT_CI_BUILD: bool = not os.getenv("CI")

if NOT_CI_BUILD:
    import readline
    from atexit import register as fn_register

EXIT_OK: int = 0
EXIT_ERR: int = 1

DEFAULT_CONFIG: Dict[str, Any] = {
    "editor-command": f"{os.environ.get('EDITOR', 'vim')} -- %s",
    "blog-dir": "b",
    "git-url": "/git",
    "py-markdown-extensions": [
        "markdown.extensions.abbr",
        "markdown.extensions.def_list",
        "markdown.extensions.fenced_code",
        "markdown.extensions.footnotes",
        "markdown.extensions.md_in_html",
        "markdown.extensions.tables",
        "markdown.extensions.admonition",
        "markdown.extensions.sane_lists",
        "markdown.extensions.toc",
        "markdown.extensions.wikilinks",
        "pymdownx.betterem",
        "pymdownx.caret",
        "pymdownx.magiclink",
        "pymdownx.mark",
        "pymdownx.tilde",
    ],
    "default-keywords": ["website", "blog", "opinion", "article", "ari-web", "ari"],
    "page-title": "Ari::web -> Blog",
    "page-description": "my blog page",
    "colourscheme-type": "dark",
    "short-name": "aris blogs",
    "home-keywords": ["ari", "ari-web", "blog", "ari-archer", "foss", "free", "linux"],
    "base-homepage": "https://ari-web.xyz/",
    "meta-icons": [{"src": "/favicon.ico", "sizes": "128x128", "type": "image/png"}],
    "theme-colour": "#f9f6e8",
    "background-colour": "#262220",
    "full-name": "Ari Archer",
    "locale": "en_GB",
    "home-page-header": "my blogs",
    "comment-url": "/c",
    "recents": 16,
    "visitor-count": "/visit",
    "rss-feed": "rss.xml",
    "page-url": "https://blog.ari-web.xyz/",
    "blogs": {},
}
DEFAULT_CONFIG_FILE: str = "blog.json"
HISTORY_FILE: str = ".blog_history"
CONTEXT_WORDS: Tuple[str, ...] = (
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
)

BLOG_MARKDOWN_TEMPLATE: str = """<header role="group">
    <h1 role="heading" aria-level="1">%s</h1>

    <nav id="info-bar" role="menubar">
        <a role="menuitem" aria-label="jump to the main content" href="#main">\
skip</a>
        <span role="seperator" aria-hidden="true">|</span>

        <span role="menuitem"><time>%s</time> UTC</span>
        <span role="seperator" aria-hidden="true">|</span>

        <span role="menuitem">visitor <img src="%s" alt="visitor count"></span>
        <span role="seperator" aria-hidden="true">|</span>

        <span role="menuitem"><time>%s</time> read</span>
        <span role="seperator" aria-hidden="true">|</span>

        <a role="menuitem" href="/">home</a>
        <span role="seperator" aria-hidden="true">|</span>

        <a role="menuitem" href="%s">comment</a>
        <span role="seperator" aria-hidden="true">|</span>

        <a role="menuitem" href="%s">website</a>
        <span role="seperator" aria-hidden="true">|</span>

        <a role="menuitem" href="%s">git</a>
        <span role="seperator" aria-hidden="true">|</span>

        <a role="menuitem" href="/%s">rss</a>

        <hr aria-hidden="true" role="seperator" />
    </nav>
</header>

<article id="main">

<!-- main blog post content : begin -->

%s

<!-- main blog post content : end -->

</article>"""

HTML_HEADER: str = f"""<head>
    <meta charset="UTF-8"/>
    <meta http-equiv="X-UA-Compatible" content="IE=edge"/>
    <meta name="viewport" content="width=device-width, initial-scale=1.0"/>

    <meta property="og:locale" content="{{locale}}"/>

    <meta name="color-scheme" content="{{theme_type}}"/>
    <meta name="author" content="{{author}}"/>
    <meta name="keywords" content="{{keywords}}"/>
    <meta name="robots" content="follow, index, max-snippet:-1, \
max-video-preview:-1, max-image-preview:large"/>
    <meta name="generator" \
content="ari-web blog generator version {__version__}"/>

    <link
        rel="stylesheet"
        href="/content/styles.min.css"
        referrerpolicy="no-referrer"
        type="text/css"
        hreflang="en"
    />
    <link
        rel="alternate"
        type="application/rss+xml"
        href="/{{rss}}"
        title="RSS feed"
    >
"""

BLOG_HTML_TEMPLATE: str = f"""<!DOCTYPE html>
<html lang="en">
{HTML_HEADER}
    <title>{{title}} -> {{blog_title}}</title>

    <meta name="description" content="{{blog_description}}"/>
    <meta property="og:type" content="article"/>
    <meta property="article:read_time" content="{{read_time}}">
</head>
<body>
    <main id="blog-content">

{{blog}}

    </main>
</body>
</html>"""

HOME_PAGE_HTML_TEMPLATE: str = f"""<!DOCTYPE html>
<html lang="en">
{HTML_HEADER}
    <title>{{title}}</title>

    <meta name="description" content="{{home_page_description}}"/>
    <meta property="og:type" content="website"/>

    <link
        rel="manifest"
        href="/manifest.json"
        referrerpolicy="no-referrer"
        type="application/json"
        hreflang="en"
    />
</head>
<body>
    <header>
        <h1 role="heading" aria-level="1">{{page_header}}</h1>

        <nav id="info-bar" role="navigation">
            <p role="menubar">
                <a
                    role="menuitem"
                    aria-label="jump to the main content"
                    href="#main"
                >skip</a>

                <span aria-hidden="true" role="seperator">|</span>

                <span role="menuitem">
                    last posted : <time>{{lastest_blog_time}}</time> UTC
                </span>

                <span aria-hidden="true" role="seperator">|</span>

                <span role="menuitem">
                    latest post : \
                    <a href="{{latest_blog_url}}">{{latest_blog_title}}</a>
                </span>
                <span role="seperator" aria-hidden="true">|</span>

                <span role="menuitem">visitor <img src="{{visitor}}" alt="visitor count"></span>
                <span aria-hidden="true" role="seperator">|</span>

                <a role="menuitem" href="{{git_url}}">git</a>
                <span aria-hidden="true" role="seperator">|</span>

                <a role="menuitem" href="/{{rss}}">rss</a>
            </p>

            <hr aria-hidden="true" role="seperator" />
        </nav>
    </header>

    <main id="main">

<!-- main home page content : begin -->

{{content}}

<!-- main home page content : end -->

    </main>
</body>
</html>"""


def remove_basic_punct(s: str) -> str:
    return "".join(c for c in s if c not in "'\"()[]{}:;.,?!=#")


def sanitise_title(
    title: str, titleset: Collection[str], *, nosep: bool = False, generic: bool = True
) -> str:
    title = title.lower().strip()
    words: list[str] = []

    if generic:
        for w in remove_basic_punct(title).split():
            if w not in CONTEXT_WORDS:
                words.append(w)
            elif len(words) >= 8:
                break

    if words:
        title = " ".join(words)

    _title: str = ""

    for char in title:
        _title += (
            char
            if char not in string.whitespace + string.punctuation
            else "-"
            if _title and _title[-1] != "-"
            else ""
        )

    _title = _title.strip("-")

    return (
        _title
        if _title not in titleset and _title.strip()
        else sanitise_title(
            _title + ("" if nosep else "-") + random.choice(string.digits),
            titleset,
            nosep=True,
            generic=generic,
        )
    )


def truncate_str(string: str, length: int) -> str:
    return string if len(string) <= length else (string[:length] + " ...")


class BetterHeaders(Treeprocessor):
    """better headers

    - downsizes headers from h1 -> h2
    - adds header links"""

    def run(self, root: etree.Element) -> None:
        ids: List[str] = []
        heading_sizes_em: Dict[str, float] = {
            "h2": 1.32,
            "h3": 1.15,
            "h4": 1.0,
            "h5": 0.87,
            "h6": 0.76,
        }

        for idx, elem in enumerate(root):
            if elem.tag == "h1":
                elem.tag = "h2"

            if elem.tag not in heading_sizes_em:
                continue

            if elem.text is None:
                elem.text = ""

            gen_id: str = sanitise_title(elem.text, ids, generic=False)
            ids.append(gen_id)

            heading_parent: etree.Element = elem.makeelement(
                "div",
                {
                    "data-pl": "",
                    "style": f"font-size:{(heading_sizes_em[elem.tag] + 0.1):.2f}".strip(
                        "0"
                    ).rstrip(
                        "."
                    )
                    + "em",
                },
            )

            heading: etree.Element = heading_parent.makeelement(
                elem.tag, {"id": gen_id}
            )
            link: etree.Element = heading.makeelement(
                "a",
                {
                    "href": f"#{gen_id}",
                    "aria-hidden": "true",
                    "focusable": "false",
                    "tabindex": "-1",
                },
            )

            link.text = "#"
            heading.text = elem.text

            heading_parent.extend(
                (
                    link,
                    heading,
                )
            )
            root.remove(elem)
            root.insert(idx, heading_parent)


class TitleLinks(InlineProcessor):
    """add support for <#:title> links"""

    def handleMatch(  # pyright: ignore
        self, match: RegexMatch, *_  # pyright: ignore
    ) -> Union[Tuple[etree.Element, Any, Any], Tuple[None, ...]]:
        text: str = match.group(1)  # type: ignore

        if not text:
            return (None,) * 3

        link: etree.Element = etree.Element("a")

        link.text = f"# {text}"
        link.set("href", f"#{sanitise_title(text, [], generic=False)}")  # type: ignore

        return link, match.start(0), match.end(0)


class AriMarkdownExts(Extension):
    """ari-web markdown extensions"""

    def extendMarkdown(
        self,
        md: markdown_core.Markdown,
        key: str = "add_header_links",
        index: int = int(1e8),
    ) -> None:
        md.registerExtension(self)

        md.treeprocessors.register(
            BetterHeaders(md.parser), key, index  # pyright: ignore
        )

        md.inlinePatterns.register(
            TitleLinks(r"<#:(.*)>", "a"), key, index  # pyright: ignore
        )


def log(message: str, header: str = "ERROR", code: int = EXIT_ERR) -> int:
    if not (not NOT_CI_BUILD and header != "ERROR"):
        sys.stderr.write(f"{header} : {message}\n")

    return code


def tmp_path(path: str) -> str:
    return os.path.join(gettempdir(), path)


def editor(config: Dict[str, Any], file: str) -> None:
    copy_file(".editorconfig", tmp_path(".editorconfig"))
    os.system(config["editor-command"] % file)


def format_time(timestamp: float) -> str:
    return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")


def iinput(prompt: str, default_text: str = "") -> str:
    default_text = default_text.strip()

    def hook():
        if not default_text:
            return

        readline.insert_text(default_text)
        readline.redisplay()

    readline.set_pre_input_hook(hook)
    user_inpt: str = input(f"({prompt}) ").strip()
    readline.set_pre_input_hook()

    return user_inpt


def yn(prompt: str, default: str = "y", current_value: str = "") -> bool:
    return (
        iinput(
            f"{prompt}? ({'y/n'.replace(default.lower(), default.upper())})",
            current_value,
        )
        + default
    ).lower()[0] == "y"


def new_config() -> None:
    log("making new config ...", "INFO")

    with open(DEFAULT_CONFIG_FILE, "w") as cfg:
        ujson.dump(DEFAULT_CONFIG, cfg, indent=4)


def pick_blog(config: Dict[str, Any]) -> str:
    try:
        blog_id: str = (
            FzfPrompt()
            .prompt(  # pyright: ignore
                map(
                    lambda key: f"{key} | {config['blogs'][key]['title']!r}",  # pyright: ignore
                    tuple(config["blogs"].keys())[::-1],
                ),
                "--prompt='pick a post : '",
            )[0]
            .split()[0]  # pyright: ignore
        )
    except ProcessExecutionError:
        log("fzf process exited unexpectedly")
        return ""

    if blog_id not in config["blogs"]:
        log(f"blog post {blog_id!r} does not exist")
        return ""

    return blog_id


def new_blog(config: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
    """make a new blog"""

    if title := iinput("blog post title"):
        readline.add_history((title := title.capitalize()))

        us_title: str = title
        s_title: str = sanitise_title(us_title, config["blogs"])
    else:
        return EXIT_ERR, config

    blog: Dict[str, Any] = {
        "title": us_title,
        "content": "",
        "time": 0.0,
        "keywords": "",
    }

    file: str = tmp_path(f"{s_title}.md")

    open(file, "w").close()
    editor(config, file)

    if not os.path.isfile(file):
        return log(f"{file!r} does not exist"), config

    with open(file, "r") as md:
        blog["content"] = md.read()

    os.remove(file)

    if not blog["content"].strip():  # type: ignore
        return log("blog post cannot be empty"), config

    user_keywords: str = iinput("keywords ( seperated by spaces )")
    readline.add_history(user_keywords)

    blog["keywords"] = html_escape(user_keywords)

    blog["time"] = datetime.utcnow().timestamp()
    config["blogs"][s_title] = blog

    return EXIT_OK, config


def build_css(config: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
    """minify ( build ) the CSS"""

    log("minifying CSS ...", "MINIFY")

    saved_stdout = sys.stdout
    sys.stdout = open(os.devnull, "w")

    css_threads: List[Thread] = []

    def _thread(t: Callable[..., Any]) -> None:
        css_threads.append(Thread(target=t, daemon=True))
        css_threads[-1].start()

    if os.path.isfile("content/styles.css"):
        log("minifying main styles", "MINIFY")
        _thread(
            lambda: process_single_css_file("content/styles.css")  # pyright: ignore
        )

    if os.path.isdir("content/fonts"):
        log("minifying fonts ...", "MINIFY")

        for font in iglob("content/fonts/*.css"):
            if font.endswith(".min.css"):
                continue

            log(f"minifying font file -- {font}", "MINIFY")
            _thread(lambda: process_single_css_file(font))  # pyright: ignore

    for t in css_threads:
        t.join()

    sys.stdout.close()
    sys.stdout = saved_stdout

    log("done minifying CSS", "MINIFY")

    return EXIT_OK, config


def build(config: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
    """build, minimise and generate site"""

    if not config["blogs"]:
        return log("no blogs to build"), config

    latest_blog_id: str = tuple(config["blogs"].keys())[-1]

    if os.path.isdir(config["blog-dir"]):
        rmtree(config["blog-dir"])

    os.makedirs(config["blog-dir"], exist_ok=True)

    log("building blogs ...", "INFO")

    def thread(blog_id: str, blog_meta: Dict[str, Any]):
        blog_dir: str = os.path.join(config["blog-dir"], blog_id)
        os.makedirs(blog_dir, exist_ok=True)

        with open(os.path.join(blog_dir, "index.html"), "w") as blog_html:
            blog_time: str = format_time(blog_meta["time"])

            blog_title: str = html_escape(blog_meta["title"])

            # 150 wpm is quite slow, but im compensating for people who
            # cant read that fast, especially with writing style of unprofessional people
            # who write blog posts -- like me

            read_time: str

            blog_base_html: str = markdown(
                BLOG_MARKDOWN_TEMPLATE
                % (
                    blog_title,
                    blog_time,
                    config["visitor-count"],
                    (read_time := read_time_of_markdown(blog_meta["content"], 150).text),  # type: ignore
                    config["comment-url"],
                    config["base-homepage"],
                    config["git-url"],
                    config["rss-feed"],
                    markdown(
                        blog_meta["content"],
                        extensions=[
                            *config["py-markdown-extensions"],
                            AriMarkdownExts(),
                        ],
                    )
                    .replace("<pre>", '<pre focusable="true" role="code" tabindex="0">')
                    .replace(
                        "<blockquote>", '<blockquote focusable="true" tabindex="0">'
                    ),
                )
            )

            blog_html_full: str = BLOG_HTML_TEMPLATE.format(
                title=config["page-title"],
                theme_type=config["colourscheme-type"],
                keywords=blog_meta["keywords"].replace(" ", ", ")
                + ", "
                + ", ".join(config["default-keywords"]),
                blog_description=f"blog post on {blog_time} UTC -- {blog_title}",
                blog_title=blog_title,
                blog=blog_base_html,
                author=config["full-name"],
                locale=config["locale"],
                read_time=read_time,  # type: ignore
                rss=config["rss-feed"],
            )

            log(f"minifying {blog_id!r} HTML", "MINIFY")
            blog_html_full = html_minify(blog_html_full)
            log(f"done minifying the HTML of {blog_id!r}", "MINIFY")

            blog_html.write(blog_html_full)

        log(f"finished building blog post {blog_id!r}", "BUILD")

    _tmp_threads: List[Thread] = []

    for blog_id, blog_meta in config["blogs"].items():
        t: Thread = Thread(target=thread, args=(blog_id, blog_meta), daemon=True)
        t.start()

        _tmp_threads.append(t)

    for awaiting_thread in _tmp_threads:
        awaiting_thread.join()

    log("building blog post index ...", "INFO")

    with open("index.html", "w") as index:
        lastest_blog: Dict[str, Any] = config["blogs"][latest_blog_id]
        lastest_blog_time: str = format_time(lastest_blog["time"])

        blog_list = '<ol reversed="true" aria-label="latest blogs">'

        for blog_id, blog_meta in reversed(config["blogs"].items()):
            blog_list += f'<li><a href="{os.path.join(config["blog-dir"], blog_id)}">{html_escape(blog_meta["title"])}</a></li>'

        blog_list += "</ol>"

        index.write(
            html_minify(
                HOME_PAGE_HTML_TEMPLATE.format(
                    title=config["page-title"],
                    theme_type=config["colourscheme-type"],
                    keywords=", ".join(config["home-keywords"])
                    + ", "
                    + ", ".join(config["default-keywords"]),
                    home_page_description=config["page-description"],
                    lastest_blog_time=lastest_blog_time,
                    latest_blog_url=os.path.join(config["blog-dir"], latest_blog_id),
                    latest_blog_title=truncate_str(
                        html_escape(lastest_blog["title"]), 20
                    ),
                    git_url=config["git-url"],
                    content=blog_list,
                    author=config["full-name"],
                    locale=config["locale"],
                    page_header=config["home-page-header"],
                    visitor=config["visitor-count"],
                    rss=config["rss-feed"],
                )
            )
        )

    return EXIT_OK, config


def list_blogs(config: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
    """list blogs"""

    if not config["blogs"]:
        return log("no blogs to list"), config

    for blog_id, blog_meta in config["blogs"].items():
        print(
            f"""ID : {blog_id}
title : {blog_meta["title"]!r}
time_of_creation : {format_time(blog_meta["time"])}
keywords : {blog_meta['keywords'].replace(" ", ", ")}
"""
        )

    return EXIT_OK, config


def remove_blog(config: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
    """remove a blog post"""

    if not config["blogs"]:
        return log("no blogs to remove"), config

    blog_id: str = pick_blog(config)

    if not blog_id:
        return EXIT_ERR, config

    del config["blogs"][blog_id]
    return EXIT_OK, config


def dummy(config: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
    """print help / usage information"""

    return EXIT_OK, config


def edit_title(blog: str, config: Dict[str, Any]) -> int:
    new_title: str = iinput(
        "edit title",
        config["blogs"][blog]["title"],
    )

    if not new_title.strip():
        return log("new title cannot be empty")

    config["blogs"][blog]["title"] = new_title.capitalize()

    return EXIT_OK


def edit_keywords(blog: str, config: Dict[str, Any]) -> int:
    new_keywords: str = iinput("edit keywords", config["blogs"][blog]["keywords"])

    if not new_keywords.strip():
        return log("keywords cannot be empty")

    config["blogs"][blog]["keywords"] = new_keywords

    return EXIT_OK


def edit_content(blog: str, config: Dict[str, Any]) -> int:
    file: str = tmp_path(f"{blog}.md")

    with open(file, "w") as blog_md:
        blog_md.write(config["blogs"][blog]["content"])

    editor(config, file)

    with open(file, "r") as blog_md_new:
        content: str = blog_md_new.read()

        if not content.strip():
            blog_md_new.close()
            return log("content of a blog post cannot be empty")

        config["blogs"][blog]["content"] = content

    return EXIT_OK


EDIT_HOOKS: Dict[str, Callable[[str, Dict[str, Any]], int]] = {
    "quit": lambda *_: EXIT_OK,  # pyright: ignore
    "title": edit_title,
    "keywords": edit_keywords,
    "content": edit_content,
}


def edit(config: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
    """edit a blog"""

    if not config["blogs"]:
        return log("no blogs to edit"), config

    blog_id: str = pick_blog(config)

    if not blog_id:
        return EXIT_ERR, config

    try:
        hook: str = FzfPrompt().prompt(  # pyright: ignore
            EDIT_HOOKS.keys(), "--prompt='what to edit : '"
        )[0]

        if hook not in EDIT_HOOKS:
            return log(f"hook {hook!r} does not exist"), config

        EDIT_HOOKS[hook](blog_id, config)
    except ProcessExecutionError:
        return log("no blog post selected"), config

    return EXIT_OK, config


def gen_def_config(config: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
    """generate default config"""

    if os.path.exists(DEFAULT_CONFIG_FILE):
        if iinput("do you want to overwite config ? ( y / n )").lower()[0] != "y":
            return log("not overwritting config", "INFO", EXIT_OK), config

    new_config()

    with open(DEFAULT_CONFIG_FILE, "r") as cfg:
        config = ujson.load(cfg)

    return EXIT_OK, config


def clean(config: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
    """clean up current directory"""

    TRASH: Set[str] = {
        HISTORY_FILE,
        config["blog-dir"],
        "index.html",
        "content/*.min.*",
        "blog_json_hash.txt",
        "manifest.json",
        "content/fonts/*.min.*",
        "recents_json_hash.txt",
        "recents.json",
        config["rss-feed"],
    }

    def remove(file: str) -> None:
        log(f"removing {file!r}", "REMOVE")

        try:
            os.remove(file)
        except IsADirectoryError:
            rmtree(file)

    for glob_ex in TRASH:
        for file in iglob(glob_ex, recursive=True):
            remove(file)

    open(HISTORY_FILE, "w").close()

    return EXIT_OK, config


def generate_metadata(config: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
    """generate metadata"""

    with open("manifest.json", "w") as manifest:
        log(f"generating {manifest.name} ...", "GENERATE")
        ujson.dump(
            {
                "$schema": "https://json.schemastore.org/web-manifest-combined.json",
                "short_name": config["short-name"],
                "name": config["page-title"],
                "description": config["page-description"],
                "icons": config["meta-icons"],
                "start_url": ".",
                "display": "standalone",
                "theme_color": config["theme-colour"],
                "background_color": config["background-colour"],
            },
            manifest,
        )

    with open("recents.json", "w") as blog_recents:
        log(f"generating {blog_recents.name!r}", "GENERATE")

        recents: Dict[str, Any] = {}

        for rid, recent in tuple(config["blogs"].items())[-(config["recents"]) :]:
            r: Dict[str, Any] = recent.copy()
            content: List[str] = r["content"].strip()[:196][::-1].split(maxsplit=1)

            r["content"] = content[len(content) > 1][::-1]
            del r["keywords"]

            recents[rid] = r

        ujson.dump(recents, blog_recents)

    for hashable in (DEFAULT_CONFIG_FILE, blog_recents.name):
        with open(hashable, "rb") as api_file:
            log(f"generating hash for {api_file.name!r}", "HASH")

            with open(
                f"{api_file.name.replace('.', '_')}_hash.txt", "w"
            ) as blog_api_hash:
                blog_api_hash.write(hashlib.sha256(api_file.read()).hexdigest())

    return EXIT_OK, config


def generate_rss(config: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
    """generate rss"""

    ftime: str = "%a, %d %b %Y %H:%M:%S GMT"
    now: datetime = datetime.utcnow()

    root: etree.Element = etree.Element("rss")
    root.set("version", "2.0")

    channel: etree.Element = etree.SubElement(root, "channel")

    etree.SubElement(channel, "title").text = config["page-title"]
    etree.SubElement(channel, "link").text = config["page-url"]
    etree.SubElement(channel, "description").text = config["page-description"]
    etree.SubElement(channel, "language").text = (
        config["locale"].lower().replace("_", "-")
    )
    etree.SubElement(channel, "lastBuildDate").text = now.strftime(ftime)

    for id, post in tuple(config["blogs"].items())[::-1]:
        content: List[str] = post["content"].strip()[:196][::-1].split(maxsplit=1)

        item: etree.Element = etree.SubElement(channel, "item")
        etree.SubElement(item, "title").text = post["title"]
        etree.SubElement(item, "link").text = (
            link := f'{config["page-url"]}{config["blog-dir"]}/{encode_url(id)}'
        )
        etree.SubElement(
            item, "description"
        ).text = f"{content[len(content) > 1][::-1]} ..."
        etree.SubElement(item, "pubDate").text = datetime.utcfromtimestamp(
            post["time"]
        ).strftime(ftime)
        etree.SubElement(item, "guid").text = link

    etree.ElementTree(root).write(config["rss-feed"])

    return EXIT_OK, config


def generate_static_full(config: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
    """generate full static site"""

    BUILD_CFG: Dict[str, Callable[[Dict[str, Any]], Tuple[int, Dict[str, Any]]]] = {
        "cleaning up": clean,
        "building CSS": build_css,
        "building static site": build,
        "generating metatata": generate_metadata,
        "generating rss": generate_rss,
    }

    for logger_msg, function in BUILD_CFG.items():
        log(f"{logger_msg} ...", "STATIC")
        code, config = function(config)

        if code != EXIT_OK:
            log("failed to generate static site")
            return EXIT_ERR, config

    return EXIT_OK, config


SUBCOMMANDS: Dict[str, Callable[[Dict[str, Any]], Tuple[int, Dict[str, Any]]]] = {
    "help": dummy,
    "new": new_blog,
    "build": build,
    "ls": list_blogs,
    "rm": remove_blog,
    "edit": edit,
    "defcfg": gen_def_config,
    "clean": clean,
    "metadata": generate_metadata,
    "static": generate_static_full,
    "css": build_css,
    "rss": generate_rss,
}


def usage(code: int = EXIT_ERR, _: Optional[Dict[str, Any]] = None) -> int:
    sys.stderr.write(f"usage : {sys.argv[0]} <subcommand>\n")

    for subcommand, func in SUBCOMMANDS.items():
        sys.stderr.write(f"  {subcommand:20s}{func.__doc__ or ''}\n")

    return code


def main() -> int:
    """entry / main function"""

    if NOT_CI_BUILD:
        if not os.path.isfile(HISTORY_FILE):
            open(HISTORY_FILE, "w").close()

        readline.parse_and_bind("tab: complete")

        fn_register(readline.write_history_file, HISTORY_FILE)
        fn_register(readline.read_history_file, HISTORY_FILE)

        readline.read_history_file(HISTORY_FILE)
        readline.set_history_length(5000)

        readline.set_auto_history(False)

    if not os.path.isfile(DEFAULT_CONFIG_FILE):
        new_config()
        log(f"please configure {DEFAULT_CONFIG_FILE!r}")
        return EXIT_ERR

    if len(sys.argv) != 2:
        return usage()
    elif sys.argv[1] not in SUBCOMMANDS:
        return log(f"{sys.argv[1]!r} is not a subcommand, try `{sys.argv[0]} help`")
    elif sys.argv[1] == "help":
        return usage(EXIT_OK)

    with open(DEFAULT_CONFIG_FILE, "r") as lcfg:
        cmd_time_init = code_timer()

        code: int
        config: Dict[str, Any]

        code, config = SUBCOMMANDS[sys.argv[1]](ujson.load(lcfg))

        log(
            f"finished in {code_timer() - cmd_time_init} seconds with code {code}",
            "TIME",
        )

        if config["blogs"] and NOT_CI_BUILD:
            log("Sorting blogs by creation time ...", "CLEANUP")

            sort_timer = code_timer()

            config["blogs"] = dict(
                map(
                    lambda k: (k, config["blogs"][k]),
                    sorted(config["blogs"], key=lambda k: config["blogs"][k]["time"]),
                )
            )

            log(f"sorted in {code_timer() - sort_timer} seconds", "TIME")

        log("redumping config", "CONFIG")

        dump_timer = code_timer()

        with open(DEFAULT_CONFIG_FILE, "w") as dcfg:
            ujson.dump(config, dcfg, indent=(4 if NOT_CI_BUILD else 0))

        log(f"dumped config in {code_timer() - dump_timer} seconds", "TIME")

    return code


if __name__ == "__main__":
    assert main.__annotations__.get("return") is int, "main() should return an integer"

    filter_warnings("error", category=Warning)
    raise SystemExit(main())
