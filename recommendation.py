import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from rapidfuzz import process

# Load datasets
movies = pd.read_csv('movies.csv')
ratings = pd.read_csv('ratings.csv')

# Create the movie-user matrix
movie_user_matrix = ratings.pivot(index='movieId', columns='userId', values='rating').fillna(0)

# Compute cosine similarity matrix
movie_similarity = cosine_similarity(movie_user_matrix)
movie_similarity_df = pd.DataFrame(movie_similarity, index=movie_user_matrix.index, columns=movie_user_matrix.index)

# List of all movie titles for fuzzy matching
all_titles = movies['title'].tolist()

def get_closest_title(query, limit=1, score_cutoff=60):
    matches = process.extract(query, all_titles, limit=limit, score_cutoff=score_cutoff)
    if matches:
        # matches is a list of tuples: (title, score, index)
        return matches[0][0]
    return None

def get_similar_movies(input_title, top_n=5):
    # Get the closest movie title using fuzzy matching
    title = get_closest_title(input_title)
    if not title:
        return None  # No close match found

    # Find movieId of the matched title
    movie_ids = movies[movies['title'] == title]['movieId']
    if movie_ids.empty:
        return None

    movie_id = movie_ids.iloc[0]

    # Get similarity scores and find top similar movies
    similarity_scores = movie_similarity_df[movie_id]
    top_similar_ids = similarity_scores.drop(movie_id).sort_values(ascending=False).head(top_n).index

    # Return matched title and list of similar movie titles
    similar_titles = movies[movies['movieId'].isin(top_similar_ids)]['title'].tolist()
    return title, similar_titles
