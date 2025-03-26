from flask import Flask, render_template, request, flash, session, redirect, url_for
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
import sqlite3
import pickle
import random
from datetime import datetime

# OOP code

class User:
    def __init__(self, username, name, password):
        self.__username = username
        self.__name = name
        self.__password = password

    @property
    def username(self):
        return self.__username

    @property
    def name(self):
        return self.__name
    
    @name.setter
    def name(self, new_name):
        self.__name = new_name
    
    @property
    def password(self):
        return self.__password
    
    @password.setter
    def password(self, new_password):
        self.__password = new_password

    def edit_profile(self, new_name=None, new_password=None):
        if new_name:
            self.name(new_name)
        if new_password:
            self.password(new_password)
        return "Profile updated successfully."

class Customer(User):
    def __init__(self, username, name, password):
        super().__init__(username, name, password)
        self.__spending = 0
        self.__membership = "New"

    
    @property
    def membership(self):
        return self.__membership
    
    @property
    def spending(self):
        return self.__spending

    @spending.setter
    def spending(self, amount):
        self.__spending += amount

    @property
    def membership(self):
        return self.__membership
    
    @membership.setter
    def membership(self, new_membership):
        self.__membership = new_membership

    def view_current_membership(self):
        return self.membership
    
    def update_membership(self, system):
        db.execute('SELECT * FROM users WHERE id=?', [session['user_id']])
        user = db.fetchall()
        user_obj = pickle.loads(user[0]['user_object'])
        current_spending = user_obj.spending
        if current_spending >= system.membership_benefits["Premium"]["spending_limit"]:
            self.membership = "Premium"
            db.execute('''
                            UPDATE users
                            SET user_object = ?
                            WHERE username = ?
                        ''', (pickle.dumps(self), self.username)) 
            con.commit()
        elif current_spending >= system.membership_benefits["Regular"]["spending_limit"]:
            self.membership = "Regular"
            db.execute('''
                            UPDATE users
                            SET user_object = ?
                            WHERE username = ?
                        ''', (pickle.dumps(self), self.username)) 
            con.commit()
        else:
            pass

    def book_appointment(self, booking_date, pet_name, pet_type, service_name, system):
        db.execute('''
                    SELECT * FROM staffs;
                   ''',)
        staffs = db.fetchall()
        staff = random.choice(staffs) if staffs else None
        if not staff:
            return "No staff available."

        new_appointment = Appointment(booking_date, self, pet_name, pet_type, pickle.loads(staffs[0]['staff_object']).username, service_name)

        # Update spending and membership level
        self.update_membership(system)
        return new_appointment

    def cancel_appointment(self, system, appointment_date, pet_name):
        for appointment in self.appointment_list:
            if appointment.date == appointment_date and appointment.pet_name == pet_name:
                system.appointment_list.remove(appointment)
                self.remove_appointment(appointment)
                return "Appointment cancelled successfully."
        return "Appointment not found."

class Staff(User):
    def __init__(self, username, name, password):
        super().__init__(username, name, password)

    def view_services(self, system):
        return system.services

    def search_pet_by_customer_name(self, username, system):
        db.execute('SELECT * FROM appointments WHERE username=?', (username,))
        appointment = db.fetchall()

        # Using lists to store unique names and types together
        nameAndTypeList = []
        try:
            for i in range(len(appointment)):
                # Deserialize the appointment object
                appointment_object = pickle.loads(appointment[i]['appointment_object'])
                
                # Check if the combination of name and type is not already in nameAndTypeList before adding it
                if [appointment_object.pet_name, appointment_object.pet_type] not in nameAndTypeList:
                    nameAndTypeList.append([appointment_object.pet_name, appointment_object.pet_type])
        except Exception as e:
            print(f"Error during deserialization or processing: {e}")

        # Return the list containing unique name and type combinations
        return nameAndTypeList

    def view_serviced_history(self, username, system):
        db.execute('SELECT * FROM appointments WHERE username=?', (username,))
        appointments = db.fetchall()
        serviced_history_list = []
        for appointment in appointments:
            appointment_obj = pickle.loads(appointment['appointment_object'])
            if appointment_obj.staff_username:
                serviced_history_list.append([appointment_obj.date, appointment_obj.pet_name, appointment_obj.pet_type, appointment_obj.service_name])
        return serviced_history_list

class Admin(User):
    def __init__(self, username, name, password):
        super().__init__(username, name, password)

    def search_appointments_by_staff_name(self, staff_name, system):
        return [app for app in system.appointment_list if app.staff_username == staff_name]

class Owner(Admin):
    def __init__(self, username, name, password):
        super().__init__(username, name, password)

class Appointment:
    def __init__(self, date, customer, pet_name, pet_type, staff_username, service_title):
        self.__date = date
        self.__username = customer.username
        self.__pet_name = pet_name
        self.__pet_type = pet_type
        self.__staff_username = staff_username
        self.__service_name = service_title

    @property
    def username(self):
        return self.__username
    
    @property
    def pet_name(self):
        return self.__pet_name
    
    @property
    def pet_type(self):
        return self.__pet_type
    
    @property
    def staff_username(self):
        return self.__staff_username
    
    @property
    def date(self):
        return self.__date
    
    @property
    def service_name(self):
        return self.__service_name
    
    @property
    def staff_username(self):
        return self.__staff_username

    @property
    def price(self):
        return self.__price

class PetSpaSystem:
    def __init__(self):

        self.__membership_benefits = {
            "New": {"discount": "0%", "spending_limit": 0},
            "Regular": {"discount": "10%", "spending_limit": 50},
            "Premium": {"discount": "30%", "spending_limit": 100}
        }
        self.services = {"Eye Cleaning": 40, "Ear Cleaning": 40, "Teeth Cleaning": 25, "Grooming": 80, "Nail Trimming": 40, "Bathing": 50}

    def signup(self, username, name, password):
        customer = Customer(username, name, password)
        return customer

    # def login(self, username, password):
    #     for user in self.customer_list + self.staff_list + self.admin_list + self.owner_list:
    #         if user.username == username and user.password == password:
    #             return f"Welcome, {user.display_name}!"
    #     return "Invalid credentials."
    
    @property
    def membership_benefits(self):
        return self.__membership_benefits

    def get_current_date(self):
        current_datetime = datetime.now()
        print("Current Date and Time:", current_datetime)

# flask

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
# Instantiate system
spa_system = PetSpaSystem()

# Route for signup page
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
            # Create user object
            user_obj = spa_system.signup(username, name, hash)

            # Serialize user instance & insert into database
            serialized_user_obj = pickle.dumps(user_obj)
            db.execute('INSERT INTO users (type, username, user_object) VALUES (?,?,?)', ('Customer', username, serialized_user_obj))
            con.commit()

            # Fetch username
            db.execute('SELECT * FROM users WHERE username=?', [username])
            user = db.fetchall()
            print(user[0]['id'])

            # Clear session and log in with the signed up account
            session.clear()
            session['user_id'] = user[0]['id']
            return redirect('/reroute')
        
    elif request.method == 'GET':
        return render_template('signup.html')

# Route for main page
# Redirecting to login page
@app.route('/')
def redirectLogin():

    # Redirect to corresponding main pages
    if 'user_id' in session:
        return redirect('/reroute')
    else:
        return redirect('/login')

# Route for log in page
@app.route('/login', methods=['GET', 'POST'])
def loginPage():
    if request.method == 'GET':
        if 'user_id' in session:
            return redirect('/reroute') 
        else:
            return render_template('login.html')
    
    elif request.method == 'POST':

        # Fetch user inputs
        username = request.form.get('username')
        password = request.form.get('password')

        # Fetch user
        db.execute('SELECT * FROM users WHERE username=?', [username])
        user = db.fetchall()

        # Check if the username exists
        if not user:
            flash("Invalid Username.")
            return render_template('login.html')
        
        # Check password validation
        unserialized_user_object = pickle.loads(user[0]['user_object'])
        if not check_password_hash(unserialized_user_object.password, password):
            flash('Invalid Username or Password.')
            return render_template('login.html')
        else:
            session['user_id'] = user[0]['id']
            return redirect('/reroute')
            
# route for user main page
@app.route('/userMain')
def userMain():
    if 'user_id' in session:
        db.execute('SELECT * FROM users WHERE id=?', [session['user_id']])
        user = db.fetchall()

        if user[0]['type'] == "Customer":
            name = pickle.loads(user[0]['user_object']).name
            # Flash name on nav bar 
            flash(name)
            return render_template('user_main.html')
        # Redirect if not customer
        else:
            return redirect('reroute')

    else:
        return redirect('/login')

# route for services
@app.route('/services', methods=['GET','POST'])
def services():
    # Ensuring user's logged in
    if 'user_id' in session:
        db.execute('SELECT * FROM users WHERE id=?', [session['user_id']])
        user = db.fetchall()

        if user[0]['type'] == "Customer":
        
            # Rerouting if the user isn't a customer
            if user[0]['type'] != 'Customer':
                return redirect('/reroute')
            
            # Flash display name on  nav bar
            name = pickle.loads(user[0]['user_object']).name
            flash(name)

            # Flash service list
            db.execute('SELECT * FROM services')
            services = db.fetchall()
            serviceList = []
            for service in services:
                serviceList.append([service['name'], service['price']])
            flash(serviceList)
            return render_template('services.html')
        
        # Redirect if not customer
        else:
            return redirect('/reroute')
        
    else:
        return redirect('/login')
    
# Route for booking appointment
@app.route('/bookService', methods=['POST'])
def bookService():

    # Fetching user data
    selected_services = request.form.getlist('services')
    date = request.form.get('date')
    petType = request.form.get('petType')
    petName = request.form.get('petName')
    # Redirect to appointmentConfirmation with data in the URL
    return redirect(url_for('appointmentConfirmation', 
                            date=date, petName=petName, petType=petType, 
                            selected_services_list=','.join(selected_services)))

# route for appointment confirmation
@app.route('/appointmentConfirmation', methods=['GET', 'POST'])
def appointmentConfirmation():
    if 'user_id' in session:

        db.execute('DELETE FROM appointment_summary;')
        con.commit()

        # To flash display name on nav bar
        db.execute('SELECT * FROM users WHERE id=?', [session['user_id']])
        user = db.fetchall()
        name = pickle.loads(user[0]['user_object']).name

        # Fetch data from the URL parameters
        date = request.args.get('date')
        petName = request.args.get('petName')
        petType = request.args.get('petType')
        selected_services = request.args.get('selected_services_list').split(',')

        # Fetch user_obj from database
        db.execute('SELECT * FROM users WHERE id=?', [session['user_id']])
        user = db.fetchall()
        username = user[0]['username']

        db.execute('SELECT * FROM services')
        services = db.fetchall()

        # Calculation of total price
        selected_services_prices = []
        for selected_service in selected_services:
            for service in services:
                if selected_service == service['name']:
                    selected_services_prices.append(service['price'])
        totalPrice = 0
        totalPrice += sum(selected_services_prices)
    
        # Fetching membership_type for final price calculation
        unserialized_user = pickle.loads(user[0]['user_object'])
        membership_type = unserialized_user.membership
        discount = int(spa_system.membership_benefits[membership_type]["discount"][:-1])
        finalPrice = int(totalPrice - (totalPrice * (discount / 100)))

        # Insert into appointment_summary database
        db.execute('''
                    INSERT INTO appointment_summary (username, name, petName, petType, date, 
                    selected_services, selected_services_prices, 
                    totalPrice, discount, finalPrice)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', 
                    (unserialized_user.username, name, petName, petType, date, 
                    pickle.dumps(selected_services), pickle.dumps(selected_services_prices), 
                    totalPrice, discount, finalPrice))
        con.commit()

        # Flashing data
        # Flash 0
        flash(name)
        # Flash 1
        flash(petName)
        # Flash 2
        flash(petType)
        # Flash 3
        flash(date)
        # Flash 4
        flash(selected_services)
        # Flash 5
        flash(selected_services_prices)
        # Flash 6
        flash(totalPrice)
        # Flash 7
        flash(discount)
        # Flash 8
        flash(finalPrice)
        return render_template("appointment_confirmation.html")
        

# Route for confirmed appointment
@app.route('/appointmentConfirmed', methods=['GET', 'POST'])
def appointmentConfirmed():
    if request.method == "POST":
        if 'user_id' in session: 

            # Fetch data from database
            db.execute('SELECT * FROM users WHERE id=?', [session['user_id']])
            user = db.fetchall()
            user_obj = pickle.loads(user[0]['user_object'])
            name = user_obj.name
            username = user_obj.username
            
            # Fetch appointment history
            db.execute('SELECT * FROM appointment_summary WHERE username = ?', (username,))
            appointmentHistory = db.fetchall()
   
            petName = appointmentHistory[0]['petName']
            petType = appointmentHistory[0]['petType']
            date = appointmentHistory[0]['date']
            selected_services = pickle.loads(appointmentHistory[0]['selected_services'])
            selected_services_prices = pickle.loads(appointmentHistory[0]['selected_services_prices'])
            totalPrice = appointmentHistory[0]['totalPrice']
            discount = appointmentHistory[0]['discount']
            finalPrice = appointmentHistory[0]['finalPrice']
            user_obj.spending += finalPrice
            user_obj.update_membership(spa_system)

            # Update user's spending in database
            db.execute('''
                            UPDATE users
                            SET user_object = ?
                            WHERE username = ?
                        ''', (pickle.dumps(user_obj), username)) 
            con.commit()
            
            # Create appointment object and insert into database
            for i in range(len(selected_services)):
                appointment_obj = user_obj.book_appointment(date, petName, petType, selected_services[i], spa_system)
                db.execute('''
                            INSERT INTO appointments(username, appointment_object)
                            VALUES (?, ?)
                        ''', (username, pickle.dumps(appointment_obj)))
                con.commit()
            
            # Flashing data
            # Flash 0
            flash(name)
            # Flash 1
            flash(petName)
            # Flash 2
            flash(petType)
            # Flash 3
            flash(date)
            # Flash 4
            flash(selected_services)
            # Flash 5
            flash(selected_services_prices)
            # Flash 6
            flash(totalPrice)
            # Flash 7
            flash(discount)
            # Flash 8
            flash(finalPrice)

            return render_template("appointment_confirmed.html")

# route for appointment
@app.route('/appointment')
def appointment():  
    db.execute('SELECT * FROM users WHERE id=?', [session['user_id']])
    user = db.fetchall()

    # Flash display name on nav bar
    name = pickle.loads(user[0]['user_object']).name
    flash(name)

    # Fetching appointments from appointments database
    username = pickle.loads(user[0]['user_object']).username
    db.execute('SELECT * FROM appointments WHERE username=?', (username,))
    appointments = db.fetchall()

    current_date = datetime.today().date()
    pastAppointments = []
    upcomingAppointments = []

    # Seperate appointments into upcoming and history tables using current date
    for appointment in appointments:
        appointment_obj = pickle.loads(appointment['appointment_object'])
        print(appointment_obj)
        appointment_date = datetime.strptime(appointment_obj.date, '%Y-%m-%d').date()
        if current_date > appointment_date:
            pastAppointments.append([appointment_obj.date, appointment_obj.pet_name, appointment_obj.pet_type, appointment_obj.service_name])
        else:
            upcomingAppointments.append([appointment_obj.date, appointment_obj.pet_name, appointment_obj.pet_type, appointment_obj.service_name])
    
    # Flash appointments
    flash(upcomingAppointments)
    flash(pastAppointments)
    return render_template('appointment.html')

# route for customer membership
@app.route('/userMembership')
def userMembership():
    db.execute('SELECT * FROM users WHERE id=?', [session['user_id']])
    user = db.fetchall()

    # Flash display name on nav bar
    name = pickle.loads(user[0]['user_object']).name
    flash(name)

    unserialized_user = pickle.loads(user[0]['user_object'])

    # Flash user's membership type
    membership_type = unserialized_user.membership
    flash(membership_type)

    # Flash user's total spending
    spending = unserialized_user.spending
    flash(spending)

    # Discounts and minimum spendings for respective member types
    # For new members
    new_discount = spa_system.membership_benefits["New"]["discount"]
    newMinimumSpending = spa_system.membership_benefits["New"]["spending_limit"]
    
    # For regular members
    regular_discount = spa_system.membership_benefits["Regular"]["discount"]
    regularMinimumSpending = spa_system.membership_benefits["Regular"]["spending_limit"]
    
    # For premium members
    premium_discount = spa_system.membership_benefits["Premium"]["discount"]
    premiumMinimumSpending = spa_system.membership_benefits["Premium"]["spending_limit"]
    
    # Flash data
    flash(new_discount)
    flash(newMinimumSpending)
    flash(regular_discount)
    flash(regularMinimumSpending)
    flash(premium_discount)
    flash(premiumMinimumSpending)
    return render_template('user_membership.html')

# Route for customer edit profile
@app.route('/customerEditProfile')
def customerEditProfile():

    # Flashing name in nav bar
    db.execute('SELECT * FROM users WHERE id=?', [session['user_id']])
    user = db.fetchall()
    user_obj = pickle.loads(user[0]['user_object'])
    flash(user_obj.name)

    return render_template('customer_edit_profile.html')

# Route to change name
@app.route('/changeName', methods=['GET','POST'])
def changeName():
    if request.method == 'POST':
        newName = request.form.get("newName")
        db.execute('SELECT * FROM users WHERE id=?', [session['user_id']])
        user = db.fetchall()
        user_obj = pickle.loads(user[0]['user_object'])

        # Update display name using setter and update in database
        user_obj.name = newName 
        db.execute('UPDATE users SET user_object=? WHERE id=?', (pickle.dumps(user_obj), session['user_id']))
        con.commit()

        db.execute('SELECT * FROM users WHERE id=?', [session['user_id']])
        user = db.fetchall()
        user_obj = pickle.loads(user[0]['user_object'])

        # Flashing display name in nav bar
        flash(user_obj.name) 
        
        flash("Name Change Success")
        return render_template('customer_edit_profile.html')

# Route for editing password
@app.route('/changePassword', methods=['GET','POST'])
def changePassword():
    if request.method == 'POST':
        db.execute('SELECT * FROM users WHERE id=?', [session['user_id']])
        user = db.fetchall()
        user_obj = pickle.loads(user[0]['user_object'])
        
        # Flashing name in nav bar
        name = user_obj.name
        flash(name)  

        # Fetch user input
        oldPassword = request.form.get("oldPassword")
        newPassword = request.form.get("newPassword")

        # Check user validation
        if not check_password_hash(user_obj.password, oldPassword):
            flash("Failed")
        else:
            print(user_obj.password)
            # Generate password hash
            user_obj.password = generate_password_hash(newPassword, method='pbkdf2:sha256', salt_length=8)
            
            # Update database with new password
            db.execute('UPDATE users SET user_object=? WHERE id=?', (pickle.dumps(user_obj), session['user_id']))
            con.commit()
            flash("Success")
        
        return render_template('customer_edit_profile.html')

@app.route('/ownerDashboard')
def ownerDashboard():   

    db.execute('SELECT * FROM users WHERE id=?', [session['user_id']])
    user = db.fetchall()
 
    # Flashing display name in nav bar
    name = pickle.loads(user[0]['user_object']).name
    flash(name)

    # Flash staff list  
    db.execute("SELECT * FROM users WHERE type = 'Admin' OR type = 'Staff'")
    staffs = db.fetchall()
    staff_list = []
    for staff in staffs:
        staff_list.append([(pickle.loads(staff['user_object'])).name,staff['username'], staff['type']])
    flash(staff_list)
    
    # Flash available services
    db.execute('SELECT * FROM services')
    services = db.fetchall()
    serviceList = []
    for service in services:
        serviceList.append([service['name'], service['price']])
    flash(serviceList)

    # Flash service dropdown to delete
    serviceListToDelete = []
    for service in services:
        serviceListToDelete.append(service['name'])
    flash(serviceListToDelete)

    return render_template('owner_dashboard.html')

# Route for generating report
@app.route('/ownerGenerateReport', methods=['GET','POST'])
def ownerGenerateReport():
    if request.method == "POST":
        db.execute('SELECT * FROM users WHERE id=?', [session['user_id']])
        user = db.fetchall()
        
        # Flash display name on nav bar
        name = pickle.loads(user[0]['user_object']).name
        flash(name)

        db.execute("SELECT * FROM appointments")
        appointments = db.fetchall()

        # Store appointments in a list to flash
        appointment_list = []
        for appointment in appointments:
            appointment_obj = pickle.loads(appointment['appointment_object'])
            appointment_list.append([appointment_obj.date, appointment_obj.pet_name, appointment_obj.pet_type, appointment_obj.service_name])
        flash(appointment_list)

        return render_template('ownerReport.html')

# Route for staff dashboard
@app.route('/staffDashboard')
def staffDashboard():   
    db.execute('SELECT * FROM users WHERE id=?', [session['user_id']])
    user = db.fetchall()
    flash(pickle.loads(user[0]['user_object']).name)
    return render_template('staff_dashboard.html')

@app.route('/adminDashboard')
def adminDashboard():
    db.execute('SELECT * FROM users WHERE id=?', [session['user_id']])

    # Flash display name on nav bar
    user = db.fetchall()
    flash(pickle.loads(user[0]['user_object']).name)

    return render_template('admin_dashboard.html')

# Route for recruiting new staff
@app.route('/recruitStaff', methods=['GET','POST'])
def recruitStaff():
    if request.method == "POST":
        db.execute('SELECT * FROM users WHERE id=?', [session['user_id']])
        user = db.fetchall()

        # Flash display name on nav bar
        name = pickle.loads(user[0]['user_object']).name
        flash(name)

        username = request.form.get("usernameToAdd")
        password = request.form.get("newUserPassword")
        db.execute("SELECT * FROM users")
        users = db.fetchall()
        
        # Check username duplication
        for user in users:
            if username == user['username']:
                flash("Failed")
                return render_template('admin_dashboard.html')
        flash("Success")

        # Create staff object and store data in database
        staff1 = Staff(username, username, generate_password_hash(password, method='pbkdf2:sha256', salt_length=8))
        db.execute('''
            INSERT INTO users (type, username, user_object)
            VALUES (?,?,?)
        ''', ("Staff", username, pickle.dumps(staff1)))

        db.execute('''
            INSERT INTO staffs (username, staff_object)
            VALUES (?,?)
        ''', (username, pickle.dumps(staff1)))

        con.commit()

        return render_template("admin_dashboard.html")
        
# Route for finding staffs
@app.route('/findStaff', methods=["GET", "POST"])
def findStaff():
    if request.method == "POST":
        # Flash display name on nav bar
        db.execute('SELECT * FROM users WHERE id=?', [session['user_id']])
        user = db.fetchall()
        name = pickle.loads(user[0]['user_object']).name
        flash(name)
        flash("Success")

        # Fetch user input and flash corresponding staff name
        staffUsernameToSearch = request.form.get("staffNameToSearch")
        db.execute('SELECT * FROM users WHERE username=?',(staffUsernameToSearch,))
        staff = db.fetchall()
        flash("Staff Name")
        flash((pickle.loads(staff[0]['user_object'])).name)

        # Flash staff's appointments
        db.execute("SELECT * FROM appointments")
        appointments = db.fetchall()
        appointment_list = []

        # Looping to see if appointments are staff's
        for appointment in appointments:
            appointment_obj = pickle.loads(appointment['appointment_object'])
            if appointment_obj.staff_username == staffUsernameToSearch:
                appointment_list.append([appointment_obj.date, appointment_obj.pet_name, appointment_obj.pet_type, appointment_obj.service_name])
        flash(appointment_list)
        return render_template("admin_dashboard.html")
    
# Route for deleting staffs
@app.route('/deleteStaff', methods=["GET", "POST"])
def deleteStaff():
    if request.method == "POST":

        # Fetch staff data and delete from database
        staffToDelete = request.form.get("staffNameToDelete")
        db.execute('''DELETE FROM users WHERE username = ?''', (staffToDelete,))
        con.commit()
        return redirect('/reroute')
    
# Route for admin dashboard
@app.route('/admin_services_membership')
def adminServicesMembership():
    db.execute('SELECT * FROM users WHERE id=?', [session['user_id']])
    user = db.fetchall()

    # Flashing display name on nav bar
    name = pickle.loads(user[0]['user_object']).name
    flash(name)
    
    # Flash services
    db.execute('SELECT * FROM services')
    services = db.fetchall()
    serviceList = []
    for service in services:
        serviceList.append([service['name'], service['price']])
    flash(serviceList)


    # Discounts and minimum spendings for respective member types
    # For new members
    new_discount = spa_system.membership_benefits["New"]["discount"]
    newMinimumSpending = spa_system.membership_benefits["New"]["spending_limit"]
    flash(new_discount)
    flash(newMinimumSpending)
    
    # For regular members
    regular_discount = spa_system.membership_benefits["Regular"]["discount"]
    regularMinimumSpending = spa_system.membership_benefits["Regular"]["spending_limit"]
    flash(regular_discount)
    flash(regularMinimumSpending)
    
    # For premium members
    premium_discount = spa_system.membership_benefits["Premium"]["discount"]
    premiumMinimumSpending = spa_system.membership_benefits["Premium"]["spending_limit"]
    flash(premium_discount)
    flash(premiumMinimumSpending)
    return render_template("admin_services_membership.html")

# Route for searching pet by Customer username
@app.route('/petSearch', methods=['GET','POST'])
def petSearch():
    if request.method == "POST":
        db.execute('SELECT * FROM users WHERE id=?', (session['user_id'],))
        user = db.fetchall()
        flash((pickle.loads(user[0]['user_object']).name))

        # Fetching username input for pet search 
        usernameForPetSearch =  request.form.get("usernameForPetSearch")

        user_obj = pickle.loads(user[0]['user_object'])
        # For searching pet by customer name
        nameAndTypeList = []
        nameAndTypeList = user_obj.search_pet_by_customer_name(usernameForPetSearch, spa_system)
        flash(nameAndTypeList)

        # Fetch and flash appointments
        db.execute('SELECT * FROM appointments WHERE username=?', (usernameForPetSearch,))
        appointments = db.fetchall()
        appointmentList = []
        for appointment in appointments:
            appointment_obj = pickle.loads(appointment['appointment_object'])
            appointmentList.append([appointment['id'],appointment_obj.date, appointment_obj.pet_name, appointment_obj.pet_type, appointment_obj.service_name])
        flash(appointmentList)

        # Service_history
        username = user_obj.username
        service_history_list = user_obj.view_serviced_history(username, spa_system)
        flash(service_history_list)
        return render_template('staff_dashboard.html')
    
# Route for logging out
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

# Route for redirecting based on user type
@app.route('/reroute')
def reroute():
    if 'user_id' in session:
        db.execute('SELECT * FROM users WHERE id=?', [session['user_id']])
        user = db.fetchall()
        user_type = user[0]['type']
        display_name = pickle.loads(user[0]['user_object']).name

        # Flash display name
        flash(display_name)
        if user_type == "Owner":
            return redirect('/ownerDashboard')
        elif user_type == "Admin":
            return redirect('/adminDashboard')
        elif user_type == "Staff":
            return redirect('/staffDashboard')
        elif user_type == "Customer":
            return redirect('/userMain')
    else:
        return redirect('/login')

# Temporary route
@app.route('/temp')
def temp():
    db.execute('SELECT * FROM staffs WHERE username=?', ('tony',))
    user = db.fetchall()
    tony_obj = user[0]['staff_object']
    print((pickle.loads(tony_obj).username))
    tony = pickle.loads(tony_obj)
    db.execute('''
                INSERT INTO users (type, username, user_object)
                VALUES (?,?,?)
            ''', ("Staff", tony.username, tony_obj))
    con.commit()
    return redirect('/')

@app.route('/addAdmin')
def addAdmin():
    admin = Admin("admin", "admin", generate_password_hash("admin", method='pbkdf2:sha256', salt_length=8))
    db.execute('''
                INSERT INTO users (type, username, user_object)
                VALUES (?,?,?)
            ''', ("Admin", admin.username, pickle.dumps(admin)))
    con.commit()
    return redirect('/reroute')

@app.route('/addOwner')
def addOwner():
    owner1 = Owner("owner", "owner", generate_password_hash("owner", method='pbkdf2:sha256', salt_length=8))
    db.execute('''
                INSERT INTO users (type, username, user_object)
                VALUES (?,?,?)
            ''', ("Owner", owner1.username, pickle.dumps(owner1)))
    con.commit()
    return redirect('/reroute')

# Route for deleting appointment
@app.route('/deleteAppointment', methods = ['GET', 'POST'])
def deleteAppointment():
    if request.method == "POST":
        appointmentIds = request.form.getlist('appointment_checkboxes')
        for appointmentId in appointmentIds:
            db.execute('DELETE FROM appointments WHERE id=?', (appointmentId,))
            con.commit()
        return redirect('/staffDashboard')
    
# Route for deleting service
@app.route('/deleteService',methods=['GET', 'POST'])
def deleteService():
    if request.method=='POST':
        serviceToDelete = request.form.get("serviceToDelete")
        db.execute('DELETE FROM services WHERE name=?', (serviceToDelete,))
        con.commit()
        return redirect('/ownerDashboard')

# Route for changing service prices
@app.route('/changeServicePrice', methods=['GET','POST'])
def changeServicePrice():
    if request.method == "POST":
        serviceToChange = request.form.get('serviceToChange')
        newServicePrice = int(request.form.get('newServicePrice'))
        db.execute('UPDATE services SET price=? WHERE name=?', (newServicePrice, serviceToChange))
        con.commit()
        return redirect('/ownerDashboard')

# Add new service
@app.route('/addNewService', methods=['GET', 'POST'])
def addNewService():
    if request.method == "POST":
        addedServiceName = request.form.get('addedServiceName')
        addedServicePrice = int(request.form.get('addedServicePrice'))
        db.execute('INSERT INTO services (name, price) VALUES (?, ?)', (addedServiceName, addedServicePrice))
        con.commit()
        return redirect('/ownerDashboard')

if __name__ == '__main__':
    app.run(debug=True)