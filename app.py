import base64
import tempfile
import threading
import uuid
from pathlib import Path

from flask import Flask, flash, jsonify, redirect, render_template, request, url_for
from werkzeug.utils import secure_filename

from utils import blur_license_plates, remove_license_plates_lama


app = Flask(__name__)
app.config["SECRET_KEY"] = "carforge-dev-secret"
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
jobs = {}
jobs_lock = threading.Lock()


def is_allowed_file(filename):
    return Path(filename).suffix.lower() in ALLOWED_EXTENSIONS


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/impressum", methods=["GET"])
def impressum():
    return render_template("impressum.html")


@app.route("/datenschutz", methods=["GET"])
def datenschutz():
    return render_template("datenschutz.html")


@app.route("/process", methods=["POST"])
def process_image():
    uploaded_file = request.files.get("image")
    method = request.form.get("method", "pixel")

    if not uploaded_file or uploaded_file.filename == "":
        return jsonify({"error": "Bitte Bild auswaehlen."}), 400

    if not is_allowed_file(uploaded_file.filename):
        return jsonify({"error": "JPG, PNG oder WebP."}), 400

    if method not in {"pixel", "lama"}:
        method = "pixel"

    safe_name = secure_filename(uploaded_file.filename)
    output_name = f"{Path(safe_name).stem or 'carforge'}_{method}.jpg"
    image_bytes = uploaded_file.read()
    job_id = uuid.uuid4().hex

    with jobs_lock:
        jobs[job_id] = {
            "status": "running",
            "percent": 0,
            "label": "Start",
            "filename": output_name,
            "method": method,
            "plate_count": None,
            "result_data_url": None,
            "error": None
        }

    thread = threading.Thread(
        target=run_processing_job,
        args=(job_id, image_bytes, safe_name, output_name, method),
        daemon=True
    )
    thread.start()

    return jsonify({"job_id": job_id})


def run_processing_job(job_id, image_bytes, input_name, output_name, method):
    def update_progress(percent, label):
        print(f"[{job_id[:8]}] {percent:3d}% {label}", flush=True)
        with jobs_lock:
            if job_id in jobs:
                jobs[job_id]["percent"] = percent
                jobs[job_id]["label"] = label

    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            temp_path = Path(temp_dir)
            input_path = temp_path / input_name
            output_path = temp_path / output_name
            input_path.write_bytes(image_bytes)

            if method == "lama":
                plate_count = remove_license_plates_lama(
                    input_path=str(input_path),
                    output_path=str(output_path),
                    show_progress=False,
                    progress_callback=update_progress
                )
            else:
                plate_count = blur_license_plates(
                    input_path=str(input_path),
                    output_path=str(output_path),
                    mode="pixel",
                    show_progress=False,
                    progress_callback=update_progress
                )

            result_base64 = base64.b64encode(output_path.read_bytes()).decode("ascii")
            result_data_url = f"data:image/jpeg;base64,{result_base64}"

            with jobs_lock:
                jobs[job_id].update({
                    "status": "done",
                    "percent": 100,
                    "label": "Fertig",
                    "plate_count": plate_count,
                    "result_data_url": result_data_url
                })
        except Exception as error:
            print(f"[{job_id[:8]}] Fehler: {error}", flush=True)
            with jobs_lock:
                jobs[job_id].update({
                    "status": "error",
                    "label": "Fehler",
                    "error": str(error)
                })


@app.route("/status/<job_id>", methods=["GET"])
def job_status(job_id):
    with jobs_lock:
        job = jobs.get(job_id)

    if not job:
        return jsonify({"error": "Job nicht gefunden."}), 404

    return jsonify({
        "status": job["status"],
        "percent": job["percent"],
        "label": job["label"],
        "error": job["error"]
    })


@app.route("/result/<job_id>", methods=["GET"])
def result(job_id):
    with jobs_lock:
        job = jobs.get(job_id)

    if not job:
        flash("Ergebnis nicht mehr verfuegbar.")
        return redirect(url_for("index"))

    if job["status"] != "done":
        return redirect(url_for("index"))

    html = render_template(
        "result.html",
        filename=job["filename"],
        method=job["method"],
        plate_count=job["plate_count"],
        result_data_url=job["result_data_url"]
    )

    with jobs_lock:
        jobs.pop(job_id, None)

    return html


@app.errorhandler(413)
def file_too_large(error):
    flash("Das Bild ist zu gross. Maximal erlaubt sind 16 MB.")
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
