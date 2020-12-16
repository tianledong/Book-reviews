# Book-reviews

Harvard CS50 - Web Programming with Python and JavaScript

# TODO #

Need to find a replacement for Goodreads as of December 8th 2020, Goodreads is no longer issuing new developer keys for
our public developer API and plans to retire these tools. :(

# Use the app #

See the live web app [here](https://book-reviews-td.herokuapp.com/).

# Features # 

- Sign up, Sign in, Sign out: Site users are able to register with a username, password, and email address. Then they
  are able to sign in and sign out of the web app.
- Search: Once sign in, users are allowed to search books using book name, author or ISBN among 5,000 books in DB.
- Comment: Once sign in, users are allowed to leave comments and rate books.
- View: Once sign in, users can view others comments and ratings and see real-time rate data from Goodreads API
- Get: if user makes a GET request to /api/isbn, they will access this app’s API