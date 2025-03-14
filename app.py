from flask import Flask, render_template, request, redirect, session, flash
from flask_mysqldb import MySQL
from flask_bcrypt import Bcrypt
import MySQLdb  
from MySQLdb._exceptions import IntegrityError  

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
bcrypt = Bcrypt(app)

# Home Page
@app.route('/')
def home():
    return render_template('index.html')

# Student Signup
@app.route('/signup/student', methods=['GET', 'POST'])
def signup_student():
    error = None 
    if request.method == 'POST':
        name = request.form['Name']
        uid = request.form['UID']
        email = request.form['Email']
        password = bcrypt.generate_password_hash(request.form['Password']).decode('utf-8')

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
         return render_template('tea.html') 
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

@app.route('/editor')
def editor():
    return render_template('editor.html')

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

if __name__ == '__main__':
    app.run(debug=True)


