from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
import psutil
import time
from datetime import datetime

app = Flask(__name__)
socketio = SocketIO(app)

cpu_uses = []
memory_uses = []
timestampcoll = []

@app.route('/api/lastmin-stats', methods=['GET'])
def lastmin_stats():
    return jsonify({"cpu": cpu_uses, "memory":memory_uses,'timstamp':timestampcoll})

def resultshortner(arr):
    if len(arr) > 60:
        arr.pop(0)
    return arr
def get_server_stats():
    while True:
        memory = psutil.virtual_memory().percent
        memory_uses.append(memory)
        resultshortner(memory_uses)
        cpu = psutil.cpu_percent(interval=0.5)
        cpu_uses.append(cpu)
        resultshortner(cpu_uses)
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        timestampcoll.append(timestamp)
        resultshortner(timestampcoll)
        socketio.emit('update_stats', {'cpu': cpu, 'memory': memory, 'timstamp':timestamp})
        time.sleep(0.5)

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
