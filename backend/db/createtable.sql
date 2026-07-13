CREATE TABLE movies (
    id       VARCHAR(10)  PRIMARY KEY,
    title    VARCHAR(100) NOT NULL,
    year     INTEGER      NOT NULL,
    director VARCHAR(100) NOT NULL
);

CREATE TABLE stars (
    id        VARCHAR(10)  PRIMARY KEY,
    name      VARCHAR(100) NOT NULL,
    birthYear INTEGER
);

CREATE TABLE stars_in_movies (
    starId  VARCHAR(10) NOT NULL,
    movieId VARCHAR(10) NOT NULL,
    FOREIGN KEY (starId)  REFERENCES stars(id),
    FOREIGN KEY (movieId) REFERENCES movies(id)
);

CREATE TABLE genres (
    id   INTEGER AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(32) NOT NULL
);

CREATE TABLE genres_in_movies (
    genreId INTEGER     NOT NULL,
    movieId VARCHAR(10) NOT NULL,
    FOREIGN KEY (genreId) REFERENCES genres(id),
    FOREIGN KEY (movieId) REFERENCES movies(id)
);

CREATE TABLE ratings (
    movieId  VARCHAR(10) NOT NULL,
    rating   FLOAT       NOT NULL,
    numVotes INTEGER     NOT NULL,
    FOREIGN KEY (movieId) REFERENCES movies(id)
);