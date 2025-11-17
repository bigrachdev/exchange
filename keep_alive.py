# keep_alive.py - Flask-based keep alive server for Render

import os
from flask import Flask, jsonify
from threading import Thread
import logging
from datetime import datetime

app = Flask('')

# Track last ping time
last_ping = datetime.now()

@app.route('/')
def home():
    global last_ping
    last_ping = datetime.now()
    return "🤖 TOPO EXCHANGE Bot is alive and running!"

@app.route('/health')
def health():
    global last_ping
    last_ping = datetime.now()
    return "OK", 200

@app.route('/status')
def status():
    global last_ping
    last_ping = datetime.now()
    uptime = (datetime.now() - start_time).total_seconds()
    return jsonify({
        "status": "online",
        "bot": "TOPO EXCHANGE",
        "message": "Bot is active and polling",
        "uptime_seconds": int(uptime),
        "last_ping": last_ping.strftime('%Y-%m-%d %H:%M:%S')
    })

@app.route('/ping')
def ping():
    """Dedicated ping endpoint"""
    global last_ping
    last_ping = datetime.now()
    return jsonify({
        "status": "pong",
        "timestamp": last_ping.strftime('%Y-%m-%d %H:%M:%S')
    })

# Track start time
start_time = datetime.now()

def run():
    """Run Flask app with production server"""
    port = int(os.environ.get('PORT', 10000))
    
    # Use waitress for production (more stable than Flask dev server)
    try:
        from waitress import serve
        logging.info(f"✅ Starting production server on port {port}")
        serve(app, host='0.0.0.0', port=port, threads=4)
    except ImportError:
        # Fallback to Flask dev server
        logging.warning("⚠️ Waitress not installed, using Flask dev server")
        app.run(host='0.0.0.0', port=port, threaded=True)

def keep_alive():
    """Start Flask server in a separate thread"""
    t = Thread(target=run, daemon=True)
    t.start()
    logging.info(f"✅ Keep-alive server started on port {os.environ.get('PORT', 10000)}")