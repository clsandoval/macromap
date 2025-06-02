from flask import Flask

app = Flask(__name__)


@app.route("/scan")
def scan():
    """Scan route that doesn't do anything yet"""
    return "Scan route - not implemented yet"


if __name__ == "__main__":
    app.run(debug=True)
