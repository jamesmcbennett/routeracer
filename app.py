import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///routeracer.db")

# Make sure API key is set
# if not os.environ.get("API_KEY"):
#    raise RuntimeError("API_KEY not set")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

###################################################################################
###################################################################################
###################################################################################

@app.route("/changepassword", methods=["GET", "POST"])
@login_required
def changepassword():

    if request.method == "POST":

        # Ensure old password was submitted
        if not request.form.get("oldpassword"):
            return apology("must provide existing password", 400)

        # Query database for password
        rows = db.execute("SELECT * FROM users WHERE id=:id", id=session["user_id"])

        # Ensure existing password is correct
        if not check_password_hash(rows[0]["hash"], request.form.get("oldpassword")):
            return apology("invalid existing password", 400)

        # Ensure password was submitted
        if not request.form.get("password"):
            return apology("must provide new password", 400)

        # Ensure confirmation password was submitted
        if not request.form.get("confirmation"):
            return apology("must confirm new password", 400)

        # Check that the new passwords match
        if request.form.get("password") != request.form.get("confirmation"):
            return apology("passwords do not match", 400)

        # Generate new hash for password and update database
        hash = generate_password_hash(request.form.get("password"))
        db.execute("UPDATE users SET hash=:hash WHERE id=:id", hash=hash, id=session["user_id"])

        # Redirect user to home page at the end of submitting a password change
        flash("Your password has been changed successfully.")
        return redirect("/")
    else:
        return render_template("changepassword.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 400)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 400)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 400)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

@app.route("/register", methods=["GET", "POST"])
def register():

    session.clear()

    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 400)

        # Ensure password was submitted
        elif not request.form.get("initials"):
            return apology("must provide initials", 400)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 400)

        # Ensure confirmation password was submitted
        elif not request.form.get("confirmation"):
            return apology("must provide password", 400)

        if request.form.get("password") != request.form.get("confirmation"):
            return apology("passwords do not match", 400)

        try:
            key = db.execute("INSERT INTO users (username, hash, initials) VALUES (:username, :hash, :initials)",
                             username=request.form.get("username"),
                             hash=generate_password_hash(request.form.get("password")),
                             initials=request.form.get("initials"))
        except:
            return apology("username is taken", 400)

        # Remember which user has logged in
        if key == None:
            return apology("error", 400)
        session["user_id"] = key

        # Redirect user to home page
        return redirect("/")

    else:
        return render_template("register.html")

###################################################################################
###################################################################################
###################################################################################

@app.route("/")
@login_required
def index():
    """Introduction page to the site"""

    # Get username to display in titles
    rows = db.execute("SELECT username FROM users WHERE id=:user_id", user_id=session["user_id"])
    username = rows[0]["username"]

    return render_template("index.html", username=username)


@app.route("/swims")
@login_required
def swims():
    """Show swims"""

    # Calculate total KM completed in each available race
    totalswims = db.execute(
        "SELECT race_name, SUM(ROUND(meters/1000,2)) as totalkilometers FROM swims WHERE user_id=:user_id GROUP BY race_name", user_id=session["user_id"])

    # List all swims by user
    swims = db.execute(
        "SELECT race_id, race_name, meters, time_stamp FROM swims WHERE user_id=:user_id", user_id=session["user_id"])


    # Get username to display in titles
    rows = db.execute("SELECT username FROM users WHERE id=:user_id", user_id=session["user_id"])
    username = rows[0]["username"]

    return render_template("swims.html", swims=swims, totalswims=totalswims, username=username)

@app.route("/map")
@login_required
def map():
    """Show map"""

    # Calculate total KM completed in each available race
    totalswims = db.execute(
    "SELECT race_name, SUM(ROUND(meters/1000,2)) as totalkilometers FROM swims WHERE user_id=:user_id GROUP BY race_name", user_id=session["user_id"])


    # Get username to display in titles
    rows = db.execute("SELECT username FROM users WHERE id=:user_id", user_id=session["user_id"])
    username = rows[0]["username"]

    return render_template("map.html", totalswims=totalswims, username=username)

@app.route("/addswim", methods=["GET", "POST"])
@login_required
def addswim():

    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("race"):
            return apology("must provide race", 400)

        # Ensure username was submitted
        elif not request.form.get("meters"):
            return apology("must provide meters", 400)

        elif not request.form.get("meters").isdigit():
            return apology("number of meters must be whole number", 400)

        # Not currently working. race_id=race_id so changed it to 1.
        # Find race ID from selected race name
        # race_id = db.execute("SELECT id FROM races WHERE race_name=:race_name",
        #            race_name=request.form.get("race"))

        # Get previous KM from current race
        prevKilometers = db.execute("SELECT kilometers FROM swims WHERE id=:user_id",
                    user_id=session["user_id"])

        db.execute("INSERT INTO swims(user_id, race_id, race_name, meters) VALUES (:user_id, :race_id, :race_name, :meters) ",
                   user_id=session["user_id"],
                   race_id=1,
                   race_name=request.form.get("race"),
                   meters=request.form.get("meters"),
                    )

        #db.execute("UPDATE swims SET kilometers = kilometers + :amount WHERE id=:user_id",
        #          amount=request.form.get("meters"), user_id=session["user_id"])

        flash("Swim Added")
        return redirect("/swims")
    else:
        rows = db.execute(
            "SELECT race_name FROM races;")
        return render_template("addswim.html", races=[row["race_name"] for row in rows])


@app.route("/races")
@login_required
def races():
    """Show races"""

    rows = db.execute("SELECT id, race_name, start, finish, distance, time FROM races")
    races = []
    for row in rows:
        races.append({
            "id": row["id"],
            "race_name": row["race_name"],
            "start": row["start"],
            "finish": row["finish"],
            "distance": row["distance"],
            "time": row["time"]
        })
    return render_template("races.html", races=races)






