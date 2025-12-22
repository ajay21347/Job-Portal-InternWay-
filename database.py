import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv

load_dotenv()

# Database configuration
DB_CONFIG = {
    "host": os.getenv("MYSQL_HOST"),
    "user": os.getenv("MYSQL_USER"),
    "password": os.getenv("MYSQL_PASSWORD"),
    "database": os.getenv("MYSQL_DATABASE"),
}


def get_db_connection():
    """Establishes and returns a database connection."""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        print(f"Connection error: {e}")
    return None


def create_tables():
    """Creates required tables if they don't exist."""
    conn = get_db_connection()
    if conn is None:
        return

    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(255) NOT NULL UNIQUE,
                password VARCHAR(255) NOT NULL,
                email VARCHAR(255) NOT NULL UNIQUE,
                user_type ENUM('seeker', 'recruiter') NOT NULL,
                profile_image_url VARCHAR(255),
                bio TEXT,
                resume_url VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS jobs (
                id INT AUTO_INCREMENT PRIMARY KEY,
                recruiter_id INT NOT NULL,
                title VARCHAR(255) NOT NULL,
                company VARCHAR(255) NOT NULL,
                location VARCHAR(255) NOT NULL,
                description TEXT NOT NULL,
                salary VARCHAR(100),
                job_type VARCHAR(100),
                job_level ENUM('fresher', 'junior', 'mid', 'senior'),
                employment_type ENUM('full-time', 'part-time'),
                posted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (recruiter_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS applications (
                id INT AUTO_INCREMENT PRIMARY KEY,
                job_id INT NOT NULL,
                seeker_id INT NOT NULL,
                application_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status ENUM('pending', 'reviewed', 'accepted', 'rejected') DEFAULT 'pending',
                FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE,
                FOREIGN KEY (seeker_id) REFERENCES users(id) ON DELETE CASCADE,
                UNIQUE (job_id, seeker_id)
            )
        """
        )

        conn.commit()
        print("All tables checked/created.")
    except Error as e:
        print(f"Error during table creation: {e}")
    finally:
        cursor.close()
        conn.close()


def add_user(username, password, email, user_type, profile_image_url=None, bio=None):
    """Adds a new user to the database."""
    conn = get_db_connection()
    if conn is None:
        return False

    cursor = conn.cursor()
    try:
        query = """
            INSERT INTO users (username, password, email, user_type, profile_image_url, bio)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(
            query, (username, password, email, user_type, profile_image_url, bio)
        )
        conn.commit()
        print(f"User '{username}' added.")
        return True
    except Error as e:
        print(f"Add user error: {e}")
        return False
    finally:
        cursor.close()
        conn.close()


def get_user_by_username(username):
    """Retrieves a user by username."""
    conn = get_db_connection()
    if conn is None:
        return None

    cursor = conn.cursor(dictionary=True)
    try:
        query = "SELECT * FROM users WHERE username = %s"
        cursor.execute(query, (username,))
        return cursor.fetchone()
    except Error as e:
        print(f"Get user error: {e}")
        return None
    finally:
        cursor.close()
        conn.close()


def add_job(
    recruiter_id,
    title,
    company,
    location,
    description,
    salary,
    job_type=None,
    job_level=None,
    employment_type=None,
):
    """Adds a job posting."""
    conn = get_db_connection()
    if conn is None:
        return False

    cursor = conn.cursor()
    try:
        query = """
            INSERT INTO jobs (recruiter_id, title, company, location, description, salary, job_type, job_level, employment_type)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(
            query,
            (
                recruiter_id,
                title,
                company,
                location,
                description,
                salary,
                job_type,
                job_level,
                employment_type,
            ),
        )
        conn.commit()
        print(f"Job '{title}' posted by recruiter ID {recruiter_id}.")
        return True
    except Error as e:
        print(f"Add job error: {e}")
        return False
    finally:
        cursor.close()
        conn.close()


def get_jobs(
    recruiter_id=None,
    job_type=None,
    location=None,
    job_level=None,
    employment_type=None,
):
    """Retrieves jobs with optional filters."""
    conn = get_db_connection()
    if conn is None:
        return []

    cursor = conn.cursor(dictionary=True)
    try:
        query = "SELECT * FROM jobs WHERE 1=1"
        params = []

        if recruiter_id:
            query += " AND recruiter_id = %s"
            params.append(recruiter_id)
        if job_type:
            query += " AND job_type LIKE %s"
            params.append(f"%{job_type}%")
        if location:
            query += " AND location LIKE %s"
            params.append(f"%{location}%")
        if job_level:
            query += " AND job_level = %s"
            params.append(job_level)
        if employment_type:
            query += " AND employment_type = %s"
            params.append(employment_type)

        query += " ORDER BY posted_at DESC"
        cursor.execute(query, tuple(params))
        return cursor.fetchall()
    except Error as e:
        print(f"Get jobs error: {e}")
        return []
    finally:
        cursor.close()
        conn.close()


def apply_for_job(job_id, seeker_id):
    """Submits a job application."""
    conn = get_db_connection()
    if conn is None:
        return False

    cursor = conn.cursor()
    try:
        query = "INSERT INTO applications (job_id, seeker_id) VALUES (%s, %s)"
        cursor.execute(query, (job_id, seeker_id))
        conn.commit()
        print(f"Application: seeker {seeker_id} -> job {job_id}")
        return True
    except Error as e:
        if e.errno == 1062:
            print(
                f"Duplicate application: seeker {seeker_id} already applied for job {job_id}."
            )
            return False
        print(f"Apply job error: {e}")
        return False
    finally:
        cursor.close()
        conn.close()


def get_applied_jobs(seeker_id):
    """Fetches jobs applied to by a specific seeker."""
    conn = get_db_connection()
    if conn is None:
        return []

    cursor = conn.cursor(dictionary=True)
    try:
        query = """
            SELECT j.*, a.application_date, a.status
            FROM applications a
            JOIN jobs j ON a.job_id = j.id
            WHERE a.seeker_id = %s
            ORDER BY a.application_date DESC
        """
        cursor.execute(query, (seeker_id,))
        return cursor.fetchall()
    except Error as e:
        print(f"Get applied jobs error: {e}")
        return []
    finally:
        cursor.close()
        conn.close()


def update_resume(user_id, resume_url):
    """Updates resume URL for a user."""
    conn = get_db_connection()
    if conn is None:
        return False

    cursor = conn.cursor()
    try:
        query = "UPDATE users SET resume_url = %s WHERE id=%s"
        cursor.execute(query, (resume_url, user_id))
        conn.commit()
        return True
    except Error as e:
        print(f"Update resume error: {e}")
        return False
    finally:
        cursor.close()
        conn.close()


def update_user_profile(user_id, username, email, bio):
    conn = get_db_connection()
    if conn is None:
        return False

    cursor = conn.cursor()
    try:
        query = """UPDATE users SET username = %s, email = %s, bio = %s WHERE id = %s"""
        cursor.execute(query, (username, email, bio, user_id))
        conn.commit()
        return True
    except Error as e:
        print(f"Update profile error {e}")
        return False
    finally:
        cursor.close()
        conn.close()


def get_job_applicants(job_id):
    conn = get_db_connection()
    if conn is None:
        return False

    cursor = conn.cursor(dictionary=True)
    try:
        query = """
        SELECT u.id,u.username,u.email,u.resume_url,a.status,a.application_date FROM applications a JOIN users u ON  a.seeker_id=u.id WHERE a.job_id = %s ORDER BY a.application_date DESC"""
        cursor.execute(query, (job_id,))
        return cursor.fetchall()
    except Error as e:
        print(f"Get applicants error: {e}")
        return []

    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    create_tables()
