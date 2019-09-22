from flask import Flask, render_template,request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json
from flask_mail import Mail


with open("config.json") as c:
    params = json.load(c)["params"]

local_server = True
app = Flask(__name__)
app.config.update(
    MAIL_SERVER = 'smtp.gmail.com',
    MAIL_PORT = '465',
    MAIL_USE_SSL = True,
    MAIL_USERNAME = params['gmail_user'],
    MAIL_PASSWORD = params['gmail_pass']
)
mail = Mail(app)
if (local_server):
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_uri']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['prod_uri']

# 'mysql://username:password@localhost/db_name'
db = SQLAlchemy(app)

class Contacts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80),nullable=False)
    phone_num = db.Column(db.String(12),nullable=False)
    mes = db.Column(db.String(120),nullable=False)
    date = db.Column(db.String(12),nullable=True)
    email = db.Column(db.String(20),nullable=False)

class Posts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    content = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(12), nullable=True)
    slug = db.Column(db.String(21), nullable=False)
    img_file = db.Column(db.String(21), nullable=False)

@app.route("/")
def home():
    return render_template('index.html',params=params)
@app.route("/index")
def home2():
    return render_template('index.html',params=params)
@app.route("/about")
def neo():
    return render_template('about.html',params=params)
@app.route("/post")
def posts():
    return render_template('post.html',params=params)

@app.route("/post/<string:post_slug>", methods = ['GET'])
def post_route(post_slug):
    post = Posts.query.filter_by(slug=post_slug).first()
    return render_template('post.html',params=params, post=post )

@app.route("/contact", methods = ['GET','POST'])
def contact():
    if(request.method == 'POST'):
        '''Add entry to the data base'''
        name = request.form.get('name')
        email= request.form.get('email')
        phone= request.form.get('phone')
        message= request.form.get('message')
        entry = Contacts(name =name, phone_num = phone, mes = message, email=email ,date=datetime.now() )       #LHS = Database name and RHS = request.get name
        db.session.add(entry)
        db.session.commit()
        mail.send_message("New Message From Blog" + name,
                  sender = email,
                  recipients=[params['gmail_user']],
                  body=message + "\n" + phone
                  )
    return render_template('contact.html',params=params)


app.run(debug = True)


