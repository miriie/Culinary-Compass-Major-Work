import random
from flask import Flask, render_template, redirect, url_for, session, request, make_response, send_from_directory
from datetime import datetime, timedelta
import pytz
import sqlite3
import bcrypt
import string
import json
from markupsafe import Markup
import re
from better_profanity import profanity
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge
import os

app = Flask(__name__)
app.secret_key = 'wowowow'

profanity.load_censor_words()
def censor_text(text):
    return profanity.censor(text) if text else text

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/static/serviceWorker.js')
def sw():
    response=make_response(
        send_from_directory('static', 'serviceWorker.js'))
    response.headers['Content-Type'] = 'application/javascript'
    return response

@app.errorhandler(RequestEntityTooLarge)
def handle_large_file(error):
    return "File too large. Max size is 2MB.", 413

def get_db_connection():
    connection = sqlite3.connect('my-database.db')
    connection.row_factory = sqlite3.Row
    return connection

def highlight_text(instructions, annotations):
    for i, ann in enumerate(annotations):
        pattern = re.escape(ann['highlighted_text'])
        replacement = f'<mark class="highlighted-text" id="highlight-{i}" data-index="{i}">{ann["highlighted_text"]}</mark>'
        instructions = re.sub(pattern, replacement, instructions, count=1)
    return Markup(instructions)

@app.route('/recipe/<int:recipe_id>', methods=['GET', 'POST'])
def recipe_page(recipe_id):
    connection = get_db_connection()
    cursor = connection.cursor()
    connection.execute("PRAGMA foreign_keys = ON;")
    
    # Fetch recipe information based on the recipe ID
    query_recipe = '''
    SELECT recipes.*, users.username AS writer_username, users.id AS writer_id, users.profile_picture AS writer_pic
    FROM recipes
    JOIN users ON recipes.user_id = users.id
    WHERE recipes.id = ?
    '''
    recipe = connection.execute(query_recipe, (recipe_id,)).fetchone()

    # Fetch reviews for the recipe
    query_reviews = '''
    SELECT users.username, reviews.*, reviews.title AS review_title
    FROM reviews
    JOIN users ON reviews.user_id = users.id
    WHERE reviews.recipe_id = ?
    '''
    reviews = connection.execute(query_reviews, (recipe_id,)).fetchall()

    # Load annotations and is favourited if logged in 
    is_favourited = False
    user_review = None
    if 'user_id' in session:
        user_id = session['user_id']
        is_favourited = cursor.execute("SELECT 1 FROM favourites WHERE recipe_id = ? AND user_id = ?", (recipe_id, user_id)).fetchone() is not None
        
        user_review = cursor.execute(
            "SELECT * FROM reviews WHERE recipe_id = ? AND user_id = ?",
            (recipe_id, user_id)
        ).fetchone()
        
        query_annotations = '''
        SELECT annotations.highlighted_text, annotations.annotation_text 
        FROM annotations
        JOIN users ON annotations.user_id = users.id
        WHERE annotations.recipe_id = ? AND annotations.user_id = ?
        '''
        annotations = connection.execute(query_annotations, (recipe_id, user_id)).fetchall()
    else:
        annotations = []
    
    if request.method == 'POST':
        user_id = session['user_id']
        action = request.form.get('action')

        if action == 'submit_review':
            # Handle the form submission for adding a review
            rating = int(request.form['rating'])
            review_title = censor_text(request.form['review_title'])
            review_text = censor_text(request.form['review'])
            profile_picture = session['profile_picture']
            
            # Get the current time in Sydney, Australia
            sydney_tz = pytz.timezone('Australia/Sydney')
            current_date = datetime.now(sydney_tz).strftime('%Y-%m-%d')

            # Insert the new review into the database
            insert_review_query = '''
            INSERT INTO reviews (recipe_id, rating, review, title, date, profile_picture, user_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            '''
            connection.execute(insert_review_query, (recipe_id, rating, review_text, review_title, current_date, profile_picture, user_id))

            # recalculate new avg rating
            cursor.execute("SELECT ROUND(AVG(rating), 1) FROM reviews WHERE recipe_id = ?", (recipe_id,))
            average_rating = cursor.fetchone()[0]
            cursor.execute("UPDATE recipes SET rating = ? WHERE id = ?", (average_rating, recipe_id))
        
        elif action == 'toggle_favourite':
            favourited = cursor.execute("SELECT 1 FROM favourites WHERE recipe_id = ? AND user_id = ?", (recipe_id, user_id)).fetchone()
            if favourited:
                cursor.execute("DELETE FROM favourites WHERE recipe_id = ? AND user_id = ?", (recipe_id, user_id))
            else:
                cursor.execute("INSERT INTO favourites (recipe_id, user_id) VALUES (?, ?)", (recipe_id, user_id))
        
        elif action == 'delete_recipe':
            if user_id == recipe['user_id'] or session.get('is_admin'):
                cursor.execute("DELETE FROM recipes WHERE id = ?", (recipe_id,))
                connection.commit()
                return redirect(url_for('homepage'))
        
        elif request.form.get("action") == "delete_annotation":
            annotation_id = request.form.get("annotation_id")
            connection.execute("DELETE FROM annotations WHERE id = ?", (annotation_id,))
            connection.commit()

        elif action == 'delete_review':
            review_title = request.form.get('review_title')
            cursor.execute("DELETE FROM reviews WHERE recipe_id = ? AND user_id = ?", (recipe_id, user_id))
            connection.commit()

        elif action == 'edit_review':
            if user_id != recipe['user_id']:
                new_rating = int(request.form['rating'])
                new_title = censor_text(request.form['review_title'])
                new_text = censor_text(request.form['review'])

                cursor.execute('''
                    UPDATE reviews
                    SET rating = ?, title = ?, review = ?
                    WHERE recipe_id = ? AND user_id = ?
                ''', (new_rating, new_title, new_text, recipe_id, user_id))

                # recalculate new avg
                cursor.execute("SELECT ROUND(AVG(rating), 1) FROM reviews WHERE recipe_id = ?", (recipe_id,))
                average_rating = cursor.fetchone()[0]
                cursor.execute("UPDATE recipes SET rating = ? WHERE id = ?", (average_rating, recipe_id))

        
        elif action == 'submit_annotation':
            highlighted_text = request.form['highlighted_text']
            annotation_text = request.form['annotation_text']
            connection.execute(
                'INSERT INTO annotations (recipe_id, user_id, highlighted_text, annotation_text) VALUES (?, ?, ?, ?)',
                (recipe_id, user_id, highlighted_text, annotation_text)
            )
        
        connection.commit()
        return redirect(url_for('recipe_page', recipe_id=recipe_id))
    
    connection.close()

    if recipe:
        # sorting tags
        tags_dict = json.loads(recipe['tags'])
        tags = []
        for tag_list in tags_dict.values():
            tags.extend(tag_list)
        
        ingredient_tags_dict = json.loads(recipe['ingredient_tags'])
        ingredient_tags = []
        for tag_list in ingredient_tags_dict.values():
            ingredient_tags.extend(tag_list)


        # display recipe data
        recipe_data = {
            "writer_username": recipe['writer_username'],
            "writer_id": recipe['writer_id'],
            "writer_pic": recipe['writer_pic'],
            "id": recipe['id'],
            "title": recipe['title'],
            "instructions": recipe['instructions'],
            "intro": recipe['intro'],
            "ingredient_list": recipe['ingredient_list'],
            "ingredient_tags": ingredient_tags,
            "tags": tags,
            "rating": recipe['rating'] if reviews else "N/A",
            "image": recipe['image'],  
            "annotations": [
                {
                    "highlighted_text": a['highlighted_text'],
                    "annotation_text": a['annotation_text']
                } for a in annotations
            ],
            "reviews": [
                {
                    "user_id": r['user_id'],
                    "username": r['username'],
                    "profile_picture": r['profile_picture'],
                    "review_title": r['review_title'],
                    "review": r['review'],
                    "rating": r['rating'],
                    "date": r['date']
                } for r in reviews
            ]
        }
        recipe_data["instructions"] = highlight_text(recipe_data["instructions"], recipe_data["annotations"])
        return render_template('recipepage.html', recipe=recipe_data, tags=tags, ingredient_tags=ingredient_tags, is_favourited=is_favourited, user_review=user_review)
    else:
        return "Page not found", 404

@app.route('/')
def homepage():
    connection = get_db_connection()

    popular_recipes_query = '''
    SELECT recipes.*, COUNT(reviews.id) AS review_count
    FROM recipes
    LEFT JOIN reviews ON reviews.recipe_id = recipes.id  -- Correct the join condition here
    GROUP BY recipes.id
    ORDER BY review_count DESC
    LIMIT 3;
    '''
    popular_recipes = connection.execute(popular_recipes_query).fetchall()

    # Fetch random recipes for Explore section
    all_recipes = connection.execute("SELECT * FROM recipes").fetchall()
    explore_recipes = random.sample(all_recipes, min(len(all_recipes), 3))  # Pick 3 random recipes

    connection.close()

    sw()

    return render_template("homepage.html", popular_recipes=popular_recipes, explore_recipes=explore_recipes)

@app.route('/search', methods=['GET', 'POST'])
def search():
    connection = get_db_connection()
    cursor = connection.cursor()

    # Fetch recipes ordered alphabetically by title
    cursor.execute("SELECT * FROM recipes ORDER BY title ASC")
    recipes = cursor.fetchall()
    
    tag_categories = {
        "Type of Meal": ["Breakfast", "Lunch", "Dinner", "Dessert", "Snack"],
        "Cuisine": ["Japanese", "Italian", "American", "Mexican", "Chinese", "Indian", "French", "Korean"],
        "Taste": ["Sweet", "Salty", "Spicy", "Savory", "Bitter", "Sour", "Umami"],
        "Diet": ["Vegan", "Vegetarian", "Pescatarian", "No Beef or Pork", "Gluten-free", "Keto", "Halal", "Kosher"],
        "Style": ["Stir-fried", "Deep-fried", "Grilled", "Baked", "Roasted", "Steamed", "Boiled", "Raw"]
    }

    ingredient_tags = {
        "Carbs": ["Flour", "Bread", "Rice", "Pasta", "Oats", "Tortilla", "Barley", "Wheat"],
        "Dairy": ["Milk", "Butter", "Cheese", "Yoghurt", "Cream", "Condensed Milk", "Ice Cream"],
        "Meat": ["Beef", "Pork", "Chicken", "Duck", "Turkey", "Goat", "Lamb", "Rabbit"],
        "Seafood": ["Fish", "Salmon", "Tuna", "Shrimp", "Prawns", "Crab", "Lobster", "Squid", "Octopus", "Mussels", "Scallops", "Clams"],
        "Non-Vegan": ["Eggs", "Lard", "Gelatin"],
        "Vegetables": ["Onion", "Garlic", "Tomato", "Carrot", "Bell Pepper", "Chilli", "Broccoli", "Spinach", "Mushroom", "Cabbage", "Zucchini", "Chickpeas", "Lentils", "Black Beans", "Kidney Beans", "Green Peas"],
        "Fruits": ["Lemon", "Avocado", "Apple", "Banana", "Strawberry", "Mango", "Grapes", "Pineapple", "Orange"],
        "Nuts": ["Nuts", "Peanuts", "Walnuts", "Hazelnuts", "Pistachios", "Almonds", "Cashews"],
        "Condiments": ["Soy Sauce", "Vinegar", "Tomato Sauce", "Mayonnaise", "Ketchup", "Mustard", "Hot Sauce"],
        "Seasonings": ["Sugar", "Salt", "Pepper", "Paprika", "Cumin", "Cinnamon", "Chilli Flakes", "Garlic Powder", "Ginger", "Oregano", "Turmeric"],
        "Oils": ["Olive Oil", "Vegetable Oil", "Canola Oil", "Sesame Oil", "Coconut Oil", "Ghee"],
        "Miscellaneous": []
    }

    include_tags = [t for t in request.form.getlist('include_tags[]') if t]
    exclude_tags = [t for t in request.form.getlist('exclude_tags[]') if t]
    include_ingredients = [i for i in request.form.getlist('include_ingredients[]') if i]
    exclude_ingredients = [i for i in request.form.getlist('exclude_ingredients[]') if i]
    searched_name = request.form.get('search-bar', '') if request.method == 'POST' else '' 
    
    search_query = "SELECT * FROM recipes WHERE 1=1"
    parameters = []

    if searched_name:
        banned_punctuation = string.punctuation + ":'" # get rid of inconsistencies when user searches up a term
        searched_name = searched_name.replace(" ", "").translate(str.maketrans("", "", banned_punctuation)).lower()
        searched_name = f"%{searched_name}%" # if the searched name is partially typed up, and is in one of the databases' recipe titles, the search works

        search_query += """ AND LOWER(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(
                title, ' ', ''),
                ',', ''),
                '.', ''),
                ':', ''),
                "'", ''),
                '"', '')) 
            LIKE ?"""
        parameters.append(searched_name)

    for tag in include_tags:
        search_query += " AND tags LIKE ?"
        parameters.append(f"%{tag}%")

    for ing in include_ingredients:
        search_query += " AND ingredient_tags LIKE ?"
        parameters.append(f"%{ing}%")

    for tag in exclude_tags:
        search_query += " AND tags NOT LIKE ?"
        parameters.append(f"%{tag}%")

    for ing in exclude_ingredients:
        search_query += " AND ingredient_tags NOT LIKE ?"
        parameters.append(f"%{ing}%")

    search_message_parts = []

    if searched_name:
        search_message_parts.append(f'Recipe Title containing "{request.form.get("search-bar", "")}"')
    if include_tags:
        search_message_parts.append(f"Tags included: {', '.join(include_tags)}")
    if exclude_tags:
        search_message_parts.append(f"Tags excluded: {', '.join(exclude_tags)}")
    if include_ingredients:
        search_message_parts.append(f"Ingredients included: {', '.join(include_ingredients)}")
    if exclude_ingredients:
        search_message_parts.append(f"Ingredients excluded: {', '.join(exclude_ingredients)}")
    if search_message_parts:
        message = "Showing Results for: " + "; ".join(search_message_parts)
    else:
        message = "All Recipes:" 

    cursor.execute(search_query, parameters)
    recipes = cursor.fetchall()
    connection.commit()
    connection.close()
    return render_template('search.html', recipes=recipes, tag_categories=tag_categories, ingredient_tags=ingredient_tags, selected_tags=include_tags, selected_ingredients=include_ingredients, message=message)

@app.route('/profile/<int:user_id>', methods=['GET', 'POST'])
def profile(user_id):
    connection = get_db_connection()
    cursor = connection.cursor()
    user = cursor.execute('SELECT id, username, profile_picture FROM users WHERE id = ?', (user_id,)).fetchone()
    query_reviews = '''SELECT reviews.*, reviews.title AS review_title, recipes.title AS recipe_title, reviews.id AS review_id
    FROM reviews JOIN recipes ON reviews.recipe_id = recipes.id WHERE reviews.user_id = ?'''
    query_favourites = '''SELECT recipes.*, recipes.title AS recipe_title, favourites.recipe_id
        FROM recipes 
        INNER JOIN favourites ON recipes.id = favourites.recipe_id
        INNER JOIN users ON users.id = favourites.user_id
        WHERE users.id = ?'''
    query_created = '''SELECT recipes.*, recipes.title AS recipe_title, recipes.id AS recipe_id
    FROM recipes JOIN users ON recipes.user_id = users.id WHERE users.id = ?'''

    user_reviews = cursor.execute(query_reviews, (user_id,)).fetchall()
    user_favourites = cursor.execute(query_favourites, (user_id,)).fetchall()
    user_created = cursor.execute(query_created, (user_id,)).fetchall()
    connection.close()
    return render_template('profile.html', reviews=user_reviews, favourites = user_favourites, created=user_created, user=user)

@app.route('/post', methods=['GET', 'POST'])
def post():
    connection = get_db_connection()
    cursor = connection.cursor()

    recipe_id = request.args.get('recipe_id') or request.form.get('recipe_id')
    recipe = None
    recipe_data = None
    selected_tags = {}
    selected_ingredients = {}
    
    tag_categories = {
        "Type of Meal": ["Breakfast", "Lunch", "Dinner", "Dessert", "Snack"],
        "Cuisine": ["Japanese", "Italian", "American", "Mexican", "Chinese", "Indian", "French", "Korean"],
        "Taste": ["Sweet", "Salty", "Spicy", "Savory", "Bitter", "Sour", "Umami"],
        "Diet": ["Vegan", "Vegetarian", "Pescatarian", "No Beef or Pork", "Gluten-free", "Keto", "Halal", "Kosher"],
        "Style": ["Stir-fried", "Deep-fried", "Grilled", "Baked", "Roasted", "Steamed", "Boiled", "Raw"]
    }
    ingredient_tags = {
        "Carbs": ["Flour", "Bread", "Rice", "Pasta", "Oats", "Tortilla", "Barley", "Wheat"],
        "Dairy": ["Milk", "Butter", "Cheese", "Yoghurt", "Cream", "Condensed Milk", "Ice Cream"],
        "Meat": ["Beef", "Pork", "Chicken", "Duck", "Turkey", "Goat", "Lamb", "Rabbit"],
        "Seafood": ["Fish", "Salmon", "Tuna", "Shrimp", "Prawns", "Crab", "Lobster", "Squid", "Octopus", "Mussels", "Scallops", "Clams"],
        "Non-Vegan": ["Eggs", "Lard", "Gelatin"],
        "Vegetables": ["Onion", "Garlic", "Tomato", "Carrot", "Bell Pepper", "Chilli", "Broccoli", "Spinach", "Mushroom", "Cabbage", "Zucchini", "Chickpeas", "Lentils", "Black Beans", "Kidney Beans", "Green Peas"],
        "Fruits": ["Lemon", "Avocado", "Apple", "Banana", "Strawberry", "Mango", "Grapes", "Pineapple", "Orange"],
        "Nuts": ["Nuts", "Peanuts", "Walnuts", "Hazelnuts", "Pistachios", "Almonds", "Cashews"],
        "Condiments": ["Soy Sauce", "Vinegar", "Tomato Sauce", "Mayonnaise", "Ketchup", "Mustard", "Hot Sauce"],
        "Seasonings": ["Sugar", "Salt", "Pepper", "Paprika", "Cumin", "Cinnamon", "Chilli Flakes", "Garlic Powder", "Ginger", "Oregano", "Turmeric"],
        "Oils": ["Olive Oil", "Vegetable Oil", "Canola Oil", "Sesame Oil", "Coconut Oil", "Ghee"],
        "Miscellaneous": []
    }

    for category in tag_categories:
        key = category.lower().replace(" ", "_")
        selected_tags[key] = []

    for category in ingredient_tags:
        key = category.lower().replace(" ", "_")
        selected_ingredients[key] = []
        
    if recipe_id:
        recipe = connection.execute("SELECT * FROM recipes WHERE id = ?", (recipe_id,)).fetchone()
        is_admin = session.get('is_admin', False)
        if recipe['user_id'] != session.get('user_id') and not is_admin:
            connection.close()
            return "You do not have permission to edit this recipe", 403
        recipe_data = recipe
        selected_tags = json.loads(recipe['tags'])
        selected_ingredients = json.loads(recipe['ingredient_tags'])

    if request.method == 'POST':
        recipe_writer = session['user_id']
        recipe_title = censor_text(request.form['recipe_title'])
        recipe_intro = censor_text(request.form['recipe_intro'])
        recipe_ingredient_list = censor_text(request.form['recipe_ingredient_list'])
        recipe_instructions = censor_text(request.form['recipe_instructions'])
        recipe_image = request.files.get('recipe_image')
        recipe_image_filename = None

        for category in tag_categories:
            key = category.lower().replace(" ", "_")
            selected_tags[key] = request.form.getlist(key)
        for category in ingredient_tags:
            key = category.lower().replace(" ", "_")
            selected_ingredients[key] = request.form.getlist(key)

        recipe_tags = json.dumps(selected_tags)
        recipe_ingredient_tags = json.dumps(selected_ingredients)

        if recipe_image and recipe_image.filename != '':
            if allowed_file(recipe_image.filename):
                filename = secure_filename(recipe_image.filename)
                upload_folder = os.path.join(app.root_path, 'static', 'uploads')
                os.makedirs(upload_folder, exist_ok=True)
                save_path = os.path.join(upload_folder, filename)
                recipe_image.save(save_path)
                recipe_image_filename = f"uploads/{filename}"
            else:
                connection.close()
                return "Invalid file type. Only PNG, JPG, JPEG, and GIF are allowed.", 400
   

        if recipe_id:
            if not recipe_image_filename:  # if user didn't upload a new image
                recipe_image_filename = recipe_data['image']
            cursor.execute('''
                UPDATE recipes SET title = ?, intro = ?, ingredient_list = ?, ingredient_tags = ?, instructions = ?, tags = ?, image = ?
                WHERE id = ?
            ''', (recipe_title, recipe_intro, recipe_ingredient_list, recipe_ingredient_tags, recipe_instructions, recipe_tags, recipe_image_filename, recipe_id))
        else:
            cursor.execute('''
                INSERT INTO recipes (user_id, title, intro, ingredient_list, ingredient_tags, instructions, tags, image)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (recipe_writer, recipe_title, recipe_intro, recipe_ingredient_list, recipe_ingredient_tags, recipe_instructions, recipe_tags, recipe_image_filename))
            recipe_id = cursor.lastrowid

        connection.commit()
        connection.close()
        return redirect(url_for('recipe_page', recipe_id=recipe_id))
    return render_template('post.html', tag_categories=tag_categories, selected_tags=selected_tags, ingredient_tags=ingredient_tags, selected_ingredients=selected_ingredients, recipe_data=recipe_data, editing=bool(recipe_id))

@app.route("/login", methods=["GET", "POST"])
def login():
    connection = get_db_connection()
    cursor = connection.cursor()

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        existing_user = cursor.fetchone()

        if existing_user:
            # Extract user data
            user_id = existing_user[0]
            db_password = existing_user[2]
            failed_attempts = existing_user[5] or 0
            lockout_timer = existing_user[6]

            now = datetime.utcnow()

            # Check lockout
            if lockout_timer:
                lockout_dt = datetime.strptime(lockout_timer, '%Y-%m-%d %H:%M:%S.%f')
                if lockout_dt > now - timedelta(minutes=5):
                    minutes_left = int(((lockout_dt + timedelta(minutes=5)) - now).total_seconds() // 60) + 1
                    return render_template("login.html", message=f"Too many failed login attempts. Try again in {minutes_left} minutes.")

            # Check password
            if bcrypt.checkpw(password.encode('utf-8'), db_password):
                # Reset failed attempts and lockout
                cursor.execute("UPDATE users SET failed_attempts = 0, lockout_timer = NULL WHERE id = ?", (user_id,))
                connection.commit()

                # Setup session
                session["user_id"] = user_id
                session['is_admin'] = existing_user[4]
                session["username"] = existing_user[1]
                session["profile_picture"] = existing_user[3]
                session["logged_in"] = True
                return redirect(url_for('homepage'))

            else:
                # Failed login
                failed_attempts += 1
                if failed_attempts >= 3:
                    cursor.execute("UPDATE users SET failed_attempts = ?, lockout_timer = ? WHERE id = ?", (failed_attempts, now, user_id))
                else:
                    cursor.execute("UPDATE users SET failed_attempts = ? WHERE id = ?", (failed_attempts, user_id))
                connection.commit()

                return render_template("login.html", message="Error: Wrong username or password")
        else:
            return render_template("login.html", message="Error: User does not exist")

    return render_template("login.html")

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('homepage'))

@app.route("/register", methods= ["GET", "POST"])
def register():
    connection = get_db_connection()
    
    images = [
        "clover.png", 
        "redpik.png", 
        "bluepik.png", 
        "yellowpik.png",
        "purplepik.png",
        "whitepik.png",
        "rockpik.png",
        "icepik.png",
        "wingpik.png",
        "glowpik.png"
    ]

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        re_password = request.form["re-password"]
        profile_picture = "images/" + request.form["pikpic"]

        cursor = connection.cursor()
        cursor.execute("SELECT username FROM users WHERE username = ?", (username,))
        existing_user = cursor.fetchone()
        
        # user taken
        if existing_user:
            return render_template("register.html", message= "Error: Username already taken", images=images)

        # password min length
        if len(password) < 8:
            return render_template("register.html", message= "Error: Password must be at least 8 characters long", images=images)

        # passwords match
        if password != re_password:
            return render_template("register.html", message= "Error: Passwords do not match", images=images)
        
        # Hash the password
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        # successful registration 
        cursor.execute("INSERT INTO users(username, password, profile_picture) VALUES (?, ?, ?)", (username, hashed_password, profile_picture))
        connection.commit()
        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        user_id  = cursor.fetchone()[0]
        session["user_id"] = user_id
        session["username"] = username
        session["profile_picture"] = profile_picture
        session["logged_in"] = True
        return redirect(url_for('homepage'))
    return render_template("register.html", images=images)

@app.route('/admin')
def admin_dashboard():
    if not session.get('is_admin'):
        return "403 Forbidden", 403
    # fetch all recipes/users/etc.
    return render_template('admin_dashboard.html')

if __name__ == "__main__":
    app.run(debug=True)
