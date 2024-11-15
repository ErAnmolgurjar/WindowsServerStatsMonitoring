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
        time.sleep(1)

@app.route('/api/process_stats', methods=['GET'])
def get_process_stats():
    process_stats = {}
    num_cores = psutil.cpu_count()
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
        try:
            cpu_percent_scaled = proc.info['cpu_percent'] / num_cores
            name = proc.info['name']
            pid = proc.info['pid']
            cpu_percent = cpu_percent_scaled
            #cpu_percent = proc.info['cpu_percent']
            memory_percent = proc.info['memory_percent']
            
            if name not in process_stats:
                process_stats[name] = {
                    'name': name,
                    'pids': [pid],
                    'cpu_percent': cpu_percent,
                    'memory_percent': memory_percent
                }
            else:
                process_stats[name]['pids'].append(pid)
                process_stats[name]['cpu_percent'] += cpu_percent
                process_stats[name]['memory_percent'] += memory_percent

        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue

    result = []
    for name, data in process_stats.items():
        result.append({
            'name': name,
            'pids': ','.join(map(str, data['pids'])),
            'cpu_percent': data['cpu_percent'],
            'memory_percent': data['memory_percent']
        })
    process_stats = sorted(result, key=lambda x: x['cpu_percent'], reverse=True)
    return jsonify({"processes":process_stats })

@app.route('/api/terminate-processes', methods=['POST'])
def terminate_processes():
    try:
        pids_string = request.json.get('pids', '')
        
        if not pids_string:
            return jsonify({"error": "No PIDs provided"}), 400
        
        pids = [int(pid) for pid in pids_string.split(',')]
        
        terminated = []
        failed = []
        
        for pid in pids:
            try:
                process = psutil.Process(pid)
                process.terminate()
                process.wait(timeout=3)
                
                terminated.append(pid)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as e:
                failed.append({'pid': pid, 'error': str(e)})
        
        if terminated:
            response = {"status": "success", "terminated": terminated}
        if failed:
            response = response or {"status": "failure", "failed": failed}

        return jsonify(response)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

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
