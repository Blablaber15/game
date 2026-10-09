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
    (
         "5. Последняя дата выпуска фильма для каждого режиссера:",
        """
        SELECT name, MAX(movies.release_date) 
        FROM movies 
        JOIN directors ON movies.director_id = directors.id 
        GROUP BY name
        """
    ),
    (
        "6.Общая сумма бюджетов всех фильмов, за все фильмы:",
        """
        SELECT name, SUM(budget) 
        FROM movies
        JOIN directors ON movies.director_id=directors.id
        GROUP BY name
        """
    ),
    (
        "7.именами режиссера и количество фильмов, которые они срежиссировали.:",
        """
        SELECT name, COUNT(movies.id)
        FROM directors
        JOIN movies ON directors.id = movies.director_id
        GROUP BY name
        """
    ),
    (
        "7.названиями фильмов и количеством жанров у каждого фильма:",
        """
        SELECT title, COUNT(movies_genres.genre_id)
        FROM movies
        JOIN movies_genres ON movies.id = movies_genres.movie_id
        GROUP BY title
        """
        ),
]

with sqlite3.connect(DATABASE_PATH) as connection:
    for query_data in queries:
        label, sql, *parameters = query_data
        
        # ВАЖНО: Если параметров нет, выполняем чистый SQL
        if not parameters:
            result = connection.execute(sql).fetchone()
        else:
            # Если это кортеж внутри списка из-за распаковки, берем первый элемент
            if len(parameters) == 1 and isinstance(parameters[0], (list, tuple)):
                parameters = parameters[0]
                
            try:
                result = connection.execute(sql, parameters).fetchone()
            except sqlite3.InterfaceError as e:
                # Этот принт покажет, какой именно запрос сломался и что в параметрах
                print(f"\n❌ ОШИБКА в запросе: '{label}'")
                print(f"SQL код: {sql}")
                print(f"Что пришло в параметры (тип {type(parameters)}): {parameters}\n")
                raise e # останавливаем программу, чтобы вы увидели вывод
            
        print(label)
        print(result if result is not None else "Совпадений не найдено")


