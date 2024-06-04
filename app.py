from flask import Flask, render_template, url_for, redirect, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError
from flask_bcrypt import Bcrypt
import os
import logging
import time
from sqlalchemy.exc import OperationalError

basedir = os.path.abspath(os.path.dirname(__file__))
instance_dir = os.path.join(basedir, 'instance')

if not os.path.exists(instance_dir):
    os.makedirs(instance_dir)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(instance_dir, 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(basedir, 'static/avatars')
app.config['SECRET_KEY'] = 'Battery-AAA'
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class Inventory(db.Model):
    __tablename__ = 'inventory'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(20), db.ForeignKey('user.id'))
    username = db.Column(db.String(20), nullable=False) 
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'))
    user_obj = db.relationship('User', back_populates='inventory')
    item = db.relationship('Item', back_populates='inventory')

    @property
    def user(self):
        return User.query.filter_by(username=self.username).first()

class AdoptedPet(db.Model):
    __tablename__ = 'adopted_pet'
    adopt_id = db.Column(db.Integer, primary_key=True)
    species = db.Column(db.String(2), db.ForeignKey('pet.species'), nullable=False)
    user_id = db.Column(db.String(20), db.ForeignKey('user.id'))
    username = db.Column(db.String(20), nullable=False) 
    pet = db.relationship('Pet', backref='adopted_by')
    user_obj = db.relationship('User', back_populates='adoptedpet')

    @property
    def user(self):
        return User.query.filter_by(username=self.username).first()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    password = db.Column(db.String(80), nullable=False)
    currency_balance = db.Column(db.Integer, default=1000)
    avatar = db.Column(db.Text, nullable=True)
    profile_pic = db.Column(db.Text, nullable=True)

    inventory = db.relationship('Inventory', back_populates='user_obj')
    adoptedpet = db.relationship('AdoptedPet', back_populates='user_obj')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.currency_balance = 1000

class Topic(db.Model):
    __tablename__ = 'topic'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, unique=True, nullable=False)
    description = db.Column(db.String)
    username = db.Column(db.String(20), nullable=False)

class Comment(db.Model):
    __tablename__ = 'comment'
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String, nullable=False)
    topicId = db.Column(db.Integer, db.ForeignKey('topic.id', ondelete='CASCADE'), nullable=False)
    topic = db.relationship('Topic', backref=db.backref('comments', lazy=True, cascade='all, delete-orphan'))
    username = db.Column(db.String(20), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('comment.id'), nullable=True)
    replies = db.relationship('Comment', backref=db.backref('parent', remote_side=[id]), lazy=True)

    __table_args__ = {'extend_existing': True}

class Pet(db.Model): 
    species = db.Column(db.String(2), primary_key=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    egg_image_url = db.Column(db.String(200), nullable=False)
    pet_image_url = db.Column(db.String(200), nullable=False)

class Item(db.Model): 
    id = db.Column(db.String(2), primary_key=True, nullable=False)
    base_id = db.Column(db.String(10), nullable=False)
    gender = db.Column(db.String(1), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    colour = db.Column(db.String(200), nullable=False)
    filter_colour = db.Column(db.String(500), nullable=False)
    thumbnail_url = db.Column(db.String(200), nullable=False)
    image_url = db.Column(db.String(200), nullable=False)

    inventory = db.relationship('Inventory', back_populates='item')

    @staticmethod
    def get_items_grouped_by_base_id():
        items = db.session.query(Item).all()
        grouped_items = {}
        for item in items:
            if item.base_id not in grouped_items:
                grouped_items[item.base_id] = []
            grouped_items[item.base_id].append(item)
        return grouped_items

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
        else:
            error_message = "Invalid username or password. Please try again."
            return render_template('login.html', form=form, error_message=error_message)
    return render_template('login.html', form=form)

@app.route('/profile')
@login_required
def profile():
    avatar_data = current_user.avatar
    if avatar_data:
        avatar_url = f"data:image/png;base64,{avatar_data}"
    else:
        avatar_url = None

    adopted_pets = db.session.query(AdoptedPet, Pet).join(Pet, AdoptedPet.species == Pet.species).filter(AdoptedPet.username == current_user.username).all()
    inventory_items = db.session.query(Inventory, Item).join(Item, Inventory.item_id == Item.id).filter(Inventory.username == current_user.username).all()

    return render_template('profile.html', avatar_url=avatar_url, inventory_items=inventory_items, adopted_pets=adopted_pets)

@app.route('/custom')
@login_required
def custom():
    user_inventory = [item.item_id for item in Inventory.query.filter_by(user_id=current_user.id).all()]
    grouped_items = Item.get_items_grouped_by_base_id()
    user_grouped_items = {base_id: [item for item in items if item.id in user_inventory] 
                          for base_id, items in grouped_items.items() if any(item.id in user_inventory for item in items)}
    
    return render_template('custom.html', grouped_items=user_grouped_items)

@app.route('/save-avatar', methods=['POST'])
@login_required
def save_avatar():
    data = request.get_json()
    image_data = data['image'].split(',')[1]
    current_user.avatar = image_data
    db.session.commit()
    return jsonify({'success': True, 'avatar_url': url_for('static', filename='avatars/avatar.png')})

@app.route('/crop-avatar')
@login_required
def crop_avatar():
    avatar_data = current_user.avatar
    if avatar_data:
        avatar_url = f"data:image/png;base64,{avatar_data}"
    else:
        avatar_url = None
    return render_template('crop_avatar.html', avatar_url=avatar_url)

@app.route('/save-avatar-cropped', methods=['POST'])
@login_required
def save_avatar_cropped():
    data = request.get_json()
    cropped_image_data = data['croppedImage']
    current_user.profile_pic = cropped_image_data
    db.session.commit()
    print(f"Saved profile_pic for user {current_user.username}: {current_user.profile_pic[:50]}...")  # Debug statement
    return jsonify({'success': True})

@app.route('/store')
@login_required
def store():
    grouped_items = Item.get_items_grouped_by_base_id()
    return render_template('store.html', grouped_items=grouped_items)

@app.route('/purchase_item/<string:item_id>', methods=['POST'])
@login_required
def purchase_item(item_id):
    try:
        item = Item.query.filter_by(id=item_id).first()
        if not item:
            return jsonify({'error': 'Item not found'}), 404

        if current_user.currency_balance < item.price:
            return jsonify({'error': 'Insufficient balance'}), 400

        current_user.currency_balance -= item.price
        db.session.commit()

        inventory = Inventory(user_id=current_user.id, username=current_user.username, item_id=item.id)
        db.session.add(inventory)
        db.session.commit()

        return jsonify({'success': True}), 200
    except Exception as e:
        # Log the exception details
        print(f'Error purchasing item: {e}')
        return jsonify({'error': 'Internal Server Error'}), 500

@app.route('/minigames')
@login_required
def minigames():
    return render_template('minigames.html')

@app.route('/minigames-feeding-time', methods=['GET', 'POST'])
@login_required
def minigamesfeedingtime():
    return render_template('minigames-feeding-time.html')

@app.route('/minigames-jump-jump-jackaloaf', methods=['GET', 'POST'])
@login_required
def minigamesjumpjumpjackaloaf():
    return render_template('minigames-jump-jump-jackaloaf.html')

@app.route('/adopt', methods=['GET', 'POST'])
@login_required
def adopt():
    pets = Pet.query.all()
    return render_template('adopt.html', pets=pets)

@app.route('/adopt_pet/<string:pet_species>', methods=['POST'])
@login_required
def adopt_pet(pet_species):
    pet = Pet.query.filter_by(species=pet_species).first()
    if pet:
        if current_user.currency_balance >= pet.price:
            current_user.currency_balance -= pet.price
            db.session.commit()
            
            adopted_pet = AdoptedPet(species=pet_species, username=current_user.username, user_id=current_user.id)
            db.session.add(adopted_pet)
            db.session.commit()
            return jsonify({'success': True})
    else:
        abort(404) 

@app.route('/forums', methods=['GET', 'POST'])
@login_required
def forums():
    error = None
    if request.method == "POST":
        title = request.form["title"].strip()
        description = request.form["description"].strip()

        if not title or not description:
            error = "Title and description cannot be empty."
        else:
            existing_topic = Topic.query.filter_by(title=title).first()
            if existing_topic:
                error = "Topic already exists."
            else:
                topic = Topic(title=title, description=description, username=current_user.username)
                db.session.add(topic)
                db.session.commit()

    topics = Topic.query.order_by(Topic.id.desc()).all()
    profile_pics = {topic.username: (User.query.filter_by(username=topic.username).first().profile_pic or '') for topic in topics}
    return render_template('forums.html', topics=topics, profile_pics=profile_pics, error=error)

@app.route("/topic/<int:id>", methods=["GET", "POST"])
def topic(id):
    topic = db.session.get(Topic, id)
    if not topic:
        abort(404)

    if request.method == "POST" and current_user.is_authenticated:
        text = request.form["comment"].strip()
        parent_id = request.form["parent_id"]
        
        if text:
            parent_comment = db.session.get(Comment, parent_id) if parent_id else None
            comment = Comment(text=text, topicId=id, username=current_user.username, parent=parent_comment)
            db.session.add(comment)
            db.session.commit()

    comments = Comment.query.filter_by(topicId=id, parent=None).all()
    profile_pics = {comment.username: (User.query.filter_by(username=comment.username).first().profile_pic or '') for comment in comments}
    profile_pics[topic.username] = User.query.filter_by(username=topic.username).first().profile_pic or ''

    return render_template("topic.html", topic=topic, comments=comments, profile_pics=profile_pics)

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
            delete_comment_replies(comment)
            db.session.delete(comment)
            db.session.commit()
            return redirect(url_for('topic', id=comment.topicId))
        else:
            abort(403)
    else:
        abort(404)

def delete_comment_replies(comment):
    for reply in comment.replies:
        delete_comment_replies(reply)
        db.session.delete(reply)

@app.route('/photobooth')
@login_required
def photobooth():
    user_id = current_user.id
    avatar_data = current_user.avatar
    avatar_url = f"data:image/png;base64,{avatar_data}" if avatar_data else None
    adopted_pets = db.session.query(AdoptedPet, Pet).join(Pet, AdoptedPet.species == Pet.species).filter(AdoptedPet.user_id == user_id).all()
    return render_template('photobooth.html', avatar_url=avatar_url, adopted_pets=adopted_pets)

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
        new_user = User(username=form.username.data, password=hashed_password, avatar="static/assets/default_avatar.png")
        db.session.add(new_user)
        try:
            commit_with_retry(db.session)

            default_items = ["H01BLACK-F", "H03BLACK-F", "H04BLACK-F", "H01BLACK-M", "H03BLACK-M", "H04BLACK-M", "U03PURPLE-F", "U04GREEN-F", "U07BLUE-F", "U01PURPLE-M", "U04GREEN-M", "U06BLUE-M", "L02GREY-F", "L03GREEN-F", "L05BLUE-F", "L01GREY-M", "L04GREY-M", "L05BLUE-M"]
            for item_id in default_items:
                item = Item.query.filter_by(id=item_id).first()
                if item:
                    inventory = Inventory(user_id=new_user.id, username=new_user.username, item_id=item.id)
                    db.session.add(inventory)
            
            commit_with_retry(db.session)

            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            return str(e), 500
    if request.method == 'POST' and form.errors:
        error_message = next(iter(form.errors.values()))[0]
        return render_template('register.html', form=form, error_message=error_message)
    return render_template('register.html', form=form)

@app.route('/gifting')
@login_required
def gifting():
    return render_template('gifting.html')

def commit_with_retry(session, retries=5, delay=1):
    for attempt in range(retries):
        try:
            session.commit()
            return
        except OperationalError as e:
            if "database is locked" in str(e):
                time.sleep(delay)
            else:
                raise
    raise Exception("Could not commit after several retries due to database being locked")

def add_items_data():
    items_data = [
        {"id": "H01BLACK-M", "base_id": "H01-M", "gender": "Male", "price": 150, "colour": "#353535", "filter_colour": "grayscale(50%) brightness(40%) saturate(400%)", "thumbnail_url": "/static/assets/thumbnails/hair/m-hair1.png", "image_url": 'assets/customization_assets/hair/m-hair1.png'},
        {"id": "H01BROWN-M", "base_id": "H01-M", "gender": "Male", "price": 250, "colour": "#7F654A", "filter_colour": "sepia(95%) hue-rotate(350deg) brightness(0.7) contrast(140%)", "thumbnail_url": "/static/assets/thumbnails/hair/m-hair1.png", "image_url": 'assets/customization_assets/hair/m-hair1.png'},
        {"id": "H01BLONDE-M", "base_id": "H01-M", "gender": "Male", "price": 350, "colour": "#E8CEA1", "filter_colour": "sepia(100%) brightness(1.3)", "thumbnail_url": "/static/assets/thumbnails/hair/m-hair1.png", "image_url": 'assets/customization_assets/hair/m-hair1.png'},
        
        {"id": "H02BLACK-M", "base_id": "H02-M", "gender": "Male", "price": 150, "colour": "#353535", "filter_colour": "grayscale(50%) brightness(40%) saturate(400%)", "thumbnail_url": "/static/assets/thumbnails/hair/m-hair2.png", "image_url": 'assets/customization_assets/hair/m-hair2.png'},
        {"id": "H02BROWN-M", "base_id": "H02-M", "gender": "Male", "price": 250, "colour": "#7F654A", "filter_colour": "sepia(95%) hue-rotate(350deg) brightness(0.7) contrast(140%)", "thumbnail_url": "/static/assets/thumbnails/hair/m-hair2.png", "image_url": 'assets/customization_assets/hair/m-hair2.png'},
        {"id": "H02BLONDE-M", "base_id": "H02-M", "gender": "Male", "price": 350, "colour": "#E8CEA1", "filter_colour": "sepia(100%) brightness(1.3)", "thumbnail_url": "/static/assets/thumbnails/hair/m-hair2.png", "image_url": 'assets/customization_assets/hair/m-hair2.png'},

        {"id": "H03BLACK-M", "base_id": "H03-M", "gender": "Male", "price": 150, "colour": "#353535", "filter_colour": "grayscale(50%) brightness(40%) saturate(400%)", "thumbnail_url": "/static/assets/thumbnails/hair/m-hair3.png", "image_url": 'assets/customization_assets/hair/m-hair3.png'},
        {"id": "H03BROWN-M", "base_id": "H03-M", "gender": "Male", "price": 250, "colour": "#7F654A", "filter_colour": "sepia(95%) hue-rotate(350deg) brightness(0.7) contrast(140%)", "thumbnail_url": "/static/assets/thumbnails/hair/m-hair3.png", "image_url": 'assets/customization_assets/hair/m-hair3.png'},
        {"id": "H03BLONDE-M", "base_id": "H03-M", "gender": "Male", "price": 350, "colour": "#E8CEA1", "filter_colour": "sepia(100%) brightness(1.3)", "thumbnail_url": "/static/assets/thumbnails/hair/m-hair3.png", "image_url": 'assets/customization_assets/hair/m-hair3.png'},
        
        {"id": "H04BLACK-M", "base_id": "H04-M", "gender": "Male", "price": 150, "colour": "#353535", "filter_colour": "grayscale(50%) brightness(40%) saturate(400%)", "thumbnail_url": "/static/assets/thumbnails/hair/m-hair4.png", "image_url": 'assets/customization_assets/hair/m-hair4.png'},
        {"id": "H04BROWN-M", "base_id": "H04-M", "gender": "Male", "price": 250, "colour": "#7F654A", "filter_colour": "sepia(95%) hue-rotate(350deg) brightness(0.7) contrast(140%)", "thumbnail_url": "/static/assets/thumbnails/hair/m-hair4.png", "image_url": 'assets/customization_assets/hair/m-hair4.png'},
        {"id": "H04BLONDE-M", "base_id": "H04-M", "gender": "Male", "price": 350, "colour": "#E8CEA1", "filter_colour": "sepia(100%) brightness(1.3)", "thumbnail_url": "/static/assets/thumbnails/hair/m-hair4.png", "image_url": 'assets/customization_assets/hair/m-hair4.png'},

        {"id": "H01BLACK-F", "base_id": "H01-F", "gender": "Female", "price": 150, "colour": "#353535", "filter_colour": "grayscale(50%) brightness(40%) saturate(400%)", "thumbnail_url": "/static/assets/thumbnails/hair/f-hair1.png", "image_url": 'assets/customization_assets/hair/f-hair1.png'},
        {"id": "H01BROWN-F", "base_id": "H01-F", "gender": "Female", "price": 250, "colour": "#7F654A", "filter_colour": "sepia(95%) hue-rotate(350deg) brightness(0.7) contrast(140%)", "thumbnail_url": "/static/assets/thumbnails/hair/f-hair1.png", "image_url": 'assets/customization_assets/hair/f-hair1.png'},
        {"id": "H01BLONDE-F", "base_id": "H01-F", "gender": "Female", "price": 350, "colour": "#E8CEA1", "filter_colour": "sepia(100%) brightness(1.3)", "thumbnail_url": "/static/assets/thumbnails/hair/f-hair1.png", "image_url": 'assets/customization_assets/hair/f-hair1.png'},
        
        {"id": "H02BLUE-F", "base_id": "H02-F", "gender": "Female", "price": 150, "colour": "#59CFB5", "filter_colour": "", "thumbnail_url": "/static/assets/thumbnails/hair/f-hair2.png", "image_url": 'assets/customization_assets/hair/f-hair2.png'},
        {"id": "H02GREEN-F", "base_id": "H02-F", "gender": "Female", "price": 250, "colour": "#86CA66", "filter_colour": "hue-rotate(300deg)", "thumbnail_url": "/static/assets/thumbnails/hair/f-hair2.png", "image_url": 'assets/customization_assets/hair/f-hair2.png'},
        {"id": "H02PINK-F", "base_id": "H02-F", "gender": "Female", "price": 350, "colour": "#FF9BA3", "filter_colour": "hue-rotate(190deg)", "thumbnail_url": "/static/assets/thumbnails/hair/f-hair2.png", "image_url": 'assets/customization_assets/hair/f-hair2.png'},
        
        {"id": "H03BLACK-F", "base_id": "H03-F", "gender": "Female", "price": 150, "colour": "#353535", "filter_colour": "grayscale(50%) brightness(40%) saturate(400%)", "thumbnail_url": "/static/assets/thumbnails/hair/f-hair3.png", "image_url": 'assets/customization_assets/hair/f-hair3.png'},
        {"id": "H03BROWN-F", "base_id": "H03-F", "gender": "Female", "price": 250, "colour": "#7F654A", "filter_colour": "sepia(95%) hue-rotate(350deg) brightness(0.7) contrast(140%)", "thumbnail_url": "/static/assets/thumbnails/hair/f-hair3.png", "image_url": 'assets/customization_assets/hair/f-hair3.png'},
        {"id": "H03BLONDE-F", "base_id": "H03-F", "gender": "Female", "price": 350, "colour": "#E8CEA1", "filter_colour": "sepia(100%) brightness(1.3)", "thumbnail_url": "/static/assets/thumbnails/hair/f-hair3.png", "image_url": 'assets/customization_assets/hair/f-hair3.png'},
        
        {"id": "H04BLACK-F", "base_id": "H04-F", "gender": "Female", "price": 150, "colour": "#353535", "filter_colour": "grayscale(50%) brightness(40%) saturate(400%)", "thumbnail_url": "/static/assets/thumbnails/hair/f-hair4.png", "image_url": 'assets/customization_assets/hair/f-hair4.png'},
        {"id": "H04BROWN-F", "base_id": "H04-F", "gender": "Female", "price": 250, "colour": "#7F654A", "filter_colour": "sepia(95%) hue-rotate(350deg) brightness(0.7) contrast(140%)", "thumbnail_url": "/static/assets/thumbnails/hair/f-hair4.png", "image_url": 'assets/customization_assets/hair/f-hair4.png'},
        {"id": "H04BLONDE-F", "base_id": "H04-F", "gender": "Female", "price": 350, "colour": "#E8CEA1", "filter_colour": "sepia(100%) brightness(1.3)", "thumbnail_url": "/static/assets/thumbnails/hair/f-hair4.png", "image_url": 'assets/customization_assets/hair/f-hair4.png'},

        {"id": "H05PURPLE-F", "base_id": "H05-F", "gender": "Female", "price": 150, "colour": "#3F5494", "filter_colour": "", "thumbnail_url": "/static/assets/thumbnails/hair/f-hair5.png", "image_url": 'assets/customization_assets/hair/f-hair5.png'},
        {"id": "H05GREY-F", "base_id": "H05-F", "gender": "Female", "price": 250, "colour": "#545454", "filter_colour": "grayscale(100%)", "thumbnail_url": "/static/assets/thumbnails/hair/f-hair5.png", "image_url": 'assets/customization_assets/hair/f-hair5.png'},
        {"id": "H05PINK-F", "base_id": "H05-F", "gender": "Female", "price": 350, "colour": "#E4A7BA", "filter_colour": "sepia(95%) hue-rotate(300deg) brightness(1.3)", "thumbnail_url": "/static/assets/thumbnails/hair/f-hair5.png", "image_url": 'assets/customization_assets/hair/f-hair5.png'},

        {"id": "H06PGREY-F", "base_id": "H06-F", "gender": "Female", "price": 50, "colour": "#848484", "filter_colour": "", "thumbnail_url": "/static/assets/thumbnails/hair/f-hair6.png", "image_url": 'assets/customization_assets/hair/f-hair6.png'},
        {"id": "H06PURPLE-F", "base_id": "H06-F", "gender": "Female", "price": 150, "colour": "#b796c2", "filter_colour": "saturate(100%) sepia(100%) hue-rotate(240deg)", "thumbnail_url": "/static/assets/thumbnails/hair/f-hair6.png", "image_url": 'assets/customization_assets/hair/f-hair6.png'},
        {"id": "H06BLUE-F", "base_id": "H06-F", "gender": "Female", "price": 250, "colour": "#79c7d9", "filter_colour": "saturate(100%) sepia(100%) hue-rotate(150deg)", "thumbnail_url": "/static/assets/thumbnails/hair/f-hair6.png", "image_url": 'assets/customization_assets/hair/f-hair6.png'},
        {"id": "H06GREEN-F", "base_id": "H06-F", "gender": "Female", "price": 350, "colour": "#8aab7f", "filter_colour": "saturate(100%) sepia(100%) hue-rotate(60deg)", "thumbnail_url": "/static/assets/thumbnails/hair/f-hair6.png", "image_url": 'assets/customization_assets/hair/f-hair6.png'},

        {"id": "U01PURPLE-M", "base_id": "U01-M", "gender": "Male", "price": 150, "colour": "#b796c2", "filter_colour": "saturate(100%) sepia(100%) hue-rotate(240deg)", "thumbnail_url": "/static/assets/thumbnails/shirt/m-shirt1.png", "image_url": 'assets/customization_assets/shirt/m-shirt1.png'},
        {"id": "U01BLUE-M", "base_id": "U01-M", "gender": "Male", "price": 250, "colour": "#79c7d9", "filter_colour": "saturate(100%) sepia(100%) hue-rotate(150deg)", "thumbnail_url": "/static/assets/thumbnails/shirt/m-shirt1.png", "image_url": 'assets/customization_assets/shirt/m-shirt1.png'},
        {"id": "U01GREEN-M", "base_id": "U01-M", "gender": "Male", "price": 350, "colour": "#8aab7f", "filter_colour": "saturate(100%) sepia(100%) hue-rotate(60deg)", "thumbnail_url": "/static/assets/thumbnails/shirt/m-shirt1.png", "image_url": 'assets/customization_assets/shirt/m-shirt1.png'},

        {"id": "U02BLUE-M", "base_id": "U02-M", "gender": "Male", "price": 150, "colour": "#3D5591", "filter_colour": "", "thumbnail_url": "/static/assets/thumbnails/shirt/m-shirt2.png", "image_url": 'assets/customization_assets/shirt/m-shirt2.png'},
        {"id": "U02GREEN-M", "base_id": "U02-M", "gender": "Male", "price": 250, "colour": "#14665F", "filter_colour": "hue-rotate(300deg)", "thumbnail_url": "/static/assets/thumbnails/shirt/m-shirt2.png", "image_url": 'assets/customization_assets/shirt/m-shirt2.png'},
        {"id": "U02BROWN-M", "base_id": "U02-M", "gender": "Male", "price": 350, "colour": "#605714", "filter_colour": "hue-rotate(190deg)", "thumbnail_url": "/static/assets/thumbnails/shirt/m-shirt2.png", "image_url": 'assets/customization_assets/shirt/m-shirt2.png'},

        {"id": "U03PURPLE-M", "base_id": "U03-M", "gender": "Male", "price": 150, "colour": "#b796c2", "filter_colour": "saturate(100%) sepia(100%) hue-rotate(240deg)", "thumbnail_url": "/static/assets/thumbnails/shirt/m-shirt3.png", "image_url": 'assets/customization_assets/shirt/m-shirt3.png'},
        {"id": "U03BLUE-M", "base_id": "U03-M", "gender": "Male", "price": 250, "colour": "#79c7d9", "filter_colour": "saturate(100%) sepia(100%) hue-rotate(150deg)", "thumbnail_url": "/static/assets/thumbnails/shirt/m-shirt3.png", "image_url": 'assets/customization_assets/shirt/m-shirt3.png'},
        {"id": "U03GREEN-M", "base_id": "U03-M", "gender": "Male", "price": 350, "colour": "#8aab7f", "filter_colour": "saturate(100%) sepia(100%) hue-rotate(60deg)", "thumbnail_url": "/static/assets/thumbnails/shirt/m-shirt3.png", "image_url": 'assets/customization_assets/shirt/m-shirt3.png'},

        {"id": "U04PURPLE-M", "base_id": "U04-M", "gender": "Male", "price": 150, "colour": "#b796c2", "filter_colour": "saturate(100%) sepia(100%) hue-rotate(240deg)", "thumbnail_url": "/static/assets/thumbnails/shirt/m-shirt4.png", "image_url": 'assets/customization_assets/shirt/m-shirt4.png'},
        {"id": "U04BLUE-M", "base_id": "U04-M", "gender": "Male", "price": 250, "colour": "#79c7d9", "filter_colour": "saturate(100%) sepia(100%) hue-rotate(150deg)", "thumbnail_url": "/static/assets/thumbnails/shirt/m-shirt4.png", "image_url": 'assets/customization_assets/shirt/m-shirt4.png'},
        {"id": "U04GREEN-M", "base_id": "U04-M", "gender": "Male", "price": 350, "colour": "#8aab7f", "filter_colour": "saturate(100%) sepia(100%) hue-rotate(60deg)", "thumbnail_url": "/static/assets/thumbnails/shirt/m-shirt4.png", "image_url": 'assets/customization_assets/shirt/m-shirt4.png'},

        {"id": "U05PURPLE-M", "base_id": "U05-M", "gender": "Male", "price": 150, "colour": "#b796c2", "filter_colour": "saturate(100%) sepia(100%) hue-rotate(240deg)", "thumbnail_url": "/static/assets/thumbnails/shirt/m-shirt5.png", "image_url": 'assets/customization_assets/shirt/m-shirt5.png'},
        {"id": "U05BLUE-M", "base_id": "U05-M", "gender": "Male", "price": 250, "colour": "#79c7d9", "filter_colour": "saturate(100%) sepia(100%) hue-rotate(150deg)", "thumbnail_url": "/static/assets/thumbnails/shirt/m-shirt5.png", "image_url": 'assets/customization_assets/shirt/m-shirt5.png'},
        {"id": "U05GREEN-M", "base_id": "U05-M", "gender": "Male", "price": 350, "colour": "#8aab7f", "filter_colour": "saturate(100%) sepia(100%) hue-rotate(60deg)", "thumbnail_url": "/static/assets/thumbnails/shirt/m-shirt5.png", "image_url": 'assets/customization_assets/shirt/m-shirt5.png'},

        {"id": "U06PURPLE-M", "base_id": "U06-M", "gender": "Male", "price": 150, "colour": "#b796c2", "filter_colour": "saturate(100%) sepia(100%) hue-rotate(240deg)", "thumbnail_url": "/static/assets/thumbnails/shirt/m-shirt6.png", "image_url": 'assets/customization_assets/shirt/m-shirt6.png'},
        {"id": "U06BLUE-M", "base_id": "U06-M", "gender": "Male", "price": 250, "colour": "#79c7d9", "filter_colour": "saturate(100%) sepia(100%) hue-rotate(150deg)", "thumbnail_url": "/static/assets/thumbnails/shirt/m-shirt6.png", "image_url": 'assets/customization_assets/shirt/m-shirt6.png'},
        {"id": "U06GREEN-M", "base_id": "U06-M", "gender": "Male", "price": 350, "colour": "#8aab7f", "filter_colour": "saturate(100%) sepia(100%) hue-rotate(60deg)", "thumbnail_url": "/static/assets/thumbnails/shirt/m-shirt6.png", "image_url": 'assets/customization_assets/shirt/m-shirt6.png'},

        {"id": "U01PURPLE-F", "base_id": "U01-F", "gender": "Female", "price": 150, "colour": "#b796c2", "filter_colour": "saturate(100%) sepia(100%) hue-rotate(240deg)", "thumbnail_url": "/static/assets/thumbnails/shirt/f-shirt1.png", "image_url": 'assets/customization_assets/shirt/f-shirt1.png'},
        {"id": "U01BLUE-F", "base_id": "U01-F", "gender": "Female", "price": 250, "colour": "#79c7d9", "filter_colour": "saturate(100%) sepia(100%) hue-rotate(150deg)", "thumbnail_url": "/static/assets/thumbnails/shirt/f-shirt1.png", "image_url": 'assets/customization_assets/shirt/f-shirt1.png'},
        {"id": "U01GREEN-F", "base_id": "U01-F", "gender": "Female", "price": 350, "colour": "#8aab7f", "filter_colour": "saturate(100%) sepia(100%) hue-rotate(60deg)", "thumbnail_url": "/static/assets/thumbnails/shirt/f-shirt1.png", "image_url": 'assets/customization_assets/shirt/f-shirt1.png'},
        
        {"id": "U02BLUE-F", "base_id": "U02-F", "gender": "Female", "price": 150, "colour": "#59CFB5", "filter_colour": "", "thumbnail_url": "/static/assets/thumbnails/shirt/f-shirt2.png", "image_url": 'assets/customization_assets/shirt/f-shirt2.png'},
        {"id": "U02GREEN-F", "base_id": "U02-F", "gender": "Female", "price": 250, "colour": "#7de877", "filter_colour": "hue-rotate(300deg)", "thumbnail_url": "/static/assets/thumbnails/shirt/f-shirt2.png", "image_url": 'assets/customization_assets/shirt/f-shirt2.png'},
        {"id": "U02PINK-F", "base_id": "U02-F", "gender": "Female", "price": 350, "colour": "#FF9BA3", "filter_colour": "hue-rotate(190deg)", "thumbnail_url": "/static/assets/thumbnails/shirt/f-shirt2.png", "image_url": 'assets/customization_assets/shirt/f-shirt2.png'},

        {"id": "U03PURPLE-F", "base_id": "U03-F", "gender": "Female", "price": 150, "colour": "#b796c2", "filter_colour": "saturate(100%) sepia(100%) hue-rotate(240deg)", "thumbnail_url": "/static/assets/thumbnails/shirt/f-shirt3.png", "image_url": 'assets/customization_assets/shirt/f-shirt3.png'},
        {"id": "U03BLUE-F", "base_id": "U03-F", "gender": "Female", "price": 250, "colour": "#79c7d9", "filter_colour": "saturate(100%) sepia(100%) hue-rotate(150deg)", "thumbnail_url": "/static/assets/thumbnails/shirt/f-shirt3.png", "image_url": 'assets/customization_assets/shirt/f-shirt3.png'},
        {"id": "U03GREEN-F", "base_id": "U03-F", "gender": "Female", "price": 350, "colour": "#8aab7f", "filter_colour": "saturate(100%) sepia(100%) hue-rotate(60deg)", "thumbnail_url": "/static/assets/thumbnails/shirt/f-shirt3.png", "image_url": 'assets/customization_assets/shirt/f-shirt3.png'},

        {"id": "U04PURPLE-F", "base_id": "U04-F", "gender": "Female", "price": 150, "colour": "#b796c2", "filter_colour": "saturate(100%) sepia(100%) hue-rotate(240deg)", "thumbnail_url": "/static/assets/thumbnails/shirt/f-shirt4.png", "image_url": 'assets/customization_assets/shirt/f-shirt4.png'},
        {"id": "U04BLUE-F", "base_id": "U04-F", "gender": "Female", "price": 250, "colour": "#79c7d9", "filter_colour": "saturate(100%) sepia(100%) hue-rotate(150deg)", "thumbnail_url": "/static/assets/thumbnails/shirt/f-shirt4.png", "image_url": 'assets/customization_assets/shirt/f-shirt4.png'},
        {"id": "U04GREEN-F", "base_id": "U04-F", "gender": "Female", "price": 350, "colour": "#8aab7f", "filter_colour": "saturate(100%) sepia(100%) hue-rotate(60deg)", "thumbnail_url": "/static/assets/thumbnails/shirt/f-shirt4.png", "image_url": 'assets/customization_assets/shirt/f-shirt4.png'},

        {"id": "U05PURPLE-F", "base_id": "U05-F", "gender": "Female", "price": 150, "colour": "#b796c2", "filter_colour": "saturate(100%) sepia(100%) hue-rotate(240deg)", "thumbnail_url": "/static/assets/thumbnails/shirt/f-shirt5.png", "image_url": 'assets/customization_assets/shirt/f-shirt5.png'},
        {"id": "U05BLUE-F", "base_id": "U05-F", "gender": "Female", "price": 250, "colour": "#79c7d9", "filter_colour": "saturate(100%) sepia(100%) hue-rotate(150deg)", "thumbnail_url": "/static/assets/thumbnails/shirt/f-shirt5.png", "image_url": 'assets/customization_assets/shirt/f-shirt5.png'},
        {"id": "U05GREEN-F", "base_id": "U05-F", "gender": "Female", "price": 350, "colour": "#8aab7f", "filter_colour": "saturate(100%) sepia(100%) hue-rotate(60deg)", "thumbnail_url": "/static/assets/thumbnails/shirt/f-shirt5.png", "image_url": 'assets/customization_assets/shirt/f-shirt5.png'},

        {"id": "U06PURPLE-F", "base_id": "U06-F", "gender": "Female", "price": 150, "colour": "#98547F", "filter_colour": "", "thumbnail_url": "/static/assets/thumbnails/shirt/f-shirt6.png", "image_url": 'assets/customization_assets/shirt/f-shirt6.png'},
        {"id": "U06GREY-F", "base_id": "U06-F", "gender": "Female", "price": 250, "colour": "#545454", "filter_colour": "grayscale(100%)", "thumbnail_url": "/static/assets/thumbnails/shirt/f-shirt6.png", "image_url": 'assets/customization_assets/shirt/f-shirt6.png'},
        {"id": "U06PINK-F", "base_id": "U06-F", "gender": "Female", "price": 350, "colour": "#E4A7BA", "filter_colour": "sepia(95%) hue-rotate(300deg) brightness(1.3)", "thumbnail_url": "/static/assets/thumbnails/shirt/f-shirt6.png", "image_url": 'assets/customization_assets/shirt/f-shirt6.png'},

        {"id": "U07PURPLE-F", "base_id": "U07-F", "gender": "Female", "price": 150, "colour": "#b796c2", "filter_colour": "saturate(100%) sepia(100%) hue-rotate(240deg)", "thumbnail_url": "/static/assets/thumbnails/shirt/f-shirt7.png", "image_url": 'assets/customization_assets/shirt/f-shirt7.png'},
        {"id": "U07BLUE-F", "base_id": "U07-F", "gender": "Female", "price": 250, "colour": "#79c7d9", "filter_colour": "saturate(100%) sepia(100%) hue-rotate(150deg)", "thumbnail_url": "/static/assets/thumbnails/shirt/f-shirt7.png", "image_url": 'assets/customization_assets/shirt/f-shirt7.png'},
        {"id": "U07GREEN-F", "base_id": "U07-F", "gender": "Female", "price": 350, "colour": "#8aab7f", "filter_colour": "saturate(100%) sepia(100%) hue-rotate(60deg)", "thumbnail_url": "/static/assets/thumbnails/shirt/f-shirt7.png", "image_url": 'assets/customization_assets/shirt/f-shirt7.png'},

        {"id": "L01GREY-M", "base_id": "L01-M", "gender": "Male", "price": 150, "colour": "#848484", "filter_colour": "", "thumbnail_url": "/static/assets/thumbnails/pants/m-pants1.png", "image_url": 'assets/customization_assets/pants/m-pants1.png'},
        {"id": "L01BLUE-M", "base_id": "L01-M", "gender": "Male", "price": 250, "colour": "#79c7d9", "filter_colour": "saturate(100%) sepia(100%) hue-rotate(150deg)", "thumbnail_url": "/static/assets/thumbnails/pants/m-pants1.png", "image_url": 'assets/customization_assets/pants/m-pants1.png'},
        {"id": "L01GREEN-M", "base_id": "L01-M", "gender": "Male", "price": 350, "colour": "#8aab7f", "filter_colour": "saturate(100%) sepia(100%) hue-rotate(60deg)", "thumbnail_url": "/static/assets/thumbnails/pants/m-pants1.png", "image_url": 'assets/customization_assets/pants/m-pants1.png'},

        {"id": "L02GREY-M", "base_id": "L02-M", "gender": "Male", "price": 150, "colour": "#848484", "filter_colour": "", "thumbnail_url": "/static/assets/thumbnails/pants/m-pants2.png", "image_url": 'assets/customization_assets/pants/m-pants2.png'},
        {"id": "L02BLUE-M", "base_id": "L02-M", "gender": "Male", "price": 250, "colour": "#79c7d9", "filter_colour": "saturate(100%) sepia(100%) hue-rotate(150deg)", "thumbnail_url": "/static/assets/thumbnails/pants/m-pants2.png", "image_url": 'assets/customization_assets/pants/m-pants2.png'},
        {"id": "L02GREEN-M", "base_id": "L02-M", "gender": "Male", "price": 350, "colour": "#8aab7f", "filter_colour": "saturate(100%) sepia(100%) hue-rotate(60deg)", "thumbnail_url": "/static/assets/thumbnails/pants/m-pants2.png", "image_url": 'assets/customization_assets/pants/m-pants2.png'},

        {"id": "L03BLUE-M", "base_id": "L03-M", "gender": "Male", "price": 150, "colour": "#3D5591", "filter_colour": "", "thumbnail_url": "/static/assets/thumbnails/pants/m-pants3.png", "image_url": 'assets/customization_assets/pants/m-pants3.png'},
        {"id": "L03GREEN-M", "base_id": "L03-M", "gender": "Male", "price": 250, "colour": "#14665F", "filter_colour": "hue-rotate(300deg)", "thumbnail_url": "/static/assets/thumbnails/pants/m-pants3.png", "image_url": 'assets/customization_assets/pants/m-pants3.png'},
        {"id": "L03BROWN-M", "base_id": "L03-M", "gender": "Male", "price": 350, "colour": "#605714", "filter_colour": "hue-rotate(190deg)", "thumbnail_url": "/static/assets/thumbnails/pants/m-pants3.png", "image_url": 'assets/customization_assets/pants/m-pants3.png'},

        {"id": "L04GREY-M", "base_id": "L04-M", "gender": "Male", "price": 150, "colour": "#848484", "filter_colour": "", "thumbnail_url": "/static/assets/thumbnails/pants/m-pants4.png", "image_url": 'assets/customization_assets/pants/m-pants4.png'},
        {"id": "L04BLUE-M", "base_id": "L04-M", "gender": "Male", "price": 250, "colour": "#79c7d9", "filter_colour": "saturate(100%) sepia(100%) hue-rotate(150deg)", "thumbnail_url": "/static/assets/thumbnails/pants/m-pants4.png", "image_url": 'assets/customization_assets/pants/m-pants4.png'},
        {"id": "L04GREEN-M", "base_id": "L04-M", "gender": "Male", "price": 350, "colour": "#8aab7f", "filter_colour": "saturate(100%) sepia(100%) hue-rotate(60deg)", "thumbnail_url": "/static/assets/thumbnails/pants/m-pants4.png", "image_url": 'assets/customization_assets/pants/m-pants4.png'},

        {"id": "L05GREY-M", "base_id": "L05-M", "gender": "Male", "price": 150, "colour": "#848484", "filter_colour": "", "thumbnail_url": "/static/assets/thumbnails/pants/m-pants5.png", "image_url": 'assets/customization_assets/pants/m-pants5.png'},
        {"id": "L05BLUE-M", "base_id": "L05-M", "gender": "Male", "price": 250, "colour": "#79c7d9", "filter_colour": "saturate(100%) sepia(100%) hue-rotate(150deg)", "thumbnail_url": "/static/assets/thumbnails/pants/m-pants5.png", "image_url": 'assets/customization_assets/pants/m-pants5.png'},
        {"id": "L05GREEN-M", "base_id": "L05-M", "gender": "Male", "price": 350, "colour": "#8aab7f", "filter_colour": "saturate(100%) sepia(100%) hue-rotate(60deg)", "thumbnail_url": "/static/assets/thumbnails/pants/m-pants5.png", "image_url": 'assets/customization_assets/pants/m-pants5.png'},

        {"id": "L01BLUE-F", "base_id": "L01-F", "gender": "Female", "price": 150, "colour": "#59CFB5", "filter_colour": "", "thumbnail_url": "/static/assets/thumbnails/pants/f-pants1.png", "image_url": 'assets/customization_assets/pants/f-pants1.png'},
        {"id": "L01GREEN-F", "base_id": "L01-F", "gender": "Female", "price": 250, "colour": "#7de877", "filter_colour": "hue-rotate(300deg)", "thumbnail_url": "/static/assets/thumbnails/pants/f-pants1.png", "image_url": 'assets/customization_assets/pants/f-pants1.png'},
        {"id": "L01PINK-F", "base_id": "L01-F", "gender": "Female", "price": 350, "colour": "#FF9BA3", "filter_colour": "hue-rotate(190deg)", "thumbnail_url": "/static/assets/thumbnails/pants/f-pants1.png", "image_url": 'assets/customization_assets/pants/f-pants1.png'},

        {"id": "L02GREY-F", "base_id": "L02-F", "gender": "Female", "price": 150, "colour": "#848484", "filter_colour": "", "thumbnail_url": "/static/assets/thumbnails/pants/f-pants2.png", "image_url": 'assets/customization_assets/pants/f-pants2.png'},
        {"id": "L02BLUE-F", "base_id": "L02-F", "gender": "Female", "price": 250, "colour": "#79c7d9", "filter_colour": "saturate(100%) sepia(100%) hue-rotate(150deg)", "thumbnail_url": "/static/assets/thumbnails/pants/f-pants2.png", "image_url": 'assets/customization_assets/pants/f-pants2.png'},
        {"id": "L02GREEN-F", "base_id": "L02-F", "gender": "Female", "price": 350, "colour": "#8aab7f", "filter_colour": "saturate(100%) sepia(100%) hue-rotate(60deg)", "thumbnail_url": "/static/assets/thumbnails/pants/f-pants2.png", "image_url": 'assets/customization_assets/pants/f-pants2.png'},
    
        {"id": "L03GREY-F", "base_id": "L03-F", "gender": "Female", "price": 150, "colour": "#848484", "filter_colour": "", "thumbnail_url": "/static/assets/thumbnails/pants/f-pants3.png", "image_url": 'assets/customization_assets/pants/f-pants3.png'},
        {"id": "L03BLUE-F", "base_id": "L03-F", "gender": "Female", "price": 250, "colour": "#79c7d9", "filter_colour": "saturate(100%) sepia(100%) hue-rotate(150deg)", "thumbnail_url": "/static/assets/thumbnails/pants/f-pants3.png", "image_url": 'assets/customization_assets/pants/f-pants3.png'},
        {"id": "L03GREEN-F", "base_id": "L03-F", "gender": "Female", "price": 350, "colour": "#8aab7f", "filter_colour": "saturate(100%) sepia(100%) hue-rotate(60deg)", "thumbnail_url": "/static/assets/thumbnails/pants/f-pants3.png", "image_url": 'assets/customization_assets/pants/f-pants3.png'},

        {"id": "L04PURPLE-F", "base_id": "L04-F", "gender": "Female", "price": 150, "colour": "#98547F", "filter_colour": "", "thumbnail_url": "/static/assets/thumbnails/pants/f-pants4.png", "image_url": 'assets/customization_assets/pants/f-pants4.png'},
        {"id": "L04GREY-F", "base_id": "L04-F", "gender": "Female", "price": 250, "colour": "#545454", "filter_colour": "grayscale(100%)", "thumbnail_url": "/static/assets/thumbnails/pants/f-pants4.png", "image_url": 'assets/customization_assets/pants/f-pants4.png'},
        {"id": "L04PINK-F", "base_id": "L04-F", "gender": "Female", "price": 350, "colour": "#E4A7BA", "filter_colour": "sepia(95%) hue-rotate(300deg) brightness(1.3)", "thumbnail_url": "/static/assets/thumbnails/pants/f-pants4.png", "image_url": 'assets/customization_assets/pants/f-pants4.png'},

        {"id": "L05GREY-F", "base_id": "L05-F", "gender": "Female", "price": 150, "colour": "#848484", "filter_colour": "", "thumbnail_url": "/static/assets/thumbnails/pants/f-pants5.png", "image_url": 'assets/customization_assets/pants/f-pants5.png'},
        {"id": "L05BLUE-F", "base_id": "L05-F", "gender": "Female", "price": 250, "colour": "#79c7d9", "filter_colour": "saturate(100%) sepia(100%) hue-rotate(150deg)", "thumbnail_url": "/static/assets/thumbnails/pants/f-pants5.png", "image_url": 'assets/customization_assets/pants/f-pants5.png'},
        {"id": "L05GREEN-F", "base_id": "L05-F", "gender": "Female", "price": 350, "colour": "#8aab7f", "filter_colour": "saturate(100%) sepia(100%) hue-rotate(60deg)", "thumbnail_url": "/static/assets/thumbnails/pants/f-pants5.png", "image_url": 'assets/customization_assets/pants/f-pants5.png'},

        {"id": "F01BLACK-M", "base_id": "F01-M", "gender": "Male", "price": 150, "colour": "#494a4c", "filter_colour": "", "thumbnail_url": "/static/assets/thumbnails/shoes/m-shoes1.png", "image_url": 'assets/customization_assets/shoes/m-shoes1.png'},
        {"id": "F01BROWN-M", "base_id": "F01-M", "gender": "Male", "price": 250, "colour": "#85775c", "filter_colour": "sepia(105%)", "thumbnail_url": "/static/assets/thumbnails/shoes/m-shoes1.png", "image_url": 'assets/customization_assets/shoes/m-shoes1.png'},
        {"id": "F01LIGHTBROWN-M", "base_id": "F01-M", "gender": "Male", "price": 350, "colour": "#a27e67", "filter_colour": "sepia(95%) hue-rotate(340deg) brightness(1.1) contrast(140%)", "thumbnail_url": "/static/assets/thumbnails/shoes/m-shoes1.png", "image_url": 'assets/customization_assets/shoes/m-shoes1.png'},

        {"id": "F01BLUE-F", "base_id": "F01-F", "gender": "Female", "price": 150, "colour": "#59CFB5", "filter_colour": "", "thumbnail_url": "/static/assets/thumbnails/shoes/f-shoes1.png", "image_url": 'assets/customization_assets/sshoes/f-shoes1.png'},
        {"id": "F01GREEN-F", "base_id": "F01-F", "gender": "Female", "price": 250, "colour": "#7de877", "filter_colour": "hue-rotate(300deg)", "thumbnail_url": "/static/assets/thumbnails/shoes/f-shoes1.png", "image_url": 'assets/customization_assets/shoes/f-shoes1.png'},
        {"id": "F01PINK-F", "base_id": "F01-F", "gender": "Female", "price": 350, "colour": "#FF9BA3", "filter_colour": "hue-rotate(190deg)", "thumbnail_url": "/static/assets/thumbnails/shoes/f-shoes1.png", "image_url": 'assets/customization_assets/shoes/f-shoes1.png'},

        {"id": "F02BLUE-F", "base_id": "F02-F", "gender": "Female", "price": 150, "colour": "#3F5494", "filter_colour": "", "thumbnail_url": "/static/assets/thumbnails/shoes/f-shoes2.png", "image_url": 'assets/customization_assets/shoes/f-shoes2.png'},
        {"id": "F02GREY-F", "base_id": "F02-F", "gender": "Female", "price": 250, "colour": "#545454", "filter_colour": "grayscale(100%)", "thumbnail_url": "/static/assets/thumbnails/shoes/f-shoes2.png", "image_url": 'assets/customization_assets/shoes/f-shoes2.png'},
        {"id": "F02PINK-F", "base_id": "F02-F", "gender": "Female", "price": 350, "colour": "#E4A7BA", "filter_colour": "sepia(95%) hue-rotate(300deg) brightness(1.3)", "thumbnail_url": "/static/assets/thumbnails/shoes/f-shoes2.png", "image_url": 'assets/customization_assets/shoes/f-shoes2.png'},
    
        {"id": "M01GREY-M", "base_id": "M01-M", "gender": "Male", "price": 150, "colour": "#848484", "filter_colour": "", "thumbnail_url": "/static/assets/thumbnails/misc/m-misc1.png", "image_url": 'assets/customization_assets/misc/m-misc1.png'},
        {"id": "M01BLUE-M", "base_id": "M01-M", "gender": "Male", "price": 250, "colour": "#79c7d9", "filter_colour": "saturate(100%) sepia(100%) hue-rotate(150deg)", "thumbnail_url": "/static/assets/thumbnails/misc/m-misc1.png", "image_url": 'assets/customization_assets/misc/m-misc1.png'},
        {"id": "M01GREEN-M", "base_id": "M01-M", "gender": "Male", "price": 350, "colour": "#8aab7f", "filter_colour": "saturate(100%) sepia(100%) hue-rotate(60deg)", "thumbnail_url": "/static/assets/thumbnails/misc/m-misc1.png", "image_url": 'assets/customization_assets/misc/m-misc1.png'},

        {"id": "M02GREY-M", "base_id": "M02-M", "gender": "Male", "price": 150, "colour": "#848484", "filter_colour": "", "thumbnail_url": "/static/assets/thumbnails/misc/m-misc2.png", "image_url": 'assets/customization_assets/misc/m-misc2.png'},
        {"id": "M02BLUE-M", "base_id": "M02-M", "gender": "Male", "price": 250, "colour": "#79c7d9", "filter_colour": "saturate(100%) sepia(100%) hue-rotate(150deg)", "thumbnail_url": "/static/assets/thumbnails/misc/m-misc2.png", "image_url": 'assets/customization_assets/misc/m-misc2.png'},
        {"id": "M02GREEN-M", "base_id": "M02-M", "gender": "Male", "price": 350, "colour": "#8aab7f", "filter_colour": "saturate(100%) sepia(100%) hue-rotate(60deg)", "thumbnail_url": "/static/assets/thumbnails/misc/m-misc2.png", "image_url": 'assets/customization_assets/misc/m-misc2.png'},

        {"id": "M03GREY-M", "base_id": "M03-M", "gender": "Male", "price": 150, "colour": "#848484", "filter_colour": "", "thumbnail_url": "/static/assets/thumbnails/misc/m-misc3.png", "image_url": 'assets/customization_assets/misc/m-misc3.png'},
        {"id": "M03BLUE-M", "base_id": "M03-M", "gender": "Male", "price": 250, "colour": "#79c7d9", "filter_colour": "saturate(100%) sepia(100%) hue-rotate(150deg)", "thumbnail_url": "/static/assets/thumbnails/misc/m-misc3.png", "image_url": 'assets/customization_assets/misc/m-misc3.png'},
        {"id": "M03GREEN-M", "base_id": "M03-M", "gender": "Male", "price": 350, "colour": "#8aab7f", "filter_colour": "saturate(100%) sepia(100%) hue-rotate(60deg)", "thumbnail_url": "/static/assets/thumbnails/misc/m-misc3.png", "image_url": 'assets/customization_assets/misc/m-misc3.png'},

        {"id": "M01BLUE-F", "base_id": "M01-F", "gender": "Female", "price": 150, "colour": "#59CFB5", "filter_colour": "", "thumbnail_url": "/static/assets/thumbnails/misc/f-misc1.png", "image_url": 'assets/customization_assets/misc/f-misc1.png'},
        {"id": "M01GREEN-F", "base_id": "M01-F", "gender": "Female", "price": 250, "colour": "#7de877", "filter_colour": "hue-rotate(300deg)", "thumbnail_url": "/static/assets/thumbnails/misc/f-misc1.png", "image_url": 'assets/customization_assets/misc/f-misc1.png'},
        {"id": "M01PINK-F", "base_id": "M01-F", "gender": "Female", "price": 350, "colour": "#FF9BA3", "filter_colour": "hue-rotate(190deg)", "thumbnail_url": "/static/assets/thumbnails/misc/f-misc1.png", "image_url": 'assets/customization_assets/misc/f-misc1.png'},

        {"id": "M02GREY-F", "base_id": "M02-F", "gender": "Female", "price": 150, "colour": "#848484", "filter_colour": "", "thumbnail_url": "/static/assets/thumbnails/misc/f-misc2.png", "image_url": 'assets/customization_assets/misc/f-misc2.png'},
        {"id": "M02WHITE-F", "base_id": "M02-F", "gender": "Female", "price": 250, "colour": "#E7E7E7", "filter_colour": "brightness(1.75)", "thumbnail_url": "/static/assets/thumbnails/misc/f-misc2.png", "image_url": 'assets/customization_assets/misc/f-misc2.png'},
        {"id": "M02PINK-F", "base_id": "M02-F", "gender": "Female", "price": 350, "colour": "#DBA5A2", "filter_colour": "sepia(100%) hue-rotate(315deg) contrast(100%) brightness(1.1)", "thumbnail_url": "/static/assets/thumbnails/misc/f-misc2.png", "image_url": 'assets/customization_assets/misc/f-misc2.png'},

        {"id": "M03GREY-F", "base_id": "M03-F", "gender": "Female", "price": 150, "colour": "#848484", "filter_colour": "", "thumbnail_url": "/static/assets/thumbnails/misc/f-misc3.png", "image_url": 'assets/customization_assets/misc/f-misc3.png'},
        {"id": "M03WHITE-F", "base_id": "M03-F", "gender": "Female", "price": 250, "colour": "#E7E7E7", "filter_colour": "brightness(1.75)", "thumbnail_url": "/static/assets/thumbnails/misc/f-misc3.png", "image_url": 'assets/customization_assets/misc/f-misc3.png'},
        {"id": "M03PINK-F", "base_id": "M03-F", "gender": "Female", "price": 350, "colour": "#DBA5A2", "filter_colour": "sepia(100%) hue-rotate(315deg) contrast(100%) brightness(1.1)", "thumbnail_url": "/static/assets/thumbnails/misc/f-misc3.png", "image_url": 'assets/customization_assets/misc/f-misc3.png'},

        {"id": "M04GREY-F", "base_id": "M04-F", "gender": "Female", "price": 150, "colour": "#848484", "filter_colour": "", "thumbnail_url": "/static/assets/thumbnails/misc/f-misc4.png", "image_url": 'assets/customization_assets/misc/f-misc4.png'},
        {"id": "M04WHITE-F", "base_id": "M04-F", "gender": "Female", "price": 250, "colour": "#E7E7E7", "filter_colour": "brightness(1.75)", "thumbnail_url": "/static/assets/thumbnails/misc/f-misc4.png", "image_url": 'assets/customization_assets/misc/f-misc4.png'},
        {"id": "M04PINK-F", "base_id": "M04-F", "gender": "Female", "price": 350, "colour": "#DBA5A2", "filter_colour": "sepia(100%) hue-rotate(315deg) contrast(100%) brightness(1.1)", "thumbnail_url": "/static/assets/thumbnails/misc/f-misc4.png", "image_url": 'assets/customization_assets/misc/f-misc4.png'},

        {"id": "M05PURPLE-F", "base_id": "M05-F", "gender": "Female", "price": 150, "colour": "#625b98", "filter_colour": "", "thumbnail_url": "/static/assets/thumbnails/misc/f-misc5.png", "image_url": 'assets/customization_assets/misc/f-misc5.png'},
        {"id": "M05GREY-F", "base_id": "M05-F", "gender": "Female", "price": 250, "colour": "#545454", "filter_colour": "grayscale(100%)", "thumbnail_url": "/static/assets/thumbnails/misc/f-misc5.png", "image_url": 'assets/customization_assets/misc/f-misc5.png'},
        {"id": "M05PINK-F", "base_id": "M05-F", "gender": "Female", "price": 350, "colour": "#E4A7BA", "filter_colour": "sepia(95%) hue-rotate(300deg) brightness(1.3)", "thumbnail_url": "/static/assets/thumbnails/misc/f-misc5.png", "image_url": 'assets/customization_assets/misc/f-misc5.png'},
    ]   
    
    for item_data in items_data:
        item = Item.query.filter_by(id=item_data["id"]).first()
        if not item:
            new_item = Item(**item_data)
            db.session.add(new_item)
    db.session.commit()

def add_pets_data():
    pets_data = [
        {"species": "A1", "name": "Aquana Blue", "price": 100, "egg_image_url": "/static/assets/eggs/aquana/Egg_Aquana_Blue.png", "pet_image_url": "/static/assets/pets/aquana/Aquana_Blue.png"},
        {"species": "A2", "name": "Aquana Pink", "price": 100, "egg_image_url": "/static/assets/eggs/aquana/Egg_Aquana_Pink.png", "pet_image_url": "/static/assets/pets/aquana/Aquana_Pink.png"},
        {"species": "A3", "name": "Aquana Yellow", "price": 100, "egg_image_url": "/static/assets/eggs/aquana/Egg_Aquana_Yellow.png", "pet_image_url": "/static/assets/pets/aquana/Aquana_Yellow.png"},
        {"species": "A4", "name": "Aquana Albino", "price": 200, "egg_image_url": "/static/assets/eggs/aquana/Egg_Aquana_Albino.png", "pet_image_url": "/static/assets/pets/aquana/Aquana_Albino.png"},
        {"species": "A5", "name": "Aquana Leucistic", "price": 200, "egg_image_url": "/static/assets/eggs/aquana/Egg_Aquana_Leucistic.png", "pet_image_url": "/static/assets/pets/aquana/Aquana_Leucistic.png"},
        {"species": "A6", "name": "Aquana Melanistic", "price": 200, "egg_image_url": "/static/assets/eggs/aquana/Egg_Aquana_Melanistic.png", "pet_image_url": "/static/assets/pets/aquana/Aquana_Melanistic.png"},
        {"species": "A7", "name": "Aquana Dragon Red", "price": 300, "egg_image_url": "/static/assets/eggs/aquana/Egg_Aquana_Dragon_Red.png", "pet_image_url": "/static/assets/pets/aquana/Aquana_Dragon_Red.png"},
        {"species": "A8", "name": "Aquana Dragon Green", "price": 300, "egg_image_url": "/static/assets/eggs/aquana/Egg_Aquana_Dragon_Green.png", "pet_image_url": "/static/assets/pets/aquana/Aquana_Dragon_Green.png"},
        {"species": "A9", "name": "Aquana Dragon Black", "price": 300, "egg_image_url": "/static/assets/eggs/aquana/Egg_Aquana_Dragon_Black.png", "pet_image_url": "/static/assets/pets/aquana/Aquana_Dragon_Black.png"},
        {"species": "J1", "name": "Jackaloaf Red Brocket", "price": 100, "egg_image_url": "/static/assets/eggs/jackaloaf/Egg_Jackaloaf_Brocket.png", "pet_image_url": "/static/assets/pets/jackaloaf/Jackaloaf_Brocket.png"},
        {"species": "J2", "name": "Jackaloaf Chinese", "price": 100, "egg_image_url": "/static/assets/eggs/jackaloaf/Egg_Jackaloaf_Chinese.png", "pet_image_url": "/static/assets/pets/jackaloaf/Jackaloaf_Chinese.png"},
        {"species": "J3", "name": "Jackaloaf Pudu", "price": 100, "egg_image_url": "/static/assets/eggs/jackaloaf/Egg_Jackaloaf_Pudu.png", "pet_image_url": "/static/assets/pets/jackaloaf/Jackaloaf_Pudu.png"},
        {"species": "J4", "name": "Jackaloaf Roe", "price": 200, "egg_image_url": "/static/assets/eggs/jackaloaf/Egg_Jackaloaf_Roe.png", "pet_image_url": "/static/assets/pets/jackaloaf/Jackaloaf_Roe.png"},
        {"species": "J5", "name": "Jackaloaf Taruca", "price": 200, "egg_image_url": "/static/assets/eggs/jackaloaf/Egg_Jackaloaf_Taruca.png", "pet_image_url": "/static/assets/pets/jackaloaf/Jackaloaf_Taruca.png"},
        {"species": "J6", "name": "Jackaloaf Eld", "price": 200, "egg_image_url": "/static/assets/eggs/jackaloaf/Egg_Jackaloaf_Eld.png", "pet_image_url": "/static/assets/pets/jackaloaf/Jackaloaf_Eld.png"},
        {"species": "J7", "name": "Jackaloaf Sika", "price": 300, "egg_image_url": "/static/assets/eggs/jackaloaf/Egg_Jackaloaf_Sika.png", "pet_image_url": "/static/assets/pets/jackaloaf/Jackaloaf_Sika.png"},
        {"species": "J8", "name": "Jackaloaf Reindeer", "price": 300, "egg_image_url": "/static/assets/eggs/jackaloaf/Egg_Jackaloaf_Reindeer.png", "pet_image_url": "/static/assets/pets/jackaloaf/Jackaloaf_Reindeer.png"},
        {"species": "J9", "name": "Jackaloaf Elk", "price": 300, "egg_image_url": "/static/assets/eggs/jackaloaf/Egg_Jackaloaf_Elk.png", "pet_image_url": "/static/assets/pets/jackaloaf/Jackaloaf_Elk.png"},
        {"species": "T1", "name": "Trotter Red", "price": 100, "egg_image_url": "/static/assets/eggs/trotter/Egg_Trotter_Red.png", "pet_image_url": "/static/assets/pets/trotter/Trotter_Red.png"},
        {"species": "T2", "name": "Trotter Brown", "price": 100, "egg_image_url": "/static/assets/eggs/trotter/Egg_Trotter_Brown.png", "pet_image_url": "/static/assets/pets/trotter/Trotter_Brown.png"},
        {"species": "T3", "name": "Trotter Pink", "price": 100, "egg_image_url": "/static/assets/eggs/trotter/Egg_Trotter_Pink.png", "pet_image_url": "/static/assets/pets/trotter/Trotter_Pink.png"},
        {"species": "T4", "name": "Trotter Albino", "price": 200, "egg_image_url": "/static/assets/eggs/trotter/Egg_Trotter_Albino.png", "pet_image_url": "/static/assets/pets/trotter/Trotter_Albino.png"},
        {"species": "T5", "name": "Trotter Leucistic", "price": 200, "egg_image_url": "/static/assets/eggs/trotter/Egg_Trotter_Leucistic.png", "pet_image_url": "/static/assets/pets/trotter/Trotter_Leucistic.png"},
        {"species": "T6", "name": "Trotter Silver", "price": 200, "egg_image_url": "/static/assets/eggs/trotter/Egg_Trotter_Silver.png", "pet_image_url": "/static/assets/pets/trotter/Trotter_Silver.png"},
        {"species": "T7", "name": "Trotter Kitsune Red", "price": 300, "egg_image_url": "/static/assets/eggs/trotter/Egg_Trotter_Kitsune_Red.png", "pet_image_url": "/static/assets/pets/trotter/Trotter_Kitsune_Red.png"},
        {"species": "T8", "name": "Trotter Kitsune White", "price": 300, "egg_image_url": "/static/assets/eggs/trotter/Egg_Trotter_Kitsune_White.png", "pet_image_url": "/static/assets/pets/trotter/Trotter_Kitsune_White.png"},
        {"species": "T9", "name": "Trotter Kitsune Black", "price": 300, "egg_image_url": "/static/assets/eggs/trotter/Egg_Trotter_Kitsune_Black.png", "pet_image_url": "/static/assets/pets/trotter/Trotter_Kitsune_Black.png"}
    ]
    for pet_data in pets_data:
        pet = Pet.query.filter_by(species=pet_data["species"]).first()
        if not pet:
            new_pet = Pet(**pet_data)
            db.session.add(new_pet)
    db.session.commit()

@app.route('/gain_currency', methods=['POST'])
@login_required
def gain_currency():
    score = request.get_json()
    current_user.currency_balance += score
    db.session.commit()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        add_items_data()
        add_pets_data()
    app.run(debug=True, threaded=True)