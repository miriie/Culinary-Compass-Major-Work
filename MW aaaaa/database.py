import sqlite3
from datetime import datetime
import bcrypt

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
        profile_picture TEXT NOT NULL
    );'''

    create_table_recipes = '''
    CREATE TABLE IF NOT EXISTS recipes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title TEXT NOT NULL UNIQUE,
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
        recipe_id INTEGER,
        highlighted_text TEXT,
        annotation_text TEXT,
        FOREIGN KEY (recipe_id) REFERENCES recipes(id)
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
            "• spaghetti\n• ground beef\n• onion\n• garlic\n• tomato\n• olive oil\n• basil\n• parmesan",
            '{"gluten": ["Pasta"], "dairy": ["Cheese"], "non-hindu_meat": ["Beef"], "hindu_meat": [], "seafood": [], "non-vegan": [], "vegetables": ["Onion", "Garlic", "Tomato"], "fruits": [], "legumes": [], "nuts": [], "condiments": [], "seasonings": ["Basil"], "oils": ["Olive Oil"], "miscellaneous": []}',
            "This hearty dish combines spaghetti with a rich meat sauce simmered with aromatic herbs and olive oil. Perfect for a comforting family meal.",
            '{"type_of_meal": ["Dinner"], "cuisine": ["Italian"], "taste": ["Comfort Food"]}',
            "images/pikmin4.jpg"
        ),

        (
            2,
            "Sushi Rolls",
            "Fresh, hand-rolled sushi with fish and vegetables.",
            "• sushi rice\n• nori\n• salmon\n• cucumber\n• avocado\n• soy sauce\n• wasabi",
            '{"gluten": ["Rice"], "dairy": [], "non-hindu_meat": [], "hindu_meat": [], "seafood": ["Fish"], "non-vegan": [], "vegetables": ["Cucumber", "Avocado"], "fruits": [], "legumes": [], "nuts": [], "condiments": ["Soy Sauce"], "seasonings": [], "oils": [], "miscellaneous": ["Seaweed", "Wasabi"]}',
            "Customize your sushi with fresh salmon, avocado, cucumber, and perfectly seasoned rice, all wrapped in crisp nori seaweed.",
            '{"type_of_meal": ["Lunch"], "cuisine": ["Japanese"], "taste": ["Light"]}',
            "images/mario_party_super.jpg"
        ),

        (
            3,
            "Classic Pancakes",
            "Fluffy breakfast pancakes with maple syrup.",
            "• flour\n• eggs\n• milk\n• baking powder\n• sugar\n• butter\n• maple syrup",
            '{"gluten": ["Flour"], "dairy": ["Milk", "Butter"], "non-hindu_meat": [], "hindu_meat": [], "seafood": [], "non-vegan": ["Eggs"], "vegetables": [], "fruits": [], "legumes": [], "nuts": [], "condiments": ["Maple Syrup"], "seasonings": ["Sugar", "Baking Powder"], "oils": [], "miscellaneous": []}',
            "Soft and golden pancakes made from scratch, served warm with butter and maple syrup for the perfect morning treat.",
            '{"type_of_meal": ["Breakfast"], "taste": ["Sweet"], "cuisine": ["American"]}',
            "images/new_horizons.jpg"
        ),

        (
            4,
            "Pad Thai",
            "Tangy and sweet Thai stir-fried noodles.",
            "• rice noodles\n• tofu\n• shrimp\n• egg\n• peanuts\n• tamarind paste\n• garlic\n• bean sprouts",
            '{"gluten": ["Rice Noodles"], "dairy": [], "non-hindu_meat": [], "hindu_meat": [], "seafood": ["Shrimp"], "non-vegan": ["Egg"], "vegetables": ["Garlic", "Bean Sprouts"], "fruits": [], "legumes": ["Tofu"], "nuts": ["Peanuts"], "condiments": [], "seasonings": [], "oils": [], "miscellaneous": ["Tamarind Paste"]}',
            "Rice noodles stir-fried with tofu, shrimp, eggs, peanuts, and a flavorful tamarind-based sauce, garnished with fresh bean sprouts.",
            '{"type_of_meal": ["Dinner"], "cuisine": ["Thai"], "style": ["Noodles"]}',
            "images/pokemon_violet.jpg"
        ),

        (
            5,
            "Beef Tacos",
            "Seasoned beef in warm tortillas with toppings.",
            "• ground beef\n• taco seasoning\n• tortillas\n• cheddar cheese\n• lettuce\n• salsa\n• sour cream",
            '{"gluten": ["Tortillas"], "dairy": ["Cheese", "Sour Cream"], "non-hindu_meat": ["Beef"], "hindu_meat": [], "seafood": [], "non-vegan": [], "vegetables": ["Lettuce"], "fruits": [], "legumes": [], "nuts": [], "condiments": ["Salsa"], "seasonings": ["Taco Seasoning"], "oils": [], "miscellaneous": []}',
            "Spicy ground beef seasoned with taco spices, served in crispy or soft tortillas with cheese, lettuce, and salsa for a tasty Mexican meal.",
            '{"type_of_meal": ["Dinner"], "cuisine": ["Mexican"], "taste": ["Spicy"]}',
            "images/kirby_dream_land.jpg"
        ),

        (
            6,
            "Avocado Toast",
            "Creamy avocado on toasted sourdough bread.",
            "• avocado\n• sourdough bread\n• lemon juice\n• salt\n• pepper\n• chili flakes\n• eggs",
            '{"gluten": [], "dairy": [], "non-hindu_meat": [], "hindu_meat": [], "seafood": [], "non-vegan": [], "vegetables": [], "fruits": [], "legumes": [], "nuts": [], "condiments": [], "seasonings": [], "oils": [], "miscellaneous": []}',
            "Simple and healthy, mashed avocado seasoned with lemon and spices served on crispy toasted sourdough, optionally topped with eggs or chili flakes.",
            '{"type_of_meal": ["Breakfast"], "taste": ["Healthy"], "diet": ["Vegetarian"]}',
            "images/splatoon3.jpg"
        ),

        (
            7,
            "Butter Chicken",
            "Rich and creamy Indian butter chicken curry.",
            "• chicken\n• butter\n• tomato sauce\n• cream\n• garlic\n• ginger\n• garam masala\n• cumin",
            '{"gluten": [], "dairy": [], "non-hindu_meat": [], "hindu_meat": [], "seafood": [], "non-vegan": [], "vegetables": [], "fruits": [], "legumes": [], "nuts": [], "condiments": [], "seasonings": [], "oils": [], "miscellaneous": []}',
            "Tender chicken pieces cooked in a luscious tomato and butter sauce, infused with aromatic spices and cream for a melt-in-your-mouth flavor.",
            '{"type_of_meal": ["Dinner"], "cuisine": ["Indian"], "taste": ["Creamy"]}',
            "images/smash_bros_ultimate.jpg"
        ),

        (
            8,
            "Vegetable Stir Fry",
            "Quick and colorful vegetable stir-fry.",
            "• broccoli\n• bell pepper\n• carrot\n• soy sauce\n• garlic\n• sesame oil\n• ginger",
            '{"gluten": [], "dairy": [], "non-hindu_meat": [], "hindu_meat": [], "seafood": [], "non-vegan": [], "vegetables": [], "fruits": [], "legumes": [], "nuts": [], "condiments": [], "seasonings": [], "oils": [], "miscellaneous": []}',
            "A medley of fresh vegetables tossed in a savory soy and sesame sauce, perfect as a light and healthy dinner or side dish.",
            '{"type_of_meal": ["Dinner"], "diet": ["Vegan"], "taste": ["Quick"]}',
            "images/cooking_mama.jpg"
        ),

        (
            9,
            "Chocolate Chip Cookies",
            "Chewy homemade chocolate chip cookies.",
            "• flour\n• sugar\n• butter\n• eggs\n• vanilla extract\n• baking soda\n• chocolate chips",
            '{"gluten": [], "dairy": [], "non-hindu_meat": [], "hindu_meat": [], "seafood": [], "non-vegan": [], "vegetables": [], "fruits": [], "legumes": [], "nuts": [], "condiments": [], "seasonings": [], "oils": [], "miscellaneous": []}',
            "Classic cookies loaded with chocolate chips, crispy on the edges and soft inside, perfect for dessert or a sweet snack.",
            '{"type_of_meal": ["Dessert"], "taste": ["Sweet"], "style": ["Baked"]}',
            "images/switch_sports.jpg"
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
        ("pik", "securepass", "images/purplepik.png"),
        ("user1", "mypassword", "images/wingpik.png"),
        ("user2", "letmein", "images/yellowpik.png"),
        ("user3", "hunter2", "images/rockpik.png"),
        ("user4", "password4", "images/glowpik.png"),
        ("rice", "firebird", "images/redpik.png"),
        ("delta", "triangular", "images/icepik.png"),
        ("mire", "fending", "images/whitepik.png"),
        ("bud", "oldpal", "images/bluepik.png")
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

    connection.commit()
    connection.close()

def add_dummy_reviews():
    """Add some dummy reviews linked to recipes and users."""
    connection = get_db_connection()
    cursor = connection.cursor()

    reviews_data = [
        ('Spaghetti Bolognese', 5, 'Best recipe ever!', 'Epic Flavour', '2024-12-01', 'images/clover.png', 'user1234'),
        ('Spaghetti Bolognese', 5, 'Simply amazing and authentic!', 'Masterpiece', '2024-12-02', 'images/wingpik.png', 'user1'),
        ('Sushi Rolls', 3, 'Good but rolling was a challenge.', 'Needs Practice', '2024-12-03', 'images/redpik.png', 'rice'),
        ('Classic Pancakes', 2, 'Kept burning the pancakes, sad!', 'Kitchen Fail', '2024-12-11', 'images/rockpik.png', 'user3'),
        ('Pad Thai', 4, 'Loved the sweet and tangy flavors!', 'Great Taste', '2024-11-30', 'images/glowpik.png', 'user4'),
        ('Beef Tacos', 2, 'Meat was too dry, needs improvement.', 'Dry Meat', '2024-12-05', 'images/rockpik.png', 'user3'),
        ('Avocado Toast', 4, 'Simple and healthy, perfect breakfast.', 'Fresh Start', '2024-12-06', 'images/icepik.png', 'delta'),
        ('Butter Chicken', 4, 'Rich and creamy, just like restaurant style!', 'Restaurant Quality', '2024-12-07', 'images/purplepik.png', 'pik'),
        ('Vegetable Stir Fry', 3, 'Quick and tasty but a bit salty.', 'Salty', '2024-12-08', 'images/whitepik.png', 'mire'),
        ('Chocolate Chip Cookies', 4, 'Chewy and delicious, kids loved them!', 'Sweet Treat', '2024-12-10', 'images/bluepik.png', 'bud')
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
