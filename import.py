import csv
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


def main():
    db.execute("CREATE TABLE users (id SERIAL PRIMARY KEY, name VARCHAR NOT NULL UNIQUE, password VARCHAR NOT NULL,"
               "email VARCHAR NOT NULL)")
    db.execute("CREATE TABLE books (isbn VARCHAR UNIQUE PRIMARY KEY, title VARCHAR NOT NULL, author VARCHAR NOT NULL,"
               "year VARCHAR NOT NULL)")
    db.execute("CREATE TABLE reviews (isbn VARCHAR NOT NULL, userName VARCHAR NOT NULL, comment VARCHAR NOT NULL,"
               "rating SMALLINT NOT NULL CONSTRAINT Invalid_Rating CHECK (rating <=5 AND rating>=1),"
               "time VARCHAR NOT NULL)")
    file = open("books.csv", 'r')
    reader = csv.reader(file)
    for isbn, title, author, year in reader:
        db.execute("INSERT INTO books (isbn, title, author, year) VALUES (:isbn, :title, :author, :year)",
                   {"isbn": isbn, "title": title, "author": author, "year": year})
        db.commit()
        print(f"Added book with {isbn, title, author, year}")


main()
