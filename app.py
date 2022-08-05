from flask import Flask, render_template, url_for, flash, redirect, session, logging, request
from flask_mysqldb import MySQL
from wtforms import Form, StringField, PasswordField, validators
from flask_wtf.file import FileField, FileAllowed, FileRequired
from werkzeug.datastructures import CombinedMultiDict
from werkzeug.utils import secure_filename
from passlib.hash import sha256_crypt
from functools import wraps
import boto3
import botocore
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
ses = boto3.client(
    'ses',
    aws_access_key_id=app.config['S3_KEY'],
    aws_secret_access_key=app.config['S3_SECRET'],
    region_name=app.config['S3_LOCATION']
)

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
    shared_file = FileField('Select file to upload   :', validators=[FileAllowed(
        ['pdf', 'doc', 'docx', 'ppt', 'pptx', 'xls', 'xlsx', 'txt', 'zip', 'rar', 'png', 'jpg', 'bmp', 'jpeg'])], render_kw={"placeholder": "Select a file"})
    shared_with = StringField('Emails to share file with :', [validators.Length(min=4, max=300), validators.DataRequired(
    )], render_kw={"placeholder": "Enter emails separated by commas"})


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
    # location = app.config["S3_LOCATION"]
    # url =  "https://%s.s3.amazonaws.com/%s" % (bucket_name, key)
    return key


def getTemproraySignedURL(key):
    response = s3.generate_presigned_url(
        ClientMethod='get_object',
        Params={
            'Bucket': app.config['S3_BUCKET'],
            'Key': key
        }
    )
    return response

# Delete file from s3


def delete_file_from_s3(key):
    try:
        s3.delete_object(
            Bucket=app.config['S3_BUCKET'],
            Key=key
        )
    except Exception as e:
        print("Something Happened: ", e)
        return e
    return True


def send_email(email, key, generated_url):
    SUBJECT = 'Shared File Received'
    BODY_HTML = '<p>Click the link below to access file</p> <a href="' + \
        generated_url+'">' + key + '</a>'
    response = ses.send_email(
        Source='director@qtechafrica.com',
        Destination={
            'ToAddresses': [
                email
            ]
        },
        Message={
            'Subject': {
                'Data': 'Link shared with you',
            },
            'Body': {
                'Html': {
                    'Data': BODY_HTML,
                }
            }
        }
    )
    return response


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
                key = upload_file_to_s3(file, app.config["S3_BUCKET"])
                temp_url = getTemproraySignedURL(key)
                userId = session['user_id']
                # Get the emails from the form
                # Loop through the emails and add them to the database

                # send and email to each email
                # send_email(email, file.filename, output)
                # log the email
                cur = mysql.connection.cursor()
                # insert the data into the database
                cur.execute("INSERT INTO links(link, emails, temp_url, user_id) VALUES(%s, %s, %s, %s)",
                            (key, emails, temp_url, userId))

                mysql.connection.commit()
                cur.close()

                # Get id of inserted Link
                cur = mysql.connection.cursor()
                cur.execute("SELECT * FROM links WHERE link = %s", [key])
                link_id = cur.fetchone()['id']
                cur.close()

                for email in emails:
                    # create  file accessor for each email
                    cur = mysql.connection.cursor()
                    cur.execute(
                        "INSERT INTO file_accessors(link_id, email) VALUES(%s, %s)", (link_id, email))
                    mysql.connection.commit()
                    cur.close()
                    # Get Id of inserted Accessor
                    cur = mysql.connection.cursor()
                    cur.execute(
                        "SELECT id FROM file_accessors WHERE link_id = %s AND email = %s", [link_id, email])
                    accessor_id = cur.fetchone()['id']
                    cur.close()

                    # create link using accessor id and link id;
                    generated_url = url_for(
                        'link',  accessor_id=accessor_id, _external=True)
                    send_email(email, key, generated_url)
                # Send emails to the provided emails

                flash('Link created successfully and mails sent', 'success')
                return redirect(url_for('index'))
        else:
            cur = mysql.connection.cursor()
            result = cur.execute(
                "SELECT * FROM links WHERE user_id = %s", [session['user_id']])
            links = cur.fetchall()
            if result > 0:
                return render_template('home.html', links=links, form=form)
            else:
                flash('You are yet to upload your first file', 'warning')
                return render_template('home.html', form=form)
    return render_template('home.html')


@ app.route('/logout')
def logout():
    session.clear()
    flash('Session Ended', 'info')
    return redirect(url_for('login'))


class LoginForm(Form):
    username = StringField('Username', [validators.Length(
        min=4, max=25), validators.DataRequired()], render_kw={"placeholder": "Username"})
    password = PasswordField('Password', [validators.DataRequired(
    ), validators.Length(min=6, max=25)], render_kw={"placeholder": "Password"})


@ app.route('/login', methods=['GET', 'POST'])
@ is_logged_in
def login():
    form = LoginForm(request.form)
    if request.method == 'POST' and form.validate():
        # Get Form Fields
        username = request.form['username']
        password_candidate = request.form['password']

        # Create cursor
        cur = mysql.connection.cursor()

        # Get user by username
        result = cur.execute(
            "SELECT * FROM users WHERE username = %s", [username])

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
    email = StringField('Enter your email address', [validators.Length(
        min=6, max=50), validators.DataRequired()], render_kw={"placeholder": "Email"})
    username = StringField('Choose your username', [validators.Length(
        min=4, max=25), validators.DataRequired()], render_kw={"placeholder": "Username"})
    name = StringField('Provide your full name', [validators.Length(
        min=4, max=25), validators.DataRequired()], render_kw={"placeholder": "Name"})
    password = PasswordField('Password', [validators.EqualTo('confirm', message='Passwords do not match'), validators.DataRequired(
    ), validators.Length(min=6, max=25)], render_kw={"placeholder": "Password"})
    confirm = PasswordField('Confirm Password', [validators.DataRequired()], render_kw={
        "placeholder": "Confirm Password"})


@app.route('/link/<string:accessor_id>/')
def link(accessor_id):
    # Select accessor with that id
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM file_accessors WHERE id = %s", [accessor_id])
    accessor = cur.fetchone()
    cur.close()

    linkId = accessor['link_id']
    # Get Link Key
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM links WHERE id = %s", [linkId])
    link = cur.fetchone()
    cur.close()

    # Generate a temporasy link
    temp_url = getTemproraySignedURL(link['link'])

    # update the accessor to accessed
    cur = mysql.connection.cursor()
    cur.execute(
        "UPDATE file_accessors SET accessed = 1 WHERE id = %s", [accessor_id])
    mysql.connection.commit()
    cur.close()

    # check if all file accessors have accesses link
    cur = mysql.connection.cursor()
    cur.execute(
        "SELECT * FROM file_accessors WHERE link_id = %s AND accessed = 0", [linkId])
    accessors = cur.fetchall()
    cur.close()
    if len(accessors) == 0:
        # Delete the file from S3
        delete_file_from_s3(link['link'])
        # Delete the link from the database
        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM links WHERE id = %s", [linkId])
        mysql.connection.commit()
        cur.close()
        # Delete the accessors from the database
        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM file_accessors WHERE link_id = %s", [linkId])
        mysql.connection.commit()
        cur.close()

    # Redirect to temp url
    return redirect(temp_url)


@ app.route('/register', methods=['GET', 'POST'])
@ is_logged_in
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
        cur.execute("INSERT INTO users(email, username, name, password) VALUES(%s, %s, %s, %s)",
                    (email, username, name, password))

        # Commit to DB
        mysql.connection.commit()

        # Close connection
        cur.close()

        flash('You are now registered and can log in', 'success')

        return redirect(url_for('login'))
    return render_template('register.html', form=form)


if __name__ == '__main__':
    app.run()
