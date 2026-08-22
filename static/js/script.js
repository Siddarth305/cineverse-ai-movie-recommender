const movieInput = document.getElementById("movieInput");
const recommendButton = document.getElementById("recommendButton");
const suggestions = document.getElementById("suggestions");
const message = document.getElementById("message");

const resultsTitle = document.getElementById("resultsTitle");
const recommendationSource = document.getElementById(
    "recommendationSource"
);

const recommendations = document.getElementById(
    "recommendations"
);

const loadMoreButton = document.getElementById(
    "loadMoreButton"
);

const loadMoreContainer = document.querySelector(
    ".load-more-container"
);


let searchTimeout = null;
let selectedMovieId = null;

let currentMovieName = null;
let currentOffset = 0;
let currentStrategy = null;

const LIMIT = 5;


/* =========================================
   SEARCH WHILE USER TYPES
========================================= */

movieInput.addEventListener("input", function () {

    selectedMovieId = null;

    clearTimeout(searchTimeout);

    const query = movieInput.value.trim();

    if (query.length < 2) {

        suggestions.innerHTML = "";

        return;
    }


    searchTimeout = setTimeout(() => {

        searchMovies(query);

    }, 350);

});


/* =========================================
   SEARCH TMDB
========================================= */

async function searchMovies(query) {

    try {

        const response = await fetch(
            `/search?query=${encodeURIComponent(query)}`
        );

        const movies = await response.json();

        showSuggestions(movies);

    } catch (error) {

        console.error("Search error:", error);

        suggestions.innerHTML = "";

    }

}


/* =========================================
   SHOW SUGGESTIONS
========================================= */

function showSuggestions(movies) {

    suggestions.innerHTML = "";

    if (!movies || movies.length === 0) {
        return;
    }


    movies.forEach(movie => {

        const suggestion = document.createElement("div");

        suggestion.classList.add("suggestion-item");


        const year = movie.release_date
            ? movie.release_date.substring(0, 4)
            : "N/A";


        suggestion.textContent =
            `${movie.title} (${year})`;


        suggestion.addEventListener("click", function () {

            movieInput.value = movie.title;

            selectedMovieId = movie.movie_id;

            suggestions.innerHTML = "";

        });


        suggestions.appendChild(suggestion);

    });

}


/* =========================================
   RECOMMEND BUTTON
========================================= */

recommendButton.addEventListener(
    "click",
    startRecommendations
);


/* =========================================
   ENTER KEY
========================================= */

movieInput.addEventListener(
    "keydown",
    function (event) {

        if (event.key === "Enter") {

            suggestions.innerHTML = "";

            startRecommendations();

        }

    }
);


/* =========================================
   START NEW RECOMMENDATION SEARCH
========================================= */

async function startRecommendations() {

    const movieName = movieInput.value.trim();


    if (!movieName) {

        message.textContent =
            "Search and select a movie first.";

        return;
    }


    if (!selectedMovieId) {

        message.textContent =
            "Please select a movie from the suggestions.";

        return;
    }


    currentMovieName = movieName;

    currentOffset = 0;

    currentStrategy = null;


    recommendations.innerHTML = "";

    resultsTitle.textContent = "";

    recommendationSource.textContent = "";

    loadMoreContainer.style.display = "none";


    await loadRecommendations(true);

}


/* =========================================
   LOAD RECOMMENDATIONS
========================================= */

async function loadRecommendations(isNewSearch = false) {

    if (!currentMovieName || !selectedMovieId) {
        return;
    }


    if (isNewSearch) {

        message.textContent =
            "AI is discovering movies for you...";

    } else {

        loadMoreButton.disabled = true;

        loadMoreButton.innerHTML =
            "<span>Loading...</span>";

    }


    try {

        let url =
            `/recommend?movie=${encodeURIComponent(currentMovieName)}` +
            `&movie_id=${selectedMovieId}` +
            `&offset=${currentOffset}` +
            `&limit=${LIMIT}`;


        if (currentStrategy) {

            url +=
                `&strategy=${encodeURIComponent(currentStrategy)}`;

        }


        const response = await fetch(url);

        const data = await response.json();


        if (!response.ok) {

            message.textContent =
                data.error || "Something went wrong.";

            loadMoreContainer.style.display = "none";

            return;

        }


        if (isNewSearch) {

            message.textContent = "";


            resultsTitle.textContent =
                `Because you liked "${data.selected_movie}"`;


            recommendationSource.textContent =
                data.recommendation_source || "AI";

        }


        if (!currentStrategy) {

            currentStrategy =
                data.strategy || null;

        }


        const movieList =
            data.recommendations || [];


        if (movieList.length === 0) {

            if (currentOffset === 0) {

                message.textContent =
                    "No recommendations were found.";

            } else {

                message.textContent =
                    "You've reached the end of available recommendations.";

            }


            loadMoreContainer.style.display = "none";

            return;

        }


        movieList.forEach((movie, index) => {

            createMovieCard(movie, index);

        });


        currentOffset += movieList.length;


        if (data.has_more) {

            loadMoreContainer.style.display = "flex";

        } else {

            loadMoreContainer.style.display = "none";

        }


        message.textContent = "";


    } catch (error) {

        console.error(
            "Recommendation error:",
            error
        );

        message.textContent =
            "Unable to connect to the server.";

    } finally {

        loadMoreButton.disabled = false;

        loadMoreButton.innerHTML =
            "<span>Load More</span><span>↓</span>";

    }

}


/* =========================================
   CREATE MOVIE CARD
========================================= */

function createMovieCard(movie, index) {

    const movieCard =
        document.createElement("article");


    movieCard.classList.add("movie-card");


    movieCard.style.animationDelay =
        `${Math.min(index * 0.08, 0.4)}s`;


    const posterHTML = movie.poster
        ? `<img src="${movie.poster}" alt="${movie.title} poster">`
        : `<div class="no-poster">
                No Poster Available
           </div>`;


    const releaseYear = movie.release_date
        ? movie.release_date.substring(0, 4)
        : "N/A";


    const rating =
        movie.rating !== null &&
        movie.rating !== undefined
            ? Number(movie.rating).toFixed(1)
            : "N/A";


    let recommendationText =
        "AI Recommendation";


    if (
        movie.similarity_score !== null &&
        movie.similarity_score !== undefined
    ) {

        recommendationText =
            `ML Similarity: ${movie.similarity_score}`;

    } else if (movie.source) {

        recommendationText =
            `Recommended by ${movie.source}`;

    }


    movieCard.innerHTML = `

        ${posterHTML}

        <div class="movie-info">

            <h3>${movie.title}</h3>

            <div class="movie-meta">

                <span>⭐ ${rating}</span>

                <span>📅 ${releaseYear}</span>

            </div>


            <p class="overview">

                ${movie.overview ||
                "No overview available for this movie."}

            </p>


            <p class="similarity">

                ${recommendationText}

            </p>

        </div>
    `;


    recommendations.appendChild(movieCard);

}


/* =========================================
   LOAD MORE BUTTON
========================================= */

loadMoreButton.addEventListener(
    "click",
    function () {

        loadRecommendations(false);

    }
);