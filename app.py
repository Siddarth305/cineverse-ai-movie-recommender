from flask import Flask, render_template, request, jsonify
import pickle
import requests
import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity


app = Flask(__name__)


# =========================================
# TMDB API KEY
# =========================================

TMDB_API_KEY = "ADD_API_HERE"


# =========================================
# LOAD ML DATA
# =========================================

with open("model/movies.pkl", "rb") as file:
    movies = pickle.load(file)

with open("model/vectors.pkl", "rb") as file:
    vectors = pickle.load(file)


movies["movie_id"] = pd.to_numeric(
    movies["movie_id"],
    errors="coerce"
)


print("Movies loaded:", len(movies))
print("Vectors shape:", vectors.shape)


# =========================================
# HOME
# =========================================

@app.route("/")
def home():

    return render_template("index.html")


# =========================================
# POSTER URL
# =========================================

def get_poster_url(poster_path):

    if poster_path:
        return (
            "https://image.tmdb.org/t/p/w500"
            f"{poster_path}"
        )

    return None


# =========================================
# GET MOVIE DETAILS
# =========================================

def get_movie_details(movie_id):

    url = f"https://api.themoviedb.org/3/movie/{movie_id}"

    params = {
        "api_key": TMDB_API_KEY,
        "language": "en-US"
    }

    try:

        response = requests.get(
            url,
            params=params,
            timeout=10
        )

        if response.status_code != 200:

            print(
                f"Details error {movie_id}:",
                response.status_code
            )

            return None

        data = response.json()

        return {
            "movie_id": data.get("id"),
            "title": data.get("title"),
            "poster": get_poster_url(
                data.get("poster_path")
            ),
            "rating": data.get("vote_average"),
            "release_date": data.get("release_date"),
            "overview": data.get("overview"),
            "genres": [
                genre["id"]
                for genre in data.get("genres", [])
            ]
        }

    except requests.exceptions.RequestException as error:

        print("Details request error:", error)

        return None


# =========================================
# SEARCH MOVIES
# =========================================

def search_movies(query):

    url = "https://api.themoviedb.org/3/search/movie"

    params = {
        "api_key": TMDB_API_KEY,
        "query": query,
        "language": "en-US",
        "page": 1
    }

    try:

        response = requests.get(
            url,
            params=params,
            timeout=10
        )

        if response.status_code != 200:
            return []

        data = response.json()

        results = []

        for movie in data.get("results", [])[:10]:

            results.append({
                "movie_id": movie.get("id"),
                "title": movie.get("title"),
                "release_date": movie.get(
                    "release_date"
                )
            })

        return results

    except requests.exceptions.RequestException as error:

        print("Search error:", error)

        return []


# =========================================
# SEARCH ROUTE
# =========================================

@app.route("/search")
def search():

    query = request.args.get(
        "query",
        ""
    ).strip()

    if not query:
        return jsonify([])

    return jsonify(
        search_movies(query)
    )


# =========================================
# FORMAT TMDB MOVIES
# =========================================

def format_tmdb_movies(movie_list, source):

    recommendations = []

    for movie in movie_list:

        recommendations.append({

            "movie_id": movie.get("id"),

            "title": movie.get("title"),

            "poster": get_poster_url(
                movie.get("poster_path")
            ),

            "rating": movie.get("vote_average"),

            "release_date": movie.get(
                "release_date"
            ),

            "overview": movie.get("overview"),

            "similarity_score": None,

            "source": source

        })

    return recommendations


# =========================================
# TMDB PAGINATED REQUEST
# =========================================

def get_tmdb_movie_list(
    endpoint,
    movie_id,
    offset,
    limit,
    source
):

    page = (offset // 20) + 1

    position_in_page = offset % 20

    url = (
        f"https://api.themoviedb.org/3/movie/"
        f"{movie_id}/{endpoint}"
    )

    params = {

        "api_key": TMDB_API_KEY,

        "language": "en-US",

        "page": page

    }

    try:

        response = requests.get(
            url,
            params=params,
            timeout=10
        )

        print(
            f"TMDB {endpoint} | "
            f"movie={movie_id} | "
            f"page={page} | "
            f"status={response.status_code}"
        )

        if response.status_code != 200:
            return [], False

        data = response.json()

        all_results = data.get("results", [])

        selected_results = all_results[
            position_in_page:
            position_in_page + limit
        ]

        formatted_results = format_tmdb_movies(
            selected_results,
            source
        )

        total_pages = data.get("total_pages", 1)

        has_more = False

        if position_in_page + limit < len(all_results):

            has_more = True

        elif page < total_pages:

            has_more = True

        return formatted_results, has_more

    except requests.exceptions.RequestException as error:

        print("TMDB request error:", error)

        return [], False


# =========================================
# TMDB RECOMMENDATIONS
# =========================================

def get_tmdb_recommendations(
    movie_id,
    offset,
    limit
):

    return get_tmdb_movie_list(

        endpoint="recommendations",

        movie_id=movie_id,

        offset=offset,

        limit=limit,

        source="TMDB"

    )


# =========================================
# TMDB SIMILAR MOVIES
# =========================================

def get_tmdb_similar_movies(
    movie_id,
    offset,
    limit
):

    return get_tmdb_movie_list(

        endpoint="similar",

        movie_id=movie_id,

        offset=offset,

        limit=limit,

        source="TMDB Similar"

    )


# =========================================
# DISCOVER MOVIES BY GENRE
# =========================================

def discover_movies(
    movie_id,
    offset,
    limit
):

    movie_details = get_movie_details(movie_id)

    if not movie_details:
        return [], False

    genres = movie_details.get("genres", [])

    if not genres:
        return [], False

    genre_id = genres[0]

    page = (offset // 20) + 1

    position_in_page = offset % 20

    url = (
        "https://api.themoviedb.org/3/"
        "discover/movie"
    )

    params = {

        "api_key": TMDB_API_KEY,

        "language": "en-US",

        "with_genres": genre_id,

        "sort_by": "popularity.desc",

        "page": page

    }

    try:

        response = requests.get(
            url,
            params=params,
            timeout=10
        )

        if response.status_code != 200:
            return [], False

        data = response.json()

        all_movies = [

            movie

            for movie in data.get("results", [])

            if movie.get("id") != movie_id

        ]

        selected_movies = all_movies[
            position_in_page:
            position_in_page + limit
        ]

        formatted_movies = format_tmdb_movies(
            selected_movies,
            "Genre Discovery"
        )

        has_more = (

            position_in_page + limit
            < len(all_movies)

            or

            page < data.get("total_pages", 1)

        )

        return formatted_movies, has_more

    except requests.exceptions.RequestException as error:

        print("Discover error:", error)

        return [], False


# =========================================
# ML RECOMMENDATIONS
# =========================================

def get_ml_recommendations(
    movie_position,
    offset,
    limit
):

    selected_movie_vector = vectors[
        movie_position
    ].reshape(1, -1)

    distances = cosine_similarity(
        selected_movie_vector,
        vectors
    )[0]

    sorted_movies = sorted(

        list(enumerate(distances)),

        key=lambda item: item[1],

        reverse=True

    )[1:]

    recommendations = []

    current_position = offset

    while (
        current_position < len(sorted_movies)
        and len(recommendations) < limit
    ):

        position, score = sorted_movies[
            current_position
        ]

        current_position += 1

        try:

            recommended_movie_id = int(
                movies.iloc[position]["movie_id"]
            )

            movie_details = get_movie_details(
                recommended_movie_id
            )

            if movie_details:

                movie_details[
                    "similarity_score"
                ] = round(
                    float(score),
                    3
                )

                movie_details["source"] = "ML"

                recommendations.append(
                    movie_details
                )

        except Exception as error:

            print(
                "ML movie error:",
                error
            )

    has_more = (
        current_position < len(sorted_movies)
    )

    return (
        recommendations,
        has_more,
        current_position
    )


# =========================================
# RECOMMENDATION ROUTE
# =========================================

@app.route("/recommend")
def recommend():

    movie_name = request.args.get(
        "movie",
        ""
    ).strip()

    movie_id = request.args.get(
        "movie_id",
        ""
    ).strip()

    strategy = request.args.get(
        "strategy",
        ""
    ).strip()

    try:

        offset = int(
            request.args.get("offset", 0)
        )

    except ValueError:

        offset = 0

    try:

        limit = int(
            request.args.get("limit", 5)
        )

    except ValueError:

        limit = 5

    offset = max(0, offset)

    limit = max(1, min(limit, 10))

    if not movie_name or not movie_id:

        return jsonify({

            "error":
            "Please select a movie from suggestions."

        }), 400

    try:

        movie_id = int(movie_id)

    except ValueError:

        return jsonify({

            "error":
            "Invalid movie ID."

        }), 400

    # =====================================
    # FIND MOVIE IN ML DATASET
    # =====================================

    matching_positions = np.where(

        movies["movie_id"].values == movie_id

    )[0]

    # =====================================
    # STRATEGY: ML
    # =====================================

    if strategy == "ml":

        if len(matching_positions) == 0:

            return jsonify({

                "selected_movie": movie_name,

                "recommendations": [],

                "recommendation_source": "ML",

                "strategy": "ml",

                "has_more": False,

                "next_offset": offset

            })

        movie_position = int(
            matching_positions[0]
        )

        recommendations, has_more, next_offset = (
            get_ml_recommendations(

                movie_position,

                offset,

                limit

            )
        )

        return jsonify({

            "selected_movie": movie_name,

            "recommendations": recommendations,

            "recommendation_source": "Machine Learning",

            "strategy": "ml",

            "has_more": has_more,

            "next_offset": next_offset

        })

    # =====================================
    # STRATEGY: TMDB RECOMMENDATIONS
    # =====================================

    if strategy == "tmdb_recommendations":

        recommendations, has_more = (
            get_tmdb_recommendations(

                movie_id,

                offset,

                limit

            )
        )

        return jsonify({

            "selected_movie": movie_name,

            "recommendations": recommendations,

            "recommendation_source":
            "TMDB Recommendations",

            "strategy":
            "tmdb_recommendations",

            "has_more": has_more

        })

    # =====================================
    # STRATEGY: TMDB SIMILAR
    # =====================================

    if strategy == "tmdb_similar":

        recommendations, has_more = (
            get_tmdb_similar_movies(

                movie_id,

                offset,

                limit

            )
        )

        return jsonify({

            "selected_movie": movie_name,

            "recommendations": recommendations,

            "recommendation_source":
            "TMDB Similar Movies",

            "strategy": "tmdb_similar",

            "has_more": has_more

        })

    # =====================================
    # STRATEGY: GENRE DISCOVERY
    # =====================================

    if strategy == "genre":

        recommendations, has_more = (
            discover_movies(

                movie_id,

                offset,

                limit

            )
        )

        return jsonify({

            "selected_movie": movie_name,

            "recommendations": recommendations,

            "recommendation_source":
            "Genre Based Discovery",

            "strategy": "genre",

            "has_more": has_more

        })

    # =====================================
    # INITIAL REQUEST
    # =====================================

    # First preference: ML

    if len(matching_positions) > 0:

        movie_position = int(
            matching_positions[0]
        )

        recommendations, has_more, next_offset = (
            get_ml_recommendations(

                movie_position,

                offset,

                limit

            )
        )

        if recommendations:

            return jsonify({

                "selected_movie": movie_name,

                "recommendations": recommendations,

                "recommendation_source":
                "Machine Learning",

                "strategy": "ml",

                "has_more": has_more,

                "next_offset": next_offset

            })

    # Second preference:
    # TMDB recommendations

    recommendations, has_more = (
        get_tmdb_recommendations(

            movie_id,

            offset,

            limit

        )
    )

    if recommendations:

        return jsonify({

            "selected_movie": movie_name,

            "recommendations": recommendations,

            "recommendation_source":
            "TMDB Recommendations",

            "strategy":
            "tmdb_recommendations",

            "has_more": has_more

        })

    # Third preference:
    # Similar movies

    recommendations, has_more = (
        get_tmdb_similar_movies(

            movie_id,

            offset,

            limit

        )
    )

    if recommendations:

        return jsonify({

            "selected_movie": movie_name,

            "recommendations": recommendations,

            "recommendation_source":
            "TMDB Similar Movies",

            "strategy": "tmdb_similar",

            "has_more": has_more

        })

    # Final fallback:
    # Genre discovery

    recommendations, has_more = (
        discover_movies(

            movie_id,

            offset,

            limit

        )
    )

    if recommendations:

        return jsonify({

            "selected_movie": movie_name,

            "recommendations": recommendations,

            "recommendation_source":
            "Genre Based Discovery",

            "strategy": "genre",

            "has_more": has_more

        })

    # Nothing found

    return jsonify({

        "selected_movie": movie_name,

        "recommendations": [],

        "recommendation_source": "None",

        "strategy": None,

        "has_more": False,

        "error":
        "No recommendations were found."

    })


# =========================================
# RUN APP
# =========================================

if __name__ == "__main__":

    app.run(debug=True)
