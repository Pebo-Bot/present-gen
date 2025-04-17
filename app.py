from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from uuid import uuid4
from pathlib import Path
from presentation import PresentationManager
import os
from threading import Thread
from flask import jsonify

generation_status = {}           # {pres_id: "in‑progress" | "done" | "error"}


app = Flask(__name__)

pm = PresentationManager()

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/presentations/<pres_id>/")
def player(pres_id):
    return render_template(
        "player.html",
        pres_id=pres_id,
        slides_url=url_for("static", filename=f"generated/{pres_id}/slides/index.html"),
    )

@app.route("/presentations/<pres_id>/assets/<path:filename>")
def pres_asset(pres_id, filename):
    base = Path(app.root_path) / "static" / "generated" / pres_id
    return send_from_directory(base, filename)
def _run_generation(topic, depth, pres_id):
    try:
        pm.generate(topic, depth, pres_id)
        generation_status[pres_id] = "done"
    except Exception as e:
        generation_status[pres_id] = f"error: {e}"

@app.route("/generate", methods=["POST"])
def generate():
    topic = request.form["topic"].strip()
    depth = request.form["depth"].strip()
    pres_id = uuid4().hex
    generation_status[pres_id] = "in‑progress"
    Thread(target=_run_generation, args=(topic, depth, pres_id), daemon=True).start()
    return redirect(url_for("generating", pres_id=pres_id))

@app.route("/generating/<pres_id>/")
def generating(pres_id):
    return render_template("generating.html", pres_id=pres_id)

@app.route("/status/<pres_id>.json")
def status(pres_id):
    return jsonify({"state": generation_status.get(pres_id, "unknown")})
    
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.getenv("PORT", 8080)))
