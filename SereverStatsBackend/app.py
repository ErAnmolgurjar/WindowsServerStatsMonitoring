from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import psutil
import time

# Initialize Flask app and SocketIO
app = Flask(__name__)
socketio = SocketIO(app)

# Function to get server stats
def get_server_stats():
    while True:
        # Get system stats using psutil
        memory = psutil.virtual_memory().percent
        cpu = psutil.cpu_percent(interval=1)  # This blocks for 1 second
        # Emit the stats via SocketIO every 1 second
        socketio.emit('update_stats', {'cpu': cpu, 'memory': memory})
        # Sleep for a while before getting stats again
        time.sleep(1)

@app.route('/')
def index():
    return render_template('index.html')

# Start the background thread when the app starts
def start_background_task():
    socketio.start_background_task(target=get_server_stats)

if __name__ == '__main__':
    # Start the background task before running the server
    start_background_task()
    socketio.run(app, debug=True)
