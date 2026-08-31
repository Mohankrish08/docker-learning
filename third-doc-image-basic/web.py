
import os
from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    if not os.path.exists("/data/messages.txt"):
        lines = ["(waiting for the writer container...)"]
    else:
        with open("/data/messages.txt") as f:
            lines = f.readlines()

    # refresh the page every 2 seconds so we can watch it grow
    return f"""
    <meta http-equiv="refresh" content="2">
    <h1>Messages: {len(lines)}</h1>
    <pre>{"".join(lines)}</pre>
    """

app.run(host="0.0.0.0", port=5000)
