import os
import re
from flask import Flask, render_template, request, redirect, session, flash, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.exceptions import HTTPException
from threading import Thread
from flask_mail import Message
from sqlalchemy.sql import func
import pytz
import PhotoTools
from flask_migrate import Migrate#, MigrateCommand
from itsdangerous import URLSafeSerializer
from flask_mail import Mail
from werkzeug.utils import secure_filename
import qrcode
from sqlalchemy import select, desc
import random
import uuid


#from flask_script import Manager
#from flask_security import Security, SQLAlchemyUserDatastore, \
#    UserMixin, RoleMixin, login_required
# from flask_qrcode import QRcode


basedir = os.path.abspath(os.path.dirname(__file__))

UPLOAD_FOLDER = os.path.join('static', 'uploads')
ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024

app.secret_key = "j*lbw8klndiuAulhjc^2"                            				# Where to store secret keys?
app.config['SQLALCHEMY_DATABASE_URI'] =\
    'sqlite:///' + os.path.join(basedir, 'data.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.permanent_session_lifetime = timedelta(days=5)

app.config['FLASKY_MAIL_SUBJECT_PREFIX'] = '[Flasky]' 
app.config['FLASKY_MAIL_SENDER'] = 'Flasky Admin <bruh@example.com>'
app.config['FLASKY_ADMIN'] = os.environ.get('FLASKY_ADMIN') 

db = SQLAlchemy(app)

s = URLSafeSerializer('KH*tYhdfY9S0&3%0')							# Another key of sorts

migrate = Migrate(app, db)
#manager = Manager(app)
#manager.add_command('db', MigrateCommand)

week = {
    0: 'monday',
    1: 'tuesday',
    2: 'wednesday',
    3: 'thursday',
    4: 'friday',
    5: 'saturday',
    6: 'sunday'
}


app.config.update(dict(
    DEBUG = True,
    MAIL_SERVER = 'smtp.gmail.com',
    MAIL_PORT = 587,
    MAIL_USE_TLS = True,
    MAIL_USE_SSL = False,
    MAIL_USERNAME = 'rectangleinteractive@gmail.com',						# Remove plaintext email and password
    MAIL_PASSWORD = 'Bogus2020',
))

mail = Mail(app)
# QRcode(app)

class Event(db.Model):
    __tablename__ = 'event'
    day_of_the_week = db.Column(db.Integer, primary_key=True, unique=True)
    title = db.Column(db.String(80))
    description = db.Column(db.String(80))
    rules = db.Column(db.String(80))

    def updateEvent(day_of_the_week=None, title=" ", description=" ", rules=" "):
        if day_of_the_week in (0, 1, 2, 3, 4, 5, 6):
            try:
                db.session.delete(Event.query.all()[day_of_the_week])
            except:
                print("bruh")

            new_event = Event(day_of_the_week = day_of_the_week, title=title, description=description, rules=rules)
            db.session.add(new_event)
            db.session.commit()
            print("done")

    

# Base posts and comments
post_like_association_table = db.Table('association', db.Model.metadata,
    db.Column('users_id', db.Integer, db.ForeignKey('users.id')),
    db.Column('posts_id', db.Integer, db.ForeignKey('posts.id'))
)

comment_like_association_table = db.Table('association1', db.Model.metadata,
    db.Column('users_id', db.Integer, db.ForeignKey('users.id')),
    db.Column('comments_id', db.Integer, db.ForeignKey('comments.id'))
)

comment_tree = db.Table(
    'comment_tree',
    db.Column('parent_id', db.Integer, db.ForeignKey('comments.id')),
    db.Column('children_id', db.Integer, db.ForeignKey('comments.id'))
)

# Event posts and comments
event_post_like_association_table = db.Table('event_association', db.Model.metadata,
    db.Column('users_id', db.Integer, db.ForeignKey('users.id')),
    db.Column('event_posts_id', db.Integer, db.ForeignKey('event_posts.id'))
)

event_comment_like_association_table = db.Table('event_association1', db.Model.metadata,
    db.Column('users_id', db.Integer, db.ForeignKey('users.id')),
    db.Column('event_comments_id', db.Integer, db.ForeignKey('event_comments.id'))
)

event_comment_tree = db.Table('event_comment_tree',
    db.Column('event_parent_id', db.Integer, db.ForeignKey('event_comments.id')),
    db.Column('event_children_id', db.Integer, db.ForeignKey('event_comments.id'))
)

user_following = db.Table(
    'user_following',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('following_id', db.Integer, db.ForeignKey('users.id'), primary_key=True)
)

def divide_chunks(l, n): 
    for i in range(0, len(l), n):  
        yield l[i:i + n] 

def send_async_email(app, msg):    
    with app.app_context():        
        mail.send(msg)

def send_email(to, subject, template, **kwargs):    
    msg = Message(app.config['FLASKY_MAIL_SUBJECT_PREFIX'] + subject,                  
    sender=app.config['FLASKY_MAIL_SENDER'], recipients=[to])    
    msg.body = "you forgot your password lol" #render_template(template + '.txt', **kwargs)    
    msg.html = "bruh" #render_template(template + '.html', **kwargs)    
    thr = Thread(target=send_async_email, args=[app, msg])    
    thr.start()    
    return thr


def login_check():
    if 'user' in session:
        user = User.query.filter_by(name=session['user']).all()
        if not user:
            return False
        else:
            return True
    else:
        return False


class Timer:
    def __init__(self):
        self.last_time = datetime.now().day
    def daily_reset(self):
        current_day = datetime.now().day
        if self.last_time != current_day:
            quer1 = Post.query.all()
            quer2 = Comment.query.all()
            for i in quer1:
                db.session.delete(i)
            for j in quer2:
                db.session.delete(j)  
            db.session.commit()
            self.last_time = current_day
    
'''
class Redirector: # scope 2 is direct to the child of something
    def scope1(self, media_type):
        # This is where we deal with feed posts and event posts
        if media_type == "post":
            link = "/feed"
        
        elif media_type == "event_post":
            link = "/events"        
    
        return(link)

    def scope2(self, origin_id, origin, media_type, parent, id):
        ## If the post acted on is the one in scope 
        pass
'''

class Feedback(db.Model):
    __tablename__ = 'feedback'
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    user = db.relationship("User", back_populates="feedbacks")


user_title_association_table = db.Table('user_title_association', db.Model.metadata,
    db.Column('users_id', db.Integer, db.ForeignKey('users.id')),
    db.Column('titles_id', db.Integer, db.ForeignKey('titles.id'))
)

class Title(db.Model):
    __tablename__ = 'titles'
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String)
    cost = db.Column(db.Integer)
    users = db.relationship("User", secondary=user_title_association_table)
    selected = db.Column(db.Integer, default=0)
    default =  db.Column(db.Integer)

    def __init__(self, text, cost, default):
        self.default = default
        self.text = text
        self.cost = cost

    @staticmethod
    def generateDailyTitles():
        titles = Title.query.all()
        titles1 = Title.query.filter_by(cost=25).all()
        titles2 = Title.query.filter_by(cost=50).all()
        titles3 = Title.query.filter_by(cost=100).all()
        print('TITLES 1:')
        for p in titles1:
            print(p.cost)

        print('TITLES 2:')
        for m in titles2:
            print(m.cost)

        print('TITLES 3:')
        for t in titles3:
            print(t.cost)
        
        for each in titles:
            each.selected = 0
        db.session.commit()
        one = 0 
        two = 0
        three = 0
        random.seed(datetime.now().day)
        one = random.randint(0, len(titles1)-1)
        two = random.randint(0, len(titles2)-1)
        three = random.randint(0, len(titles3)-1)
        titles1[one].selected = 1
        titles2[two].selected = 1
        titles3[three].selected = 1
        db.session.commit()
    


class Report(db.Model):
    __tablename__ = 'reports'
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String)
    time_created = db.Column(db.DateTime(timezone=True))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    user = db.relationship("User", back_populates="rports")

    def __init__(self, text):
        self.time_created = datetime.now()
        self.text = text



class Newsletter(db.Model):
    __tablename__ = 'newsletters'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String)
    text = db.Column(db.String(80))

    def __init__(self, text):
        self.text = text
        self.date = get_date_time()


# Types of notifications
# Liked post
# Liked event_post
# Liked comment
# liked event_comment


# What notifications should contain
# Redirect location
# User who it's for

class Notification(db.Model):
    __tablename__ = 'notifications'
    id = db.Column(db.Integer, primary_key=True)
    link = db.Column(db.String)
    message = db.Column(db.String(80))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    user = db.relationship("User", back_populates="notifications")
    time_created = db.Column(db.DateTime(timezone=True)) 
    def __init__(self, user_from, user, ttype, obj):
        if ttype == 'post_like':
            text = ' liked your post'
            link = ('/comments/feed/post/{0}/Top').format(obj.id)

        elif ttype == 'event_post_like':
            text = ' liked your event submission'
            link = '/event_comments/events/event_post/{0}/Top'.format(obj.id)

        elif ttype == 'comment_like':
            text = ' liked your comment'
            link = ('/comments/None/comment/{0}/Top').format(obj.id)

        elif ttype == 'post_comment':
            text = ' commented on your post'
            link = ('/comments/feed/post/{0}').format(obj.id)

        elif ttype == 'event_post_comment':
            text = ' commented on your event submission'
            link = '/event_comments/None/event_comment/{0}/Top'.format(obj.id)

        elif ttype == 'event_comment_like':
            text = ' liked your event comment'
            link = '/event_comments/None/event_comment/{0}/Top'.format(obj.id)

        elif ttype == 'event_comment_comment':
            text = ' replied to your comment'
            link = '/event_comments/None/event_comment/{0}/Top'.format(obj.id)

        elif ttype == 'comment_comment':
            text = ' replied to your comment'
            link = ('/comments/None/comment/{0}').format(obj.id)
        
        elif ttype == 'follow':
            text = ' started following you'
            link = '/profile/{0}'.format(obj.name)

        else:
            print("Invalid value for type")
            text = None
            link = None
            
        # All notifications redirect to the comment section of the post
        self.user = user
        self.message = user_from.name + text
        self.link = link
        self.time_created = datetime.now(tz=pytz.timezone('America/Chicago'))

class Event_Post(db.Model):
    __tablename__ = 'event_posts'
    id = db.Column(db.Integer, primary_key=True, unique=True)
    like_count = db.Column(db.Integer)
    likes = db.relationship("User", secondary=event_post_like_association_table)
    text = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    user = db.relationship("User", back_populates="event_posts")
    event_comments = db.relationship("Event_Comment", back_populates="event_post", lazy=True)    
    time_created = db.Column(db.DateTime(timezone=True))

class Event_Comment(db.Model):
    __tablename__ = 'event_comments'
    id = db.Column(db.Integer, primary_key=True, unique=True)
    text = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    user = db.relationship("User", back_populates="event_comments")
    event_post_id = db.Column(db.Integer, db.ForeignKey('event_posts.id'))
    event_post = db.relationship("Event_Post", back_populates="event_comments") 
    parents = db.relationship(
        'Event_Comment', 
        secondary=comment_tree,
        primaryjoin=(comment_tree.c.parent_id == id),
        secondaryjoin=(comment_tree.c.children_id == id),
        backref=db.backref('children_comments', lazy='dynamic'),
        lazy='dynamic'
        )
    likes = db.relationship("User", secondary=event_comment_like_association_table)
    #date = db.Column(db.DateTime)
    time_created = db.Column(db.DateTime(timezone=True))


def getAllUserNames():
    rp = db.session.execute(select([User.name]).order_by(User.name))
    for user in rp:
        print(user)


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, unique=True)
    email = db.Column(db.String(80))
    name = db.Column(db.String(80))
    bio = db.Column(db.String(80))
    password_hash = db.Column(db.String(128))
    post_streak = db.Column(db.Integer, default=0)
    coins = db.Column(db.Integer, default=0)
    accepted_coins = db.Column(db.Integer, default=0)
    event = db.Column(db.Integer, default=0)
    titles = db.relationship("Title", secondary=user_title_association_table)
    admin = db.Column(db.Integer, default=0)
    title = db.Column(db.String(80), default="Newbie")

    user_since = db.Column(db.DateTime())

    following = db.relationship(
        'User', lambda: user_following,
        primaryjoin=lambda: User.id == user_following.c.user_id,
        secondaryjoin=lambda: User.id == user_following.c.following_id,
        backref='followers'
    )


    like_count = db.Column(db.Integer, default=0)
    level = db.Column(db.Integer, default=1)
    like_goal = db.Column(db.Integer, default=3)

    def level_up(self):
        if self.like_count >= self.like_goal:
            self.level = self.level + 1
            self.like_goal = self.level * 3 + self.like_goal
        db.session.commit()

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    comments = db.relationship("Comment", back_populates="user")
    event_comments = db.relationship("Event_Comment", back_populates="user")
    posts = db.relationship("Post", back_populates="user")
    event_posts = db.relationship("Event_Post", back_populates="user")
    notifications = db.relationship("Notification", back_populates="user")
    rports = db.relationship("Report", back_populates="user")
    feedbacks = db.relationship("Feedback", back_populates="user")
    
    #comments = db.relationship("Comment", back_populates="user")

    def __init__(self, email, name, password):
        self.email = email
        self.name = name
        self.password = password
        self.like_count = 0
        self.user_since = datetime.now()

class Post(db.Model):
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True, unique=True)
    like_count = db.Column(db.Integer)
    likes = db.relationship("User", secondary=post_like_association_table)
    text = db.Column(db.Text)
    # USER - POST
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    user = db.relationship("User", back_populates="posts")

    #COMMENTS
    comments = db.relationship("Comment", back_populates="post", lazy=True)
    time_created = db.Column(db.DateTime(timezone=True))

#http://codeomitted.com/flask-sqlalchemy-many-to-many-self-referential/
class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True, unique=True)
    text = db.Column(db.Text)

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    user = db.relationship("User", back_populates="comments")

    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'))
    post = db.relationship("Post", back_populates="comments") 

    parents = db.relationship(
        'Comment', 
        secondary=comment_tree,
        primaryjoin=(comment_tree.c.parent_id == id),
        secondaryjoin=(comment_tree.c.children_id == id),
        backref=db.backref('children_comments', lazy='dynamic'),
        lazy='dynamic'
    )
        
    #likes
    likes = db.relationship("User",
                     secondary=comment_like_association_table)

    
    #date = db.Column(db.DateTime)
    time_created = db.Column(db.DateTime(timezone=True)) 

def reset_data_base(tables):
    if tables == "all":
        print("reseting all")
    
    if tables == "keep_user_role":
        print("reseting everything but users and their roles")

# Mail Shtuff

def send_async_email(app, msg):
    with app.app_context():
            mail.send(msg)

def send_email(subject, sender, recipients, text_body, html_body):
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    Thread(target=send_async_email, args=(app, msg)).start()


def deletemeth(media, media_type):    
    if media_type == "post":
        PhotoTools.deleteImage(media, media_type)
        children = media.comments            


    elif media_type == "comment":
        children = media.children_comments.all()
    
    elif media_type == "event_post":
        PhotoTools.deleteImage(media, media_type)
        children = media.event_comments

    elif media_type == "event_comment":
        children = media.children_comments.all()

    if children:
        for i in children:
            if media_type == "event_post" or media_type == "event_comment":
                deletemeth(i, "event_comment")
            elif media_type == "post" or media_type == "comment":
                deletemeth(i, "comment")

    db.session.delete(media)
    db.session.commit()


def get_current_user():
    try:
        return User.query.filter_by(name=session["user"]).all()[0] 
    except:
        return None


def get_date_time():
    current = datetime.now()
    current_day = datetime.now().day
    current_month = datetime.now().month
    current_year = datetime.now().year
    new_date = str(current_day) + "/" + str(current_month) + "/" + str(current_year)
    return new_date


@app.route('/')
def index():
    if not login_check():
        return redirect('/login')
    #t1.daily_reset()
    return redirect('/feed/0/Top')
    #render_template("main_page.html")

@app.route('/comments/<origin>/<posttype>/<id>/<which>')
def comments(origin, posttype, id, which):
    _current_user = get_current_user()
    if posttype == "post":
        parent = Post.query.filter_by(id=id).all()[0]
        sub_comments = parent.comments
        parent = [parent, PhotoTools.getExtension(parent, 'post') ]  
    elif posttype == "comment":
        parent = Comment.query.filter_by(id=id).all()[0]
        sub_comments = parent.children_comments.all()
    primary = sub_comments
    out2 = []
    out1 = []
    i = 0
    final_out_list = []
    for comment in primary:
        single_comment = []
        try:
            a = comment.children_comments.all()[0]
        except:
            print("no children for comment on search")
            a = 'None'
        r_lis_one = []
        r_lis_one.append(a)
        try:
            r_lis_one.append(a.children_comments.all()[0])
        except:
            r_lis_one.append("None")
        try:
             b = comment.children_comments.all()[1]
        except:
            print("no children for comment on second search")
            b = 'None'
        r_lis_two = []
        r_lis_two.append(b)
        try:
            r_lis_two.append(b.children_comments.all()[0])
        except:
            r_lis_two.append("None")
        single_comment.append(comment)
        single_comment.append(r_lis_one)
        single_comment.append(r_lis_two)
        final_out_list.append(single_comment)
    try:
        try:
            parent_of_parent = Post.query.with_parent(parent).all()[0]
            parent_of_parent_type = "post"
        except:
            parent_of_parent = parent.parents.all()[0]
            parent_of_parent_type = "comment"
            
        print("Parent of ", parent, " is: ", parent_of_parent)
    except:
        print("couldn't find parent of ", parent)
        parent_of_parent = "missing"
        parent_of_parent_type = "missing"


    print("yo this is the final out list:  ", final_out_list)
    if posttype == 'comment':
        return render_template('comments_parent_comment.html', parent=parent, comments=final_out_list, user = _current_user, posttype = posttype, parent_of_parent = parent_of_parent, parent_of_parent_type=parent_of_parent_type, which=which, origin=origin, id=id, base_or_event="base") #posts and comments variable required
    elif posttype == 'post':
        return render_template('comments_parent_post.html', parent=parent, comments=final_out_list, user = _current_user, posttype = posttype, parent_of_parent = parent_of_parent, parent_of_parent_type=parent_of_parent_type, which=which, origin=origin, id=id, base_or_event="base") #posts and comments variable required

@app.route('/event_comments/<origin>/<posttype>/<id>/<which>')
def event_comments(origin, posttype, id, which):
    _current_user = get_current_user()
    if posttype == "event_post":
        parent = Event_Post.query.filter_by(id=id).all()[0]
        primary = parent.event_comments
        parent = [parent, PhotoTools.getExtension(parent, 'event_post') ] 
    elif posttype == "event_comment":
        parent = Event_Comment.query.filter_by(id=id).all()[0]
        primary = parent.children_comments.all()

    # Create comment threads
    final_out_list = []
    for comment in primary:
        single_comment = []
        try: 
            a = comment.children_comments.all()[0]
        except:
            a = 'None'
        r_lis_one = []
        r_lis_one.append(a)
        try:
            r_lis_one.append(a.children_comments.all()[0])
        except:
            r_lis_one.append("None")
        try:
            b = comment.children_comments.all()[1]
        except:
            b = 'None'
        r_lis_two = []
        r_lis_two.append(b)
        try:
            r_lis_two.append(b.children_comments.all()[0])
        except:
            r_lis_two.append("None")
        single_comment.append(comment)
        single_comment.append(r_lis_one)
        single_comment.append(r_lis_two)
        final_out_list.append(single_comment)
    try:
        try:
            parent_of_parent = Event_Post.query.with_parent(parent).all()[0]
            parent_of_parent_type = "event_post"
        except:
            parent_of_parent = parent.parents.all()[0]
            parent_of_parent_type = "event_comment"
    except:
        parent_of_parent = "missing"
        parent_of_parent_type = "missing"

    print("Yo this is the final out list: ", final_out_list)

    for i in final_out_list:
        print(i[2][0])
    print(parent)    
    if posttype == 'event_comment':
        return render_template('event_comments_parent_comment.html', parent=parent, comments=final_out_list, user = _current_user, posttype = posttype, parent_of_parent = parent_of_parent, parent_of_parent_type=parent_of_parent_type, which=which, origin=origin, id=id) #posts and comments variable required
    elif posttype == 'event_post':
        return render_template('event_comments_parent_post.html', parent=parent, comments=final_out_list, user = _current_user, posttype = posttype, parent_of_parent = parent_of_parent, parent_of_parent_type=parent_of_parent_type, which=which, origin=origin, id=id) #posts and comments variable required

@app.route('/report/<user_name>', methods=['GET', 'POST'])
def report(user_name):
    user = User.query.filter_by(name=user_name).all()[0]
    if request.method == "POST":
        text = request.form['text']
        new_report = Report(text)
        db.session.add(new_report)
        return render_template('report_submitted.html')
    else:
        return render_template('report.html', user=user)

@app.route('/back')
def back():
    print('redirecting to:', session['last_route'])
    return redirect(session['last_route'])

@app.route('/follow/<name>')
def fol(name):
    _current_user = get_current_user()
    followed = User.query.filter_by(name=name).all()[0]
    if _current_user in followed.followers:
        followed.followers.remove(_current_user)
    else:
        followed.followers.append(_current_user)
        
        new_Notification = Notification(_current_user, followed, "follow", _current_user)
        followed.notifications.append(new_Notification)
        db.session.add(new_Notification)
        db.session.commit()

    db.session.commit()
    return redirect('/profile/{0}'.format(name))


@app.route('/followers')
def followers():
    _current_user = get_current_user()
    followers_and_pp = []
    followers = _current_user.followers
    for user in followers:
        image_extension = PhotoTools.getExtension(user, 'user')
        followers_and_pp.append([user, image_extension])

    return render_template('followers.html', followers=followers_and_pp, cu=_current_user)


@app.route('/following')
def following():
    _current_user = get_current_user()

    following_and_pp = []
    following =_current_user.following

    for user in following:
        image_extension = PhotoTools.getExtension(user, 'user')
        following_and_pp.append([user, image_extension])

    print(following_and_pp)
    return render_template('following.html', following=following_and_pp, cu=_current_user)


@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        mail = request.form['email']
        try:
            user_id = User.query.filter_by(email=mail).all()[0].id
        except:
            error = "invalid or unregistered email"
            return render_template('forgot_password.html', error=error)

        reset_token = s.dumps([user_id])
        send_email('Rectangle Interactive - Reset Your Password',
            sender='rectangleinteractive@gmail.com',
            recipients=[mail],
            text_body=render_template('reset_password.txt',
                url='rectangleinteractive/reset_password/{0}'.format(reset_token)),
            html_body=render_template('reset_password.html',
                url='rectangleinteractive/reset_password/{0}'.format(reset_token)))
        
        error = "Recovery email sent! (It might be in spam)"
        return render_template('forgot_password.html', error=error)   

    else:
        return render_template('forgot_password.html')


@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    i = s.loads(token)[0]
    try:
        user = User.query.filter_by(id=i).all()[0]    
    except:
        return "invalid token"

    if request.method == 'POST':
        pas = request.form['password']
        pas2 = request.form['password2']
        string_check = re.compile('[@_!#$%^&*()<>?/\|}{~:]') 
        if pas != pas2:
            error = "passwords do not match"
            return render_template('_reset_password.html', error=error, token=token)

        elif (len(pas) < 6 or len(pas2) < 6):
            error = "password must be at least six digits in length"
            return render_template('_reset_password.html', error=error, token=token)
     
        elif (string_check.search(pas) == None): 
            error=" password must contain a special character (example: [@_!#$%^&*()<>?/\|}{~:]) "
            return render_template("_reset_password.html", error=error, token=token)
        else:
            user.password = pas
            db.session.commit()
            return redirect('/login')
    else:
        return render_template('_reset_password.html', token=token)


@app.route('/delete_notification/<id>')
def delete_notification(id):
    try:
        quer = Notification.query.filter_by(id=id).all()[0]
        db.session.delete(quer)
        db.session.commit()
        return redirect('/notifications/None/None')

    except: return "bruh"

@app.route('/notifications/<act>/<id>',  methods=['GET', 'POST'])
def notifications(act, id):
    _current_user = get_current_user()
    notifications = _current_user.notifications
    if act != 'None':
        quer = Notification.query.filter_by(id=id).all()[0]
        link = quer.link
        db.session.delete(quer)
        db.session.commit()
        return redirect(link)
    else:
        return render_template('notifications.html', notifications=notifications, _current_user=_current_user)


@app.route('/createaccount', methods=['GET', 'POST'])
def createAccount():
    if request.method == 'POST':
        mail = request.form['email']
        user = request.form['username']
        pas = request.form['password']
        pas2 = request.form['password2']
        error = None
        if not (mail and user and pas):
            error="Please complete the form before submission"
            return render_template("create_account.html", error=error)

        # EMAIL
        email = User.query.filter_by(email=mail).all()

        if email:
            error="Email already in use"
            return render_template("create_account.html", error=error)

        if (not("@" in mail)) or (not('.' in mail)):
            error="Invalid email"
            return render_template("create_account.html", error=error)

        # USERNAME

        name = User.query.filter_by(name=user).all()  # switch to condition (get_current_user == None)
        if name:         
            error="Username already taken"
            return render_template("create_account.html", error=error)

        if len(user) >= 12:
            error="Username must be less than 12 characters in length"
            return render_template("create_account.html", error=error)

        if " " in user:
            error="Username cannot include any spaces"
            return render_template("create_account.html", error=error)

        if (not (user.isalpha)):
            error="Username can may only contain letters"
            return render_template("create_account.html", error=error)

        # PASSWORD
        if pas != pas2:
            error="Passwords do not match "
            return render_template("create_account.html", error=error)


        if len(pas) < 6:
            error="Password must be at least 6 digits in length "
            return render_template("create_account.html", error=error)

        string_check = re.compile('[@_!#$%^&*()<>?/\|}{~:]')      
        if (string_check.search(pas) == None): 
            error="Password must contain a special character example: [@_!#$%^&*()<>?/\|}{~:] "
            return render_template("create_account.html", error=error)
                
        # PASSED ALL TESTS
        temp = User(mail, user, pas)
        titles = Title.query.filter_by(default=1).all()
        for each in titles:
            temp.titles.append(each)
        session["user"] = temp.name
        db.session.add(temp)
        db.session.commit()
        return render_template("welcome.html")
    else:    
        return render_template("create_account.html")


@app.route('/event_delete/<origin>/<origin_id>/<origin_type>/<media_type>/<id>')
def event_delete(origin, origin_id, origin_type, media_type, id):
    
    # Delete
    if media_type == "event_post":
        quer = Event_Post.query.filter_by(id=id).all()[0]
        deletemeth(quer, "event_post")
        return redirect('/events/0/Top/Event/False')

    elif media_type == "event_comment":
        quer = Event_Comment.query.filter_by(id=id).all()[0]
        deletemeth(quer, "event_comment")

        if origin_id == id:
            try:
                parent = Event_Comment.query.with_parent(quer).all()[0]
                return redirect('/{0}/{1}/event_comment/{2}/Top'.format(origin, media_type, parent.id))
            except:
                parent = Event_Post.query.with_parent(quer).all()[0]
                return redirect('/{0}/{1}/event_post/{2}/Top'.format(origin, media_type, parent.id))
            
        if origin == "profile":
            return redirect('/profile/{0}'.format(origin_id))

        if origin_type == "event_comment":
            return redirect('/{0}/{1}/event_comment/{2}/Top'.format(origin, media_type, origin_id))
            
        elif origin_type == "event_post":
            return redirect('/{0}/{1}/event_post/{2}/Top'.format(origin, media_type, origin_id))
            
    # Redirect



@app.route('/post_delete/<origin>/<origin_id>/<origin_type>/<media_type>/<id>')
def post_delete(origin, origin_id, origin_type, media_type, id):
    _current_user = get_current_user()
    quer = Post.query.filter_by(id=id).all()[0]
    deletemeth(quer, "post")
    
    # Redirect
    return redirect('/feed/0/Top')

@app.route('/comment_delete/<origin>/<origin_id>/<origin_type>/<media_type>/<id>')
def comment_delete(origin, origin_id, origin_type, media_type, id):
    _current_user = get_current_user()
    quer = Comment.query.filter_by(id=id).all()[0]
    deletemeth(quer, "comment")

    if origin_id == id:
        try:
            parent = Comment.query.with_parent(quer).all()[0]
            return redirect('/{0}/{1}/comment/{2}/Top'.format(origin, media_type, parent.id))
        except:
            parent = Post.query.with_parent(quer).all()[0]
            return redirect('/{0}/{1}/post/{2}/Top'.format(origin, media_type, parent.id))
    
    if origin == "profile":
        return redirect('/profile/{0}'.format(origin_id))

    if origin_type == "comment":
        return redirect('/{0}/{1}/comment/{2}/Top'.format(origin, media_type, origin_id))
    
    elif origin_type == "post":
        return redirect('/{0}/{1}/post/{2}/Top'.format(origin, media_type, origin_id))

    else:
        return "bruh"


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/editprofile', methods=['GET','POST'])
def editprofile():
    _current_user = get_current_user()
    if request.method == 'POST':
        if 'file' in request.files:
            file = request.files['file']
            print(_current_user, "type: ", type(_current_user))
            PhotoTools.createImage(_current_user, file, 'user')

        newbio = request.form['bio']
        if len(newbio) < 200:
            _current_user.bio = newbio
            select = request.form.get('select')
            print("-------", select)
            _current_user.title = request.form.get('select')
            db.session.commit()
            return redirect('/profile/{0}'.format(session["user"]))
            
        else:
            return render_template('edit_profile.html', error="Post must be under 200 characters in length ( you had {} )".format(len(newbio)))
    else:
        return render_template("edit_profile.html", user=_current_user)

@app.route('/feed/<int:pagenum>/<which>')
def main(pagenum, which):
    _current_user = get_current_user()
    if "user" in session:
        if not _current_user:
            return redirect("/login")
        print(_current_user)
        if which == "Top":
            posts=db.session.query(Post).order_by(Post.like_count.desc())
            posts = posts.all()
        elif which == "New":
            posts=db.session.query(Post).order_by(Post.time_created.desc())
            posts = posts.all()
        elif which == "Following":
            posts=db.session.query(Post).order_by(Post.time_created.desc()).all()
            for i in posts:
                if not (_current_user in i.user.followers):
                    posts.remove(i)
        else:
            print("Invalid value for which")
            posts = None
        posts_and_pictures = []
        for post in posts:
            image_extension = PhotoTools.getExtension(post, 'post')
            print(image_extension)
            posts_and_pictures.append([post, image_extension])
        if not posts:
            posts = "none"
            page_num = 0
            max = 0        
        else:
            paged_posts = list(divide_chunks(posts_and_pictures, 8))
            max = paged_posts.__len__()
            posts = paged_posts[pagenum]

        print("++++++++++++++++++++++++++++++++++++++++", _current_user.admin)
        return render_template("feed.html", posts=posts, user=_current_user, page=pagenum, max=max, which=which, first_login = True)

    else:
        return redirect('/login')


def rankUsers():
    ranking_users = Event_Post.query.order_by(Event_Post.like_count.desc()).all()
    ranks = []
    a = False
    for j in ranking_users:
        for k in ranks:
            if k == j.user:
                a = True
        if not a:
            ranks.append(j.user)
    ranking_users = ranks
    for i in range(3 - len(ranking_users)):
        ranking_users.append(None)

    return ranking_users

def getEventData():
    week_day = datetime.now(tz=pytz.timezone('America/Chicago')).today().weekday()
    event = Event.query.all()[week_day]
    return event.title, event.description, event.rules

@app.route('/events/<int:pagenum>/<which>/<event_which>/<not_enough_coins>')
def events(pagenum, which, event_which, not_enough_coins):
    _current_user = get_current_user()
    if not _current_user:
        return redirect("/login")

    event_posts = Event_Post.query.order_by(Event_Post.like_count.desc()).all()
    
    event_title, event_description, event_rules = getEventData()

    if _current_user.event == 0:
        _current_user.event = 1
    elif _current_user.event == 1:
        _current_user.event = 2
    db.session.commit()
        
    if which == "Top":
        event_posts=db.session.query(Event_Post).order_by(Event_Post.like_count.desc())
        event_posts = event_posts.all()

    elif which == "New":
        event_posts=db.session.query(Event_Post).order_by(Event_Post.time_created.desc())
        event_posts = event_posts.all()

    elif which == "Following":
        event_posts=db.session.query(Event_Post).order_by(Event_Post.time_created.desc()).all()
        for i in event_posts:
            if  not (_current_user in i.user.followers):
                event_posts.remove(i)


    # Rank Users
    ranking_users = rankUsers()
    
    extensions = []
    for i in ranking_users:
        if i:
            extensions.append(PhotoTools.getExtension(i, 'user'))
    
    event_posts_and_photos = []
    for post in event_posts:
        image_extension = PhotoTools.getExtension(post, 'event_post')
        event_posts_and_photos.append([post, image_extension])
    

    if not event_posts_and_photos:
        posts = "none"
        page_num = 0
        max = 0        
    else:
        paged_posts = list(divide_chunks(event_posts_and_photos, 8))
        max = paged_posts.__len__()
        posts = paged_posts[pagenum]

    return render_template('/events.html', event_which=event_which, which=which, posts=posts, page=pagenum, user=_current_user, max=max, ranking_users=ranking_users, extensions=extensions, day="monday", not_enough_coins=not_enough_coins, event_title=event_title, event_description=event_description, event_rules=event_rules)

@app.route('/create_post', methods=['GET', 'POST'])
def createPost():
    _current_user = get_current_user()
    if request.method == "POST":
        length = len(request.form['text'])
        if request.form['text']:
            new_comment = Comment(text=request.form['text'], time_created = datetime.now(tz=pytz.timezone('America/Chicago')))
            new_comment.user = _current_user
        else:
            error="Post cannot be empty"
            return render_template('/create_post.html', error=error, base_or_event="base")

        if length < 1000:
            new_post = Post(user=_current_user, text=request.form['text'], like_count=0, time_created = datetime.now(tz=pytz.timezone('America/Chicago')))
            image_extension = "None"
            db.session.add(new_post)
            db.session.commit()
            _posts = Post.query.all()
            if 'file' in request.files:
                file = request.files['file']
                if file and allowed_file(file.filename):
                    file = request.files['file']
                    PhotoTools.createImage(new_post, file, 'post')
            return redirect('/feed/0/Top')
        else:
            return render_template('/create_post.html', error="Post must be under 1000 characters in length ( you had {} )".format(length), base_or_event = "base")
    
    return render_template('/create_post.html', base_or_event="base")


@app.route('/create_event_post', methods=['GET', 'POST'])
def createEventPost():
    _current_user = get_current_user()
    if request.method == "POST":
        length = len(request.form['text'])
        if request.form['text']:
            new_comment = Comment(text=request.form['text'], time_created = datetime.now(tz=pytz.timezone('America/Chicago')))
            new_comment.user = _current_user
        else:
            error="Post cannot be empty"
            return render_template('/create_post.html', error=error)

        if length < 1000:
            new_post = Event_Post(user=_current_user, text=request.form['text'], like_count=0, time_created = datetime.now(tz=pytz.timezone('America/Chicago')))
            image_extension = "None"
            db.session.add(new_post)
            db.session.commit()
            if 'file' in request.files:
                file = request.files['file']
                if file and allowed_file(file.filename):
                    file = request.files['file']
                    PhotoTools.createImage(new_post, file, 'event_post')
            return redirect('/events/0/Top/Event/False')    
            
                
        else:
            return render_template('/create_post.html', error="Post must be under 1000 characters in length ( you had {} )".format(length), base_or_event = "event")
    
    return render_template('/create_post.html', base_or_event="event")


@app.route('/create_comment/<origin>/<posttype>/<id>/<which>', methods=['GET', 'POST'])
def createComment(origin, posttype, id, which):
    _current_user = get_current_user()
    if request.method == "POST":
        # Later make a post validation function
        if request.form['text']:
            new_comment = Comment(text=request.form['text'], time_created = datetime.now(tz=pytz.timezone('America/Chicago')))
            new_comment.user = _current_user
        else:
            error="Comment cannot be empty"
            return render_template('/create_comment.html', origin=origin, posttype=posttype, id=id, which=which, error=error, base_or_event="base")

        if posttype == "post":
            parent = Post.query.filter_by(id=id).all()[0]
            sub_comments = parent.comments    
            parent.comments.append(new_comment)
            db.session.add(new_comment)
            db.session.commit()

            # Creating Notification
            if (parent.user.id != _current_user.id):
                new_Notification = Notification(_current_user, parent.user, "post_comment", parent)
                parent.user.notifications.append(new_Notification)
                db.session.add(new_Notification)
                db.session.commit()

            return redirect('/comments/origin/post/{0}/{1}'.format(id, which))
            
        elif posttype == "comment":
            parent = Comment.query.filter_by(id=id).all()[0]
            sub_comments = parent.children_comments.all()
            parent.children_comments.append(new_comment)
            db.session.add(new_comment)
            db.session.commit()
                
            # Creating Notification
            
            if (parent.user.id != _current_user.id):
                new_Notification = Notification(_current_user, parent.user, "comment_comment", parent)
                parent.user.notifications.append(new_Notification)
                db.session.add(new_Notification)
                db.session.commit()

            return redirect('/comments/None/comment/{0}/Top'.format(id))
    else:
        return render_template('/create_comment.html', origin=origin, posttype=posttype, id=id, which=which, base_or_event="base")

@app.route('/create_event_comment/<origin>/<posttype>/<id>/<which>', methods=['GET', 'POST'])
def createEventComment(origin, posttype, id, which):
    _current_user = get_current_user()
    if request.method == "POST":

        if request.form['text']:
            new_comment = Event_Comment(text=request.form['text'], time_created = datetime.now(tz=pytz.timezone('America/Chicago')))
            new_comment.user = _current_user
        else:
            error="Comment cannot be empty"
            return render_template('/create_comment.html', origin=origin, posttype=posttype, id=id, which=which, error=error)

        if posttype == "event_post":
            parent = Event_Post.query.filter_by(id=id).all()[0]
            sub_comments = parent.event_comments
            parent.event_comments.append(new_comment)
            db.session.add(new_comment)
            db.session.commit()
            
            if parent.user.id != _current_user.id:
                new_Notification = Notification(_current_user, parent.user, "event_post_comment", new_comment)
                parent.user.notifications.append(new_Notification)
                db.session.add(new_Notification)
                db.session.commit()
            
            return redirect('/event_comments/events/event_post/{0}/{1}'.format(id, which))

        elif posttype == "event_comment":
            parent = Event_Comment.query.filter_by(id=id).all()[0]
            sub_comments = parent.children_comments.all()
            parent.children_comments.append(new_comment)
            db.session.add(new_comment)
            db.session.commit()
            
            if parent.user.id != _current_user.id:
                new_Notification = Notification(_current_user, parent.user, "event_comment_comment", new_comment)
                parent.user.notifications.append(new_Notification)
                db.session.add(new_Notification)
                db.session.commit()
            
            return redirect('/event_comments/None/event_comment/{0}/Top'.format(id))

        else:
            return ("Something went wrong")
    else:
        return render_template('/create_comment.html', origin=origin, posttype=posttype, id=id, which=which, base_or_event="event")    
    

@app.route('/addcoins')
def addcoins():
    _current_user = get_current_user()
    coin_count = _current_user.post_streak + 1
    if _current_user.accepted_coins == 0:
        _current_user.coins =_current_user.coins + coin_count
        _current_user.accepted_coins = 1
        db.session.commit()
        #return redirect('profile/{0}'.format(_current_user.name))
    #else:
    return redirect('/feed/0/Top')

@app.route('/like/<origin>/<origin_id>/<origin_type>/<media_type>/<which>/<id>')
def like(id, origin, origin_id, origin_type, media_type, which):
    _current_user = get_current_user()
    if media_type == "post":
        _post = Post.query.filter_by(id=id).all()[0]
        if _current_user in _post.likes:
            _post.likes.remove(_current_user)
            _post.like_count = _post.like_count - 1
            _post.user.like_count = _post.user.like_count - 1
        else:
            _post.likes.append(_current_user)
            _post.like_count = _post.like_count + 1
            _post.user.level_up()

            if _post.user.id != _current_user.id:
                new_notification = Notification(_current_user, _post.user, 'post_like', _post)
                db.session.add(new_notification)
                db.session.commit()
                _post.user.like_count = _post.user.like_count + 1
            
            

    elif media_type == "comment":
        _comment = Comment.query.filter_by(id=id).all()[0]
        if _current_user in _comment.likes:
            _comment.likes.remove(_current_user)
            _comment.user.like_count = _comment.user.like_count - 1
        else:
            _comment.likes.append(_current_user)
            _comment.user.level_up()

            if _comment.user.id != _current_user.id:
                new_notification = Notification(_current_user, _comment.user, 'comment_like', _comment)
                db.session.add(new_notification)
                db.session.commit()
                _comment.user.like_count = _comment.user.like_count + 1
                


    db.session.commit()
    if origin == "feed":
        return redirect('/feed/0/{0}'.format(which))
    
    if origin_type == "comment":
        return redirect('/{0}/{1}/comment/{2}/Top'.format(origin, media_type, origin_id))

    elif origin_type == "post":
        return redirect('/{0}/{1}/post/{2}/Top'.format(origin, media_type, origin_id))

    if origin_id == "None":
        return redirect('/{0}'.format(origin))
    else:
        return redirect('/{0}/{1}/Top'.format(origin, origin_id))

#           /event_like/events/None/None/event_post/{{ which }}/{{ parent[0].id }}
@app.route('/event_like/<origin>/<origin_id>/<origin_type>/<media_type>/<which>/<id>')
def event_like(id, origin, origin_id, origin_type, media_type, which):
    _current_user = get_current_user()
    not_enough_coins = False
    print("current user: ", _current_user)
    if media_type == "event_post":
        _post = Event_Post.query.filter_by(id=id).all()[0]
        if _current_user in _post.likes:
            _post.likes.remove(_current_user)
            _post.like_count = _post.like_count - 1
            _post.user.like_count = _post.user.like_count - 1
        else:
            if _current_user.coins <= 0:
                not_enough_coins = True
                flash('Not enough coins')
            else:
                _post.likes.append(_current_user)
                _post.like_count = _post.like_count + 1
                _post.user.level_up()
                _current_user.coins = _current_user.coins - 1
                _post.user.coins = _post.user.coins + 1

                if _post.user.id != _current_user.id:
                    _post.user.like_count = _post.user.like_count + 1
                    new_notification = Notification(_current_user, _post.user, 'event_post_like', _post)
                    db.session.add(new_notification)
                    db.session.commit()
                

    elif media_type == "event_comment":
        _comment = Event_Comment.query.filter_by(id=id).all()[0]
        if _current_user in _comment.likes:
            _comment.likes.remove(_current_user)
            _comment.user.like_count = _comment.user.like_count - 1
        else:
            _comment.likes.append(_current_user)
            _comment.user.like_count = _comment.user.like_count + 1
            _comment.user.level_up()

        if _comment.user.id != _current_user.id:
            new_notification = Notification(_current_user, _comment.user, 'event_comment_like', _comment)
            _comment.user.like_count = _comment.user.like_count + 1
            db.session.add(new_notification)
            db.session.commit()

    print(origin_id, ":", id)
    db.session.commit()

    print("origin: ", origin)
    if origin == "events":
        return redirect('/events/0/{0}/Event/False'.format(which))
    
    if origin_type == "event_comment":
        return redirect('/{0}/{1}/event_comment/{2}/Top'.format(origin, media_type, origin_id))

    elif origin_type == "event_post":
        return redirect('/{0}/{1}/event_post/{2}/Top'.format(origin, media_type, origin_id))

    if origin_id == "None":
        return redirect('/{0}'.format(origin))
    else:
        return redirect('/{0}/{1}/Top'.format(origin, origin_id))


    db.session.commit()
    


@app.route('/login', methods=['GET', 'POST'])
def login():
    try:
        newsletters = Newsletter.query.all()

    except:
        newsletters = "none"
    
    if request.method == "POST":
        session.permanent = True
        username = request.form['username']
        password = request.form['password']
        qur = User.query.filter_by(name=username).all()
        try:
            db_username = qur[0].name
            if qur[0].verify_password(password):
                session['user'] = username
                return redirect('/profile/{0}'.format(session["user"]))

            else:
                error="Incorrect username or password"
                return render_template("login.html", error=error)
        except:
            error="Incorrect username or password"
            return render_template("login.html", error=error)
    else:
        return render_template("login.html", newsletters=newsletters)

@app.route('/logout')
def logout():
    session.pop("user", None)
    return redirect('/login')


@app.route('/newsletter')
def mainn():
    if "user" in session:
        try:
            newsletters = Newsletter.query.all()
        except:
            newsletters = "none"
        return render_template("newsletter.html", newsletters=newsletters)
    else:
        return redirect('/login')


@app.route('/search/<typ>', methods=['GET', 'POST'])
def search(typ):
    _current_user = get_current_user()
    if request.method == 'POST':
        if request.form['search']:
            if typ == 'User':
                name = request.form['search']
                followers = User.query.filter(User.name.like('%' + name + '%'))
                followers_and_pp = []
                for user in followers:
                    image_extension = PhotoTools.getExtension(user, "user")
                    followers_and_pp.append([user, image_extension])
                posts = None

            elif typ == 'Post':
                stuff = request.form['search']
                posts = Post.query.filter(Post.text.like('%' + stuff + '%'))
                followers_and_pp = None

        else:
        
            followers_and_pp = None
            posts = None

        return render_template('search.html', user_results=followers_and_pp, posts=posts, typ=typ, cu=_current_user)
    else:
        return render_template('search.html', typ=typ)


@app.route('/profile/<usr>', methods=['GET', 'POST'])
def profile(usr):
    _current_user = get_current_user()
    
    if not _current_user:
        return redirect("/login")

    if "user" in session:
        _user = User.query.filter_by(name=usr).all()[0]
        _current_user = get_current_user()
        _posts = Post.query.filter_by(user=_user).all()
        

        posts_and_pictures = []
        for post in _posts:
            image_extension = PhotoTools.getExtension(post, 'post')
            posts_and_pictures.append([post, image_extension])


        progress = (((_user.like_count) / (_user.like_goal)) * 100)
        users = db.session.query(User).order_by(User.like_count.desc())
        users = users.all()
        rank = users.index(_current_user) + 1
        image_extension = PhotoTools.getExtension(_user, "user")
        print("ext", image_extension)
        streak_progress = _user.post_streak / 7 * 100
        return render_template("profile.html", user=_user, posts=posts_and_pictures, _cu=_current_user, progress=progress, streak_progress=streak_progress, extension=image_extension, rank=rank)
    else:
        return redirect('/login')

@app.route('/settings')
def settings():
    if 'user' in session:
        return render_template("settings.html")
    else:
        return redirect('/login')


@app.route('/feedback', methods=['GET', 'POST'])
def feedback():
    if get_current_user():
        if request.method == 'POST':
            text = request.form['text']
            db.session.add(Feedback(text=text, user=get_current_user()))
            db.session.commit()
            return redirect('/newsletter')
        else:
            return render_template('/feedback.html')
    else:
        return redirect('/login')

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return "bruh" #render_template('500.html'), 500



@app.route('/share/<name>')
def share(name):
    try:
        user = User.query.filter_by(name=name).all()[0]
    except:
        return "uh oh"
    return render_template('share.html', user=user)




# Moderator Routes
@app.route('/moderator')
def moderator():
    if get_current_user().admin == 1:
        return render_template("moderation.html")

    else:
        return redirect('/feed/0/Top')


@app.route('/edit_users/<delete>/<user>')
def edit_user(delete, user):
    if get_current_user().admin == 1:
        if delete == "delete":
            user = User.query.filter_by(name=user).all()[0]
            db.session.delete(user)
            db.session.commit()

        followers = User.query.all()
        followers_and_pp = []
        for user in followers:
            image_extension = PhotoTools.getExtension(user, "user")
            followers_and_pp.append([user, image_extension])
        posts = None

        return render_template("edit_users.html", user_results=followers_and_pp)
    else:
        return redirect('/feed/0/Top')

@app.route('/edit_events/<edit>', methods=['GET', 'POST'])
def edit_events(edit):
    if request.method == 'POST':
        text1 = request.form['text1']
        text2 = request.form['text2']
        text3 = request.form['text3']
        dotw = int(request.form.get('select'))
        print(type(dotw))
        print(text1)
        print(text2)
        Event.updateEvent(day_of_the_week=dotw, title=text1, rules=text2, description=text3)
        events = Event.query.all()
        return render_template("edit_events.html", events=events, edit="None")
    else:
        if get_current_user().admin == 1:
            events = Event.query.all()
            return render_template("edit_events.html", events=events, edit=edit)

        else:
            return redirect('/feed/0/Top')

@app.route('/edit_titles/<id>', methods=['GET', 'POST'])
def edit_titles(id):
    if get_current_user().admin == 1:
        if request.method == 'POST':
            Title.query.all()
            text1 = request.form['text1']
            text2 = request.form['text2']
            default = request.form.get('check')
            if default:
                db.session.add(Title(text1, text2, 1))
            else:
                db.session.add(Title(text1, text2, 0))
            db.session.commit()
            titles = Title.query.all()
            
            return render_template("edit_titles.html", titles=titles)

        else:
            if id != "None":
                title = Title.query.filter_by(id=id)[0]
                db.session.delete(title)
                db.session.commit()
                return redirect("/edit_titles/None")

            titles = Title.query.all()
            return render_template("edit_titles.html", titles=titles)
    else:
        return redirect('/feed/0/Top')

@app.route('/read_feedback')
def read_back():
    if get_current_user().admin == 1:
        feedback = Feedback.query.all()
        return render_template("read_feedback.html", feedback=feedback)
    else:
        return redirect('/feed/0/Top')


@app.route('/read_reports')
def read_reports():
    if get_current_user().admin == 1:
        reports = Report.query.all()
        return render_template("read_reports.html", reports=reports)
    else:
        return redirect('/feed/0/Top')



@app.route('/shop/<id>')
def shop(id):
    titles = Title.query.filter_by(selected=1).all()
    j = []
    one = 0 
    two = 0
    three = 0
    for i in titles:
        if i.cost == 25:
            one=i
        elif i.cost == 50:
            two=i
        elif i.cost == 100:
            three=i

    titles = [one, two, three]


    cu = get_current_user()

    if id != 'None':
        tit = Title.query.filter_by(id=id).all()[0]
        if tit in titles:
            # do they have enough money
            if tit not in cu.titles:
                if cu.coins >= tit.cost:
                    # add to users titles and subtract money
                    cu.coins = cu.coins - tit.cost
                    cu.titles.append(tit)
                    db.session.commit()
                    flash("Purchased!")
                    #return redirect('/profile/{0}'.format(cu.name))
                else:
                    flash('Not enough coins')
            else:
                flash("Already Owned")
        else:
            return "Bruh"

    return render_template('shop.html', titles=titles, user=cu)


def chunks(lst, n):
	for i in range(0, len(lst), n):
		yield lst[i:i +n]


@app.route('/letsapp/<username>/<password>/get/<int:id>')
def letsappget(username, password, id):
	qur = User.query.filter_by(name=username).all()
	try:
		db_username = qur[0].name
	except:
		return jsonify({'status': 'NONAME'})

	if qur[0].verify_password(password):
		try:
			chunked = chunks(os.listdir(os.path.join(app.config['UPLOAD_FOLDER'], "letsapp", "use")), 5)
			your_photos = list(chunked)[qur[0].id-1]
			return send_file(os.path.join(app.config['UPLOAD_FOLDER'], "letsapp", "use", your_photos[id-1]))
		except:
			return jsonify({'status': 'NEP'})
	
	return jsonify({'status': 'FLOPPED'});

@app.route('/letsapp/upload', methods=['GET', 'POST'])
def letsappupload():
	file = request.files['file']
	# if user does not select file, browser also
	# submit an empty part without filename
	if file.filename == '':
		flash('No selected file')
		return jsonify({'status':'NO'})
	if file and allowed_file(file.filename):
		#filename = secure_filename(file.filename)
		filename = str(uuid.uuid4()) + ".jpg"
		file.save(os.path.join(app.config['UPLOAD_FOLDER'], "letsapp", "uploads", filename))
		return jsonify({'status':'OK'})

	# somehow save the content to a folder 
	return jsonify({'status':'NO'})


@app.route('/letsapp/login/<username>/<password>')
def letsapplogin(username, password):
	try:
		qur = User.query.filter_by(name=username).all()
		db_username = qur[0].name
		if qur[0].verify_password(password):
			return jsonify({'status':'SUCCESS'})
		else:
			return jsonify({'status':'FAILED'})
	except:
		return jsonify({'status': 'FAILED'})
	

#if __name__ == "__main__":
#    tz = pytz.timezone('America/Chicago')
#    #manager.run()
#    app.run(host='0.0.0.0')


