// Create a WebSocket connection to the Django Channels endpoint
const wsProtocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
const socket = new WebSocket(wsProtocol + '://' + window.location.host + '/ws/ec2_updates/');

// Listen for messages
socket.onmessage = function(e) {
    const data = JSON.parse(e.data);
    console.log(JSON.stringify(data, null, 2));

    const instances = data.instances;

    for (const key in instances) {
        if (instances.hasOwnProperty(key)) {
            const instance = instances[key];
            updateStatus(key, instance.status, instance.time_remaining)
        }
    }
};

socket.onopen = function(e) {
    console.log('WebSocket connection established');
};

socket.onclose = function(e) {
    console.error('WebSocket connection closed unexpectedly');
};