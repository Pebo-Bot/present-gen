from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from uuid import uuid4
from pathlib import Path
from presentation import PresentationManager
import os

app = Flask(__name__)

pm = PresentationManager()

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/generate", methods=["POST"])
def generate():
    topic = request.form.get("topic", "").strip()
    depth = request.form.get("depth", "intro").strip()
    if not topic:
        return "Topic required", 400

    pres_id = uuid4().hex
    pm.generate(topic, depth, pres_id)  # synchronous for POC

    return redirect(url_for("player", pres_id=pres_id))

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

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
