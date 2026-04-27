import chromadb
from sentence_transformers import SentenceTransformer
import numpy as np
import json

model = SentenceTransformer("all-MiniLM-L6-v2")

recipes = [
    {"id": "r1", "name": "Classic Spaghetti Carbonara",
     "description": "Creamy Italian pasta with eggs, bacon, parmesan and black pepper. Quick 20-minute dinner.",
     "cuisine": "italian", "difficulty": "easy", "time_minutes": 20, "vegetarian": False},
    {"id": "r2", "name": "Thai Green Curry",
     "description": "Spicy coconut curry with chicken, vegetables, and fragrant basil. Served over jasmine rice.",
     "cuisine": "thai", "difficulty": "medium", "time_minutes": 45, "vegetarian": False},
    {"id": "r3", "name": "Vegan Buddha Bowl",
     "description": "Healthy bowl with quinoa, roasted vegetables, avocado, chickpeas and tahini dressing.",
     "cuisine": "fusion", "difficulty": "easy", "time_minutes": 30, "vegetarian": True},
    {"id": "r4", "name": "Beef Wellington",
     "description": "Elegant beef tenderloin wrapped in mushroom duxelles and golden puff pastry. Showstopper dish.",
     "cuisine": "french", "difficulty": "hard", "time_minutes": 180, "vegetarian": False},
    {"id": "r5", "name": "Chocolate Chip Cookies",
     "description": "Classic homemade cookies with melty chocolate chips. Perfect afternoon treat.",
     "cuisine": "american", "difficulty": "easy", "time_minutes": 25, "vegetarian": True},
    {"id": "r6", "name": "Vegetable Stir Fry",
     "description": "Quick healthy stir fry with broccoli, peppers, mushrooms in soy-ginger sauce.",
     "cuisine": "chinese", "difficulty": "easy", "time_minutes": 15, "vegetarian": True},
    {"id": "r7", "name": "Homemade Sourdough Bread",
     "description": "Artisan bread with crispy crust and chewy interior. Requires patience and 24-hour fermentation.",
     "cuisine": "european", "difficulty": "hard", "time_minutes": 1440, "vegetarian": True},
    {"id": "r8", "name": "Greek Salad",
     "description": "Fresh Mediterranean salad with tomatoes, cucumber, feta, olives and olive oil.",
     "cuisine": "greek", "difficulty": "easy", "time_minutes": 10, "vegetarian": True},
]

client = chromadb.Client()
collection = client.create_collection(name="recipes")

collection.add(
    documents=[r["description"] for r in recipes],
    metadatas=[{"cuisine": r["cuisine"],"difficulty": r["difficulty"], "vegetarian": r["vegetarian"], "time_minutes": r["time_minutes"]} for r in recipes ],
    ids=[r["id"] for r in recipes]
)

results = collection.query(
    query_texts=["something quick and healthy", "comfort food for a lazy Sunday"],
    n_results=3
)
print(results)


results = collection.query(
    query_texts=["something quick and healthy", "comfort food for a lazy Sunday"],
    n_results=3,
    where={
        "$and":[
            {"vegetarian": {"$eq": True}},
            {"time_minutes": {"$lt": 30}},
            {"difficulty": {"$eq": "easy"}}
        ]
    }
)
print(results)
