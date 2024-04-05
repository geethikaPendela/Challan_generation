import os
from pymongo import MongoClient
import datetime
from flask import Flask, render_template, request
from flask_mail import Mail, Message
from deeplearning import object_detection
from flask import redirect, url_for
import threading
from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
mail = Mail(app)
app.secret_key = 'your_secret_key_here'
# MongoDB configuration
client = MongoClient('mongodb://localhost:27017/')
db = client['Details']
collection = db['data']

# Flask-Mail configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'khsyooooo@gmail.com'  # Replace with your Gmail address
app.config['MAIL_PASSWORD'] = 'pzwclfwjdsvbshzo'  # Replace with your Gmail password

mail.init_app(app)

BASE_PATH = os.getcwd()
UPLOAD_PATH = os.path.join(BASE_PATH, 'static/upload/')

def send_reminder_email(challan_id):
    with app.app_context():
        challan = db['challans'].find_one({'_id': challan_id})
        if challan:
            lc_number = challan['lc_number']
            owner_name = challan['ownername']
            email = challan['email']
            violation = challan['offence']
            datetime_of_offence = challan['datetime_of_offence']

            # Send reminder email to the vehicle owner
            print("Sending reminder email to:", email)
            msg = Message('Reminder: Challan on your vehicle no: ' + lc_number,
                          sender='khsyooooo@gmail.com',
                          recipients=[email])
            msg.body = 'This is a reminder for the challan issued on your vehicle no: ' + lc_number + ' due to ' + violation + \
                       ' on the owner of the vehicle ' + owner_name + ' on ' + str(datetime_of_offence) + \
                       '. Please pay your challan as soon as possible.'
            try:
                mail.send(msg)
                print("Reminder email sent successfully!")
            except Exception as e:
                print("Failed to send reminder email:", str(e))



# Function to schedule reminder emails
def schedule_reminder_email(challan_id):
    # Define the delay in seconds (2 minutes = 120 seconds)
    delay = 120
    timer = threading.Timer(delay, send_reminder_email, args=[challan_id])
    timer.start()
@app.route('/', methods=['GET'])
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        print(username, password)  # Check if the values are received correctly

        # Check if the username and password match
        if username == 'harini' and password == '123@':
            # Store the login status in the session
            session['logged_in'] = True
            print("success")
            # Redirect to the index page or any other protected route
            return redirect(url_for('index'))
        else:
            # Invalid credentials, display error message
            error_message = 'Invalid username or password'
            return render_template('login.html', error_message=error_message)
    
    # If it's a GET request or login attempt failed, render the login page
    return render_template('login.html')

@app.route('/index', methods=['POST', 'GET'])
def index():
    print(session.get('logged_in'))
    if not session.get('logged_in'):
        # If not logged in, redirect to the login page
        return redirect(url_for('login'))
    if request.method == 'POST':
        upload_file = request.files['image_name']
        filename = upload_file.filename
        path_save = os.path.join(UPLOAD_PATH, filename)
        upload_file.save(path_save)

        # Perform object detection on the uploaded image
        text_list = object_detection(path_save, filename)
        print(text_list)
        lc_number = text_list[0]  # Access the first (and only) element of the list
          # Output: CC 161193 
        print(lc_number)
        violation = request.form.get('violation')

        # Retrieve details from MongoDB based on license plate number
        details = collection.find_one({'number_plate': lc_number})
        print(details)
        if details:
            owner_name = details['name']
            email = details['email']
            # Example offense, replace with your logic
            current_time = datetime.datetime.now()

            # Insert challan details into MongoDB
            challan = {
                'lc_number': lc_number,
                'ownername': owner_name,
                'email': email,
                'offence': violation,
                'datetime_of_offence': current_time
            }
            challan_id = db['challans'].insert_one(challan).inserted_id

            # Send email to the vehicle owner
            msg = Message('Challan on your vehicle no: ' + lc_number,
                          sender='khsyooooo@gmail.com',
                          recipients=[email])
            msg.body = 'Challan has been raised on your vehicle no: ' + lc_number + ' due to ' + violation + \
                       ' on the owner of the vehicle ' + owner_name + ' on ' + str(current_time) + \
                       '. Pay your challan before the due date i.e ' + str(current_time + datetime.timedelta(days=15))
            mail.send(msg)

            # Schedule a reminder email after a specific amount of time
            schedule_reminder_email(challan_id)

            return render_template('index.html', upload=True, upload_image=filename, text=text_list,
                                   no=len(text_list))
        else:
            # License plate not found in the database
            return render_template('index.html', upload=True, upload_image=filename, text=text_list,
                                   no=len(text_list), error_message='License plate not found')


    return render_template('index.html', upload=False)


@app.route('/challans_page', methods=['GET', 'POST'])
def challans_page():
    if not session.get('logged_in'):
        # If not logged in, redirect to the login page
        return redirect(url_for('login'))
    if request.method == 'GET':
        # Retrieve challan details from MongoDB
        challans = list(db['challans'].find())
        return render_template('nextpage.html', challans=challans)
    elif request.method == 'POST':
        # Handle the form submission from the next page if needed
        # Add the necessary logic here
        return redirect(url_for('index'))
    # Add a default return statement in case none of the above conditions are met
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    # Clear the session and set 'logged_in' to False
    session.clear()
    session['logged_in'] = False
    return redirect(url_for('login'))


if __name__ == "__main__":
    app.run(debug=True)