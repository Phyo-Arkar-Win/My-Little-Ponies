from flask import Flask, render_template, request, flash, session, redirect
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
import sqlite3

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secretkey'

# Connection to database
con = sqlite3.connect('data.db', check_same_thread=False)
con.row_factory = sqlite3.Row

# Create db cursor
db = con.cursor()

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Route for main page
# Redirecting to login page
@app.route('/')
def redirectLogin():

    # NEEDS EDITING
    # Redirect to corresponding main pages
    session.clear()
    if 'user_id' in session:
        db.execute('SELECT * FROM users WHERE id=?', [session['user_id']])
        user = db.fetchall()
        # Redirections based on account type
        if user[0]['type'] == 'Owner':
            pass
        elif user[0]['type'] == 'Admin':
            pass
        elif user[0]['type'] == 'Staff':
            pass
        else:
            return redirect('/userMain')
    
    else:
        return redirect('/login')

# Route for log in page
@app.route('/login', methods=['GET', 'POST'])
def loginPage():

    if request.method == 'GET':
        if 'user_id' in session:
            # NEEDS EDITING
            if user[0]['type'] == 'Owner':
                pass
            elif user[0]['type'] == 'Admin':
                pass
            elif user[0]['type'] == 'Staff':
                pass
            else:
                return render_template('user_main.html')
            return render_template('login.html')
            
        return render_template('login.html')
    
    elif request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        db.execute('SELECT * FROM users WHERE username=?', [username])
        user = db.fetchall()
        # print(user[0].get['password'])
        # print(check_password_hash(user[0]['password'], password))
        if not user:
            flash("Invalid Username.")
            return render_template('login.html')
        elif not check_password_hash(user[0]['password'], password):
            flash('Invalid Username or Password.')
            return render_template('login.html')
        else:
            session['user_id'] = user[0]['id']
            # Redirections based on account type
            if user[0]['type'] == 'Owner':
                pass
            elif user[0]['type'] == 'Admin':
                pass
            elif user[0]['type'] == 'Staff':
                pass
            else:
                return redirect('/userMain')
            

@app.route('/signup', methods = ['GET', 'POST'])
def signupPage():
    if request.method == 'POST':
        # Retrieve inputs from users
        name = request.form.get('name')
        username = request.form.get('username')
        password = request.form.get('password')
        confirmation = request.form.get('confirmation')

        # Generate password hash
        hash = generate_password_hash(password, method='pbkdf2:sha256', salt_length=8)
        
        # Username duplication check
        db.execute('SELECT * FROM users WHERE username=(?)', [username])
        duplicationCheck = db.fetchall()
        
        # User input validation
        if password != confirmation:
            flash("Passwords don't match!")
            return render_template('signup.html')
        elif duplicationCheck:
            flash('Username already exists.')
            return render_template('signup.html')
        
        # Insert into users table
        else:
            print("Testing!")
            db.execute('INSERT INTO users (type, name, username, password) VALUES (?,?,?,?)', ('Customer', name, username, hash))
            con.commit()

            # Remembering users using session
            db.execute('SELECT * FROM users WHERE username=?', [username])
            user = db.fetchall()
            session.clear()
            session['user_id'] = user[0]['id']
            return redirect('/userMain')

    else:
        return render_template('signup.html')
    
# route for user main page
@app.route('/userMain')
def userMainPage():
    if 'user_id' in session:
        return render_template('user_main.html')
    else:
        return redirect('/login')
    
# route for services
@app.route('/services')
def services():
    return render_template('services.html')

@app.route('/')
def mainpage():
    return render_template('mainpage.html')

# route for appointment
@app.route('/appointment')
def appointment():
    return render_template('appointment.html')

# Route for logging out
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

if __name__ == '__main__':
    app.run(debug=True)