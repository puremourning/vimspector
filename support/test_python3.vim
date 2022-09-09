let &verbosefile=argv(0)
" ffs neovim https://github.com/neovim/neovim/issues/14438
let ignored_neovim_bug = py3eval( "0" )
execute 'cquit' py3eval( "0" )
cquit
