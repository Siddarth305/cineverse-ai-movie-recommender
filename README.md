# CineVerse AI Movie Recommender

CineVerse AI is a Flask-based movie recommendation web application that combines machine learning with TMDB data to help users discover movies similar to their selections.

## Features

- Search movies using the TMDB API
- Machine-learning recommendations using cosine similarity
- TMDB recommendations, similar movies, and genre-based discovery
- Movie posters, ratings, release dates, and overviews
- Responsive browser interface
- Ready for deployment with Gunicorn

## Live Demo

https://cineverse-ai-movie-recommender.onrender.com/

## Local Setup

```powershell
python -m pip install -r requirements.txt
$env:TMDB_API_KEY="your_tmdb_api_key"
python app.py
```

Open http://127.0.0.1:5000 in your browser.

The TMDB key must be provided as the `TMDB_API_KEY` environment variable. Never commit API keys to the repository.

## Deployment

The included `Procfile` runs the application with Gunicorn. On Render or another hosting provider, set `TMDB_API_KEY` in the service's environment variables and use:

```text
gunicorn --bind 0.0.0.0:$PORT app:app
```

## Technology

- Python
- Flask
- Pandas and NumPy
- Scikit-learn
- TMDB API
- HTML, CSS, and JavaScript
