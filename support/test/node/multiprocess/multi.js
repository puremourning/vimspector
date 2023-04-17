const cluster = require('node:cluster');
const http = require('node:http');
const process = require('node:process');

const fibSlow = function( i ) {
  if ( i < 2 ) {
    return i;
  }
  return fibSlow( i - 1 ) + fibSlow( i - 2 )
}

if (cluster.isPrimary) {
  console.log(`Primary ${process.pid} is running`);

  // Fork workers.
  const numWorkers = 4;
  workers = []
  for (let i = 0; i < numWorkers; i++) {
    const worker = cluster.fork();
    worker.on( 'message', (msg) => {
      console.log(`worker ${i} calculated: fib(${msg[0]}) = ${msg[1]}`);
    } );
    workers.push( worker );
  }

  cluster.on('exit', (worker, code, signal) => {
    console.log(`worker ${worker.process.pid} died`);
  });

  for ( let i = 0 ; i < 20 ; ++ i ) {
    workers[ i % numWorkers ].send( i );
  }
} else {
  console.log(`Worker ${process.pid} started`);
  process.on( 'message', (msg) => {
    process.send( [ msg, fibSlow( msg ) ] );
  } );
}
