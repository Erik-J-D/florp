var socket = io.connect();

socket.on('new body', (...args) => { document.body.innerHTML = args[0] })
