from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import psutil
import time
from datetime import datetime

app = Flask(__name__)
socketio = SocketIO(app)

def get_server_stats():
    while True:
        memory = psutil.virtual_memory().percent
        cpu = psutil.cpu_percent(interval=0.5)
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        socketio.emit('update_stats', {'cpu': cpu, 'memory': memory, 'timstamp':timestamp})
        #time.sleep(1)

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
