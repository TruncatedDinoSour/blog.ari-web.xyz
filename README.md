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
