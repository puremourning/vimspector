if argc() < 2
  echom 'Usage:' v:argv[ 0 ] 'processName binary'
  cquit!
endif

setfiletype cpp
call vimspector#LaunchWithSettings( #{
      \ configuration: 'C++ - Attach Local Process',
      \ processName: argv( 0 ),
      \ binary: argv( 1 ),
      \ } )

1,2argd
