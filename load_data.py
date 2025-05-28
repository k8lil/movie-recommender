import pandas as pd

# Load movies and ratings data
movies = pd.read_csv('movies.csv')
ratings = pd.read_csv('ratings.csv')

# Quick peek at the data
print(movies.head())
print(ratings.head())

# Merge ratings with movie titles for easier use
data = pd.merge(ratings, movies, on='movieId')

print(data.head())

# Basic stats
print(f"Number of users: {data['userId'].nunique()}")
print(f"Number of movies rated: {data['movieId'].nunique()}")
print(f"Total ratings: {len(data)}")

# Check for missing values
print(data.isnull().sum())