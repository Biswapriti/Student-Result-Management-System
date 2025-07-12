from flask import Flask, render_template, request,session,redirect,url_for,flash
import mysql.connector
    
app = Flask(__name__)   # Flask constructor 

app.secret_key = 'priti098'  # Set a secret key for session management

conn= mysql.connector.connect(
    host='127.0.0.11',
    user='root',
    password='#Priti2002',  # Replace with your actual password
    database='Priti'
)
cursor = conn.cursor(dictionary=True)  
# A decorator used to tell the application 
# which URL is associated function 
@app.route('/')

@app.route('/index', methods=['GET', 'POST'])
def index():
    msg = ''
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form.get('role')  # Get selected role

        cursor.execute("SELECT * FROM users WHERE username=%s AND password=%s", (username, password))
        user = cursor.fetchone()

        if user:
            session['username'] = user['username']
            session['users_id'] = user['id']
            session['is_admin'] = user.get('is_admin', False)

            # Check if role matches user's actual role
            if role == 'admin' and not user.get('is_admin', False):
                msg = "You are not registered as admin."
                return render_template('index.html', msg=msg)
            if role == 'student' and user.get('is_admin', False):
                msg = "You are not registered as student."
                return render_template('index.html', msg=msg)

            # Redirect based on actual role
            if user.get('is_admin', False):
                return redirect(url_for('admin'))   # <-- Go to admin page to see student list
            else:
                return redirect(url_for('dashboard'))
        else:
            flash("Invalid username or password", "error")
            return redirect(url_for('index'))

    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    if 'users_id' in session:
        users_id = session['users_id']

        # Fetch student info from users table
        cursor.execute("SELECT username, email, course, year, department FROM users WHERE id = %s", (users_id,))
        student = cursor.fetchone()

        # If student not found, redirect to login
        if not student:
            return redirect(url_for('index'))

        # Fetch marks
        cursor.execute("SELECT subject, marks FROM marks WHERE users_id = %s", (users_id,))
        rows = cursor.fetchall()

        results = {}
        total_marks = 0  # Start from 0
        for row in rows:
            results[row['subject']] = row['marks']
            total_marks += row['marks']

        num_subjects = len(results)
        percentage = round(total_marks / num_subjects, 2) if num_subjects else 0

        # Grade logic
        if percentage >= 90:
            grade = 'A+'
        elif percentage >= 75:
            grade = 'A'
        elif percentage >= 60:
            grade = 'B'
        elif percentage >= 40:
            grade = 'C'
        else:
            grade = 'F'

        return render_template('dashboard.html',
                               username=student['username'],
                               email=student['email'],
                               course=student['course'],
                               year=student['year'],
                               department=student['department'],
                               results=results,
                               total_marks=total_marks,
                               percentage=percentage,
                               grade=grade)

    # If not logged in, redirect to login
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])       
def register(): 
    msg = ''
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        course = request.form['course']
        year = request.form['year']
        department = request.form['department']

        cursor.execute(
            "INSERT INTO users (username, password, email, course, year, department) VALUES (%s, %s, %s, %s, %s, %s)",
            (username, password, email, course, year, department)
        )
        conn.commit()
        msg = 'Registered successfully! Please log in.'
        return render_template('register.html', msg=msg)

    return render_template('register.html')

@app.route('/admin')
def admin():
    if not session.get('is_admin'):
        return redirect(url_for('dashboard'))  # Only admin can access

    search = request.args.get('search', '').strip()
    if search:
        query = """
            SELECT id, username, department, course, year, email
            FROM users
            WHERE is_admin = 0 AND (
                username LIKE %s OR
                email LIKE %s OR
                department LIKE %s OR
                course LIKE %s OR
                year LIKE %s
            )
        """
        
        like_search = f"%{search}%"
        cursor.execute(query, (like_search, like_search, like_search, like_search, like_search))
    else:
        cursor.execute("SELECT id, username, department, course, year, email FROM users WHERE is_admin = 0")
    students = cursor.fetchall()
    return render_template('admin.html', students=students)

@app.route('/marks', methods=['GET', 'POST'])
def marks():
    if not session.get('is_admin'):
        return redirect(url_for('dashboard'))

    msg = ''
    username = request.args.get('username', '')
    department = ''
    year = ''
    if username:
        cursor.execute("SELECT department, year FROM users WHERE username=%s", (username,))
        user_info = cursor.fetchone()
        if user_info:
            department = user_info['department']
            year = str(user_info['year'])  # Ensure year is a string

    if request.method == 'POST':
        username = request.form['username']
        subject = request.form['subject']
        department = request.form['department']
        marks = request.form['marks']
        cursor.execute("SELECT id FROM users WHERE username=%s", (username,))
        user = cursor.fetchone()
        if user:
            cursor.execute("INSERT INTO marks (users_id, subject, department, marks) VALUES (%s, %s, %s, %s)", (user['id'], subject, department, marks))
            conn.commit()
            msg = "Marks added successfully!"
        else:
            msg = "User not found."
    return render_template('marks.html', msg=msg, username=username, department=department, year=year)

@app.route('/admin_register', methods=['GET', 'POST'])
def admin_register():
    msg = ''
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        is_admin = 1  # Always register as admin

        cursor.execute(
            "INSERT INTO users (username, password, email, course, year, department, is_admin) VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (username, password, email, '', '', '', is_admin)
        )
        conn.commit()
        msg = 'Admin registered successfully! Please log in.'
        return render_template('admin_register.html', msg=msg) 

    return render_template('admin_register.html', msg=msg)
  
if __name__=='__main__': 
   app.run(debug=True,port=5000)