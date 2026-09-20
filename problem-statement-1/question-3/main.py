import csv
import sqlite3

CSV_FILE = "users.csv"
DB_FILE = "users.db"


def create_table(connection):
    connection.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE
        )
    """)


def import_users(connection):
    with open(CSV_FILE, "r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        users = [
            (row["name"].strip(), row["email"].strip())
            for row in reader
            if row.get("name") and row.get("email")
        ]

    connection.executemany(
        "INSERT OR IGNORE INTO users (name, email) VALUES (?, ?)",
        users
    )

    connection.commit()


def display_users(connection):
    cursor = connection.execute(
        "SELECT id, name, email FROM users"
    )

    print("Users currently in the database:")

    for user in cursor.fetchall():
        print(user)


def main():
    with sqlite3.connect(DB_FILE) as connection:
        create_table(connection)
        import_users(connection)
        display_users(connection)


if __name__ == "__main__":
    main()