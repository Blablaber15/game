import sqlite3
from pathlib import Path

DATABASE_PATH = Path(__file__).resolve().with_name("movie.db")

queries = [
    (
        "1. Самый популярный фильм и его бюджет:",
        """
        SELECT title, budget
        FROM movies
        ORDER BY popularity DESC
        LIMIT 1
        """,
    ),
    (
        "2. Самый дорогой фильм, вышедший в декабре 2009 года:",
        """
        SELECT title
        FROM movies
        WHERE release_date >= '2009-12-01'
          AND release_date < '2010-01-01'
        ORDER BY budget DESC
        LIMIT 1
        """,
    ),
    (
        '3. Фильм со слоганом "The battle within.":',
        """
        SELECT title
        FROM movies
        WHERE tagline = ?
        LIMIT 1
        """,
        ("The battle within.",),
    ),
    (
        "4. Фильм до 1980 года с рейтингом выше 8 и максимумом голосов:",
        """
        SELECT title, vote_count
        FROM movies
        WHERE release_date < '1980-01-01'
          AND vote_average > 8
        ORDER BY vote_count DESC
        LIMIT 1
        """,
    ),
]

with sqlite3.connect(DATABASE_PATH) as connection:
    for query_data in queries:
        label, sql, *parameters = query_data
        result = connection.execute(sql, *parameters).fetchone()
        print(label)
        print(result if result is not None else "Совпадений не найдено")
