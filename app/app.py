from flask import Flask, render_template, request, redirect, url_for, jsonify
import mysql.connector
import os
import time

app = Flask(__name__)

# Database configuration
db_config = {
    "host": os.environ.get("DB_HOST", "db"),
    "user": os.environ.get("DB_USER", "me_1"),
    "password": os.environ.get("DB_PASSWORD", "my_p"),
    "database": os.environ.get("DB_NAME", "my_db"),
}

# --- NEW: Hardcoded Admin Credentials (NOT SECURE FOR PRODUCTION) ---
ADMIN_EMAIL = "admin@admin"
ADMIN_PASSWORD = "admin_password_123"  # Replace with a slightly better dummy password


def get_db_connection():
    """Attempts to connect to the database with retry logic."""
    retries = 10
    delay = 5  # seconds
    for i in range(retries):
        try:
            conn = mysql.connector.connect(**db_config)
            print(f"Database connection successful after {i + 1} attempt(s).")
            return conn
        except mysql.connector.Error as err:
            print(f"Attempt {i + 1}/{retries} to connect to database failed: {err}")
            if i < retries - 1:
                time.sleep(delay)
            else:
                print("Max retries reached. Could not connect to database.")
    return None


# Function to create the users table if it doesn't exist
def create_users_table():
    """Checks if the 'users' table exists and creates it if not."""
    conn = get_db_connection()
    if conn is None:
        print("Skipping table creation due to database connection failure.")
        return

    cursor = conn.cursor()
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                email VARCHAR(255) NOT NULL UNIQUE
            )
        """)
        conn.commit()
        print("'users' table checked/created successfully.")
    except mysql.connector.Error as err:
        print(f"Error creating 'users' table: {err}")
        conn.rollback()
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


# Route to display users and the add user form
@app.route("/")
def index():
    """Renders the index page with users list and add user form."""
    conn = get_db_connection()
    users = []
    error = None
    if conn is None:
        error = "Database connection failed. Please check database service."
    else:
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("SELECT * FROM users")
            users = cursor.fetchall()
        except mysql.connector.Error as err:
            print(f"Error fetching users: {err}")
            error = "Error fetching users from database."
        finally:
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()

    return render_template("index.html", users=users, error=error)


# Route to handle adding a new user
@app.route("/add_user", methods=["POST"])
def add_user():
    """Handles the form submission to add a new user."""
    name = request.form.get("name")
    email = request.form.get("email")

    if not name or not email:
        # Redirect back with an error message if fields are missing (optional enhancement)
        return redirect(url_for("index"))

    conn = get_db_connection()
    if conn is None:
        # Redirect back with an error message if connection failed (optional enhancement)
        return redirect(url_for("index"))

    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (name, email) VALUES (%s, %s)", (name, email))
        conn.commit()
    except mysql.connector.Error as err:
        print(f"Error adding user: {err}")
        conn.rollback()
        # Redirect back with an error message (optional enhancement)
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()

    return redirect(url_for("index"))  # Redirect back to the index page after adding


# --- Modify delete_user to require admin credentials ---
@app.route("/delete_user/<int:user_id>", methods=["POST"])
def delete_user(user_id):
    """Handles the deletion of a user by ID, requires admin credentials."""
    admin_email = request.form.get("admin_email")
    admin_password = request.form.get("admin_password")

    # --- NEW: Basic Admin Authentication Check (NOT SECURE) ---
    if admin_email == ADMIN_EMAIL and admin_password == ADMIN_PASSWORD:
        conn = get_db_connection()
        if conn is None:
            # Redirect back with an error message (optional enhancement)
            return redirect(url_for("index"))

        cursor = conn.cursor()
        try:
            # Execute the DELETE query
            cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
            conn.commit()
            # You could check cursor.rowcount here to see if a row was actually deleted
            # if cursor.rowcount == 0:
            #     print(f"User with ID {user_id} not found for deletion.")
            # else:
            #     print(f"User with ID {user_id} deleted successfully.")

        except mysql.connector.Error as err:
            print(f"Error deleting user with ID {user_id}: {err}")
            conn.rollback()
            # Redirect back with an error message (optional enhancement)
        finally:
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()
    else:
        # --- NEW: Handle Authentication Failure ---
        print("Admin authentication failed for delete request.")
        # In a real app, you'd provide feedback to the user, e.g., redirect with a query param
        # return redirect(url_for("index", error="Authentication Failed")) # requires index route to handle 'error' query param

    return redirect(url_for("index"))  # Redirect back to the index page


# You can keep the remove user API route if you still need it for other purposes
# @app.route("/users/<int:user_id>", methods=["DELETE"])
# def remove_user(user_id):
#     """API endpoint to remove a user by ID (using DELETE method)."""
#     # ... (your existing remove_user code) ...
#     pass


if __name__ == "__main__":
    # Call the function to create the table before running the app
    create_users_table()
    # When running in Docker, listen on 0.0.0.0 to be accessible from outside
    app.run(host="0.0.0.0", debug=True)
