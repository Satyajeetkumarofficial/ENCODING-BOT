from flask import Flask
import threading

app = Flask(__name__)

@app.route("/")
def home():
    return "OK", 200

def run():
    app.run(host="0.0.0.0", port=8080)

threading.Thread(target=run, daemon=True).start()
