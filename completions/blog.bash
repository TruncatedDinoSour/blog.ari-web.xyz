# blog completion                                     -*- shell-script -*-

_blog() {
    local cur

    _init_completion -s || return
    COMPREPLY=($(compgen -W "help new build list\
        rm edit new-config clean metadata static" -- "$cur"))

} && complete -F _blog -o bashdefault -o default blog

# ex: filetype=sh
