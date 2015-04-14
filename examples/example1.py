from datetime import datetime
from flask import Flask
from flask_json import FlaskJSON, JsonErrorResponse, json_response

app = Flask(__name__)
FlaskJSON(app)


@app.route('/get_time')
def get_time():
    return json_response(time=datetime.utcnow())


@app.route('/raise_error')
def raise_error():
    raise JsonErrorResponse(description='Example text.', code=123)


if __name__ == '__main__':
    app.run()
