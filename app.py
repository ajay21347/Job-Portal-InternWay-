from flask import Flask, render_template, request, session, jsonify, redirect
from werkzeug.utils import secure_filename
import database
import os

app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "root123")


database.create_tables()
app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024  # 2 MB


@app.errorhandler(413)
def file_too_large(error):
    return redirect("/profile?error=file_too_large")


@app.route("/")
def index():
    user_data = {
        "user_id": session.get("user_id"),
        "username": session.get("username"),
        "user_type": session.get("user_type"),
        "profile_image_url": session.get("profile_image_url"),
        "bio": session.get("bio"),
    }
    return render_template("index.html", user=user_data)


@app.route("/api/signup", methods=["POST"])
def api_signup():
    username = request.form["username"]
    password = request.form["password"]
    email = request.form["email"]
    user_type = request.form["user_type"]

    if database.add_user(username, password, email, user_type):
        return jsonify({"success": True, "message": "Signup successful! Please login."})
    else:
        return jsonify(
            {
                "success": False,
                "message": "Signup failed. Username or email might be taken.",
            }
        )


@app.route("/api/login", methods=["POST"])
def api_login():
    username = request.form["username"]
    password = request.form["password"]

    user = database.get_user_by_username(username)

    if user and user["password"] == password:
        session["user_id"] = user["id"]
        session["username"] = user["username"]
        session["user_type"] = user["user_type"]
        session["profile_image_url"] = user["profile_image_url"]
        session["bio"] = user["bio"]
        session["email"] = user["email"]
        session["resume_url"] = user.get("resume_url")
        return jsonify(
            {
                "success": True,
                "user": {
                    "user_id": user["id"],
                    "username": user["username"],
                    "user_type": user["user_type"],
                    "profile_image_url": user["profile_image_url"],
                    "bio": user["bio"],
                },
            }
        )
    else:
        return jsonify({"success": False, "message": "Invalid username or password."})


@app.route("/api/logout", methods=["POST"])
def api_logout():
    session.clear()
    return jsonify({"success": True, "message": "Logged out successfully."})


@app.route("/api/post_job", methods=["POST"])
def api_post_job():
    if "user_id" not in session or session["user_type"] != "recruiter":
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    recruiter_id = session["user_id"]
    title = request.form["title"]
    company = request.form["company"]
    location = request.form["location"]
    description = request.form["description"]
    salary = request.form.get("salary", "")
    job_type = request.form.get("job_type", "")
    job_level = request.form.get("job_level", "")
    employment_type = request.form.get("employment_type", "")

    print("POST Job Data Received:")
    print(f"Recruiter ID: {recruiter_id}")
    print(f"Title: {title}")
    print(f"Company: {company}")
    print(f"Location: {location}")
    print(f"Description: {description}")
    print(f"Salary: {salary}")
    print(f"Job Type: {job_type}")
    print(f"Job Level: {job_level}")
    print(f"Employment Type: {employment_type}")

    if database.add_job(
        recruiter_id,
        title,
        company,
        location,
        description,
        salary,
        job_type,
        job_level,
        employment_type,
    ):
        return jsonify({"success": True, "message": "Job posted successfully!"})
    else:
        return jsonify({"success": False, "message": "Failed to post job."})


@app.route("/api/apply_job", methods=["POST"])
def api_apply_job():
    if "user_id" not in session or session["user_type"] != "seeker":
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    seeker_id = session["user_id"]
    job_id = request.form["job_id"]

    if database.apply_for_job(job_id, seeker_id):
        return jsonify(
            {"success": True, "message": "Application submitted successfully!"}
        )
    else:
        return jsonify(
            {
                "success": False,
                "message": "Failed to submit application or already applied.",
            }
        )


@app.route("/api/jobs", methods=["GET"])
def api_get_all_jobs():
    job_type = request.args.get("job_type")
    location = request.args.get("location")
    job_level = request.args.get("job_level")
    employment_type = request.args.get("employment_type")

    jobs = database.get_jobs(
        job_type=job_type,
        location=location,
        job_level=job_level,
        employment_type=employment_type,
    )
    return jsonify({"success": True, "jobs": jobs})


@app.route("/api/recruiter_jobs", methods=["GET"])
def api_get_recruiter_jobs():
    if "user_id" not in session or session["user_type"] != "recruiter":
        return jsonify({"success": False, "message": "Unauthorized", "jobs": []}), 401
    jobs = database.get_jobs(recruiter_id=session["user_id"])
    return jsonify({"success": True, "jobs": jobs})


@app.route("/api/seeker_applications", methods=["GET"])
def api_get_seeker_applications():
    if "user_id" not in session or session["user_type"] != "seeker":
        return (
            jsonify({"success": False, "message": "Unauthorized", "applications": []}),
            401,
        )
    applications = database.get_applied_jobs(session["user_id"])
    return jsonify({"success": True, "applications": applications})


@app.route("/profile")
def profile():
    if not session.get("user_id"):
        return redirect("/")
    return render_template(
        "profile.html",
        user={
            "user_id": session.get("user_id"),
            "username": session.get("username"),
            "email": session.get("email"),
            "bio": session.get("bio"),
            "profile_image_url": session.get("profile_image_url"),
            "resume_url": session.get("resume_url"),
            "user_type": session.get("user_type"),
        },
    )


@app.route("/api/update_profile", methods=["POST"])
def update_profile():
    if "user_id" not in session:
        return redirect("/")

    username = request.form["username"]
    email = request.form["email"]
    bio = request.form.get("bio", "")

    if database.update_user_profile(session["user_id"], username, email, bio):
        # Update session values
        session["username"] = username
        session["email"] = email
        session["bio"] = bio

    return redirect("/profile")


@app.route("/api/upload_resume", methods=["POST"])
def upload_resume():
    if "user_id" not in session:
        return redirect("/")

    if "resume" not in request.files:
        return redirect("/profile")

    file = request.files["resume"]

    if file.filename == "":
        return redirect("/profile")

    # Allowed file types
    allowed_extensions = {"pdf", "doc", "docx"}
    filename = secure_filename(file.filename)
    ext = filename.rsplit(".", 1)[-1].lower()

    if ext not in allowed_extensions:
        return redirect("/profile")

    # Create folder if not exists
    upload_folder = os.path.join("static", "resumes")
    os.makedirs(upload_folder, exist_ok=True)

    # Delete old resume
    old_resume_url = session.get("resume_url")
    if old_resume_url:
        old_resume_path = old_resume_url.lstrip("/")
        if os.path.exists(old_resume_path):
            try:
                os.remove(old_resume_path)
            except Exception as e:
                print(f"Failed to delete old resume")

    # Unique filename per user
    saved_filename = f"user_{session['user_id']}.{ext}"
    file_path = os.path.join(upload_folder, saved_filename)

    # Save file
    file.save(file_path)

    # Save path in DB
    resume_url = f"/static/resumes/{saved_filename}"
    database.update_resume(session["user_id"], resume_url)

    # Update session
    session["resume_url"] = resume_url

    return redirect("/profile?resume=success")


@app.route("/api/job_applicants/<int:job_id>")
def job_applicants(job_id):
    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 403

    if session.get("user_type") != "recruiter":
        return jsonify({"error": "Only recruiters allowed"}), 403

    applicants = database.get_job_applicants(job_id)
    return jsonify({"success": True, "applicants": applicants})


if __name__ == "__main__":
    os.makedirs("templates", exist_ok=True)
    os.makedirs("static", exist_ok=True)
    app.run(debug=True)
