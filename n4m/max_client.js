var WebSocketClient = require('websocket').client;
const maxApi = require("max-api");

let client = new WebSocketClient();

client.on('connectFailed', function(error) {
    console.log('Connect Error: ' + error.toString());
});

function sendToMax(eventTime, intervalMS, delay, category, velocity, interval, rand, i) {
    const currTime = Date.now();
    const expTime = eventTime + intervalMS;
	maxApi.post(`${eventTime}, ${delay}, ${intervalMS}, ${currTime}`)
    maxApi.outlet(category, velocity, interval, rand)
}

client.on('connect', function(connection) {
    console.log('WebSocket Client Connected');
    connection.on('error', function(error) {
        console.log("Connection Error: " + error.toString());
    });
    connection.on('close', function() {
        console.log('echo-protocol Connection Closed');
    });
    connection.on('message', function(message) {

        const jsonString = message.utf8Data.replace(/'/g, '"');
        const respObj = JSON.parse(jsonString);
        const eventTime = respObj['eventTime'];
		const events = respObj['predictedEvents'];

		for (let i = 0; i < events.length; i++) {

            const category = events[i][0]
            const intervalMS = events[i][1];
            const velocity = events[i][2]
            const randPlaceholder = events[i][3]

            // the time we expect the event
            const delay = (eventTime + intervalMS) - Date.now();

            setTimeout(() => {
                Promise.resolve().then(() => sendToMax(eventTime, intervalMS, delay, category, velocity, intervalMS, randPlaceholder, i));
            }, delay);

		}

    });

    maxApi.addHandler('input', (dir) => {

        var currentDate = new Date();

        // Get the Unix time in milliseconds and convert it to seconds
        var unixTime = currentDate.getTime()

        connection.send(JSON.stringify({
			'type': 'note',
			'noteInfo': {
			  'value': dir
			},
			'clientTime': unixTime
		}))

    });

});



client.connect('ws://localhost:9998/feed', null, null, {
    'Sec-WebSocket-Protocol': 'subprotocols'
});
