from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.utils import secure_filename

import os
import uuid
import json

from ai import analyze_resume


app = Flask(__name__)

app.secret_key = "jobs-ai-development-key"


RESUME_FOLDER = "resumes"
ANALYSIS_FOLDER = "analysis"

os.makedirs(RESUME_FOLDER, exist_ok=True)
os.makedirs(ANALYSIS_FOLDER, exist_ok=True)


ALLOWED_EXTENSIONS = {"pdf"}


def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/option1", methods=["GET", "POST"])
def option1():

    # --------------------------------
    # UPLOAD RESUME
    # --------------------------------

    if request.method == "POST":

        file = request.files.get("resume")

        if not file or file.filename == "":
            return render_template(
                "option1.html",
                error="Please select a resume."
            )

        if not allowed_file(file.filename):
            return render_template(
                "option1.html",
                error="Only PDF files are allowed."
            )

        # Delete previous resume if one exists
        old_resume = session.get("resume_path")

        if old_resume and os.path.exists(old_resume):
            os.remove(old_resume)

        # Delete previous analysis
        old_analysis = session.get("analysis_path")

        if old_analysis and os.path.exists(old_analysis):
            os.remove(old_analysis)

        # Clean original filename
        original_filename = secure_filename(file.filename)

        # Unique ID
        resume_id = uuid.uuid4().hex

        filename = f"{resume_id}_{original_filename}"

        file_path = os.path.join(
            RESUME_FOLDER,
            filename
        )

        # Save PDF
        file.save(file_path)

        # Store resume information in session
        session["resume_path"] = file_path
        session["resume_filename"] = original_filename

        # --------------------------------
        # ANALYZE RESUME AUTOMATICALLY
        # --------------------------------

        try:

            analysis = analyze_resume(file_path)

            analysis_filename = f"{resume_id}.json"

            analysis_path = os.path.join(
                ANALYSIS_FOLDER,
                analysis_filename
            )

            with open(
                analysis_path,
                "w",
                encoding="utf-8"
            ) as f:

                json.dump(
                    analysis,
                    f,
                    indent=4,
                    ensure_ascii=False
                )

            session["analysis_path"] = analysis_path

        except Exception as e:

            print("AI analysis error:", e)

            return render_template(
                "option1.html",
                resume_filename=original_filename,
                error="Resume uploaded, but AI analysis failed."
            )

        return redirect(url_for("option1"))

    # --------------------------------
    # DISPLAY DASHBOARD
    # --------------------------------

    resume_filename = session.get("resume_filename")
    analysis_path = session.get("analysis_path")

    analysis = None

    if analysis_path and os.path.exists(analysis_path):

        with open(
            analysis_path,
            "r",
            encoding="utf-8"
        ) as f:

            analysis = json.load(f)

    return render_template(
        "option1.html",
        resume_filename=resume_filename,
        analysis=analysis
    )


@app.route("/clear_resume", methods=["POST"])
def clear_resume():

    resume_path = session.get("resume_path")
    analysis_path = session.get("analysis_path")

    if resume_path and os.path.exists(resume_path):
        os.remove(resume_path)

    if analysis_path and os.path.exists(analysis_path):
        os.remove(analysis_path)

    session.pop("resume_path", None)
    session.pop("resume_filename", None)
    session.pop("analysis_path", None)

    return redirect(url_for("option1"))


@app.route("/option2")
def option2():
    return render_template("option2.html")


if __name__ == "__main__":
    app.run(debug=True)