# [ari-web blogs](https://blog.ari-web.xyz/)

<p align="center">
  <img src="https://img.shields.io/badge/Maintained-Yes-green?color=red&style=flat-square">
  <img src="https://img.shields.io/github/last-commit/TruncatedDinosour/blog.ari-web.xyz?color=red&style=flat-square">
  <img src="https://img.shields.io/github/repo-size/TruncatedDinosour/blog.ari-web.xyz?color=red&style=flat-square">
  <img src="https://img.shields.io/github/issues/TruncatedDinosour/blog.ari-web.xyz?color=red&style=flat-square">
  <img src="https://img.shields.io/github/stars/TruncatedDinosour/blog.ari-web.xyz?color=red&style=flat-square">
</p>

<p align="center">
  <a href="https://app.netlify.com/sites/blog-ari-web/deploys"><img src="https://api.netlify.com/api/v1/badges/bbd7d670-9152-41a8-8c99-df57e4669606/deploy-status"></a>
</p>

## installing dependencies

```sh
$ python3 -m virtualenv venv
$ . venv/bin/activate
$ pip install -r requirements.txt
```

Or

```sh
$ python3 -m pip install --user -r requirements.txt
```

## completions

-   bash

```bash
$ . completions/blog.bash
```

## building

-   generate full-on static site

```bash
$ CI=1 ./scripts/blog static
```

-   only build blogs

```bash
$ CI=1 ./scripts/blog static
```

`CI` environment variable is optional,
though setting it in a build/CI environment is good
to save time on some operations that are useless
in that context, for example sorting blogs.

`CI` can have any value.

## the API

-   <https://blog.ari-web.xyz/b/ari-web-blog-api-change/>
-   <https://blog.ari-web.xyz/b/ari-web-apis--how-to-use-them/>

## why ari-web blog manager

-   writer friendly -- uses markdown, keeps tracks of dates useful custom markdown extensions, support for editing, removal of posts,, and u can style ur blog the way you want it to b using css, easy build directory cleanup, support for custom fonts, locales, licenses, etc
-   reader friendly -- the blog posts are sorted from newest to oldest making it easy to get latest blog posts, they can also get a shortcut on their device as it has a `manifest.json` so they can open ur blog as an app, also support for an rss feed meaning ur users can subscribe to ur blog to get latest posts on their rss feeder app
-   writer-developer friendly -- the script is easily extensible by developers, markdown extensions, etc,, testing of each component using subcommands and a built-in testing http server
-   reader-developer friendly -- api access to latest blog posts and ur blog as a whole though `blog.json`, apis are hashed and minified
-   search engine optimization ( seo ) -- generator tries to follow best seo practices and adds a bunch of metadata not only in html but in other files too -- `robots.txt`, `manifest.json`, `sitemap.xml`, `rss.xml` and ofc the apis ( `recents.json`, `recents_json_hash.txt`, `blog_json_hash.txt` )
-   payload size -- generator generates minified content ( all apis, `rss.xml`, generated html of blog posts and home page, all css and fonts ) making it fast to load for readers
-   accessibility -- the blog generator follows best a11y practices making it easy for people with disabilities to read ur posts
-   google pagespeed optimized -- this metric shows us how accessible and fast our pages r and this generator tries to optimize for it
-   fast -- the generator uses fast libraries, data structures and threading, it doesnt import useless libraries in build time ( unless theyre pointless to exclude ), meaning its very quick to build ur blog into a full-blown static website
-   open source -- this generator and all of the content on it are licensed under gplv3 and the code and content are free to the public making it open source
-   overall pleasant experience to grow ur blog :)
