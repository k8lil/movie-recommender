from flask import Flask, request, render_template, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from models import db, User, UserPreference
from recommendation import get_similar_movies
from flask import jsonify
from models import Movie
import requests
from flask import request, render_template

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

@app.route('/favorites')
@login_required
def favorites():
    liked_movies = UserPreference.query.filter_by(user_id=current_user.id).all()
    return render_template('favorites.html', liked_movies=liked_movies)

@app.route('/remove_favorite/<int:movie_id>', methods=['POST'])
@login_required
def remove_favorite(movie_id):
    preference = UserPreference.query.filter_by(user_id=current_user.id, id=movie_id).first()

    if preference:
        db.session.delete(preference)
        db.session.commit()
        flash('Movie removed from favorites.', 'success')
    else:
        flash('Favorite not found.', 'error')

    return redirect(url_for('favorites'))

TMDB_API_KEY = 'e454138589053ddd5a2dd061e3e35ac5'

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query', '').strip()
    if not query:
        return render_template('search_results.html', search_results=[], input_title=query)

    url = 'https://api.themoviedb.org/3/search/movie'
    params = {
        'api_key': TMDB_API_KEY,
        'query': query,
        'language': 'en-US',
        'page': 1,
        'include_adult': False
    }

    response = requests.get(url, params=params)
    if response.status_code != 200:
        return render_template('search_results.html', search_results=[], input_title=query)

    data = response.json()
    results = data.get('results', [])

    search_results = [{
        'title': movie['title'],
        'id': movie['id'],
        'poster_path': movie['poster_path'],
        'release_date': movie.get('release_date', ''),
        'overview': movie.get('overview', '')
    } for movie in results]

    return render_template('search_results.html', search_results=search_results, input_title=query)


@app.route('/recommend', methods=['GET', 'POST'])
def recommend():
    if request.method == 'POST':
        movie_title = request.form.get('movie')
    else:
        movie_title = request.args.get('movie')

    if not movie_title:
        return render_template('index.html', message="Please enter a movie title.")

    # Step 1: Search for the movie
    search_url = 'https://api.themoviedb.org/3/search/movie'
    search_params = {
        'api_key': TMDB_API_KEY,
        'query': movie_title
    }
    search_response = requests.get(search_url, params=search_params)
    search_data = search_response.json()
    results = search_data.get('results')

    if not results:
        return render_template('index.html', message="Movie not found.", input_title=movie_title)

    # Step 2: Get the ID of the first matching movie
    movie_id = results[0]['id']

    # Step 3: Get recommendations based on this movie ID
    rec_url = f'https://api.themoviedb.org/3/movie/{movie_id}/recommendations'
    rec_params = {
        'api_key': TMDB_API_KEY,
        'language': 'en-US',
        'page': 1
    }
    rec_response = requests.get(rec_url, params=rec_params)
    rec_data = rec_response.json()
    recommendations = rec_data.get('results', [])  # limit to 8 results

    movies = [{
        'title': movie['title'],
        'id': movie['id'],
        'poster_path': movie['poster_path']
    } for movie in recommendations]

    return render_template('index.html', recommendations=movies, input_title=movie_title)

if __name__ == '__main__':
    app.run(debug=True)
