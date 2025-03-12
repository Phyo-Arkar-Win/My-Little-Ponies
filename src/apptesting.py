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
        self.__pet_list = []
        self.__appointment_list = []
        self.__spending = 0
        self.__membership = "New"

    @property
    def pet_list(self):
        return self.__pet_list
    
    @property
    def membership(self):
        return self.__membership
    
    def add_pet(self, new_pet):
        self.__pet_list.append(new_pet)
    
    def remove_pet(self, target_pet):
        self.__pet_list.remove(target_pet) 

    @property
    def appointment_list(self):
        return self.__appointment_list
    
    def add_appointment(self, new_appointment):
        self.__appointment_list.append(new_appointment)

    def remove_appointment(self, target_appointment):
        self.__appointment_list.remove(target_appointment)
    
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

    def view_services(self, system):
        return system.services

    def view_membership_benefits(self, system):
        return system.membership_benefits
    
    def view_current_membership(self):
        return self.membership
    
    def update_membership(self, system):
        db.execute('SELECT * FROM testing WHERE id=?', [session['user_id']])
        user = db.fetchall()
        user_obj = pickle.loads(user[0]['user_object'])
        current_spending = user_obj.spending
        if current_spending >= system.membership_benefits["Premium"]["spending_limit"]:
            self.membership = "Premium"
            db.execute('''
                            UPDATE your_table_name
                            SET user_object = ?
                            WHERE username = ?
                        ''', (self, self.username)) 
            con.commit()
        elif current_spending >= system.membership_benefits["Regular"]["spending_limit"]:
            self.membership = "Regular"
            db.execute('''
                            UPDATE your_table_name
                            SET user_object = ?
                            WHERE username = ?
                        ''', (self, self.username)) 
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

        # #update_price_according_to_discount_rate
        # org_price = system.services[service_name]
        # discount_rate_str = system.membership_benefits[self.membership]["discount"]
        # if discount_rate_str != "0%":
        #     discount_rate = int(discount_rate_str[0:2])/100
        #     price = org_price - (org_price * discount_rate)
        # else:
        #     price = org_price

        # print(pickle.loads(staffs[0]['staff_object']))
        new_appointment = Appointment(booking_date, self, pet_name, pet_type, pickle.loads(staffs[0]['staff_object']).username, service_name)
        # system.appointment_list.append(new_appointment)
        # self.add_appointment(new_appointment)
        self.add_pet([pet_name, pet_type])

        # Update spending and membership level
        self.update_membership(system)

        return new_appointment

    def view_appointments(self):
        return self.appointment_list if self.appointment_list else "No appointments found."

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


    def cancel_appointment(self, system, appointment_date):
        for appointment in system.appointment_list:
            if appointment.date == appointment_date:
                system.appointment_list.remove(appointment)
                return "Appointment cancelled."
        return "Appointment not found."

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

    def add_staff(self, system, staff=Staff):
        system.staff_list.append(staff)
        return f"Staff {staff.username} added successfully."

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

    def edit_membership_discount(self, system, membership_title, new_discount):
        if membership_title in system.membership_discounts:
            system.membership_discounts[membership_title] = new_discount
            return f"Discount for {membership_title} updated to {new_discount}%."
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

    # def __str__(self):
    #     return (f"Customer: {self.__username} made an appointment on {self.__date}. +++\n"
    #             f"{self.__staff_username} will service {self.__pet_name} ({self.__pet_type}) "
    #             f"for {self.__service_name} treatment.\nTotal Price: ${self.__price}.")


class PetSpaSystem:
    def __init__(self):
        self.customer_list = []
        self.staff_list = []
        self.admin_list = []
        self.owner_list = []
        self.appointment_list = []
        self.__membership_benefits = {
            "New": {"discount": "0%", "spending_limit": 0},
            "Regular": {"discount": "10%", "spending_limit": 50},
            "Premium": {"discount": "30%", "spending_limit": 100}
        }
        self.services = {"Eye Cleaning": 40, "Ear Cleaning": 40, "Teeth Cleaning": 25, "Grooming": 80, "Nail Trimming": 40, "Bathing": 50}

    def signup(self, username, name, password):
        customer = Customer(username, name, password)
        return customer

    def login(self, username, password):
        for user in self.customer_list + self.staff_list + self.admin_list + self.owner_list:
            if user.username == username and user.password == password:
                return f"Welcome, {user.display_name}!"
        return "Invalid credentials."
    
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
    if 'user_id' in session:
        return redirect('/reroute')
    
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
                return render_template('staffDashboard.html')
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
                return redirect('/staffDashboard')
            else:
                return redirect('/userMain')
            
# route for user main page
@app.route('/userMain')
def userMainPage():
    if 'user_id' in session:
        db.execute('SELECT * FROM testing WHERE id=?', [session['user_id']])
        user = db.fetchall()
        username = pickle.loads(user[0]['user_object']).name
        flash(username)
        return render_template('user_main.html')
    else:
        return redirect('/login')
    
# route for services
@app.route('/services', methods=['GET','POST'])
def services():
    # Ensuring user's logged in
    if 'user_id' in session:
        if request.method == 'GET':
            # Flashing username in nav bar
            db.execute('SELECT * FROM testing WHERE id=?', [session['user_id']])
            user = db.fetchall()
            username = pickle.loads(user[0]['user_object']).name
            flash(username)
            return render_template('services.html')
        
        # For redirecting to appointmentConfirmation after pressing "book"
        elif request.method == 'POST':
            # Fetching user data
            selected_services = request.form.getlist('services')
            date = request.form.get('date')
            petType = request.form.get('petType')
            petName = request.form.get('petName')
            # Redirect to appointmentConfirmation with data in the URL
            return redirect(url_for('appointmentConfirmation', 
                                    date=date, petName=petName, petType=petType, 
                                    selected_services_list=','.join(selected_services)))
    else:
        return redirect('/login')

# route for appointment confirmation
@app.route('/appointmentConfirmation', methods=['GET', 'POST'])
def appointmentConfirmation():

    if request.method == "GET":
        if 'user_id' in session:
            db.execute('DELETE FROM appointment_summary;')
            con.commit()
            # Fetch username
            db.execute('SELECT * FROM testing WHERE id=?', [session['user_id']])
            user = db.fetchall()
            name = pickle.loads(user[0]['user_object']).name
            # Fetch data from the URL parameters
            date = request.args.get('date')
            petName = request.args.get('petName')
            petType = request.args.get('petType')
            selected_services = request.args.get('selected_services_list').split(',')

            # Fetch user_obj from database
            db.execute('SELECT * FROM testing WHERE id=?', [session['user_id']])
            user = db.fetchall()

            # Calculation of total price
            selected_services_prices = []
            for selected_service in selected_services:
                if selected_service in spa_system.services:
                    selected_services_prices.append(spa_system.services[selected_service])
            
            totalPrice = 0
            totalPrice += sum(selected_services_prices)
        
            # Fetching membership_type for final price calculation
            unserialized_user = pickle.loads(user[0]['user_object'])
            membership_type = unserialized_user.membership
            discount = int(spa_system.membership_benefits[membership_type]["discount"][:-1])
            finalPrice = int(totalPrice - totalPrice * (discount / 100))

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
        # flash(name, petName, petType, date, selected_services,selected_services_prices, totalPrice, discount, finalPrice)
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

        # Create appointment object
        # unserialized_user.book_appointment(date, petName, petType, selected_services, spa_system)
        return render_template("appointment_confirmation.html")
    elif request.method == "POST":
        return redirect(url_for('appointmentConfirmed'))
        # return redirect(url_for('appointmentConfirmed', 
        #                 name=name, petName=petName, petType=petType, 
        #                 date=date, selected_services_list=",".join(selected_services), 
        #                 selected_services_prices_list=",".join(selected_services_prices),
        #                 discount=discount,finalPrice=finalPrice))

# Route for confirmed appointment
@app.route('/appointmentConfirmed', methods=['GET', 'POST'])
def appointmentConfirmed():

    if request.method == "GET":
        if 'user_id' in session: 
            # Fetch username
            db.execute('SELECT * FROM testing WHERE id=?', [session['user_id']])
            user = db.fetchall()
            user_obj = pickle.loads(user[0]['user_object'])
            name = user_obj.name
            username = user_obj.username
            
            # Fetch appointment history
            db.execute('SELECT * FROM appointment_summary WHERE username = ?', (username,))
            appointmentHistory = db.fetchall()
            print(pickle.loads(appointmentHistory[0]['selected_services_prices']))
            # name = appointmentHistory[name]
            petName = appointmentHistory[0]['petName']
            petType = appointmentHistory[0]['petType']
            date = appointmentHistory[0]['date']
            selected_services = pickle.loads(appointmentHistory[0]['selected_services'])
            selected_services_prices = pickle.loads(appointmentHistory[0]['selected_services_prices'])
            totalPrice = appointmentHistory[0]['totalPrice']
            discount = appointmentHistory[0]['discount']
            finalPrice = appointmentHistory[0]['finalPrice']
            
        # Flash 0
        flash(username)
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

        # Create appointment object
        for i in range(len(selected_services)):
            appointment_obj = user_obj.book_appointment(date, petName, petType, selected_services[i], spa_system)
            db.execute('''
                        INSERT INTO appointments(username, appointment_object)
                        VALUES (?, ?)
                       ''', (username, pickle.dumps(appointment_obj)))
            con.commit()
        user_obj.spending = finalPrice
        user_obj.update_membership(spa_system)

        # unserialized_user.book_appointment(date, petName, petType, selected_services, spa_system)
        return render_template("appointment_confirmed.html")

# route for appointment
@app.route('/appointment')
def appointment():
    db.execute('SELECT * FROM testing WHERE id=?', [session['user_id']])
    user = db.fetchall()
    username = pickle.loads(user[0]['user_object']).name
    flash(username)
    return render_template('appointment.html')

# route for customer membership
@app.route('/membership')
def membership():
    db.execute('SELECT * FROM testing WHERE id=?', [session['user_id']])
    user = db.fetchall()
    username = pickle.loads(user[0]['user_object']).name
    membership_type = pickle.loads(user[0]['user_object']).membership

    unserialized_user = pickle.loads(user[0]['user_object'])

    membership_type = unserialized_user.membership
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
    flash(username)
    flash(membership_type)
    flash(new_discount)
    flash(newMinimumSpending)
    flash(regular_discount)
    flash(regularMinimumSpending)
    flash(premium_discount)
    flash(premiumMinimumSpending)
    return render_template('user_membership.html')

# Route for staff dashboard
@app.route('/staffDashboard')
def staffDashboard():   
    db.execute('SELECT * FROM testing WHERE id=?', [session['user_id']])
    user = db.fetchall()
    flash(pickle.loads(user[0]['user_object']).name)
    return render_template('staff_dashboard.html')

# Route for searching pet by Customer username
@app.route('/petSearch', methods=['GET','POST'])
def petSearch():
    if request.method == "POST":
        db.execute('SELECT * FROM testing WHERE id=?', (session['user_id'],))
        user = db.fetchall()
        flash((pickle.loads(user[0]['user_object']).name))
        usernameForPetSearch =  request.form.get("usernameForPetSearch")

        user_obj = pickle.loads(user[0]['user_object'])
        # For searching pet by customer name
        nameAndTypeList = []
        nameAndTypeList = user_obj.search_pet_by_customer_name(usernameForPetSearch, spa_system)
        flash(nameAndTypeList)

        # Appointments
        db.execute('SELECT * FROM appointments WHERE username=?', (usernameForPetSearch,))
        appointments = db.fetchall()
        # print(appointments[0]["appointment_object"])
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
        db.execute('SELECT * FROM testing WHERE id=?', [session['user_id']])
        user = db.fetchall()
        user_type = user[0]['type']
        if user_type == "Owner":
            pass
        elif user_type == "Admin":
            pass
        elif user_type == "Staff":
            return redirect('/staffDashboard')
        elif user_type == "Customer":
            return redirect('/userMain')

# Route for creating staffs
@app.route('/createStaff')
def createStaff():
    tony = Staff("tony", "Tony", generate_password_hash("tony", method='pbkdf2:sha256', salt_length=8))
    romulus = Staff("romulus", "Romulus", generate_password_hash("romulus", method='pbkdf2:sha256', salt_length=8))
    yu = Staff("yu", "Yu Yu", generate_password_hash("yu", method='pbkdf2:sha256', salt_length=8))
    db.execute('''
                INSERT INTO staffs (username, staff_object)
                VALUES (?, ?)''', 
                ("tony", pickle.dumps(tony)))
    con.commit()
    db.execute('''
                INSERT INTO staffs (username, staff_object)
                VALUES (?, ?)''', 
                ("romulus", pickle.dumps(romulus)))
    con.commit()
    db.execute('''
                INSERT INTO staffs (username, staff_object)
                VALUES (?, ?)''', 
                ("yu", pickle.dumps(yu)))
    con.commit()
    # flash(name, petName, petType, date, se
    return redirect('/')

# Temporary route
@app.route('/temp')
def temp():
    db.execute('SELECT * FROM staffs WHERE username=?', ('tony',))
    user = db.fetchall()
    tony_obj = user[0]['staff_object']
    print((pickle.loads(tony_obj).username))
    tony = pickle.loads(tony_obj)
    db.execute('''
                INSERT INTO testing (type, username, user_object)
                VALUES (?,?,?)
            ''', ("Staff", tony.username, tony_obj))
    con.commit()
    return redirect('/')

# Route for deleting appointment
@app.route('/deleteAppointment', methods = ['GET', 'POST'])
def deleteAppointment():
    if request.method == "POST":
        appointmentIds = request.form.getlist('appointment_checkboxes')
        for appointmentId in appointmentIds:
            db.execute('DELETE FROM appointments WHERE id=?', (appointmentId,))
            con.commit()
        return redirect('/staffDashboard')
 
if __name__ == '__main__':
    app.run(debug=True)