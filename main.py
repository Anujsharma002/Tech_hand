import math
import smtplib

from flask import Flask,render_template ,request,session,redirect,flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from sqlalchemy.sql import text
import os
from flask_mail import Mail,Message
from datetime import datetime
import json
app = Flask(__name__)
app.secret_key = 'super-secret-key'
with open('config.json','r') as c:
       params = json.load(c) ["params"]
local_server=True
app.config.update(
  MAIL_SERVER = 'smtp.gmail.com',
  MAIL_PORT = 465,
  MAIL_USERNAME = params['mail_username'],
  MAIL_PASSWORD = params['mail_password'],
  MAIL_USE_TLS=False,
  MAIL_USE_SSL = True)
mail = Mail(app)
app.config['UPLOAD_FILE'] = params['upload_location']
if local_server:
    app.config["SQLALCHEMY_DATABASE_URI"] =  params["local_uri"]
else:
    app.config["SQLALCHEMY_DATABASE_URI"] = params["prod_uri"]
db = SQLAlchemy(app)
class Contacts(db.Model):
    '''sno name phone_num msg date email'''
    __tablename__ = 'contacts'
    sno = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(80),nullable=False)
    phone_num = db.Column(db.String(12),nullable=False)
    msg = db.Column(db.String(120),nullable=False)
    date = db.Column(db.String(12),nullable=True)
    email = db.Column(db.String(20),nullable=False)

class Posts(db.Model):
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.String(100), nullable=False)
    img_file = db.Column(db.String(25), nullable=True)
    date = db.Column(db.String(12), nullable=True)
    slug = db.Column(db.String(100), nullable=False)
    tag = db.Column(db.String(100), nullable=False)


@app.route('/')
@app.route('/post/index')
@app.route('/index')
def index():
    posts = Posts.query.filter_by().all()
    # [0:params['No_blog']]
    last = math.ceil(len(posts)/int(params['No_blog']))
    page = request.args.get('page')
    if(not str(page).isnumeric()):
        page=1
    page = int(page)
    posts = posts[(page-1)*int(params['No_blog']):(page-1)*int(params['No_blog'])+int(params['No_blog'])]
    if(page == 1):
        prev = '#'
        next = '/?page='+str(page+1)
    elif page == last:
        prev = '/?page='+str(page-1)
        next = '#'
    else:
        prev = '/?page='+str(page-1)
        next = '/?page='+str(page+1)
    return render_template('index.html',params = params,posts = posts,prev = prev,next = next)

@app.route('/logout')
def logout():
    session.pop('user',None)
    session.clear()
    session.modified = True
    return redirect('/dashboard')

@app.after_request
def add_header(response):
    response.cache_control.no_store = True
    return response

@app.route('/delete/<string:id>',methods = ['GET','POST'])
def delete(id):
    if 'user' in session and session['user'] == params['admin_user']:
        post = Posts.query.filter_by(id = id).first()
        db.session.delete(post)
        db.session.commit()

    return redirect('/dashboard')

@app.route('/uploader',methods = ['GET','POST'])
def uploader():
    if 'user' in session and session['user'] == params['admin_user']:
        if request.method == 'POST':
            f = request.files['file1']
            f.save(os.path.join(app.config['UPLOAD_FILE'],secure_filename(f.filename)))
            return redirect('/dashboard')

@app.route('/post/dashboard')
@app.route('/dashboard',methods = ['GET','POST'])
def dashboard():
    posts = Posts.query.filter_by().all()
    if 'user' in session and session['user'] == params['admin_user']:
        posts = Posts.query.filter_by().all()
        return render_template('dashboard.html',params= params,posts=posts)
    if request.method == 'POST':
      user_name = request.form.get('Email')
      password = request.form.get('Password')
      print(user_name,password)
      if(user_name == params['admin_user'] and password == params['admin_password']):
            session['user'] = user_name
            posts = Posts.query.filter_by().all()
            return render_template('dashboard.html',params = params,posts = posts)

    return render_template('admin.html',params = params)

@app.route("/post/<post_slug>", methods=['GET'])
def post_route(post_slug):
    posts = Posts.query.filter_by(slug = post_slug).first_or_404()
    if not posts:
        return "not any data in posts"
    return render_template('post.html', params=params, posts = posts)
@app.route('/post/about')
@app.route('/about')
def about():
    return render_template('about.html',params = params)

@app.route('/edit/<string:id>',methods = ['GET','POST'])
def edit(id):
    if "user" in session and session['user'] == params['admin_user']:
        if request.method == "POST":
            box_title = request.form.get('title')
            tline = request.form.get('tag')
            slug = request.form.get('slug')
            content = request.form.get('content')
            img_file = request.form.get('img_file')
            date = datetime.now()

            if id == '0':
               post = Posts(title=box_title, slug=slug, content=content, tag=tline, img_file=img_file, date=date)
               db.session.add(post)
               db.session.commit()
            else:
                post = Posts.query.filter_by(id = id).first()
                post.title = box_title
                post.tag = tline
                post.slug = slug
                post.content = content
                post.img_file = img_file
                post.date = date
                db.session.commit()
                return redirect('/edit/'+id)
        post = Posts.query.filter_by(id=id).first()
        return render_template('edit.html',params = params,post = post,id = id)

@app.route('/post/contact')
@app.route('/contact',methods =['GET','POST'])
def contact():
    if(request.method == 'POST'):
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')
        phone = request.form.get('phone')
        entry = Contacts(name=name,phone_num=phone,msg=message,date = datetime.now(),email=email)
        db.session.add(entry)
        db.session.commit()

        server = smtplib.SMTP("smtp.gmail.com",587)
        server.starttls()
        server.login(params['mail_username'],params['mail_password'])
        msg = Message(subject=f"query from {name} by {email}",sender = params['mail_username'],recipients=[params['mail_username']])
        msg.body = message
        mail.send(msg)
        flash("sucessfully send","success")

    return render_template('contact.html',params = params)

@app.route('/edit/post')
@app.route('/post/post')
@app.route('/post/')
@app.route('/post')
def post():
    # slug = ''
    posts = Posts.query.first_or_404()
    return render_template('post.html',params = params,posts = posts)


app.run(debug=True)