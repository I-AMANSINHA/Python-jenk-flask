from flask import Flask
from db import get_connection

app = Flask(__name__)

@app.route("/")
def home():

    conn = get_connection()

    cur = conn.cursor()

    cur.execute("SELECT version();")

    version = cur.fetchone()

    cur.close()
    conn.close()

    return f"Connected to PostgreSQL: {version[0]}"


@app.route("/health")
def health():
    return "UP"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
