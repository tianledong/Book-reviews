import os

import requests

from helper import login_required
from flask import Flask, session, render_template, request, redirect, jsonify
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from datetime import datetime

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


@app.route("/")
def index():
    return render_template("landing.html")


@app.route("/login", methods=["POST", "GET"])
def login():
    session.clear()
    if request.method == "GET":
        return render_template("login.html")
    elif request.method == "POST":
        login_username = request.form.get("login_username")
        login_password = request.form.get("login_password")

        if not login_username:
            return render_template("error.html", error_message="Please enter username!")

        if not login_password:
            return render_template("error.html", error_message="Please enter password!")

        login_username = login_username.lower()

        row = db.execute("SELECT * FROM users WHERE name = :name", {"name": login_username})
        user = row.fetchone()
        if user is None:
            return render_template("error.html", error_message="Invalid username/password. Please try again!")
        else:
            if user.password == str(login_password) and user.name == login_username:
                session["name"] = user[1]
            return render_template("search.html")


@app.route("/register", methods=["POST", "GET"])
def register():
    session.clear()
    if request.method == "GET":
        return render_template("register.html")
    elif request.method == "POST":
        register_username = request.form.get("register_username")
        register_password = request.form.get("register_password")
        register_confirm_password = request.form.get("register_confirm_password")
        register_email = request.form.get("register_email")

        if not register_username:
            return render_template("error.html", error_message="Please enter username!")

        if not register_password:
            return render_template("error.html", error_message="Please enter password!")

        if not register_confirm_password or register_password != register_confirm_password:
            return render_template("error.html", error_message="Please confirm password!")

        if not register_email:
            return render_template("error.html", error_message="Please enter email!")

        register_username = register_username.lower()
        # search for the register name in db.
        exist_user = db.execute("SELECT * FROM users WHERE name = :name", {"name": register_username}).fetchone()

        if exist_user:
            return render_template("error.html", error_message="This user name is already been taken!")
        else:
            db.execute("INSERT INTO users (name, password, email) VALUES (:name, :password, :email)",
                       {"name": register_username, "password": register_password, "email": register_email})
            db.commit()
            return redirect("/login")


@app.route("/logout")
def logout():
    session.clear()
    return render_template("logout.html")


@app.route("/search", methods=["POST", "GET"])
@login_required
def search():
    if request.method == "GET":
        return render_template("search.html")
    elif request.method == "POST":
        post_data = request.form.get("search")

        if not post_data:
            return render_template("error.html", error_message="Please enter search information!")

        search_data = '%' + str(post_data).title() + '%'

        book_row = db.execute(
            "SELECT * FROM books WHERE isbn LIKE :data OR title LIKE :data OR author LIKE :data LIMIT 12",
            {"data": search_data})
        result_books = book_row.fetchall()
        if result_books:
            return render_template("search.html", result_books=result_books, post_data=post_data)
        else:
            return render_template("error.html", error_message="No book found. Please search again!")


@app.route("/api/<string:isbn>")
@login_required
def api(isbn):
    target_row = db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn": isbn})
    if not target_row:
        return jsonify({"error": "Invalid book ISBN"}), 422
    review_count = db.execute("SELECT isbn, COUNT(*) FROM reviews GROUP BY isbn HAVING isbn = :isbn",
                              {"isbn": isbn}).fetchone()
    average_score = db.execute("SELECT AVG(rating) FROM reviews WHERE isbn = :isbn", {"isbn": isbn}).fetchone()
    target_book = target_row.fetchone()
    res = dict(target_book)
    if review_count:
        res["review_count"] = review_count[0]
    else:
        res["review_count"] = 0

    if average_score:
        res["average_score"] = average_score[0]

    return jsonify(res), 400


@app.route("/book/<string:isbn>", methods=["POST", "GET"])
@login_required
def book(isbn):
    target_row = db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn": isbn})

    if not target_row:
        return render_template("error.html", error_message="Could not find the page!")

    target_book = target_row.fetchone()

    comments = db.execute("SELECT * FROM reviews WHERE isbn = :isbn", {"isbn": isbn}).fetchall()

    url = f"https://openlibrary.org/isbn/{isbn}.json"

    res = requests.get(url)
    publisher = res.json()['publishers'][0]
    if request.method == "GET":
        return render_template("book.html", target_book=target_book, comments=comments, publisher=publisher)
    elif request.method == "POST":
        user_rating = request.form.get("rating")
        user_comment = request.form.get("comment")
        user_name = session["name"]
        now = datetime.now()
        user_time = now.strftime("%d/%m/%Y %H:%M:%S")

        if not user_rating:
            return render_template("error.html", error_message="Please rate before submit!")
        if not user_comment:
            return render_template("error.html", error_message="Please leave some comment before submit!")

        exist_user = db.execute("SELECT * FROM reviews WHERE userName = :userName AND isbn = :isbn",
                                {"userName": user_name, "isbn": isbn}).fetchone()
        if exist_user:
            return render_template("error.html", error_message="You have rated this book!")

        db.execute(
            "INSERT INTO reviews (isbn, userName, comment, rating, time) "
            "VALUES (:isbn, :userName, :comment, :rating, :time)",
            {"isbn": isbn, "userName": user_name, "comment": user_comment, "rating": user_rating, "time": user_time})
        db.commit()

        comments = db.execute("SELECT * FROM reviews WHERE isbn = :isbn", {"isbn": isbn}).fetchall()
        return render_template("book.html", target_book=target_book, comments=comments, average_rating=average_rating,
                               ratings_count=ratings_count)
