from flask import Flask, request, jsonify
import subprocess
import socket

app = Flask(__name__)

@app.route('/get_port/<ip>/<int:start>/<int:end>', methods=['GET'])
def get_available_port(ip, start, end):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    for port in range(start, end):
        try:
            s.bind((ip, port))
            s.close()
            return jsonify({'port': port})
        except OSError:
            continue
    return jsonify({'error': 'No available port found'})


@app.route('/run', methods=['POST'])
def run_command():
    command = request.json['command']
    process = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
    # run the process with exit code
    output, error = process.communicate()
    exit_code = process.wait()

    return {
        'output': output.decode('utf-8'),
        'error': error,
        'exit_code': exit_code
    }

if __name__ == '__main__':
    # run app on 0.0.0.0:8888
    app.run(host='0.0.0.0', port=8888, debug=True)