import sqlite3
import requests

API_URL = "https://bookie.com/api/books"
DATABASE = "books.db"


def fetch_books(url: str) -> list[dict]:
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        data = response.json()

        if not isinstance(data, list):
            raise ValueError("API response must be a list of books.")

        return data

    except requests.RequestException as exc:
        raise RuntimeError(f"Failed to fetch books: {exc}") from exc

    except ValueError as exc:
        raise RuntimeError(f"Invalid API response: {exc}") from exc


def initialize_database(db_path: str) -> None:
    with sqlite3.connect(db_path) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS books (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                author TEXT NOT NULL,
                publication_year INTEGER
            )
        """)


def save_books(db_path: str, books: list[dict]) -> None:
    records = []

    for book in books:
        records.append((
            book.get("title"),
            book.get("author"),
            book.get("publication_year")
        ))

    with sqlite3.connect(db_path) as conn:
        conn.executemany(
            """
            INSERT INTO books (
                title,
                author,
                publication_year
            )
            VALUES (?, ?, ?)
            """,
            records
        )


def display_books(db_path: str) -> None:
    with sqlite3.connect(db_path) as conn:
        cursor = conn.execute(
            "SELECT id, title, author, publication_year FROM books"
        )

        for book in cursor.fetchall():
            print(book)


def main() -> None:
    books = fetch_books(API_URL)

    initialize_database(DATABASE)
    save_books(DATABASE, books)
    display_books(DATABASE)


if __name__ == "__main__":
    main()