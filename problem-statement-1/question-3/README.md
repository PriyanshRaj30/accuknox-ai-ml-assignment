# Simple script that reads a list of users from a CSV file and saves them into a local SQLite database.

## What it does

- Reads `users.csv`
- Creates a `users.db` database (if it doesn’t already exist)
- Stores each user’s name and email
- Skips any rows that are missing a name or email
- Ignores duplicate emails
- Prints all the users currently in the database
