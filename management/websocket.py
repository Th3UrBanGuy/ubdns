from flask_socketio import SocketIO, emit
import json
from monitoring.logger import QueryLogger

# This will be initialized in app.py with socketio instance
query_logger = QueryLogger()

def register_websocket_events(socketio):
    @socketio.on('connect', namespace='/query-stream')
    def handle_connect():
        emit('message', {'msg': 'Connected to query stream'})
    
    @socketio.on('disconnect', namespace='/query-stream')
    def handle_disconnect():
        print('Client disconnected from query stream')
    
    # This function will be called by the DNS resolver to push events
    def push_query_event(event_data):
        socketio.emit('query', event_data, namespace='/query-stream')
    
    return push_query_event
