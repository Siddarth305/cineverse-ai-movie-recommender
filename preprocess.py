import pandas as pd
import ast
import pickle

from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# -----------------------------------
# 1. LOAD DATASETS
# -----------------------------------

movies = pd.read_csv("data/tmdb_5000_movies.csv")
credits = pd.read_csv("data/tmdb_5000_credits.csv")


# -----------------------------------
# 2. MERGE DATASETS
# -----------------------------------

movies = movies.merge(credits, on="title")


# -----------------------------------
# 3. SELECT REQUIRED COLUMNS
# -----------------------------------

movies = movies[
    [
        "movie_id",
        "title",
        "overview",
        "genres",
        "keywords",
        "cast",
        "crew"
    ]
]


# -----------------------------------
# 4. REMOVE MISSING VALUES
# -----------------------------------

movies.dropna(inplace=True)


# -----------------------------------
# 5. EXTRACT GENRES AND KEYWORDS
# -----------------------------------

def convert(obj):
    names = []

    for item in ast.literal_eval(obj):
        names.append(item["name"])

    return names


# -----------------------------------
# 6. EXTRACT FIRST 3 CAST MEMBERS
# -----------------------------------

def convert_cast(obj):
    names = []

    for item in ast.literal_eval(obj)[:3]:
        names.append(item["name"])

    return names


# -----------------------------------
# 7. EXTRACT DIRECTOR
# -----------------------------------

def get_director(obj):
    names = []

    for item in ast.literal_eval(obj):
        if item["job"] == "Director":
            names.append(item["name"])
            break

    return names


# -----------------------------------
# 8. APPLY FEATURE EXTRACTION
# -----------------------------------

movies["genres"] = movies["genres"].apply(convert)
movies["keywords"] = movies["keywords"].apply(convert)
movies["cast"] = movies["cast"].apply(convert_cast)
movies["crew"] = movies["crew"].apply(get_director)


# -----------------------------------
# 9. CONVERT OVERVIEW INTO WORDS
# -----------------------------------

movies["overview"] = movies["overview"].apply(lambda x: x.split())


# -----------------------------------
# 10. REMOVE SPACES FROM FEATURES
# -----------------------------------

movies["genres"] = movies["genres"].apply(
    lambda x: [item.replace(" ", "") for item in x]
)

movies["keywords"] = movies["keywords"].apply(
    lambda x: [item.replace(" ", "") for item in x]
)

movies["cast"] = movies["cast"].apply(
    lambda x: [item.replace(" ", "") for item in x]
)

movies["crew"] = movies["crew"].apply(
    lambda x: [item.replace(" ", "") for item in x]
)


# -----------------------------------
# 11. CREATE TAGS
# -----------------------------------

movies["tags"] = (
    movies["overview"]
    + movies["genres"]
    + movies["keywords"]
    + movies["cast"]
    + movies["crew"]
)


# -----------------------------------
# 12. CONVERT TAGS LIST INTO TEXT
# -----------------------------------

movies["tags"] = movies["tags"].apply(
    lambda x: " ".join(x)
)


# -----------------------------------
# 13. CREATE FINAL DATAFRAME
# -----------------------------------

new_movies = movies[
    ["movie_id", "title", "tags"]
].copy()


# -----------------------------------
# 14. TEXT TO NUMERICAL VECTORS
# -----------------------------------

cv = CountVectorizer(
    max_features=5000,
    stop_words="english"
)

vectors = cv.fit_transform(
    new_movies["tags"]
).toarray()


print("Number of movies:", new_movies.shape[0])
print("Vector shape:", vectors.shape)


# -----------------------------------
# 15. SAVE ML DATA
# -----------------------------------

with open("model/movies.pkl", "wb") as file:
    pickle.dump(new_movies, file)


with open("model/vectors.pkl", "wb") as file:
    pickle.dump(vectors, file)


print("\nModel files saved successfully!")
print("Movies shape:", new_movies.shape)
print("Vectors shape:", vectors.shape)

# -----------------------------------
# 17. RECOMMENDATION FUNCTION
# -----------------------------------

def recommend(movie_name):

    # Find the selected movie
    movie_index = new_movies[
        new_movies["title"] == movie_name
    ].index[0]

    # Get similarity scores
    distances = similarity[movie_index]

    # Sort by similarity score
    movie_list = sorted(
        list(enumerate(distances)),
        reverse=True,
        key=lambda x: x[1]
    )[1:6]

    recommendations = []

    # Get top 5 movie titles
    for index, score in movie_list:
        recommendations.append(
            new_movies.iloc[index]["title"]
        )

    return recommendations


# -----------------------------------
# 18. TEST THE RECOMMENDER
# -----------------------------------

movie_to_test = "Interstellar"

print(f"\nRecommendations for {movie_to_test}:")

for movie in recommend(movie_to_test):
    print(movie)