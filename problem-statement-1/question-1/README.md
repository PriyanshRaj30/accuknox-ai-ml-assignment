
# Simple script that grabs a list of books from an API and dumps them into a local SQLite database.

## What it does

1. Hits `https://bookie.com/api/books`
2. Creates a `books.db` file (if it doesn’t already exist)
3. Stores the books in a table with title, author, and publication year
4. Prints everything out so you can see what got saved
