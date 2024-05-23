from flask import Flask, render_template, url_for, redirect, request, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError
from flask_bcrypt import Bcrypt
from flask import jsonify
import os
basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'instance', 'database.db')
app.config['SECRET_KEY'] = 'Battery-AAA'
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)


login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class Inventory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(20), db.ForeignKey('user.username'), unique=True)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), unique=True)
    user = db.relationship('User', back_populates='inventory')
    item = db.relationship('Item', back_populates='inventory')

class AdoptedPet(db.Model):
    adopt_id = db.Column(db.Integer, primary_key=True)
    species = db.Column(db.String(2), db.ForeignKey('pet.species'), nullable=False)
    username = db.Column(db.String(20), nullable=False) 
    pet = db.relationship('Pet', backref='adopted_by')

    @property
    def user(self):
        return User.query.filter_by(username=self.username).first()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    password = db.Column(db.String(80), nullable=False)
    currency_balance = db.Column(db.Integer, default=1000)

    inventory = db.relationship('Inventory', back_populates='user')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.currency_balance = 1000

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
    username = StringField(validators=[InputRequired(), Length(
        min=4, max=20)], render_kw={"placeholder": "Username"})
    
    password = PasswordField(validators=[InputRequired(), Length(
        min=4, max=20)], render_kw={"placeholder": "Password"})
    
    submit = SubmitField("Register")

    def validate_username(self, username):
        existing_user_username = User.query.filter_by(
            username=username.data).first()
        
        if existing_user_username:
            raise ValidationError(
                "That username already exists. Please choose a different one.")


class LoginForm(FlaskForm): 
    username = StringField(validators=[InputRequired(), Length(
        min=4, max=20)], render_kw={"placeholder": "Username"})
    
    password = PasswordField(validators=[InputRequired(), Length(
        min=4, max=20)], render_kw={"placeholder": "Password"})
    
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
    adopted_pets = db.session.query(AdoptedPet, Pet).join(Pet, AdoptedPet.species == Pet.species).filter(AdoptedPet.username == current_user.username).all()
    return render_template('profile.html', adopted_pets=adopted_pets)

@app.route('/gifting')
@login_required
def gifting():
    return render_template('gifting.html')

@app.route('/store')
@login_required
def store():
    grouped_items = Item.get_items_grouped_by_base_id()
    return render_template('store.html', grouped_items=grouped_items)

@app.route('/purchase_item/<string:item_id>', methods=['POST'])
@login_required
def purchase_item(item_id):
    item = Item.query.filter_by(id=item_id).first()
    if item:
        if current_user.currency_balance >= item.price:
            current_user.currency_balance -= item.price
            db.session.commit()
            
            inventory = Inventory(id=item_id, username=current_user.username)
            db.session.add(inventory)
            db.session.commit()
            return jsonify({'success': True})
    else:
        abort(404) 

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
            
            adopted_pet = AdoptedPet(species=pet_species, username=current_user.username)
            db.session.add(adopted_pet)
            db.session.commit()
            return jsonify({'success': True})
    else:
        abort(404) 

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
        if topic.username == current_user.username:  # Check if the current user is the author of the topic
            db.session.delete(topic)
            db.session.commit()
            return redirect(url_for('forums'))
        else:
            abort(403)  # User is not authorized to delete this topic
    else:
        abort(404)  # Topic not found

@app.route('/delete/comment/<int:id>', methods=['POST'])
@login_required
def delete_comment(id):
    comment = Comment.query.get(id)
    if comment:
        if comment.username == current_user.username:  # Check if the current user is the author of the comment
            db.session.delete(comment)
            db.session.commit()
            return redirect(url_for('topic', id=comment.topicId))
        else:
            abort(403)  # User is not authorized to delete this comment
    else:
        abort(404)  # Comment not found

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

def add_items_data():
    items_data = [
        {"id": "H01BLACK-F", "base_id": "H01-F", "gender": "F", "price": 150, "colour": "#000000", "filter_colour": "grayscale(50%) brightness(40%) saturate(400%)", "thumbnail_url": "/static/assets/character_customization/thumbnails/hair/f-hair1.png", "image_url": '/static/assets/character_customization/customization_assets/hair/f-hair1.png'},
        {"id": "H01BROWN-F", "base_id": "H01-F", "gender": "F", "price": 250, "colour": "#744700", "filter_colour": "sepia(95%) hue-rotate(350deg) brightness(0.4) contrast(140%)", "thumbnail_url": "/static/assets/character_customization/thumbnails/hair/f-hair1.png", "image_url": '/static/assets/character_customization/customization_assets/hair/f-hair1.png'},
        {"id": "H01BLONDE-F", "base_id": "H01-F", "gender": "F", "price": 350, "colour": "#D9B380", "filter_colour": "sepia(100%) brightness(1.3)", "thumbnail_url": "/static/assets/character_customization/thumbnails/hair/f-hair1.png", "image_url": '/static/assets/character_customization/customization_assets/hair/f-hair1.png'},
        {"id": "H02BLUE-F", "base_id": "H02-F", "gender": "F", "price": 150, "colour": "#59CFB5", "filter_colour": "", "thumbnail_url": "/static/assets/character_customization/thumbnails/hair/f-hair2.png", "image_url": '/static/assets/character_customization/customization_assets/hair/f-hair2.png'},
        {"id": "H02GREEN-F", "base_id": "H02-F", "gender": "F", "price": 250, "colour": "#86CA66", "filter_colour": "hue-rotate(300deg)", "thumbnail_url": "/static/assets/character_customization/thumbnails/hair/f-hair2.png", "image_url": '/static/assets/character_customization/customization_assets/hair/f-hair2.png'},
        {"id": "H02PINK-F", "base_id": "H02-F", "gender": "F", "price": 350, "colour": "#FF9BA3", "filter_colour": "hue-rotate(190deg)", "thumbnail_url": "/static/assets/character_customization/thumbnails/hair/f-hair2.png", "image_url": '/static/assets/character_customization/customization_assets/hair/f-hair2.png'},
        {"id": "U01PURPLE-F", "base_id": "U01-F", "gender": "F", "price": 150, "colour": "#c77fde", "filter_colour": "saturate(100%) sepia(100%) hue-rotate(240deg)", "thumbnail_url": "/static/assets/character_customization/thumbnails/shirt/f-shirt1.png", "image_url": '/static/assets/character_customization/customization_assets/shirt/f-shirt1.png'},
        {"id": "U01BLUE-F", "base_id": "U01-F", "gender": "F", "price": 250, "colour": "#79c7d9", "filter_colour": "saturate(100%) sepia(100%) hue-rotate(150deg)", "thumbnail_url": "/static/assets/character_customization/thumbnails/shirt/f-shirt1.png", "image_url": '/static/assets/character_customization/customization_assets/shirt/f-shirt1.png'},
        {"id": "U01GREEN-F", "base_id": "U01-F", "gender": "F", "price": 350, "colour": "#7de877", "filter_colour": "saturate(100%) sepia(100%) hue-rotate(60deg)", "thumbnail_url": "/static/assets/character_customization/thumbnails/shirt/f-shirt1.png", "image_url": '/static/assets/character_customization/customization_assets/shirt/f-shirt1.png'},
        {"id": "U01PURPLE-M", "base_id": "U01-M", "gender": "M", "price": 150, "colour": "#c77fde", "filter_colour": "saturate(100%) sepia(100%) hue-rotate(240deg)", "thumbnail_url": "/static/assets/character_customization/thumbnails/shirt/m-shirt1.png", "image_url": '/static/assets/character_customization/customization_assets/shirt/m-shirt1.png'},
        {"id": "U01BLUE-M", "base_id": "U01-M", "gender": "M", "price": 250, "colour": "#79c7d9", "filter_colour": "saturate(100%) sepia(100%) hue-rotate(150deg)", "thumbnail_url": "/static/assets/character_customization/thumbnails/shirt/m-shirt1.png", "image_url": '/static/assets/character_customization/customization_assets/shirt/m-shirt1.png'},
        {"id": "U01GREEN-M", "base_id": "U01-M", "gender": "M", "price": 350, "colour": "#7de877", "filter_colour": "saturate(100%) sepia(100%) hue-rotate(60deg)", "thumbnail_url": "/static/assets/character_customization/thumbnails/shirt/m-shirt1.png", "image_url": '/static/assets/character_customization/customization_assets/shirt/m-shirt1.png'},
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
    app.run(debug=True)