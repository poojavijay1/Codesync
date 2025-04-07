from flask import Flask, render_template, request, redirect, session, flash, jsonify
from flask_mysqldb import MySQL
from flask_bcrypt import Bcrypt
import MySQLdb  
from MySQLdb._exceptions import IntegrityError  
import requests,re

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change this to a secure key
bcrypt = Bcrypt(app)

# MySQL Configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'mysql0208'
app.config['MYSQL_DB'] = 'user_auth'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
mysql = MySQL(app)

# UID and Email pattern
STUDENT_EMAIL_DOMAIN = "rajagiri.edu.in"
TEACHER_EMAIL_DOMAIN = "rajagiritech.edu.in"
PASSWORD_REGEX = re.compile(r"^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{6,}$")
UID_REGEX = re.compile(r"^[uU]\d{7}$")

# *Validation Function*
def validate_student_signup(uid, email, password):
    uid = uid.lower()  # Convert UID to lowercase
    email = email.lower()  # Convert email to lowercase
    if not UID_REGEX.match(uid):
        return "Invalid UID!"
    expected_email = f"{uid}@{STUDENT_EMAIL_DOMAIN}"
    if email != expected_email:
        return "Invalid email!"
    if not PASSWORD_REGEX.match(password):
        return "Password must contain a letter, a number, and a special character."
    return None 
      
def validate_teacher_signup(uid, email, password):
    uid = uid.lower()
    email = email.lower()
    if not UID_REGEX.match(uid):
        return "Invalid UID!."
    if not email.endswith("@" + TEACHER_EMAIL_DOMAIN):
        return "Invalid email!"
    if not PASSWORD_REGEX.match(password):
        return "Password must contain a letter, a number, and a special character."
    return None

# Home Page
@app.route('/')
def home():
    return render_template('index.html')

# Judge0 API Configuration
JUDGE0_API_KEY = "47a66c4bb4msha357a474ec068f4p1a82a5jsn0d232652151a"
JUDGE0_SUBMIT_URL = "https://judge0-ce.p.rapidapi.com/submissions"
JUDGE0_GET_RESULT_URL = "https://judge0-ce.p.rapidapi.com/submissions/{token}"
print("JUDGE0_API_KEY:", JUDGE0_API_KEY)
HEADERS = {
    "X-RapidAPI-Key": JUDGE0_API_KEY,  # Replace with your API Key
    "X-RapidAPI-Host": "judge0-ce.p.rapidapi.com",
    "Content-Type": "application/json"
}

@app.route('/editor')
def editor():
    if 'user_id' not in session:
        return redirect('/login/student')  # Redirect to login if not authenticated
    return render_template('editor.html')

@app.route("/compile", methods=["POST"])
def compile_code():
    try:
        data = request.json
        source_code = data.get("source_code", "")
        language_id = data.get("language_id", "")
        print(source_code,language_id)
        if not source_code or not language_id:
            return jsonify({"error": "Missing source_code or language_id"}), 400

        # Step 1: Submit code to Judge0 API
        submission_response = requests.post(JUDGE0_SUBMIT_URL, json={
            "source_code": source_code,
            "language_id": int(language_id),
            "stdin": "",
            "base64_encoded": False
        }, headers=HEADERS)

        if submission_response.status_code != 201:
            return jsonify({"error": "Failed to submit code"}), submission_response.status_code

        token = submission_response.json().get("token")

        # Step 2: Retrieve the result
        result_response = requests.get(JUDGE0_GET_RESULT_URL.format(token=token), headers=HEADERS)
        print(result_response)
        if result_response.status_code != 200:
            return jsonify({"error": "Failed to fetch result"}), result_response.status_code

        result = result_response.json()
        output = result.get('stdout', result.get('stderr', 'No output'))

        # # Store submission in MySQL
        # cursor = mysql.connection.cursor()
        # cursor.execute("INSERT INTO submissions (user_id, language_id, source_code, output) VALUES (%s, %s, %s, %s)",
        #                (session['user_id'], language_id, source_code, output))
        # mysql.connection.commit()
        # cursor.close()

        return jsonify({'output': output})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/submissions', methods=['GET'])
def get_submissions():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    cursor = mysql.connection.cursor()
    cursor.execute("SELECT id, language_id, source_code, output, created_at FROM submissions WHERE user_id = %s ORDER BY created_at DESC", (session['user_id'],))
    submissions = cursor.fetchall()
    cursor.close()

    return jsonify(submissions)

@app.route('/save_code', methods=['POST'])
def save_code():
    if 'user_id' not in session:
        return jsonify({"message": "Unauthorized"}), 401  # Ensure user is logged in

    data = request.json
    filename = data.get("filename")
    source_code = data.get("source_code")
    semester = data.get("semester")
    lab = data.get("lab")  

    if not filename or not source_code or not semester or not lab:
        return jsonify({"message": "Missing required fields"}), 400

    try:
        cursor = mysql.connection.cursor()
        user_id = session['user_id']  
        # Store user ID from session, not from request
        query = "SELECT id FROM saved_files WHERE filename = %s"
        cursor.execute(query, (filename,))  # Pass a tuple (filename,)
        fid = cursor.fetchone()
        
        if(fid):
            id = fid['id']
            print(id)
            sql = """
            UPDATE saved_files 
            SET filename = %s, source_code = %s, semester = %s,  lab = %s, status = 'saved' 
            WHERE id = %s
            """
            cursor.execute(sql, (filename, source_code, semester, lab, id))
        else:
            sql = "INSERT INTO saved_files (filename, source_code, semester, uid, lab, status) VALUES (%s, %s, %s, %s, %s, 'saved')"
            cursor.execute(sql, (filename, source_code, semester, user_id, lab))

        mysql.connection.commit()
        cursor.close()

        return jsonify({"message": "Code saved successfully!"}), 200

    except Exception as e:
        return jsonify({"message": f"Error saving file: {str(e)}"}), 500

@app.route('/get_saved_files', methods=['GET'])
def get_saved_files():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    user_id = session['user_id']  # Get user ID from session
    semester = request.args.get('semester')

    if not semester:
        return jsonify({"error": "Missing semester"}), 400

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    query = """
    SELECT sf.*, l.lab_name 
    FROM saved_files sf
    JOIN labs l ON sf.lab = l.lab_id
    WHERE sf.uid = %s AND sf.semester = %s
"""
    cursor.execute(query, (user_id, semester))
    files = cursor.fetchall()
    cursor.close()

    return jsonify(files)

# Student Signup
@app.route('/signup/student', methods=['GET', 'POST'])
def signup_student():
    error = None 
    if request.method == 'POST':
        name = request.form['Name']
        uid = request.form['UID']
        email = request.form['Email']
        password = bcrypt.generate_password_hash(request.form['Password']).decode('utf-8')
        error = validate_student_signup(uid, email, password)
        if error:
            return render_template('stdsign.html', error=error)
        
        cursor = mysql.connection.cursor()

        # Check if UID or Email already exists in students or teachers table
        cursor.execute("SELECT uid FROM students WHERE uid = %s OR email = %s UNION SELECT uid FROM teachers WHERE uid = %s OR email = %s", (uid, email, uid, email))
        existing_user = cursor.fetchone()

        if existing_user:
            error = "UID or Email already exists!"
        else:
            try:
                cursor.execute("INSERT INTO students (name, uid, email, password) VALUES (%s, %s, %s, %s)", 
                               (name, uid, email, password))
                mysql.connection.commit()
                flash('Signup successful! You can now log in.', 'success')
                return redirect('/login/student')
            except IntegrityError:
                error = "An unexpected error occurred! Please try again."
        
        cursor.close()
    
    return render_template('stdsign.html', error=error)

# Student Login
@app.route('/login/student', methods=['GET', 'POST'])
def login_student():
    error = None 
    if request.method == 'POST':
        uid = request.form['UID']
        password = request.form['Password']

        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM students WHERE UID = %s", (uid,))
        user = cursor.fetchone()
        cursor.close()

        if user and bcrypt.check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['role'] = 'student'
            flash('Login successful!', 'success')
            return redirect('/dashboard/student')
        else:
            error = "Invalid UID or password!"

    return render_template('student.html', error=error)
# Student Dashboard
@app.route('/dashboard/student')
def dashboard_student():
    if 'user_id' in session and session.get('role') == 'student':
       return render_template('std.html') 
    return redirect('/login/student')

# Teacher Signup (Similar to Student Signup)
@app.route('/signup/teacher', methods=['GET', 'POST'])
def signup_teacher():
    error = None 
    if request.method == 'POST':
        name = request.form['Name']
        uid = request.form['UID']
        email = request.form['Email']
        password = bcrypt.generate_password_hash(request.form['Password']).decode('utf-8')
        error = validate_teacher_signup(uid, email, password)
        if error:
            return render_template('teasign.html', error=error)

        cursor = mysql.connection.cursor()

        # Check if UID or Email already exists in teachers or students table
        cursor.execute("SELECT uid FROM teachers WHERE uid = %s OR email = %s UNION SELECT uid FROM students WHERE uid = %s OR email = %s", (uid, email, uid, email))
        existing_user = cursor.fetchone()

        if existing_user:
            error = "UID or Email already exists!"
        else:
            try:
                cursor.execute("INSERT INTO teachers (name, uid, email, password) VALUES (%s, %s, %s, %s)", 
                               (name, uid, email, password))
                mysql.connection.commit()
                flash('Signup successful! You can now log in.', 'success')
                return redirect('/login/teacher')
            except IntegrityError:
                error = "An unexpected error occurred! Please try again."
        
        cursor.close()
    
    return render_template('teasign.html', error=error)

# Teacher Login (Similar to Student Login)
@app.route('/login/teacher', methods=['GET', 'POST'])
def login_teacher():
    error = None 
    if request.method == 'POST':
        uid = request.form['UID']
        password = request.form['Password']
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM teachers WHERE UID = %s", (uid,))
        user = cursor.fetchone()
        cursor.close()

        if user and bcrypt.check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['role'] = 'teacher'
            flash('Login successful!', 'success')
            return redirect('/dashboard/teacher')
        else:
             error = "Invalid UID or password!"
    return render_template('teacher.html', error=error)

# Teacher Dashboard
@app.route('/dashboard/teacher')
def dashboard_teacher():
    if 'user_id' in session and session.get('role') == 'teacher':
        #return render_template('tea.html') 
        cursor = mysql.connection.cursor()

        # Query to fetch records with status 'Pending', 'Approved', or 'Rejected'
        cursor.execute("""
            SELECT s.uid, s.name, sf.id, sf.filename, sf.semester, 
                   l.lab_name, sf.created_at, sf.status 
            FROM saved_files sf
            JOIN students s ON sf.uid = s.id
            JOIN labs l ON sf.lab = l.lab_id
            WHERE sf.status in ('pending','approved','rejected')
            ORDER BY sf.semester asc
        """)
        pending_files = cursor.fetchall()
        # Fetch submission statistics
        cursor.execute("""
            SELECT 
                COUNT(CASE WHEN status = 'pending' THEN 1 END) AS pending_count,
                COUNT(CASE WHEN status = 'approved' THEN 1 END) AS approved_count,
                COUNT(CASE WHEN status = 'rejected' THEN 1 END) AS rejected_count
            FROM saved_files
        """)
        stats = cursor.fetchone()
        stats['total_submissions'] = (
            stats['pending_count'] + stats['approved_count'] + stats['rejected_count']
        )
        cursor.close()

        # Pass the data to the template
        return render_template('tea.html', pending_files=pending_files, stats=stats) 
    return redirect('/login/teacher')

#folder page for student
@app.route('/folders')
def folders():
    if 'user_id' in session and session.get('role') == 'student':
        return render_template('sems.html')
    return redirect('/login/student')

@app.route('/experiments')
def experiments():
    semester = request.args.get('semester', 'Unknown')
    return render_template('experiments.html', semester=semester)

@app.route('/student')
def student():
    return render_template('student.html')

@app.route('/teacher')
def teacher():
    return render_template('teacher.html')
# Logout
@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect('/')

@app.route('/toggle_submission', methods=['POST'])
def toggle_submission():
    data = request.json
    file_id = data.get('file_id')

    if not file_id:
        return jsonify({"error": "Missing file_id"}), 400

    cursor = mysql.connection.cursor()
    cursor.execute("SELECT status FROM saved_files WHERE id = %s", (file_id,))
    file = cursor.fetchone()

    if not file:
        return jsonify({"error": "File not found"}), 404

    # Toggle between 'saved' and 'pending'
    new_status = "pending" if file["status"] == "saved" else "saved"

    cursor.execute("UPDATE saved_files SET status = %s WHERE id = %s", (new_status, file_id))
    mysql.connection.commit()
    cursor.close()

    return jsonify({"message": f"Status updated to {new_status}", "new_status": new_status}), 200

@app.route('/update_status', methods=['POST'])
def update_status():
    try:
        data = request.get_json()
        file_id = data.get("file_id")
        new_status = data.get("status")
        print('file_id is: ',file_id)
        if not file_id or new_status not in ["approved", "rejected"]:
            return jsonify({"error": "Invalid data"}), 400

        cursor = mysql.connection.cursor()
        cursor.execute("UPDATE saved_files SET status = %s WHERE id = %s", (new_status, file_id))
        mysql.connection.commit()
        cursor.close()

        return jsonify({"message": f"File {file_id} marked as {new_status}", "new_status": new_status})

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/delete_file', methods=['POST'])
def delete_file():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    file_id = data.get('file_id')

    try:
        cursor = mysql.connection.cursor()
        cursor.execute("DELETE FROM saved_files WHERE id = %s", (file_id,))
        mysql.connection.commit()
        cursor.close()
        return jsonify({"message": "File deleted successfully."}), 200
    except Exception as e:
        print("Error deleting file:", e)
        return jsonify({"error": "Database error"}), 500

from flask import Flask, jsonify

@app.route('/view_code/<int:file_id>')
def view_code(file_id):
    try:
        cursor=mysql.connection.cursor()
        query = "SELECT source_code FROM saved_files WHERE id = %s"
        cursor.execute(query, (file_id,))
        result = cursor.fetchone()

        if result:
            return jsonify({"success": True, "code": result['source_code']})
        else:
            return jsonify({"success": False, "message": "Code not found"}), 404

    except Exception as e:
        print(f"Error fetching code: {e}")
        return jsonify({"success": False, "message": "Server error"}), 500

@app.route('/get_file_by_id/<int:file_id>')
def get_file_by_id(file_id):
    try:
        print(file_id)
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT source_code,lab FROM saved_files WHERE id = %s", (file_id,))
        row = cursor.fetchone()
        print(row)
        if row:
            return row
        else:
            return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)