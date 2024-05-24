from flask import Flask, render_template, url_for, redirect, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError
from flask_bcrypt import Bcrypt
import base64
import os

basedir = os.path.abspath(os.path.dirname(__file__))
instance_dir = os.path.join(basedir, 'instance')

if not os.path.exists(instance_dir):
    os.makedirs(instance_dir)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(instance_dir, 'database.db')
app.config['UPLOAD_FOLDER'] = os.path.join(basedir, 'static/avatars')
app.config['SECRET_KEY'] = 'Battery-AAA'
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    password = db.Column(db.String(80), nullable=False)
    currency_balance = db.Column(db.Integer(), default=1000)
    avatar = db.Column(db.Text, nullable=True)

class Topic(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, unique=True, nullable=False)
    description = db.Column(db.String)
    username = db.Column(db.String(20), nullable=False)

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String, nullable=False)
    topicId = db.Column(db.Integer, db.ForeignKey('topic.id', ondelete='CASCADE'), nullable=False)
    topic = db.relationship('Topic', backref=db.backref('comments', lazy=True, cascade='all, delete-orphan'))
    username = db.Column(db.String(20), nullable=False)

class RegisterForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Username"})
    password = PasswordField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Password"})
    submit = SubmitField("Register")

    def validate_username(self, username):
        existing_user_username = User.query.filter_by(username=username.data).first()
        if existing_user_username:
            raise ValidationError("That username already exists. Please choose a different one.")

class LoginForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Username"})
    password = PasswordField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Password"})
    submit = SubmitField("Login")

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user)
            return redirect(url_for('home'))
    return render_template('login.html', form=form)

@app.route('/profile')
@login_required
def profile():
    avatar_data = current_user.avatar
    if avatar_data:
        avatar_url = f"data:image/png;base64,{avatar_data}"
    else:
        avatar_url = None
    return render_template('profile.html', avatar_url=avatar_url)

@app.route('/custom')
def custom():
    return render_template('custom.html')

@app.route('/save-avatar', methods=['POST'])
@login_required
def save_avatar():
    data = request.get_json()
    image_data = data['image']

    # Remove the data URL prefix
    image_data = image_data.split(',')[1]

    # Update the user's avatar in the database
    current_user.avatar = image_data
    db.session.commit()

    return jsonify({'success': True, 'avatar_url': url_for('static', filename='avatars/avatar.png')})

@app.route('/store')
@login_required
def store():
    return render_template('store.html')

@app.route('/minigames')
@login_required
def minigames():
    return render_template('minigames.html')

@app.route('/minigames-feeding-time', methods=['GET', 'POST'])
@login_required
def minigamesfeedingtime():
    return render_template('minigames-feeding-time.html')

@app.route('/adopt', methods=['GET', 'POST'])
@login_required
def adopt():
    return render_template('adopt.html')

@app.route('/forums', methods=['GET', 'POST'])
@login_required
def forums():
    if request.method == "POST":
        title = request.form["title"]
        existing_topic = Topic.query.filter_by(title=title).first()
        if existing_topic:
            return render_template('forums.html', error="Topic already exists.")
        
        description = request.form["description"]
        topic = Topic(title=title, description=description, username=current_user.username)
        db.session.add(topic)
        db.session.commit()
    
    topics = Topic.query.order_by(Topic.id.desc()).all()
    return render_template('forums.html', topics=topics, username=current_user.username)

@app.route("/topic/<int:id>", methods=["GET", "POST"])
def topic(id):
    topic = Topic.query.get(id)
    comments = None

    if request.method == "POST" and current_user.is_authenticated:
        text = request.form["comment"]
        comment = Comment(text=text, topicId=id, username=current_user.username)
        db.session.add(comment)
        db.session.commit()

    comments = Comment.query.filter_by(topicId=id).all()
    return render_template("topic.html", topic=topic, comments=comments)

@app.route('/delete/topic/<int:id>', methods=['POST'])
@login_required
def delete_topic(id):
    topic = Topic.query.get(id)
    if topic:
        if topic.username == current_user.username:  
            db.session.delete(topic)
            db.session.commit()
            return redirect(url_for('forums'))
        else:
            abort(403)
    else:
        abort(404)

@app.route('/delete/comment/<int:id>', methods=['POST'])
@login_required
def delete_comment(id):
    comment = Comment.query.get(id)
    if comment:
        if comment.username == current_user.username:  
            db.session.delete(comment)
            db.session.commit()
            return redirect(url_for('topic', id=comment.topicId))
        else:
            abort(403)
    else:
        abort(404)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        new_user = User(username=form.username.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)