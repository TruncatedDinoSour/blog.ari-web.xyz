#!/usr/bin/env sh

set -xe

main() {
    python3 scripts/blog clean || true

    git add -A
    git commit -sam "update @ $(date)"
    git push -u origin "$(git rev-parse --abbrev-ref HEAD)"
}

main "$@"
