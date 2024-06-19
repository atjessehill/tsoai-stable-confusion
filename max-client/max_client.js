var WebSocketClient = require('websocket').client;
const maxApi = require("max-api");

let client = new WebSocketClient();

client.on('connectFailed', function(error) {
    console.log('Connect Error: ' + error.toString());
});

client.on('connect', function(connection) {
    console.log('WebSocket Client Connected');
    connection.on('error', function(error) {
        console.log("Connection Error: " + error.toString());
    });
    connection.on('close', function() {
        console.log('echo-protocol Connection Closed');
    });
    connection.on('message', function(message) {
        maxApi.post(`Received Message: ${message.utf8Data}`);
//        if (message.type === 'utf8') {
//            console.log("Received: '" + message.utf8Data + "'");
//        }
    });

    maxApi.addHandler('input', (dir) => {
        connection.send(JSON.stringify({
			'type': 'note',
			'noteInfo': {
			  'value': dir
			}
		}))
    });

});



client.connect('ws://localhost:9999/feed', null, null, {
    'Sec-WebSocket-Protocol': 'subprotocols'
});
