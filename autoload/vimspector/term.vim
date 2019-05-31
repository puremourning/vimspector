
let s:is_neovim = has('nvim')

function! vimspector#term#start ( args, opts )
  if s:is_neovim
    if get(a:opts, 'vertical', 0)
      vsplit
    end
    return termopen(a:args, a:opts)
  else
    return term_start(a:args, a:opts)
  end
endfunc
