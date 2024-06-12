from flask import Flask, render_template, url_for, redirect, request, abort, jsonify, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, DecimalField, SubmitField, SelectField
from wtforms.validators import InputRequired, Length, ValidationError, DataRequired, EqualTo
from flask_bcrypt import Bcrypt
from datetime import datetime, timedelta
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
    adopt_name = db.Column(db.String(20), nullable=False)
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
    last_gift_time = db.Column(db.DateTime)
    last_played_time_ft = db.Column(db.String)
    last_played_time_jjj = db.Column(db.String)
    daily_chances_ft = db.Column(db.Integer, default=10)
    daily_chances_jjj = db.Column(db.Integer, default=5)

    inventory = db.relationship('Inventory', back_populates='user_obj')
    adoptedpet = db.relationship('AdoptedPet', back_populates='user_obj')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.currency_balance = 1000

    def set_password(self, password):
        self.password = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password, password)

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

    def get_nesting_level(self):
        level = 0
        current = self
        while current.parent_id:
            level += 1
            current = current.parent
        return level

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

class GiftingForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Username"})
    currency = DecimalField(validators=[InputRequired()], render_kw={"placeholder": "Currency"})
    submit = SubmitField("Send My Gift!")

    def validate_username_gifting(self, username):
        existing_user_username = User.query.filter_by(username=username.data).first()
        if not existing_user_username:
            raise ValidationError("This user doesn't exist!")
        
class ChangePasswordForm(FlaskForm):
    old_password = PasswordField('Old Password', validators=[DataRequired()], render_kw={"placeholder": "Old Password"})
    new_password = PasswordField('New Password', validators=[DataRequired()], render_kw={"placeholder": "New Password"})
    confirm_new_password = PasswordField('Confirm New Password', validators=[DataRequired(), EqualTo('new_password')], render_kw={"placeholder": "Confirm Password"})
    submit = SubmitField('Change Password')

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            if bcrypt.check_password_hash(user.password, form.password.data):
                login_user(user)
                return redirect(url_for('home'))
            else:
                error_message = "Invalid password. Please try again."
        else:
            error_message = "Username does not exist. Please try again."
        return render_template('login.html', form=form, error_message=error_message)
    return render_template('login.html', form=form)

@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    message = None
    message_type = None
    if form.validate_on_submit():
        if current_user.check_password(form.old_password.data):
            current_user.set_password(form.new_password.data)
            db.session.commit()
            message = 'Your password has been updated!'
            message_type = 'success'
            return render_template('change_password.html', form=form, message=message, message_type=message_type)
        else:
            message = 'Old password is incorrect.'
            message_type = 'danger'
    return render_template('change_password.html', form=form, message=message, message_type=message_type)

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
    print(f"Saved profile_pic for user {current_user.username}: {current_user.profile_pic[:50]}...") 
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
    data = request.get_json()
    pet_name = data.get('pet_name')

    if not (4 <= len(pet_name) <= 20):
        return jsonify(success=False, message="Pet name must be between 4 and 20 characters."), 400

    pet = Pet.query.filter_by(species=pet_species).first()

    if pet:
        if current_user.currency_balance >= pet.price:
            current_user.currency_balance -= pet.price
            db.session.commit()
            
            adopted_pet = AdoptedPet(species=pet_species, username=current_user.username, user_id=current_user.id, adopt_name=pet_name)
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


#Limit nested comments
MAX_NESTING_LEVEL = 2

@app.route("/topic/<int:id>", methods=["GET", "POST"])
def topic(id):
    topic = db.session.get(Topic, id)
    if not topic:
        abort(404)

    error = None

    if request.method == "POST" and current_user.is_authenticated:
        text = request.form["comment"].strip()
        parent_id = request.form["parent_id"]

        if text:
            parent_comment = db.session.get(Comment, parent_id) if parent_id else None
            if parent_comment and parent_comment.get_nesting_level() >= MAX_NESTING_LEVEL:
                error = f"Maximum nesting level of {MAX_NESTING_LEVEL} reached. Cannot add more replies."
            else:
                comment = Comment(text=text, topicId=id, username=current_user.username, parent=parent_comment)
                db.session.add(comment)
                db.session.commit()

    comments = Comment.query.filter_by(topicId=id, parent=None).all()
    profile_pics = {comment.username: (User.query.filter_by(username=comment.username).first().profile_pic or '') for comment in comments}
    profile_pics[topic.username] = User.query.filter_by(username=topic.username).first().profile_pic or ''

    return render_template("topic.html", topic=topic, comments=comments, profile_pics=profile_pics, error=error, MAX_NESTING_LEVEL=MAX_NESTING_LEVEL)

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

@app.route('/delete_account', methods=['POST'])
@login_required
def delete_account():
    # Delete user's related data
    Inventory.query.filter_by(user_id=current_user.id).delete()
    AdoptedPet.query.filter_by(user_id=current_user.id).delete()
    Comment.query.filter_by(username=current_user.username).delete()
    Topic.query.filter_by(username=current_user.username).delete()
    # Delete the user
    user = User.query.get(current_user.id)
    db.session.delete(user)
    db.session.commit()
    logout_user()
    return jsonify({'success': True, 'message': 'Account deleted successfully'}), 200

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
        new_user = User(username=form.username.data, password=hashed_password, avatar="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")
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

@app.route('/gifting', methods=['GET', 'POST'])
@login_required
def gifting():
    form = GiftingForm()
    if form.validate_on_submit():
        gifted_money = int(form.currency.data)
        
        if gifted_money <= 0:
            return jsonify({'status': 'error', 'message': 'Gift amount must be a positive number.'})
        
        if gifted_money > 100:
            return jsonify({'status': 'error', 'message': 'You can\'t gift more than $100 at a time.'})
        
        user = User.query.filter_by(username=form.username.data).first()
        
        if not user:
            return jsonify({'status': 'error', 'message': 'The username you entered does not exist.'})
        
        if user.username == current_user.username:
            return jsonify({'status': 'error', 'message': 'You can\'t gift to yourself.'})
        
        if current_user.currency_balance < gifted_money:
            return jsonify({'status': 'error', 'message': 'You do not have enough balance to gift that amount.'})
        
        last_gift_time = current_user.last_gift_time
        if last_gift_time and datetime.utcnow() - last_gift_time < timedelta(hours=4):
            return jsonify({'status': 'error', 'message': 'You can only gift once every 4 hours.'})

        current_user.currency_balance -= gifted_money
        user.currency_balance += gifted_money
        current_user.last_gift_time = datetime.utcnow()
        db.session.commit()
        
        return jsonify({'status': 'success', 'message': f'You have successfully gifted {gifted_money} coins to {user.username}.'})
    
    return render_template('gifting.html', form=form)

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
    if current_user.daily_chances_ft > 0:
        score = request.get_json()
        current_user.currency_balance += score
        db.session.commit()
        current_user.daily_chances_ft -= 1
        db.session.commit()
        current_user.last_played_time_ft = datetime.now().strftime("%m/%d/%Y")
        db.session.commit()
    if current_user.daily_chances_ft == 0:
        current_user.daily_chances_ft = 0
        db.session.commit()

@app.route('/reset_chances_ft', methods=['POST'])
@login_required
def reset_chances_ft():
    temp_date = datetime.now().strftime("%m/%d/%Y")
    if current_user.last_played_time_ft != temp_date:
        current_user.daily_chances_ft = 5
        db.session.commit()
        current_user.last_played_time_ft = datetime.now().strftime("%m/%d/%Y")
        db.session.commit()
    return redirect(url_for('minigames-feeding-time'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        add_items_data()
        add_pets_data()
    app.run(debug=True, threaded=True)