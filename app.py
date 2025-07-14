from flask import Flask, request, jsonify, render_template
from pymongo import MongoClient
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

# Debug print to confirm environment variable loaded
print("MONGO_URI =", os.getenv("MONGO_URI"))

app = Flask(__name__)

# Connect to MongoDB with TLS workaround
client = MongoClient(os.getenv("MONGO_URI"), tls=True, tlsAllowInvalidCertificates=True)
db = client.webhookdb
events = db.events

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    event_type = request.headers.get('X-GitHub-Event')
    timestamp = datetime.utcnow().strftime("%d %B %Y - %I:%M %p UTC")

    if event_type == "push":
        author = data["pusher"]["name"]
        to_branch = data["ref"].split("/")[-1]
        msg = f'{author} pushed to {to_branch} on {timestamp}'

    elif event_type == "pull_request":
        action = data["action"]
        author = data["pull_request"]["user"]["login"]
        from_branch = data["pull_request"]["head"]["ref"]
        to_branch = data["pull_request"]["base"]["ref"]

        if data["pull_request"].get("merged", False):
            msg = f'{author} merged branch {from_branch} to {to_branch} on {timestamp}'
        else:
            msg = f'{author} submitted a pull request from {from_branch} to {to_branch} on {timestamp}'

    else:
        return jsonify({"msg": "Unhandled event"}), 400

    events.insert_one({"event": msg})
    return jsonify({"msg": "Event stored"}), 200

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/events')
def get_events():
    latest = events.find().sort("_id", -1).limit(10)
    return jsonify([e["event"] for e in latest])

if __name__ == "__main__":
    app.run(debug=True)
