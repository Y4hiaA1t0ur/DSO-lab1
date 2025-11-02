import os

from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST
from flask import Response, request

# Define a simple counter
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total number of HTTP requests',
    ['method', 'endpoint']
)

@app.before_request
def before_request():
    REQUEST_COUNT.labels(method=request.method, endpoint=request.path).inc()

@app.route("/metrics")
def metrics():
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)

app = Flask(__name__)


@app.route('/calculate', methods=['GET'])
def calculate():
    op = request.args.get('op')  # operation: add, sub, mul, div
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
    app.run(host="0.0.0.0", port=5000, debug=debug_mode) # nosec B104
