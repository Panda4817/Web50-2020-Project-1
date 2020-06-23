import os
import datetime
import requests
from tempfile import mkdtemp

from flask import Flask, flash, redirect, render_template, request, session, jsonify
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from dotenv import load_dotenv
from login_helper import login_required

# Set up flask app
app = Flask(__name__)

# Load environment variable
load_dotenv("C:/Users/Kanta/Documents.env")

# Make sure noone can edit to session data
app.secret_key="SECRET_KEY"

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")
if not os.getenv("GOODREADS_API_KEY"):
    raise RuntimeError("GOODREADS_API_KEY is not set")


# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Configure session to use filesystem
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

# Get goodreads api key
GOODREADS_API_KEY = os.getenv("GOODREADS_API_KEY")

# Global user variable
user = ""

@app.route("/")
def index():
    # Check if user is logged in, if so nav bar links will change
    if session.get("user_id") is None:    
        return render_template("index.html")
    global user
    user = db.execute("SELECT * FROM users WHERE id = :user_id", {"user_id":session["user_id"]}).fetchall()
    return render_template("index.html", username=user[0]["username"])

@app.route("/login", methods=["GET", "POST"])
def login():
    # Forget any user_id
    session.clear()
    # Check if method is get
    if request.method == "GET":
        return render_template("login.html")
    # Else method is post
    else:
        # Ensure username was submitted
        username = request.form.get("username")
        if not username:
            flash("Must provide username", "error")
            return render_template("login.html")

        password = request.form.get("password")
        # Ensure password was submitted
        if not password:
            flash("Must provide password", "error")
            return render_template("login.html")
        
        # check username
        user = db.execute("SELECT * FROM users WHERE username = :username", {"username":username}).fetchall()
        if db.execute("SELECT * FROM users WHERE username = :username", {"username":username}).rowcount == 0:
            flash("Must provide valid username", "error")
            return render_template("login.html")
        
        # check password
        if check_password_hash(user[0]["hash"], password) == False:
            flash("Must provide valid password", "error")
            return render_template("login.html")
        
        # Remember user using sessions
        session["user_id"] = user[0]["id"]

        return redirect("/")

@app.route("/register", methods=["GET", "POST"])
def register():
    # Check if method is get
    if request.method == "GET":
        return render_template("register.html")
    else:
        # Get username from form
        username = request.form.get("username")

        # Ensure username was submitted
        if not username:
            flash("Must provide username", "error")
            return render_template("register.html")

        # Check username only contains alphanumeric characters
        for i in range(len(username)):
            if not username[i].isalnum():
                flash("Username must only have letters and/or numbers", "error")
                return render_template("register.html")

        # Check if username exists
        if db.execute("SELECT username FROM users WHERE username = :username_check", {"username_check":username}).rowcount != 0:
            flash("Username taken", "error")
            return render_template("register.html")

        # Get password from form
        password = request.form.get("password")

        # Ensure password and confirmation fields filled out
        if not password or not request.form.get("confirmation"):
            flash("Must provide password", "error")
            return render_template("register.html")
        
        # Ensure password is at last 6 characters
        if len(password) < 6:
            flash("Password too short", "error")
            return render_template("register.html")
        
        # Check password field and confirmation field match
        if password != request.form.get("confirmation"):
            flash("Password fields do not match", "error")
            return render_template("register.html")
        
        # Generate password hash
        hash = generate_password_hash(password)

        # Insert new data into database
        db.execute("INSERT INTO users (username, hash) VALUES (:username, :hash)", {"username":username, "hash":hash})
        db.commit()

        # Redirect user to login form with a flash message
        flash("You have sucessfully registered, now you can login")
        return render_template("login.html")

@app.route("/user_check", methods=["POST"])
def username_check():
    # real-time username check through AJAX
    try:
        username = request.form["username_input"]
        if username != "" and username != None:
            for i in range(len(username)):
                if not username[i].isalnum():
                    result="Username must only contain letters and/or numbers"
                    return result
            if db.execute("SELECT username FROM users WHERE username = :username_check", {"username_check":username}).rowcount > 0:
                result = "Username unavailable"
                return result
            else:
                result = "Username available"
                return result
        else:
            result = "Username is required field"
            return result
    except Exception as e:
        return e

@app.route("/log_out", methods=["GET"])
def log_out():
    # Forget any user_id
    session.clear()
    global user
    user = ""

    # Redirect user to login form
    return redirect("/")

@app.route("/search", methods=["GET", "POST"])
@login_required
def search():
    # Check if method is get
    if request.method == "GET":
        global user
        return render_template("search.html", username=user[0]["username"])
    # else it is post
    else:
        # Get user input
        isbn = request.form.get("isbn")
        title = request.form.get("title")
        author = request.form.get("author")

        # Check at least one input field is filled in
        if not isbn and not title and not author:
            return "<h2 style='color: red;'>Must complete at least 1 search field</h2>"
        
        # Check all combinations of fields inputted (could be one, two or all 3)
        if isbn and not title and not author:
            isbn = '%' + isbn + '%'    
            search_results = db.execute("SELECT * FROM books WHERE isbn ILIKE :isbn", {"isbn": isbn}).fetchall()
        if title and not isbn and not author:
            title = '%' + title + '%'
            search_results = db.execute("SELECT * FROM books WHERE title ILIKE :title", {"title": title}).fetchall()
        if author and not isbn and not title:
            author = '%' + author + '%'
            search_results = db.execute("SELECT * FROM books WHERE author ILIKE :author", {"author": author}).fetchall()
        
        if isbn and title and not author:
            isbn = '%' + isbn + '%'
            title = '%' + title + '%'
            search_results = db.execute("SELECT * FROM books WHERE isbn ILIKE :isbn AND title ILIKE :title", 
                {"isbn": isbn, "title": title}).fetchall()
        elif isbn and author and not title:
            isbn = '%' + isbn + '%'
            author = '%' + author + '%'
            search_results = db.execute("SELECT * FROM books WHERE isbn ILIKE :isbn AND author ILIKE :author", 
                {"isbn": isbn, "author": author}).fetchall()
        elif author and title and not isbn:
            title = '%' + title + '%'
            author = '%' + author + '%'
            search_results = db.execute("SELECT * FROM books WHERE author ILIKE :author AND title ILIKE :title", 
                {"author": author, "title": title}).fetchall()
        else:
            isbn = '%' + isbn + '%'
            title = '%' + title + '%'
            author = '%' + author + '%'
            search_results = db.execute("SELECT * FROM books WHERE isbn ILIKE :isbn AND title ILIKE :title AND author ILIKE :author", 
                {"isbn": isbn, "title": title, "author": author}).fetchall()
        
        # Check rowcount of results and if 0, means no books found
        if len(search_results) == 0:
            return "<h2>No books found</h2>"    
    
    return render_template("search_results.html", search_results=search_results)

@app.route("/search/<string:book_isbn>", methods=["GET", "POST"])
@login_required
def book(book_isbn):
    # check method is get
    if request.method == "GET":
        
        # Make sure book exists and get book data.
        book = db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn": book_isbn}).fetchone()
        if book is None:
            flash("404 ISBN not found", "error")
            return render_template("search.html", username=user[0]['username'])
        
        # Get all book reviews.
        book_reviews = db.execute("SELECT * FROM reviews WHERE book_isbn = :isbn ORDER BY date_time DESC",
            {"isbn": book_isbn}).fetchall()
        
        # Goodreads data
        res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": GOODREADS_API_KEY, "isbns": book_isbn})
        if res.status_code != 200:
            raise Exception("ERROR: API request unsuccessful.")
        data = res.json()
        if data['books'][0]['work_ratings_count'] == 0 or not data['books'][0]['work_ratings_count']:
                data['books'][0]['work_ratings_count'] = "No ratings"
                data['books'][0]['average_rating'] = "No rating to show"
        return render_template("book.html", 
            book=book, book_reviews=book_reviews, username=user[0]["username"], 
            g_rating=data['books'][0]['average_rating'], g_num_rating=data['books'][0]['work_ratings_count'])
    # else method is post for review submission
    else:
        
        # Check rating filled out
        rating =  request.form.get("rating")
        if not rating:
            book = db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn": book_isbn}).fetchone()
            book_reviews = db.execute("SELECT * FROM reviews WHERE book_isbn = :isbn ORDER BY date_time DESC",
                {"isbn": book_isbn}).fetchall()
            res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": GOODREADS_API_KEY, "isbns": book_isbn})
            if res.status_code != 200:
                raise Exception("ERROR: API request unsuccessful.")
            data = res.json()
            if data['books'][0]['work_ratings_count'] == 0 or not data['books'][0]['work_ratings_count']:
                data['books'][0]['work_ratings_count'] = "No ratings"
                data['books'][0]['average_rating'] = "No rating to show"
            flash("Must provide star rating", "error")
            return render_template("book.html", 
                book=book, book_reviews=book_reviews, username=user[0]["username"], 
                g_rating=data['books'][0]['average_rating'], g_num_rating=data['books'][0]['work_ratings_count'])
        rating = int(rating)
        
        # Check opinion provided
        review = request.form.get("review")
        if not review:
            book = db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn": book_isbn}).fetchone()
            book_reviews = db.execute("SELECT * FROM reviews WHERE book_isbn = :isbn ORDER BY date_time DESC",
                {"isbn": book_isbn}).fetchall()
            res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": GOODREADS_API_KEY, "isbns": book_isbn})
            if res.status_code != 200:
                raise Exception("ERROR: API request unsuccessful.")
            data = res.json()
            if data['books'][0]['work_ratings_count'] == 0 or not data['books'][0]['work_ratings_count']:
                data['books'][0]['work_ratings_count'] = "No ratings"
                data['books'][0]['average_rating'] = "No rating to show"
            flash("Must provide star opinion", "error")
            return render_template("book.html", 
                book=book, book_reviews=book_reviews, username=user[0]["username"], 
                g_rating=data['books'][0]['average_rating'], g_num_rating=data['books'][0]['work_ratings_count'])
        
        # Check if user has already provided a review for this book
        if db.execute("SELECT * FROM reviews WHERE user_id = :id AND book_isbn = :book_isbn", {"id": user[0]["id"], "book_isbn": book_isbn}).rowcount != 0:
            book = db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn": book_isbn}).fetchone()
            book_reviews = db.execute("SELECT * FROM reviews WHERE book_isbn = :isbn ORDER BY date_time DESC",
                {"isbn": book_isbn}).fetchall()
            res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": GOODREADS_API_KEY, "isbns": book_isbn})
            if res.status_code != 200:
                raise Exception("ERROR: API request unsuccessful.")
            data = res.json()
            if data['books'][0]['work_ratings_count'] == 0 or not data['books'][0]['work_ratings_count']:
                data['books'][0]['work_ratings_count'] = "No ratings"
                data['books'][0]['average_rating'] = "No rating to show"
            flash("Already reviewed book", "error")
            return render_template("book.html", 
                book=book, book_reviews=book_reviews, username=user[0]["username"], 
                g_rating=data['books'][0]['average_rating'], g_num_rating=data['books'][0]['work_ratings_count'])
        
        # if it passes the above checks, enter data into the reviews table in database
        db.execute("INSERT INTO reviews (book_isbn, user_id, review, rating) VALUES (:book_isbn, :id, :review, :rating)", 
            {"book_isbn": book_isbn, "id": user[0]["id"], "review": review, "rating": rating})
        db.commit()
    
    # Return book page with new review data
    book = db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn": book_isbn}).fetchone()
    book_reviews = db.execute("SELECT * FROM reviews WHERE book_isbn = :isbn ORDER BY date_time DESC",
        {"isbn": book_isbn}).fetchall()
    res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": GOODREADS_API_KEY, "isbns": book_isbn})
    if res.status_code != 200:
        raise Exception("ERROR: API request unsuccessful.")
    data = res.json()
    if data['books'][0]['work_ratings_count'] == 0 or not data['books'][0]['work_ratings_count']:
        data['books'][0]['work_ratings_count'] = "No ratings"
        data['books'][0]['average_rating'] = "No ratings to show"    
    flash("Review added")
    return render_template("book.html", 
        book=book, book_reviews=book_reviews, username=user[0]["username"], 
        g_rating=data['books'][0]['average_rating'], g_num_rating=data['books'][0]['work_ratings_count'])

@app.route("/api/<string:book_isbn>", methods=["GET"])
def book_api(book_isbn):
    # Make sure book exists and get book data.
    book = db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn": book_isbn}).fetchone()
    if book is None:
        return jsonify({"404 Error": "ISBN not found"}), 404

    # Get goodreads data if any
    res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": GOODREADS_API_KEY, "isbns": book_isbn})
    if res.status_code != 200:
        raise Exception("ERROR: API request unsuccessful.")
    data = res.json()
    if data['books'][0]['work_ratings_count'] == 0 or not data['books'][0]['work_ratings_count']:
        data['books'][0]['work_ratings_count'] = "0"
        data['books'][0]['average_rating'] = "None"   

    # Return json format
    return jsonify({
                "title": book.title,
                "author": book.author,
                "year": book.year,
                "isbn": book.isbn,
                "review_count": data['books'][0]['work_ratings_count'],
                "average_rating": data['books'][0]['average_rating']
            })

@app.route("/account", methods=["GET"])
@login_required
def account():
    # Account page shows user's reviews so query database for book data specific to user reviews data
    user_reviews = db.execute("SELECT * FROM books JOIN reviews ON books.isbn = reviews.book_isbn WHERE reviews.user_id = :id ORDER BY reviews.date_time DESC", 
        {"id": user[0]["id"]}).fetchall()
    return render_template("account.html", user_reviews=user_reviews, username=user[0]["username"])
