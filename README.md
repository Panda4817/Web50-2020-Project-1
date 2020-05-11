# Web50 2020 Project 1 - Book review website

Users can register and then login to the website to leave reviews for books and see other reviews. Users can see data about the book like , author, publication year, ISBN, goodreads average rating and review count. There is also an API GET request which returns json formatted data about a book through its API.

## Set up

Created a PostgresSQL database via Heroku and created three tables: books, reviews and users.
I also created a .env file to set all my environment variables and load them automatically when flask is run.
the .env file contains DATABASE_URL, GOODREADS_KEY, FLASK_SECRET_KEY, FLASK_APP=path_to_application.py and FLASK_DEBUG=1. 

## import.py

A python program used to read and copy books.csv data into the books table in the psql database.

## application.py

This file contains all the routes and config for the web application.
The routes include: index, login, logout, register, account page, search page, book page and API.

## login_helpers.py

This file contains the function login_required that checks a user is logged in before they can go to certain pages on the website.

## templates folder

Contains all the html files that are rendered through routes in application.py.

## static folder

Contains app.js with some javascript functions used in real-time checking of username and password fields.
Contains styles.scss and styles.css with all css for all html pages. Most of the styling is through bootstrap 4.

## requirements.txt

A file containing all the Python packages I have used in this project.
