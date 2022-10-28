from flask import Flask
from waitress import serve
from data import db_session

app = Flask(__name__)
app.config['SECRET_KEY'] = 'test_secret_key'


@app.route('/')
def base():
    return ''


def main():
    db_session.global_init("db/conventus.db")
    serve(app, host='0.0.0.0', port=5000)


if __name__ == '__main__':
    main()
