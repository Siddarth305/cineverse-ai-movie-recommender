import pandas as pd

movies = pd.read_csv("data/tmdb_5000_movies.csv")
credits = pd.read_csv("data/tmdb_5000_credits.csv")

print("MOVIES DATASET")
print(movies.shape)

print("\nMOVIES COLUMNS:")
print(movies.columns.tolist())

print("\nFirst 5 MOVIES:")
print(movies[["id", "title", "genres", "keywords", "overview"]].head(5))

print("\nCREDITS DATASET")
print(credits.shape)

print("\nCREDITS COLUMNS:")
print(credits.columns.tolist())

print('\nFirst 5 CREDIT RECORDS:')
print(credits[["movie_id", "title", "cast", "crew"]].head(5))