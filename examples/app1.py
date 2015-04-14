from datetime import datetime
from flask import Flask, request
from flask_json import FlaskJSON, JsonErrorResponse, json_response

app = Flask(__name__)
FlaskJSON(app)


@app.route('/get_time')
def get_time():
    now = datetime.utcnow()
    return json_response(time=now)


@app.route('/increment_value', methods=['POST'])
def increment_value():
    # We use 'force' to skip mimetype checking to have shorter curl command.
    data = request.get_json(force=True)
    try:
        value = int(data['value'])
    except (KeyError, TypeError, ValueError):
        raise JsonErrorResponse(description='Invalid value.')
    return json_response(value=value + 1)


if __name__ == '__main__':
    app.run()
