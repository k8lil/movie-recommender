from flask import Flask, request, render_template, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from models import db, User, UserPreference
from recommendation import get_similar_movies
from flask import jsonify

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SECRET_KEY'] = 'supersecretkey'

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/', methods=['GET', 'POST'])
def home():
    recommendations = []
    message = ""
    input_title = ""

    if request.method == 'POST':
        input_title = request.form.get('movie')
        if input_title:
            result = get_similar_movies(input_title)
            if result is None:
                message = f"Sorry, couldn't find any movie matching '{input_title}'. Please try again."
            else:
                matched_title, recommendations = result
                if matched_title.lower() != input_title.lower():
                    message = f"Showing results for closest match: '{matched_title}'"
        else:
            message = "Please enter a movie title."

    return render_template('index.html', recommendations=recommendations, message=message, input_title=input_title)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists. Try another.', 'danger')
            return redirect(url_for('register'))

        new_user = User(username=username)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        login_user(new_user)
        flash('Registered and logged in!', 'success')
        return redirect(url_for('home'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user)
            flash('Logged in successfully.', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid username or password', 'danger')

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('home'))


@app.route('/like', methods=['POST'])
@login_required
def like_movie():
    movie_title = request.form.get('movie_title')
    if not movie_title:
        return jsonify({'status': 'error', 'message': 'No movie title provided.'})

    liked = UserPreference.query.filter_by(user_id=current_user.id, movie_title=movie_title).first()
    if liked:
        return jsonify({'status': 'info', 'message': f'You already liked "{movie_title}".'})

    new_like = UserPreference(user_id=current_user.id, movie_title=movie_title)
    db.session.add(new_like)
    db.session.commit()

    return jsonify({'status': 'success', 'message': f'You liked "{movie_title}".'})


if __name__ == '__main__':
    app.run(debug=True)
