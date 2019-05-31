" wincmd s
" enew

" func! s:TextEntered(text)
  " if a:text == 'exit' || a:text == 'quit'
    " stopinsert
    " close
  " else
    " call append(line('$') - 1, 'Entered: "' . a:text . '"')
    " " Reset 'modified' to allow the buffer to be closed.
    " set nomodified
  " endif
" endfunc

" if has('nvim')
  " call buffer_prompt#set_callback(bufnr(''), function('s:TextEntered'))
" else
  " set buftype=prompt
  " call prompt_setcallback(bufnr(''), function('s:TextEntered'))
" end

let s:is_vim = !has('nvim')

function! s:is_buftype_prompt(buf)
  if s:is_vim
    return getbufvar(a:buf, '&buftype') == 'prompt'
  else
    return getbufvar(a:buf, 'is_prompt_buffer') == v:true
  end
endfunc

function! s:set_buftype_prompt(buf, value)
  if a:value
    if s:is_buftype_prompt(a:buf)
      return
    end

    if s:is_vim
      call setbufvar(a:buf, '&buftype', 'prompt')
    else
      call s:start_buffer_prompt(a:buf)
    end
  else
    if !s:is_buftype_prompt(a:buf)
      return
    end

    if s:is_vim
      call setbufvar(a:buf, '&buftype', '')
    else
      call s:stop_buffer_prompt(a:buf)
    end
  end
endfunc

function! s:start_buffer_prompt(buf)
  call setbufvar(a:buf, 'is_prompt_buffer', v:true)
  call setbufvar(a:buf, 'prompt_buffer_callback', v:null)
  call setbufvar(a:buf, 'prompt_buffer_prompt', '% ')

  let current_buffer = bufnr('')
  noautocmd exec 'buffer ' . a:buf
  call setline('$', b:prompt_buffer_prompt)

  nnoremap <buffer><silent> i         :call <SID>do_insert()<CR>
  nnoremap <buffer><silent> a         :call <SID>do_append()<CR>
  nnoremap <buffer><silent> A         :call <SID>do_append_end()<CR>
  nnoremap <buffer><silent> <CR>      :call <SID>enter_prompt()<CR>
  inoremap <buffer><silent> <CR> <C-O>:call <SID>enter_prompt()<CR>
  noautocmd exec 'buffer ' . current_buffer
endfunc

function! s:stop_buffer_prompt(buf)
  call setbufvar(a:buf, 'is_prompt_buffer', v:false)

  let current_buffer = bufnr('')
  noautocmd exec 'buffer ' . a:buf
  nunmap <buffer> i
  nunmap <buffer> a
  nunmap <buffer> A
  nunmap <buffer> <CR>
  iunmap <buffer> <CR>
  noautocmd exec 'buffer ' . current_buffer
endfunc

function! s:enter_prompt()
  let current_buf = v:null
  let buf = bufnr('')
  let input = getline('$')[len(b:prompt_buffer_prompt):]
  normal! o
  stopinsert
  call b:prompt_buffer_callback(input)

  if !bufexists(buf)
    return
  end

  let current_buf = bufnr('')

  if current_buf != buf
    noautocmd exec 'buffer ' . buf
  end

  call append(line('$') - 1, b:prompt_buffer_prompt)
  normal! Gdd

  if current_buf != buf
    noautocmd exec 'buffer ' . current_buf
  else
    call s:do_insert()
  end
endfunc

function! s:do_insert ()
  let target_col = max([col('.'), len(b:prompt_buffer_prompt) + 1])
  startinsert
  call setpos('.', [bufnr(''), line('$'), target_col, 0, target_col])
endfunc

function! s:do_append ()
  let target_col = max([col('.') + 1, len(b:prompt_buffer_prompt) + 1])
  startinsert
  call setpos('.', [bufnr(''), line('$'), target_col, 0, target_col])
endfunc

function! s:do_append_end ()
  let target_col = len(getline('$')) + 1
  startinsert
  call setpos('.', [bufnr(''), line('$'), target_col, 0, target_col])
endfunc


" API

function! buffer_prompt#set_callback(buf, expr)
  if a:expr != ''
    call s:set_buftype_prompt(a:buf, v:true)

    if s:is_vim
      call prompt_setcallback(a:buf, a:expr)
    else
      call setbufvar(a:buf, 'prompt_buffer_callback', a:expr)
    end
  else
    if s:is_vim
      call prompt_setcallback(a:buf, a:expr)
    else
      call setbufvar(a:buf, 'prompt_buffer_callback', v:null)
    end

    call s:set_buftype_prompt(a:buf, v:false)
  end
endfunc

function! buffer_prompt#set_prompt(buf, expr)
  if s:is_vim
    call prompt_setprompt(a:buf, a:expr)
  else
    call setbufvar(a:buf, 'prompt_buffer_prompt', a:expr)
  end
endfunc
