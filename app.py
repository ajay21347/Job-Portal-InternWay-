from flask import Flask, render_template, request, session, jsonify
import database
import os

app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "root123")

database.create_tables()


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


if __name__ == "__main__":
    os.makedirs("templates", exist_ok=True)
    os.makedirs("static", exist_ok=True)
    app.run(debug=True)
