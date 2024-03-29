import math
from flask import Flask, render_template,request,session,redirect
from flask_sqlalchemy import SQLAlchemy
import os
from datetime import datetime
import json
from flask_mail import Mail
from werkzeug.utils import secure_filename
import pandas as pd
import matplotlib.pyplot as plt
import time


with open("config.json") as c:
    params = json.load(c)["params"]

local_server = True
app = Flask(__name__)
app.secret_key = 'super-secret-key'
app.config['UPLOAD_FOLDER'] = params['upload_location']

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
    tagline = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(12), nullable=True)
    slug = db.Column(db.String(21), nullable=False)
    img_file = db.Column(db.String(21), nullable=False)
    url = db.Column(db.String(60),nullable=True)

@app.route("/")
def home():
    posts = Posts.query.filter_by().all()
    #[1:params['no_of_posts']]
    last = math.ceil(len(posts)/int(params['no_of_posts']))
    page = request.args.get('page')
    if(not str(page).isnumeric()):
        page= last
    page = int(page)
    posts = posts[(page-1)*int(params['no_of_posts']) : (page-1)*int(params['no_of_posts']) + int(params['no_of_posts'])]
    #Pagination
    if(page == 1):
        prev = "#"
        next = "/?page="+str(page+1)
    elif(page == last):
        next = "#"
        prev = "/?page=" + str(page - 1)
    else:
        next = "/?page=" + str(page + 1)
        prev = "/?page=" + str(page - 1)



    return render_template('index.html',params=params,postr=posts,prev=prev,next=next)


@app.route("/dashboard", methods=['GET','POST'])
def log_in():
    if ('user' in session and session['user'] == params['admin_user']):
        posts = Posts.query.all()
        return render_template('dashboard.html', params=params,posts=posts)
    if request.method =='POST':
        passs  = request.form.get('password')
        uname = request.form.get('username')
        if (uname == params['admin_user'] and passs == params['admin_pass']) :
            session['user'] = uname
            posts = Posts.query.all()
            return render_template('dashboard.html', params=params,posts=posts)
        else:
            return render_template('login.html', params=params)


        # Redirect to admin
    return render_template('login.html',params=params)
@app.route("/logout")
def logout():
    session.pop('user')
    return redirect('/dashboard')

@app.route("/delete/<int:sno>")
def delete(sno):
    if ('user' in session and session['user'] == params['admin_user']):
        del_post= Posts.query.filter_by(sno=sno).first()
        db.session.delete(del_post)
        db.session.commit()
        return redirect("/dashboard")


@app.route("/uploader", methods = ["GET","POST"])
def uploader():
    if ('user' in session and session['user'] ==params['admin_user']):
        if (request.method == "POST"):
            f = request.files['file1']
            f.save(os.path.join(app.config['UPLOAD_FOLDER'],secure_filename(f.filename)))
            return "UPLOADED SUCCESSFULLY"


@app.route("/edit/<string:sno>", methods = ["GET","POST"])
def edit_po(sno):
    if ('user' in session and session['user'] == params['admin_user']):
        if request.method == "POST":
            box_title = request.form.get('title')
            tline= request.form.get('tline')
            slug= request.form.get('slug')
            content = request.form.get('content')
            img_file =  request.form.get('img_file')
            url = request.form.get('url')
            date = datetime.now()

            if sno == '0':
                post = Posts(title = box_title, slug=slug,content=content,img_file=img_file,tagline=tline,date=date,url=url)
                db.session.add(post)
                db.session.commit()
            else:
                post = Posts.query.filter_by(sno = sno).first()
                post.title = box_title
                post.slug = slug
                post.tagline = tline
                post.content = content
                post.img_file = img_file
                post.date = date
                post.url=url
                db.session.commit()
                return redirect('/edit/'+sno)
        post = Posts.query.filter_by(sno = sno).first()
        return render_template('edit.html',params=params,post=post,sno=sno)

@app.route("/about")
def neo():
    return render_template('about.html',params=params)
@app.route("/post")
def posts():
    return render_template('spost.html',params=params)

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

@app.route("/niswas", methods = ['GET','POST'])
def plotattr():
    if request.method =="POST" :
        url = request.form.get("urlforcsv")
        columnno = request.form.get("col1")
        cl = int(columnno)
        global df
        df = pd.read_csv(url)
        plt.cla() # Clear axis
        plt.clf() # Clear figure
        plt.close()  # Close a figure window
        plt.plot(df.iloc[:, cl])
        plt.savefig("D:\\neonature\\neonature\\static\\img\\plot1.png",transpharent =False)
        global colnames
        colnames = "img/plot1.png"
        Message = "The data is {}".format(df.columns[cl])
    else :
        colnames = "img/neo-py.jpg"
        Message = "Sorry"
    return render_template('plots.html', params=params, col=colnames, msg=Message)
app.run(debug = True)


