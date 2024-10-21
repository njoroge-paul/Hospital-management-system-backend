from flask import Flask
from db import db

app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'Hello, World!'

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)