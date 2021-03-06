import os
from os import path
from flask import (
    Flask, flash, render_template,
    redirect, request, session, url_for)
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
if os.path.exists("env.py"):
    import env


app = Flask(__name__)

app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.secret_key = os.environ.get("SECRET_KEY")


mongo = PyMongo(app)


@app.route("/")
def Home():
    return render_template(
        "index.html")

# display all recpies
@app.route("/recipes")
def recipes():
    query = request.args.get("query")
    if not query:
        recipes = mongo.db.recipes.find().sort('added_on', -1)
    else:
        # Finds the recipe using keywords the user enters
        mongo.db.recipes.create_index([('$**', 'text')])
        recipes = mongo.db.recipes.find(
            {"$text": {"$search": query}}).limit(10)
    return render_template("recipes.html", recipes=recipes)


@app.route("/search", methods=["GET", "POST"])
def search():
    query = request.form.get("query")
    recipes = mongo.db.recipes.find(
            {"$text": {"$search": query}}).limit(10)
    return render_template("recipes.html", recipes=recipes)


# display full recpie
@app.route('/show_recipe/<recipe_id>')
def show_recipe(recipe_id):
    my_recipe = mongo.db.recipes.find_one({'_id': ObjectId(recipe_id)})
    all_categories = mongo.db.categories.find()
    mongo.db.recipes.update(
        my_recipe, {'$inc': {'views': 1}})
    return render_template(
        'show_recipe.html', recipe=my_recipe, categories=all_categories)

# register user
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # check if the usernmae already exist in db
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})
        if existing_user:
            flash("Username already exist")
            return redirect(url_for("register"))
        register = {
            "username": request.form.get("username").lower(),
            "password": generate_password_hash(request.form.get("password"))
        }
        mongo.db.users.insert_one(register)

        # put  the new user into 'session' cookie
        session["user"] = request.form.get("username").lower()
        flash("Registration Successful!")
        return redirect(url_for(
            "profile", username=session["user"]))
    return render_template("register.html")

# login user
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # check if usernameexist in db
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            # ensure hashed password matches userinput
            if check_password_hash(
                    existing_user["password"], request.form.get("password")):
                        session["user"] = request.form.get("username").lower()
                        flash("Welcome, {}".format(
                            request.form.get("username")))
                        return redirect(url_for(
                            "profile", username=session["user"]))
            else:
                # invalid password match
                flash("Incorrect Username and /or Password")
                return redirect(url_for("login"))

        else:
            # userna,e dosen't exist
            flash("IncorrectUsername and/or Password")
            return redirect(url_for("login"))

    return render_template("login.html")

# user profile
@app.route("/profile/<username>", methods=["GET", "POST"])
def profile(username):
    # grab the session user's username from db
    username = mongo.db.users.find_one(
        {"username": session["user"]})["username"]

    if session["user"]:    
        return render_template("profile.html", username=username)

    return redirect(url_for("login"))

#logout user
@app.route("/logout")
def logout():
    # remover user from session cookies
    flash("You have been logged out")
    session.pop("user")
    return redirect(url_for("login"))

# add a recipe
@app.route("/add_recipe", methods=["GET", "POST"])
def add_recipe():
    if request.method == "POST":
        recipe = {
            "category_name": request.form.get("category_name"),
            "recipe_name": request.form.get("recipe_name"),
            "recipe_short_description": request.form.get(
            "recipe_short_description"),
            "recipe_ingredients": request.form.get(
            "recipe_ingredients"),
            "recipe_steps": request.form.get("recipe_steps"),
            "recipe_prep_time": request.form.get("recipe_prep_time"),
            "recipe_cooking_time": request.form.get("recipe_cooking_time"),
            "recipe_image_url": request.form.get("recipe_image_url"),
            "created_by": session["user"]
        }
        mongo.db.recipes.insert_one(recipe)
        flash("Recipe Successfully Added")
        return redirect(url_for("recipes"))

    categories = mongo.db.categories.find().sort("category_name", 1)
    return render_template("add_recipe.html", categories=categories)

# edit existing recipe
@app.route("/edit_recipe/<recipe_id>", methods=["GET", "POST"])
def edit_recipe(recipe_id):
    if request.method == "POST":
        submit = {
            "category_name": request.form.get("category_name"),
            "recipe_name": request.form.get("recipe_name"),
            "recipe_short_description": request.form.get(
            "recipe_short_description"),
            "recipe_ingredients": request.form.get(
            "recipe_ingredients"),
            "recipe_steps": request.form.get("recipe_steps"),
            "recipe_prep_time": request.form.get("recipe_prep_time"),
            "recipe_cooking_time": request.form.get("recipe_cooking_time"),
            "recipe_image_url": request.form.get("recipe_image_url"),
            "created_by": session["user"]
        }
        mongo.db.recipes.update({"_id": ObjectId(recipe_id)}, submit)
        flash("Recipe Successfully Updated")

    recipe = mongo.db.recipes.find_one({"_id": ObjectId(recipe_id)})
    categories = mongo.db.categories.find().sort("category_name", 1)
    return render_template("edit_recipe.html", recipe=recipe, categories=categories)

# delete a recipe
@app.route("/delete_recipe/<recipe_id>")
def delete_recipe(recipe_id):
    mongo.db.recipes.remove({"_id": ObjectId(recipe_id)})
    flash("Recipe Successfully Deleted")
    return redirect(url_for("recipes"))    


if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")),
            debug=False)
