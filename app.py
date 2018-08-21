from flask import Flask, render_template, flash, redirect, request,url_for, session, logging 
#from data import Errors 
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps

app = Flask(__name__)

#Config MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'ellie'
app.config['MYSQL_DB'] = 'FlaskApp'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

#Initialize MySQL
mysql = MySQL(app)

#Errors = Errors()

@app.route('/')
def index():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/errors')
def errors():
    #Create cursor
    cur = mysql.connection.cursor()

    #Get errors
    result = cur.execute("SELECT * FROM errors")

    errors = cur.fetchall()

    if result>0:
        return render_template('errors.html', errors=errors)
    else:
        msg = 'No reported errors found'
        return render_template('errors.html',msg=msg)

    # Close connection
    cur.close()
    

@app.route('/error/<string:id>/')
def error(id):
    #Create cursor
    cur = mysql.connection.cursor()

    #Get errors
    result = cur.execute("SELECT * FROM errors WHERE id =%s", [id])

    error1 = cur.fetchone()


    return render_template('error.html',error1=error1)

class RegisterForm(Form):
    name = StringField('Employee Name', [validators.Length(min=1,max=50)])
    username = StringField('Username',[validators.Length(min=4,max=25)])
    email = StringField('Email',[validators.Length(min=6,max=50)])
    password = PasswordField('Password',[
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords do not match')
    ])
    confirm = PasswordField('Cofirm Password')

@app.route('/register', methods=['GET','POST'])
def register():

    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))

        #Create cursor
        cur = mysql.connection.cursor()

        cur.execute("INSERT INTO users(name, email, username, password) VALUES(%s, %s, %s, %s)",(name, email, username, password))

        #Commit to DB
        mysql.connection.commit()

        #Close Connection
        cur.close()

        flash('You are now registered and can log in', 'success')

        return redirect(url_for('login'))

    return render_template('register.html', form=form)

#User Login
@app.route('/login',methods=['GET','POST'])
def login():
    if request.method == 'POST':
        #Get Form Fields
        username = request.form['username']
        password_candidate = request.form['password']

#Dashboard
        #Create a cursor
        cur = mysql.connection.cursor()
        #Get user by username
        result = cur.execute("SELECT * FROM users WHERE username = %s",[username])

        if result > 0:
            #Get stored hash
            data = cur.fetchone()
            password = data['password']

            #Compare passwords
            if sha256_crypt.verify(password_candidate,password):
               #PASSED
               session['logged_in'] = True
               session['username'] = username

               flash('You are now logged in', 'success')
               return redirect(url_for('dashboard'))


            else:
                error = 'Invalid Login'
                return render_template('login.html',error=error)
            #Close connection

            cur.close()
        else:
            error = 'Username not found'
            return render_template('login.html',error=error)


    return render_template('login.html')

#Check if user logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized. Please Login!','danger')
            return redirect(url_for('login'))
    return wrap 

#LOGOUT
@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash('You are now logged out','success')
    return redirect(url_for('login'))

#Dashboard
@app.route('/dashboard')
@is_logged_in
def dashboard():
    #Create cursor
    cur = mysql.connection.cursor()

    #Get errors
    result = cur.execute("SELECT * FROM errors WHERE author = %s",[session['username']] )

    errors = cur.fetchall()

    if result>0:
        return render_template('dashboard.html', errors=errors)
    else:
        msg = 'No reported errors found'
        return render_template('dashboard.html',msg=msg)

    # Close connection
    cur.close()


#Error Form Class
class ErrorForm(Form):
    title = StringField('Error Title', [validators.Length(min=1,max=200)])
    body = StringField('Description',[validators.Length(min=30)])

#Add Error
@app.route('/report_error', methods=['GET','POST'])
@is_logged_in
def report_error():
    form = ErrorForm(request.form)
    if request.method == 'POST' and form.validate():
        title = form.title.data
        body = form.body.data

        #Create cursor
        cur = mysql.connection.cursor()

        #Execute
        cur.execute("INSERT INTO errors(title, body,author) VALUES(%s, %s, %s)",(title, body, session['username']))
   
        #Commit to DB
        mysql.connection.commit()

        #Close connection
        cur.close()

        flash('Error reported', 'success')

        return redirect(url_for('dashboard'))

        #Dashboard
    return render_template('report_error.html',form =form)
   
@app.route('/edit_error/<string:id>', methods=['GET','POST'])
@is_logged_in
def edit_error(id):
    #Create cursor
    cur = mysql.connection.cursor()

    #Get article by id
    result = cur.execute("SELECT * FROM errors WHERE id =%s",[id])

    error = cur.fetchone()

    #Get form
    form = ErrorForm(request.form)

    #populate article form fields
    form.title.data = error['title']
    form.body.data = error['body']

    if request.method == 'POST' and form.validate():
        title = request.form['title']
        body = request.form['body']

        #Create cursor
        cur = mysql.connection.cursor()

        #Execute
        cur.execute("UPDATE errors SET title=%s, body=%s WHERE id=%s",(title,body,id))
        #Commit to DB
        mysql.connection.commit()

        #Close connection
        cur.close()

        flash('Error Updated', 'success')

        return redirect(url_for('dashboard'))

        
    return render_template('edit_error.html',form =form)

@app.route('/delete_error/<string:id>',methods=['POST'])
@is_logged_in
def delete_error(id):

    #Create cursor
    cur = mysql.connection.cursor()

    #Execute
    cur.execute("DELETE FROM errors WHERE id =%s",[id])

    #Commit to DB
    mysql.connection.commit()

    #Close connection
    cur.close()

    flash('Error Deleted', 'success')

    return redirect(url_for('dashboard'))


  
if __name__ == '__main__':
    app.secret_key='secret456'
    app.run(debug=True)
