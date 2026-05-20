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
@app.route("/metrics", methods=["GET"])
def metrics():
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)


def _calculate_result(op: str, a: float, b: float):
    if op == 'add':
        return a + b
    if op == 'sub':
        return a - b
    if op == 'mul':
        return a * b
    if op == 'div':
        return a / b
    return None


# Your calculator route
@app.route('/calculate', methods=['GET'])
def calculate():
    op = request.args.get('op')
    a = float(request.args.get('a'))
    b = float(request.args.get('b'))

    result = _calculate_result(op, a, b)
    if result is None:
        return jsonify({'error': 'Invalid operation'})

    return jsonify({'result': result})

if __name__ == "__main__":
    debug_mode = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    host = os.getenv("FLASK_HOST", "127.0.0.1")
    app.run(host=host, port=5000, debug=debug_mode)  # nosec B104
