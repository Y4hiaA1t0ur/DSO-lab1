import os
from flask import Flask, jsonify, request, Response
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST

# Create the Flask app first ✅
app = Flask(__name__)

# Define a simple counter
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total number of HTTP requests',
    ['method', 'endpoint']
)

# Increment counter for every request
@app.before_request
def before_request():
    REQUEST_COUNT.labels(method=request.method, endpoint=request.path).inc()

# Metrics endpoint
@app.route("/metrics", methods=['GET'])
def metrics():
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)

# Your calculator route
@app.route('/calculate', methods=['GET'])
def calculate():
    op = request.args.get('op')
    a = float(request.args.get('a'))
    b = float(request.args.get('b'))

    if op == 'add':
        result = a + b
    elif op == 'sub':
        result = a - b
    elif op == 'mul':
        result = a * b
    elif op == 'div':
        result = a / b
    else:
        return jsonify({'error': 'Invalid operation'})

    return jsonify({'result': result})


if __name__ == "__main__":
    debug_mode = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    host = os.getenv("FLASK_HOST", "127.0.0.1")
    app.run(host=host, port=5000, debug=debug_mode) # nosec B104
