import json
import os
from functools import wraps
from flask import Flask, request, jsonify, render_template, redirect, url_for, session, flash, abort
from flask_wtf.csrf import CSRFProtect
from config import Config
from analyzer.full_analyzer import analyze_full_code
from analyzer.ai_analyzer import fix_code, teach_code, find_errors
from databases.users_db import (
    register_user,
    verify_user,
    get_user_by_id,
    update_user_profile,
    update_user_preferences,
    change_user_password
)
from databases.analysis_db import save_analysis, list_analyses, get_analysis, delete_analysis
from databases.reports_db import create_report, list_reports, get_report
from databases.feedback_db import save_feedback

app = Flask(__name__)
app.config.from_object(Config)
csrf = CSRFProtect(app)
SUPPORTED_LANGUAGES = {"python", "c", "cpp", "c++", "java"}


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "info")
            return redirect(url_for("login", next=request.path))
        return view(*args, **kwargs)
    return wrapped_view


def api_login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({"error": "Your session has expired. Please log in again."}), 401
        return view(*args, **kwargs)
    return wrapped_view


def current_user():
    return {"id": session.get("user_id"), "full_name": session.get("user_name"), "email": session.get("user_email")}


@app.route("/")
def home():
    return redirect(url_for("dashboard")) if session.get("user_id") else render_template("home.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if session.get("user_id"):
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")
        if not full_name or not email or not password:
            flash("Please complete all required fields.", "error")
        elif len(full_name) > 150 or len(email) > 255:
            flash("Name or email is too long.", "error")
        elif len(password) < 8 or len(password) > 128:
            flash("Password must contain between 8 and 128 characters.", "error")
        elif password != confirm:
            flash("Passwords do not match.", "error")
        else:
            try:
                result = register_user(full_name, email, password)
                if result.get("success"):
                    flash("Account created successfully. Please sign in.", "success")
                    return redirect(url_for("login"))
                flash(result.get("error", "Unable to create account."), "error")
            except Exception:
                app.logger.exception("Registration failed")
                flash("Registration service is unavailable. Check your database settings.", "error")
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if not email or not password:
            flash("Enter your email and password.", "error")
        else:
            try:
                user = verify_user(email, password)
                if user:
                    session.clear()
                    session.permanent = True
                    session["user_id"] = user["id"]
                    session["user_name"] = user["full_name"]
                    session["user_email"] = user["email"]
                    target = request.args.get("next", "")
                    if target.startswith("/") and not target.startswith("//"):
                        return redirect(target)
                    return redirect(url_for("dashboard"))
                flash("Invalid email or password.", "error")
            except Exception:
                app.logger.exception("Login failed")
                flash("Login service is unavailable. Check your database settings.", "error")
    return render_template("login.html")


@app.post("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("home"))


@app.route("/dashboard")
@login_required
def dashboard():
    try:
        recent = list_analyses(session["user_id"], limit=5)
    except Exception:
        app.logger.exception("Could not load dashboard history")
        recent = []
        flash("Your dashboard loaded, but analysis history could not be reached.", "warning")
    return render_template("dashboard.html", user_name=session["user_name"], user_email=session["user_email"], recent=recent)


@app.route("/analyzer")
@login_required
def analyzer_page():
    return render_template("analyzer.html", user_name=session["user_name"])


@app.post("/api/analyze")
@api_login_required
def analyze():
    data = request.get_json(silent=True) or {}
    code = data.get("code", "")
    language = str(data.get("language", "")).lower().strip()
    user_input = data.get("user_input", "")
    if not isinstance(code, str) or not code.strip():
        return jsonify({"error": "Please enter your code."}), 400
    if len(code) > 50000:
        return jsonify({"error": "Code is too large. Maximum size is 50,000 characters."}), 400
    if language not in SUPPORTED_LANGUAGES:
        return jsonify({"error": "Choose Python, C, C++ or Java."}), 400
    if not isinstance(user_input, str) or len(user_input) > 5000:
        return jsonify({"error": "Program input is invalid or too large."}), 400
    try:
        result = analyze_full_code(code, language, user_input)
        try:
            analysis_id = save_analysis(session["user_id"], language, code, result)
            result["analysis_id"] = analysis_id
        except Exception:
            app.logger.exception("Analysis completed but history could not be saved")
            result["history_saved"] = False
        return jsonify(result)
    except Exception:
        app.logger.exception("Analysis failed")
        return jsonify({"error": "Analysis failed. Check the execution tools and AI configuration, then try again."}), 500


@app.post("/api/assistant")
@api_login_required
def assistant():
    data = request.get_json(silent=True) or {}
    code = data.get("code", "")
    language = str(data.get("language", "")).lower().strip()
    action = str(data.get("action", "")).lower().strip()
    execution = data.get("execution", {})
    if not isinstance(code, str) or not code.strip() or len(code) > 50000:
        return jsonify({"error": "Enter code (up to 50,000 characters)."}), 400
    if language not in SUPPORTED_LANGUAGES:
        return jsonify({"error": "Unsupported language."}), 400
    functions = {"fix": fix_code, "teach": teach_code, "errors": find_errors}
    if action not in functions:
        return jsonify({"error": "Unknown assistant action."}), 400
    try:
        if action == "teach":
            answer = teach_code(code, language)
        else:
            answer = functions[action](code, language, execution)
        return jsonify({"answer": answer})
    except Exception:
        app.logger.exception("AI assistant action failed")
        return jsonify({"error": "The AI assistant could not complete this request."}), 500


@app.route("/history")
@login_required
def history():
    try:
        records = list_analyses(session["user_id"], limit=100)
        error = None
    except Exception:
        app.logger.exception("History retrieval failed")
        records, error = [], "Could not connect to the Analysis database."
    return render_template("history.html", records=records, error=error)


@app.route("/history/<int:analysis_id>")
@login_required
def history_detail(analysis_id):
    try:
        record = get_analysis(session["user_id"], analysis_id)
    except Exception:
        app.logger.exception("History detail retrieval failed")
        flash("Could not retrieve this analysis.", "error")
        return redirect(url_for("history"))
    if not record:
        abort(404)
    return render_template("history_detail.html", record=record)


@app.post("/history/<int:analysis_id>/delete")
@login_required
def history_delete(analysis_id):
    try:
        deleted = delete_analysis(session["user_id"], analysis_id)
        flash("Analysis deleted." if deleted else "Analysis was not found.", "success" if deleted else "warning")
    except Exception:
        app.logger.exception("History delete failed")
        flash("Could not delete this analysis.", "error")
    return redirect(url_for("history"))


@app.post("/reports/create/<int:analysis_id>")
@login_required
def report_create(analysis_id):
    try:
        record = get_analysis(session["user_id"], analysis_id)
        if not record:
            abort(404)
        report_id = create_report(session["user_id"], f"{record['language'].upper()} analysis #{analysis_id}", record["result_json"], analysis_id)
        flash("Report saved successfully.", "success")
        return redirect(url_for("report_detail", report_id=report_id))
    except Exception:
        app.logger.exception("Report creation failed")
        flash("Could not save the report. Check the Reports database.", "error")
        return redirect(url_for("history_detail", analysis_id=analysis_id))


@app.route("/reports")
@login_required
def reports():
    try:
        records = list_reports(session["user_id"])
        error = None
    except Exception:
        app.logger.exception("Reports retrieval failed")
        records, error = [], "Could not connect to the Reports database."
    return render_template("reports.html", records=records, error=error)


@app.route("/reports/<int:report_id>")
@login_required
def report_detail(report_id):
    try:
        record = get_report(session["user_id"], report_id)
    except Exception:
        app.logger.exception("Report retrieval failed")
        flash("Could not retrieve this report.", "error")
        return redirect(url_for("reports"))
    if not record:
        abort(404)
    return render_template("report_detail.html", record=record)


@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():

    if request.method == "POST":

        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()

        if not full_name or not email:
            flash("Name and email are required.", "error")
            return redirect(url_for("profile"))

        if len(full_name) > 150 or len(email) > 255:
            flash("Name or email is too long.", "error")
            return redirect(url_for("profile"))

        result = update_user_profile(
            session["user_id"],
            full_name,
            email
        )

        if not result.get("success"):
            flash(result.get("error"), "error")
            return redirect(url_for("profile"))

        session["user_name"] = full_name
        session["user_email"] = email

        flash("Profile updated successfully.", "success")
        return redirect(url_for("profile"))

    try:
        user = get_user_by_id(session["user_id"])

        if not user:
            session.clear()
            return redirect(url_for("login"))

        return render_template("profile.html", user=user)

    except Exception:
        app.logger.exception("Profile loading failed")
        flash("Could not load your profile.", "error")
        return redirect(url_for("dashboard"))


@app.post("/profile/preferences")
@login_required
def profile_preferences():

    preferred_languages = request.form.getlist("preferred_languages")

    allowed_languages = {"Python", "C", "C++", "Java"}

    if not set(preferred_languages).issubset(allowed_languages):
        flash("Invalid programming language selection.", "error")
        return redirect(url_for("profile"))

    try:
        result = update_user_preferences(
            session["user_id"],
            preferred_languages
        )

        if result.get("success"):
            flash("Preferences saved successfully.", "success")
        else:
            flash("Could not save preferences.", "error")

    except Exception:
        app.logger.exception("Preference update failed")
        flash("Could not update your preferences.", "error")

    return redirect(url_for("profile"))


@app.post("/profile/change-password")
@login_required
def change_password():

    current_password = request.form.get("current_password", "")
    new_password = request.form.get("new_password", "")
    confirm_password = request.form.get("confirm_password", "")

    if not current_password or not new_password or not confirm_password:
        flash("All password fields are required.", "error")
        return redirect(url_for("profile"))

    if len(new_password) < 8:
        flash("New password must contain at least 8 characters.", "error")
        return redirect(url_for("profile"))

    if new_password != confirm_password:
        flash("New passwords do not match.", "error")
        return redirect(url_for("profile"))

    try:
        result = change_user_password(
            session["user_id"],
            current_password,
            new_password
        )

        if result.get("success"):
            flash("Password changed successfully.", "success")
        else:
            flash(result.get("error"), "error")

    except Exception:
        app.logger.exception("Password update failed")
        flash("Could not update your password.", "error")

    return redirect(url_for("profile"))


@app.route("/feedback", methods=["GET", "POST"])
@login_required
def feedback():
    if request.method == "POST":
        message = request.form.get("message", "").strip()
        rating_raw = request.form.get("rating", "")
        try:
            rating = int(rating_raw) if rating_raw else None
        except ValueError:
            rating = None
        if not message:
            flash("Please enter your feedback.", "error")
        elif len(message) > 5000 or (rating is not None and rating not in range(1, 6)):
            flash("Please check your feedback and rating.", "error")
        else:
            try:
                save_feedback(session["user_id"], rating, message)
                flash("Thank you! Your feedback has been submitted.", "success")
                return redirect(url_for("feedback"))
            except Exception:
                app.logger.exception("Feedback submission failed")
                flash("Feedback could not be saved. Check the Feedback database.", "error")
    return render_template("feedback.html")


@app.route("/help")
@login_required
def help_page():
    return render_template("help.html")


@app.route("/about")
@login_required
def about():
    return render_template("about.html")


@app.get("/health")
def health():
    return jsonify({"status": "ok", "application": "CodeClarity", "languages": sorted(SUPPORTED_LANGUAGES)})


@app.errorhandler(404)
def not_found(_error):
    return render_template("error.html", code=404, message="The page you requested could not be found."), 404


@app.errorhandler(413)
def too_large(_error):
    return jsonify({"error": "Request is too large."}), 413


if __name__ == "__main__":
    app.run(host=os.getenv("FLASK_HOST", "127.0.0.1"), port=int(os.getenv("FLASK_PORT", "5001")), debug=os.getenv("FLASK_DEBUG", "false").lower() == "true")
