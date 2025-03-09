from flask import Flask, render_template, request, flash, session, redirect
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
import sqlite3
import json
import pickle

# OOP code
import random
from datetime import datetime

class User:
    def __init__(self, username, name, password):
        self.username = username
        self.name = name
        self.password = password

    def edit_profile(self, new_name=None, new_password=None):
        if new_name:
            self.name = new_name
        if new_password:
            self.password = new_password
        return "Profile updated successfully."


class Customer(User):
    def __init__(self, username, name, password):
        super().__init__(username, name, password)
        self.pet_list = []
        self.appointment_list = []
        self.spending = 0
        self.membership = "new"

    def view_services(self, system):
        return system.services

    def view_membership_benefits(self, system):
        return system.membership_benefits
    
    def view_current_membership(self):
        return self.membership
    
    def update_membership(self, system):
        if self.spending >= system.membership_benefits["premium"]["spending_limit"]:
            self.membership = "premium"
        elif self.spending >= system.membership_benefits["regular"]["spending_limit"]:
            self.membership = "regular"
        else:
            self.membership = "new"

    def book_appointment(self, booking_date, pet_name, pet_type, service_name, system):
        if service_name not in system.services:
            return "Invalid service."
        
        staff = random.choice(system.staff_list) if system.staff_list else None
        if not staff:
            return "No staff available."

        #update_price_according_to_discount_rate
        org_price = system.services[service_name]
        discount_rate_str = system.membership_benefits[self.membership]["discount"]
        if discount_rate_str != "0%":
            discount_rate = int(discount_rate_str[0:2])/100
            price = org_price - (org_price * discount_rate)
        else:
            price = org_price

        appointment = Appointment(booking_date, self, pet_name, pet_type, staff.username, service_name, price)
        self.appointment_list.append(appointment)
        system.appointment_list.append(appointment)
        self.pet_list.append((pet_name, pet_type))

        # Update spending and membership level
        self.spending += price
        self.update_membership(system)

        return f"Appointment booked successfully:\n{appointment}"

    def view_appointments(self):
        return self.appointment_list if self.appointment_list else "No appointments found."

    def cancel_appointment(self, system, appointment_date):
        for appointment in self.appointment_list:
            if appointment.date == appointment_date:
                self.appointment_list.remove(appointment)
                system.appointment_list.remove(appointment)
                return "Appointment cancelled successfully."
        return "Appointment not found."


class Staff(User):
    def __init__(self, username, name, password):
        super().__init__(username, name, password)
        self.service_history = []

    def view_services(self, system):
        return system.services

    def search_pet_by_customer_name(self, customer_name, system):
        for customer in system.customer_list:
            if customer.username == customer_name:
                return customer.pet_list
        return "Customer not found."

    def cancel_appointment(self, system, appointment_date):
        for appointment in system.appointment_list:
            if appointment.date == appointment_date:
                system.appointment_list.remove(appointment)
                return "Appointment cancelled."
        return "Appointment not found."

    def view_serviced_history(self):
        return self.service_history


class Admin(User):
    def __init__(self, username, name, password):
        super().__init__(username, name, password)

    def view_membership_benefits(self, system):
        return system.membership_benefits

    def view_services(self, system):
        return system.services

    def search_appointments_by_staff_name(self, staff_name, system):
        return [app for app in system.appointment_list if app.staff_username == staff_name]

    def search_pet_by_customer_name(self, customer_name, system):
        for customer in system.customer_list:
            if customer.username == customer_name:
                return customer.pet_list
        return "Customer not found."

    def cancel_appointment(self, system, appointment_date):
        return Staff.cancel_appointment(self, system, appointment_date)

    def add_staff(self, system, staff_username, password, name=None):
        staff = Staff(staff_username, name or staff_username, password)
        system.staff_list.append(staff)
        return f"Staff {staff_username} added successfully."

    def remove_staff(self, system, staff_username):
        system.staff_list = [staff for staff in system.staff_list if staff.username != staff_username]
        return f"Staff {staff_username} removed successfully."

    def generate_report(self, system):
        return {
            "total_customers": len(system.customer_list),
            "total_staff": len(system.staff_list),
            "total_admins": len(system.admin_list),
            "total_appointments": len(system.appointment_list),
            "generated_income": sum(app.price for app in system.appointment_list)
        }


class Owner(Admin):
    def __init__(self, username, name, password):
        super().__init__(username, name, password)

    def edit_membership_discount(self, system, membership_name, new_discount):
        if membership_name in system.membership_discounts:
            system.membership_discounts[membership_name] = new_discount
            return f"Discount for {membership_name} updated to {new_discount}%."
        return "Membership not found. Cannot update discount."

    def add_service(self, system, service_name, price):
        system.services[service_name] = price
        return f"Service {service_name} added."

    def delete_service(self, system, service_name):
        if service_name in system.services:
            del system.services[service_name]
            return f"Service {service_name} deleted."
        return "Service not found."

    def promote_to_admin(self, system, staff_username):
        for staff in system.staff_list:
            if staff.username == staff_username:
                admin = Admin(staff.username, staff.name, staff.password)
                system.admin_list.append(admin)
                system.staff_list.remove(staff)
                return f"Staff {staff_username} promoted to admin."
        return "Staff not found."

    def delete_admin_account(self, system, username):
        system.admin_list = [admin for admin in system.admin_list if admin.username != username]
        return f"Admin {username} deleted."


class Appointment:
    def __init__(self, date, customer, pet_name, pet_type, staff_username, service_name, price):
        self.date = date
        self.username = customer.username
        self.pet_name = pet_name
        self.pet_type = pet_type
        self.staff_username = staff_username
        self.service_name = service_name
        self.price = price

    def __str__(self):
        return f"Customer: {self.username} made an appointment on {self.date}. +++\n{self.staff_username} will service {self.pet_name} ({self.pet_type}) for {self.service_name} treatment.\nTotal Price: ${self.price}."


class PetSpaSystem:
    def __init__(self):
        self.customer_list = []
        self.staff_list = []
        self.admin_list = []
        self.owner_list = []
        self.appointment_list = []
        self.membership_benefits = {
            "new": {"discount": "0%", "spending_limit": 0},
            "regular": {"discount": "10%", "spending_limit": 50},
            "premium": {"discount": "30%", "spending_limit": 100}
        }
        self.services = {"Grooming": 50, "Bathing": 30, "Nail Trimming": 20}

    def signup(self, username, name, password):
        customer = Customer(username, name, password)
        self.customer_list.append(customer)
        return customer

    def login(self, username, password):
        for user in self.customer_list + self.staff_list + self.admin_list + self.owner_list:
            if user.username == username and user.password == password:
                return f"Welcome, {user.name}!"
        return "Invalid credentials."

    def get_current_date(self):
        current_datetime = datetime.now()
        print("Current Date and Time:", current_datetime)




# # Register staff using Owner's add_staff() method
# owner = Owner("owner1", "Owner", "ownerpass")
# spa_system.owner_list.append(owner)  # Adding owner to the system
# owner.add_staff(spa_system, "staff1", "staffpass1", "Staff One")
# owner.add_staff(spa_system, "staff2", "staffpass2", "Staff Two")
# owner.add_staff(spa_system, "staff3", "staffpass3", "Staff Three")
# owner.add_staff(spa_system, "staff4", "staffpass4", "Staff Four")

# # Add an admin (manually appending to the admin list)
# admin = Admin("admin1", "Admin One", "adminpass")
# spa_system.admin_list.append(admin)

# # Register customers using existing signup() method
# spa_system.signup("alice123", "Alice", "pass123")
# spa_system.signup("bob456", "Bob", "pass456")
# spa_system.signup("carol789", "Carol", "pass789")
# spa_system.signup("dave321", "Dave", "pass321")
# spa_system.signup("eve654", "Eve", "pass654")
# spa_system.signup("frank987", "Frank", "pass987")

# # Fetch customers from the system
# alice = next(user for user in spa_system.customer_list if user.username == "alice123")
# bob = next(user for user in spa_system.customer_list if user.username == "bob456")
# carol = next(user for user in spa_system.customer_list if user.username == "carol789")
# dave = next(user for user in spa_system.customer_list if user.username == "dave321")
# eve = next(user for user in spa_system.customer_list if user.username == "eve654")
# frank = next(user for user in spa_system.customer_list if user.username == "frank987")

# # Booking services using book_appointment() (without a separate Pet class)
# alice.book_appointment("20.3.2025", "Buddy", "Dog", "Grooming", spa_system)
# bob.book_appointment("15.3.2025", "Kitty", "Cat", "Nail Trimming", spa_system)
# carol.book_appointment("22.3.2025","Tommy", "Bird", "Bathing", spa_system)
# dave.book_appointment("23.3.2025","Linn", "Dog", "Grooming", spa_system)
# eve.book_appointment("16.3.2025", "Whiskers", "Cat", "Nail Trimming", spa_system)
# frank.book_appointment("25.3.2025", "Bruno", "Dog", "Grooming", spa_system)
# frank.book_appointment("20.3.2025", "Romulus", "Dog", "Grooming", spa_system)

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
spa_system = PetSpaSystem()

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
            serialized_user_obj = pickle.dumps(user_obj)
            db.execute('INSERT INTO testing (type, username, user_object) VALUES (?,?,?)', ('Customer', username, serialized_user_obj))
            con.commit()

            # Remembering users using session
            db.execute('SELECT * FROM testing WHERE username=?', [username])
            user = db.fetchall()
            session.clear()
            session['user_id'] = user[0]['id']
            return redirect('/userMain')

    elif request.method == 'GET':
        return render_template('signup.html')

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
        db.execute('SELECT * FROM testing WHERE username=?', [username])
        user = db.fetchall()
        if not user:
            flash("Invalid Username.")
            return render_template('login.html')
        unserialized_user_object = pickle.loads(user[0]['user_object'])
        if not check_password_hash(unserialized_user_object.password, password):
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
            
    
# route for user main page
@app.route('/userMain')
def userMainPage():
    if 'user_id' in session:
        return render_template('user_main.html')
    else:
        return redirect('/login')
    
# route for services
@app.route('/services', methods=['GET','POST'])
def services():
    if request.method == 'GET':
        return render_template('services.html')
    elif request.method == 'POST':
        selected_services = request.form.getlist('services')
        print(selected_services)
        return redirect('/userMain')

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


