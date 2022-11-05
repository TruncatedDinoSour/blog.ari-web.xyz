#!/usr/bin/env sh

set -xe

main() {
    python3 scripts/blog.py clean

    git diff >/tmp/ari-web-blog.diff

    git add -A
    git commit -sam "${m:-"update @ $(date)"}"
    git push -u origin "$(git rev-parse --abbrev-ref HEAD)"
}

main "$@"
