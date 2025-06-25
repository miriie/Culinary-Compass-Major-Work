import sqlite3
from datetime import datetime
import bcrypt
import json

def get_db_connection():
    """Connect to the SQLite database and return the connection object with row factory."""
    connection = sqlite3.connect('my-database.db')
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON;")  # Ensure foreign keys are enforced
    return connection

def initialise_database():
    """Create tables for users, recipes, and reviews if they do not exist."""
    connection = get_db_connection()
    cursor = connection.cursor()

    create_table_users = '''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        profile_picture TEXT NOT NULL,
        is_admin INTEGER DEFAULT 0,
        failed_attempts INTEGER DEFAULT 0,
        lockout_timer TIMESTAMP NULL
    );'''

    create_table_recipes = '''
    CREATE TABLE IF NOT EXISTS recipes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        intro TEXT,
        ingredient_list TEXT,
        ingredient_tags TEXT,
        instructions TEXT,
        tags TEXT,
        rating REAL,
        image TEXT
    );'''

    create_table_reviews = '''
    CREATE TABLE IF NOT EXISTS reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        recipe_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        rating INTEGER NOT NULL,
        review TEXT,
        title TEXT,
        date TEXT NOT NULL,
        profile_picture TEXT,
        FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );'''

    create_table_favourites = '''
    CREATE TABLE IF NOT EXISTS favourites (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        recipe_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        UNIQUE(recipe_id, user_id),
        FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );'''

    create_table_annotations = '''
    CREATE TABLE annotations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        recipe_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        highlighted_text TEXT,
        annotation_text TEXT,
        FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );'''

    cursor.execute(create_table_users)
    cursor.execute(create_table_recipes)
    cursor.execute(create_table_reviews)
    cursor.execute(create_table_favourites)
    cursor.execute(create_table_annotations)

    connection.commit()
    connection.close()
    print('Database initialized successfully.')

def add_recipe_entries():
    """Add predefined recipe entries if they do not already exist."""
    connection = get_db_connection()
    cursor = connection.cursor()

    recipe_data = [
        (
            1,
            "Spaghetti Bolognese",
            "A classic Italian pasta dish made with ground beef and tomatoes.",
            "• 200g spaghetti\n• 250g ground beef\n• 1 onion, finely chopped\n• 2 cloves garlic, minced\n• 400g canned tomatoes\n• 2 tbsp olive oil\n• 1 tsp dried basil\n• Grated parmesan, to serve",
            '{"gluten": ["Spaghetti"], "dairy": ["Parmesan"], "non-hindu_meat": ["Beef"], "vegetables": ["Onion", "Garlic", "Tomato"], "seasonings": ["Basil"], "oils": ["Olive Oil"]}',
            "1. Cook the spaghetti according to package instructions. Drain and set aside.\n2. Heat olive oil in a pan. Sauté onion until soft.\n3. Add garlic and cook briefly.\n4. Brown the beef in the pan.\n5. Stir in tomatoes and basil. Simmer 20 minutes.\n6. Season to taste and serve over spaghetti with parmesan.",
            '{"type_of_meal": ["Dinner"], "cuisine": ["Italian"], "taste": ["Savory", "Comfort Food"]}',
            "images/spaghetti.jpg"
        ),
        (
            2,
            "Sushi Rolls",
            "Fresh, hand-rolled sushi with fish and vegetables.",
            "• 2 cups sushi rice\n• 4 sheets nori\n• 100g raw salmon, sliced\n• 1/2 cucumber, sliced\n• 1/2 avocado, sliced\n• Soy sauce, to serve\n• Wasabi, to serve",
            '{"gluten": [], "seafood": ["Salmon"], "vegetables": ["Cucumber", "Avocado"], "condiments": ["Soy Sauce"], "miscellaneous": ["Nori", "Wasabi"]}',
            "1. Cook sushi rice and let cool.\n2. Lay nori on bamboo mat.\n3. Spread rice evenly over nori.\n4. Add salmon, cucumber, and avocado.\n5. Roll tightly and slice.\n6. Serve with soy sauce and wasabi.",
            '{"type_of_meal": ["Lunch"], "cuisine": ["Japanese"], "taste": ["Light"]}',
            "images/sushi.jpg"
        ),
        (
            3,
            "Classic Pancakes",
            "Fluffy breakfast pancakes with maple syrup.",
            "• 1 cup flour\n• 2 eggs\n• 1 cup milk\n• 2 tsp baking powder\n• 2 tbsp sugar\n• 2 tbsp butter, melted\n• Maple syrup, to serve",
            '{"gluten": ["Flour"], "dairy": ["Milk", "Butter"], "non-vegan": ["Eggs"], "condiments": ["Maple Syrup"], "seasonings": ["Sugar", "Baking Powder"]}',
            "1. Whisk flour, baking powder, and sugar.\n2. Add milk, eggs, and butter. Mix until smooth.\n3. Heat pan and pour batter.\n4. Cook until bubbles form, then flip.\n5. Serve with maple syrup.",
            '{"type_of_meal": ["Breakfast"], "taste": ["Sweet"], "cuisine": ["American"]}',
            "images/pancakes.jpg"
        ),
        (
            4,
            "Pad Thai",
            "Tangy and sweet Thai stir-fried noodles.",
            "• 200g rice noodles\n• 100g tofu, cubed\n• 100g shrimp\n• 1 egg\n• 2 tbsp crushed peanuts\n• 2 tbsp tamarind paste\n• 2 cloves garlic, minced\n• 1 cup bean sprouts",
            '{"gluten": [], "seafood": ["Shrimp"], "non-vegan": ["Egg"], "vegetables": ["Garlic", "Bean Sprouts"], "legumes": ["Tofu"], "nuts": ["Peanuts"], "miscellaneous": ["Tamarind Paste"]}',
            "1. Soak noodles in warm water until soft.\n2. Sauté garlic, then add shrimp and tofu.\n3. Push aside, scramble egg in pan.\n4. Add noodles, tamarind paste, and mix well.\n5. Stir in bean sprouts and peanuts.\n6. Serve hot.",
            '{"type_of_meal": ["Dinner"], "cuisine": ["Thai"], "style": ["Stir-fried"]}',
            "images/padthai.jpg"
        ),
        (
            5,
            "Beef Tacos",
            "Seasoned beef in warm tortillas with toppings.",
            "• 250g ground beef\n• 1 packet taco seasoning\n• 6 small tortillas\n• 1/2 cup shredded cheddar\n• 1 cup shredded lettuce\n• 1/2 cup salsa\n• 1/4 cup sour cream",
            '{"gluten": ["Tortillas"], "dairy": ["Cheddar", "Sour Cream"], "non-hindu_meat": ["Beef"], "vegetables": ["Lettuce"], "condiments": ["Salsa"], "seasonings": ["Taco Seasoning"]}',
            "1. Cook beef in pan. Add taco seasoning.\n2. Warm tortillas.\n3. Assemble with beef, cheese, lettuce, salsa, and sour cream.\n4. Serve immediately.",
            '{"type_of_meal": ["Dinner"], "cuisine": ["Mexican"], "taste": ["Spicy"]}',
            "images/taco.jpg"
        ),
        (
            6,
            "Avocado Toast",
            "Creamy avocado on toasted sourdough bread.",
            "• 1 avocado\n• 2 slices sourdough bread\n• 1 tsp lemon juice\n• Salt to taste\n• Pepper to taste\n• Chili flakes (optional)\n• 1 egg, poached or fried (optional)",
            '{"gluten": ["Sourdough Bread"], "non-vegan": ["Eggs"], "fruits": ["Avocado", "Lemon"], "seasonings": ["Salt", "Pepper", "Chili Flakes"]}',
            "1. Toast the bread.\n2. Mash avocado with lemon, salt, and pepper.\n3. Spread on toast.\n4. Top with chili flakes and egg if using.",
            '{"type_of_meal": ["Breakfast"], "taste": ["Healthy"], "diet": ["Vegetarian"]}',
            "images/avocadotoast.jpg"
        ),
        (
            7,
            "Butter Chicken",
            "Rich and creamy Indian butter chicken curry.",
            "• 300g chicken breast, cubed\n• 2 tbsp butter\n• 1 cup tomato sauce\n• 1/2 cup cream\n• 2 cloves garlic, minced\n• 1 tsp grated ginger\n• 1 tsp garam masala\n• 1 tsp ground cumin",
            '{"non-hindu_meat": ["Chicken"], "dairy": ["Butter", "Cream"], "vegetables": ["Garlic"], "seasonings": ["Garam Masala", "Cumin", "Ginger"]}',
            "1. Sauté garlic and ginger in butter.\n2. Add chicken and cook until browned.\n3. Add tomato sauce and spices.\n4. Simmer for 15 mins.\n5. Stir in cream and cook 5 more mins.\n6. Serve hot.",
            '{"type_of_meal": ["Dinner"], "cuisine": ["Indian"], "taste": ["Creamy"]}',
            "images/butterchicken.jpg"
        ),
        (
            8,
            "Vegetable Stir Fry",
            "Quick and colorful vegetable stir-fry.",
            "• 1 cup broccoli florets\n• 1 bell pepper, sliced\n• 1 carrot, julienned\n• 2 tbsp soy sauce\n• 2 cloves garlic, minced\n• 1 tbsp sesame oil\n• 1 tsp grated ginger",
            '{"vegetables": ["Broccoli", "Bell Pepper", "Carrot", "Garlic", "Ginger"], "condiments": ["Soy Sauce"], "oils": ["Sesame Oil"]}',
            "1. Heat sesame oil in wok.\n2. Add garlic and ginger.\n3. Stir-fry vegetables until tender.\n4. Add soy sauce and stir.\n5. Serve hot.",
            '{"type_of_meal": ["Dinner"], "diet": ["Vegan"], "taste": ["Quick"]}',
            "images/vegstirfry.jpg"
        ),
        (
            9,
            "Chocolate Chip Cookies",
            "Chewy homemade chocolate chip cookies.",
            "• 2 cups flour\n• 1 cup sugar\n• 1/2 cup butter\n• 2 eggs\n• 1 tsp vanilla extract\n• 1 tsp baking soda\n• 1 cup chocolate chips",
            '{"gluten": ["Flour"], "dairy": ["Butter"], "non-vegan": ["Eggs"], "seasonings": ["Sugar", "Baking Soda"], "miscellaneous": ["Chocolate Chips"]}',
            "1. Cream butter and sugar.\n2. Add eggs and vanilla. Mix.\n3. Stir in flour, baking soda, and chips.\n4. Scoop dough onto tray.\n5. Bake at 180°C for 10–12 mins.\n6. Cool before serving.",
            '{"type_of_meal": ["Dessert"], "taste": ["Sweet"], "style": ["Baked"]}',
            "images/cookies.jpg"
        )
    ]



    for recipe in recipe_data:
        cursor.execute("SELECT COUNT(*) FROM recipes WHERE title = ?", (recipe[0],))
        if cursor.fetchone()[0] == 0:
            cursor.execute(
                "INSERT INTO recipes (user_id, title, intro, ingredient_list, ingredient_tags, instructions, tags, image) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                recipe
            )
            print(f"Recipe '{recipe[1]}' added.")
        else:
            print(f"Recipe '{recipe[1]}' already exists. Skipping.")

    connection.commit()
    connection.close()
    print("Recipe entries processed.")

def add_dummy_users():
    """Add some dummy users with hashed passwords."""
    connection = get_db_connection()
    cursor = connection.cursor()

    users_data = [
        ("user1234", "password123", "images/clover.png"),
        ("pik", "securepass", "images/toast.png"),
        ("user1", "mypassword", "images/toast.png"),
        ("user2", "letmein", "images/icecream.png"),
        ("user3", "hunter2", "images/icecream.png"),
        ("user4", "password4", "images/cookie.png"),
        ("rice", "firebird", "images/cookie.png"),
        ("delta", "triangular", "images/pear.png"),
        ("mire", "fending", "images/pear.png"),
        ("bud", "oldpal", "images/apple.png")
    ]

    for username, password, picture in users_data:
        cursor.execute("SELECT COUNT(*) FROM users WHERE username = ?", (username,))
        if cursor.fetchone()[0] == 0:
            hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            cursor.execute(
                "INSERT INTO users (username, password, profile_picture) VALUES (?, ?, ?)",
                (username, hashed_pw, picture)
            )
            print(f"User '{username}' added with hashed password.")
        else:
            print(f"User '{username}' already exists. Skipping.")

    cursor.execute('''UPDATE users SET is_admin = 1 WHERE username = "mire"''')
    connection.commit()
    connection.close()

def add_dummy_reviews():
    """Add some dummy reviews linked to recipes and users."""
    connection = get_db_connection()
    cursor = connection.cursor()

    reviews_data = [
        ('Spaghetti Bolognese', 5, 'Best recipe ever!', 'Epic Flavour', '2024-12-01', 'images/clover.png', 'user1234'),
        ('Spaghetti Bolognese', 5, 'Simply amazing and authentic!', 'Masterpiece', '2024-12-02', 'images/toast.png', 'user1'),
        ('Sushi Rolls', 3, 'Good but rolling was a challenge.', 'Needs Practice', '2024-12-03', 'images/cookie.png', 'rice'),
        ('Classic Pancakes', 2, 'Kept burning the pancakes, sad!', 'Kitchen Fail', '2024-12-11', 'images/icecream.png', 'user2'),
        ('Pad Thai', 4, 'Loved the sweet and tangy flavors!', 'Great Taste', '2024-11-30', 'images/cookie.png', 'user4'),
        ('Beef Tacos', 2, 'Meat was too dry, needs improvement.', 'Dry Meat', '2024-12-05', 'images/icecream.png', 'user3'),
        ('Avocado Toast', 4, 'Simple and healthy, perfect breakfast.', 'Fresh Start', '2024-12-06', 'images/pear.png', 'delta'),
        ('Butter Chicken', 4, 'Rich and creamy, just like restaurant style!', 'Restaurant Quality', '2024-12-07', 'images/toast.png', 'pik'),
        ('Vegetable Stir Fry', 3, 'Quick and tasty but a bit salty.', 'Salty', '2024-12-08', 'images/pear.png', 'mire'),
        ('Chocolate Chip Cookies', 4, 'Chewy and delicious, kids loved them!', 'Sweet Treat', '2024-12-10', 'images/apple.png', 'bud')
    ]

    for recipe_title, rating, review_text, review_title, review_date, profile_pic, username in reviews_data:
        cursor.execute("SELECT id FROM recipes WHERE title = ?", (recipe_title,))
        recipe_id_row = cursor.fetchone()

        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        user_id_row = cursor.fetchone()

        if recipe_id_row and user_id_row:
            recipe_id = recipe_id_row['id']
            user_id = user_id_row['id']
            cursor.execute(
                "INSERT INTO reviews (recipe_id, rating, review, title, date, profile_picture, user_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (recipe_id, rating, review_text, review_title, review_date, profile_pic, user_id)
            )
            print(f"Review for '{recipe_title}' added by '{username}'.")
        else:
            if not recipe_id_row:
                print(f"Recipe '{recipe_title}' not found. Skipping review.")
            if not user_id_row:
                print(f"User '{username}' not found. Skipping review.")

    connection.commit()
    connection.close()

def calculate_avg_rating():
    """Calculate and update the average rating for each recipe."""
    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("SELECT id FROM recipes")
    recipes = cursor.fetchall()

    for recipe in recipes:
        recipe_id = recipe['id']
        cursor.execute("SELECT ROUND(AVG(rating), 1) FROM reviews WHERE recipe_id = ?", (recipe_id,))
        avg_rating = cursor.fetchone()[0] or 0  # fallback to 0 if no reviews
        cursor.execute("UPDATE recipes SET rating = ? WHERE id = ?", (avg_rating, recipe_id))

    connection.commit()
    connection.close()
    print("Average ratings updated for all recipes.")

if __name__ == "__main__":
    initialise_database()
    add_recipe_entries()
    add_dummy_users()
    add_dummy_reviews()
    calculate_avg_rating()
