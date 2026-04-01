from pathlib import Path
import subprocess
import sys
from typing import Optional

from flask import Flask, abort, render_template, request, send_file, send_from_directory


BASE_DIR = Path(__file__).resolve().parent
RESULT_DIR = BASE_DIR / "result"
ADDRESSES_FILE = BASE_DIR / "adresses.csv"
LOCATIONS_FILE = BASE_DIR / "locations.csv"

app = Flask(__name__)


def save_uploaded_csv(uploaded_file, destination: Path) -> None:
    raw_bytes = uploaded_file.read()
    encodings = ("utf-8", "utf-8-sig", "cp1252", "latin-1")
    decoded_text = None

    for encoding in encodings:
        try:
            decoded_text = raw_bytes.decode(encoding)
            break
        except UnicodeDecodeError:
            continue

    if decoded_text is None:
        raise UnicodeDecodeError("unknown", raw_bytes, 0, len(raw_bytes), "Impossible de decoder le CSV")

    destination.write_text(decoded_text, encoding="utf-8")


def run_python_script(script_name: str) -> dict:
    script_path = BASE_DIR / script_name
    completed = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=BASE_DIR,
        capture_output=True,
        text=True,
        check=False,
    )
    return {
        "script": script_name,
        "ok": completed.returncode == 0,
        "returncode": completed.returncode,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
    }


def find_latest_map() -> Optional[Path]:
    if not RESULT_DIR.exists():
        return None

    maps = sorted(
        (
            item for item in RESULT_DIR.glob("map_*.html")
            if item.name != "map_latest.html"
        ),
        key=lambda item: item.stat().st_mtime,
        reverse=True,
    )
    return maps[0] if maps else None


@app.route("/", methods=["GET", "POST"])
def index():
    execution_results = []
    previous_map = None
    newly_generated_map = None

    if request.method == "POST":
        action = request.form.get("action", "").strip().lower()

        if action == "upload_csv":
            uploaded_file = request.files.get("csv_file")
            if uploaded_file and uploaded_file.filename:
                previous_map = find_latest_map()
                save_uploaded_csv(uploaded_file, LOCATIONS_FILE)
                execution_results.append(
                    {
                        "script": "upload_csv",
                        "ok": True,
                        "returncode": 0,
                        "stdout": f"Fichier charge : {LOCATIONS_FILE.name}",
                        "stderr": "",
                    }
                )
                execution_results.append(run_python_script("mapping.py"))
                if execution_results[-1]["ok"]:
                    newly_generated_map = find_latest_map()
            else:
                execution_results.append(
                    {
                        "script": "upload_csv",
                        "ok": False,
                        "returncode": 1,
                        "stdout": "",
                        "stderr": "Aucun fichier CSV n'a ete fourni.",
                    }
                )
        elif action == "geocode":
            execution_results.append(run_python_script("coordinates.py"))
        elif action == "map":
            previous_map = find_latest_map()
            execution_results.append(run_python_script("mapping.py"))
            if execution_results[-1]["ok"]:
                newly_generated_map = find_latest_map()
        elif action == "all":
            execution_results.append(run_python_script("coordinates.py"))
            if execution_results[-1]["ok"]:
                previous_map = find_latest_map()
                execution_results.append(run_python_script("mapping.py"))
                if execution_results[-1]["ok"]:
                    newly_generated_map = find_latest_map()

    latest_map = find_latest_map()
    latest_map_version = int(latest_map.stat().st_mtime) if latest_map else None
    previous_map_version = int(previous_map.stat().st_mtime) if previous_map else None
    newly_generated_map_version = int(newly_generated_map.stat().st_mtime) if newly_generated_map else None
    return render_template(
        "index.html",
        latest_map=latest_map.name if latest_map else None,
        latest_map_version=latest_map_version,
        previous_map=previous_map.name if previous_map else None,
        previous_map_version=previous_map_version,
        newly_generated_map=newly_generated_map.name if newly_generated_map else None,
        newly_generated_map_version=newly_generated_map_version,
        locations_exists=LOCATIONS_FILE.exists(),
        execution_results=execution_results,
    )


@app.route("/result/<path:filename>")
def serve_result(filename: str):
    response = send_from_directory(RESULT_DIR, filename, max_age=0)
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


@app.route("/download/map")
def download_latest_map():
    latest_map = find_latest_map()
    if latest_map is None:
        abort(404, description="Aucune carte generee.")
    return send_file(latest_map, as_attachment=True, download_name=latest_map.name)


@app.route("/download/locations")
def download_locations():
    if not LOCATIONS_FILE.exists():
        abort(404, description="Le fichier locations.csv est introuvable.")
    return send_file(LOCATIONS_FILE, as_attachment=True, download_name="locations.csv")


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
