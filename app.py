from flask import Flask, render_template,url_for,flash,redirect, session,logging, request
from data import Link
from flask_mysqldb import MySQL
from wtforms import Form, StringField, PasswordField, validators
from flask_wtf.file import FileField, FileAllowed, FileRequired
from werkzeug.datastructures import CombinedMultiDict
from werkzeug.utils import secure_filename
from passlib.hash import sha256_crypt 
from functools import wraps
import boto3, botocore
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders


app = Flask(__name__)
app.config.from_pyfile('config.py')

# Initialize MySQL
mysql = MySQL(app)

# Config S3

s3 = boto3.client(
   "s3",
   aws_access_key_id=app.config['S3_KEY'],
   aws_secret_access_key=app.config['S3_SECRET']
)

# mail = Mail(app)


Link = Link()

# Check if user is logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return redirect(url_for('index'))
        else:
             return f(*args, **kwargs)
    return wrap

class UploadForm(Form):
        # a file and array of emails
        shared_file = FileField('File',validators=[FileAllowed(['pdf','doc','docx','ppt','pptx','xls','xlsx','txt','zip','rar'])], render_kw={"placeholder": "Select a file"})
        shared_with = StringField('Emails',[validators.Length(min=4, max=300), validators.DataRequired()], render_kw={"placeholder": "Enter emails separated by commas"})

def upload_file_to_s3(file, bucket_name):
    try:
        s3.upload_fileobj(
            file,
            bucket_name,
            file.filename,
        )
    except Exception as e:
        print("Something Happened: ", e)
        return e
    key = file.filename    
    location = app.config["S3_LOCATION"]
    url = "https://%s.s3.amazonaws.com/%s" % (bucket_name, key)
    return url

def send_email(email, link):
    fromaddr = "arnoldwamae2@gmail.com"
    toaddr = email
    msg = MIMEMultipart()
    msg['From'] = fromaddr
    msg['To'] = toaddr
    msg['Subject'] = "File Share"
    body = "You have been shared a file with you. Click the link below to download the file: " + link
    msg.attach(MIMEText(body, 'plain'))
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(user,password)


@app.route('/', methods=['GET', 'POST'])
def index():
    # if logged in, create a form with file upload
    if 'logged_in' in session:
        form = UploadForm(CombinedMultiDict((request.files, request.form)))
        if request.method == 'POST' and form.validate():
            # get data from the form
            file = form.shared_file.data
            if file.filename == "":
                flash('Please select a file', 'danger')
                return render_template('home.html', link=Link, form=form)
            emails = form.shared_with.data.split(',')
            # if more than 5 emails, return error
            if len(emails) > 5:
                flash('Please enter less than 5 emails', 'danger')
                return render_template('home.html', link=Link, form=form)
            if len(emails) < 0:
                flash('Please Provide Emails', 'danger')
                return render_template('home.html', link=Link, form=form)
            if file:
                file.filename = secure_filename(file.filename)
                # Upload File To S3
                output = upload_file_to_s3(file, app.config["S3_BUCKET"])
                # Get the emails from the form
               
                # Loop through the emails and add them to the database
                # for email in emails:
                    #send and email to each email
                    #send_email(email, file.filename, output)
                    # log the email
                cur = mysql.connection.cursor()
                # insert the data into the database
                cur.execute("INSERT INTO links(link,emails,user_id) VALUES(%s,%s,%s)",(str(output),'test@test.com',session['user_id']))
                mysql.connection.commit()
                cur.close()

                # Send emails to the provided emails

                flash('Link created successfully', 'success')
                return redirect(url_for('index'))
        return render_template('home.html', link=Link, form=form)
    return render_template('home.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Session Ended', 'info')
    return redirect(url_for('login'))

class LoginForm(Form):
    username = StringField('Username', [validators.Length(min=4, max=25), validators.DataRequired()], render_kw={"placeholder": "Username"})
    password = PasswordField('Password', [validators.DataRequired(), validators.Length(min=6, max=25)], render_kw={"placeholder": "Password"})


@app.route('/login', methods=['GET', 'POST'])
@is_logged_in
def login():
    form = LoginForm(request.form)
    if request.method == 'POST' and form.validate():  
        # Get Form Fields
        username = request.form['username']
        password_candidate = request.form['password']

        # Create cursor
        cur = mysql.connection.cursor()

        # Get user by username
        result = cur.execute("SELECT * FROM users WHERE username = %s", [username])

        if result > 0:
            # Get stored hash
            data = cur.fetchone()
            password = data['password']


            # Compare Passwords
            if sha256_crypt.verify(password_candidate, password):
                # Passed
                session['logged_in'] = True
                session['username'] = username
                session['user_id'] = data['id']

                flash('You are now logged in', 'success')
                return redirect(url_for('index'))
            else:
                error = 'Invalid login'
                flash(error, 'danger')
                return render_template('login.html', form=form)
            # Close connection
            cur.close()
        else:
            error = 'Username not found'
            flash(error, 'danger')
            return render_template('login.html', form=form) 
    return render_template('login.html', form=form)



class RegisterForm(Form):
    email = StringField('Email', [validators.Length(min=6, max=50), validators.DataRequired()], render_kw={"placeholder": "Email"})
    username = StringField('Username', [validators.Length(min=4, max=25), validators.DataRequired()], render_kw={"placeholder": "Username"})
    name = StringField('Name', [validators.Length(min=4, max=25), validators.DataRequired()], render_kw={"placeholder": "Name"})
    password = PasswordField('Password', [validators.EqualTo('confirm', message='Passwords do not match'), validators.DataRequired(), validators.Length(min=6, max=25)], render_kw={"placeholder": "Password"})
    confirm = PasswordField('Confirm Password', [validators.DataRequired()], render_kw={"placeholder": "Confirm Password"})

@app.route('/register', methods=['GET', 'POST']) 
@is_logged_in
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        email = form.email.data
        username = form.username.data
        name = form.name.data
        password = sha256_crypt.encrypt(str(form.password.data))

        # Create cursor
        cur = mysql.connection.cursor()

        # Execute query
        cur.execute("INSERT INTO users(email, username, name, password) VALUES(%s, %s, %s, %s)", (email, username, name, password))

        # Commit to DB
        mysql.connection.commit()

        # Close connection
        cur.close()

        flash('You are now registered and can log in', 'success')

        return redirect(url_for('login'))
    return render_template('register.html', form=form)

if __name__ == '__main__':
    app.run()