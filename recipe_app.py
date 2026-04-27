import os
import streamlit as st
import chromadb
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

DISTANCE_THRESHHOLD = 1.5

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

@st.cache_resource
def build_collection():
    client = chromadb.Client()
    collection = client.create_collection(name="recipes")
    collection.add(
        documents=[r["description"] for r in recipes],
        metadatas=[{
            "name": r["name"],
            "cuisine": r["cuisine"],
            "difficulty": r["difficulty"],
            "vegetarian": r["vegetarian"],
            "time_minutes": r["time_minutes"]
        } for r in recipes],
        ids=[r["id"] for r in recipes]
    )
    return collection

def search_recipes(collection, query, filters=None, n_results=5):
    kwargs = {"query_texts": [query], "n_results": n_results}
    if filters:
        kwargs["where"] = filters

    raw = collection.query(**kwargs)

    results = []
    for i, doc in enumerate(raw["documents"][0]):
        results.append({
           "name": raw["metadatas"][0][i]["name"],
           "description": doc,
            "cuisine": raw["metadatas"][0][i]["cuisine"],
            "difficulty": raw["metadatas"][0][i]["difficulty"],
            "time_minutes": raw["metadatas"][0][i]["time_minutes"],
            "vegetarian": raw["metadatas"][0][i]["vegetarian"],
            "distance": round(raw["distances"][0][i], 3)
        })
    
    return [r for r in results if r["distance"] < DISTANCE_THRESHHOLD]

def generate_answer(query, results):
    if not results:
        return "I couldn't find recipes matching your criteria. Try relaxing your filters."
    
    client = Groq(api_key=os.getenv("API_KEY"))
    context = "Available recipes:\n"

    for r in results:
        veg = "vegetarian" if r["vegetarian"] else "non-vegetarian"
        context += f"- {r['name']} ({r['cuisine']}, {r['difficulty']}, {r['time_minutes']}min, {veg}): {r['description']}\n"

    prompt = f"""You are a friendly recipe assistant. Recommend recipes from the list below.
   
    {context}

    User's request: {query}

    Pick the 1-2 best matches and explain why in 2-3 sentences. Always include the recipe name, time, and cuisine."""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=300
    )
    return response.choices[0].message.content

st.set_page_config(page_title="Recipe Assistant", page_icon="🍳", layout="wide")

st.title("🍳 Recipe Recommendation Assistant")
st.caption("Ask in natural language — find recipes that match your mood and constraints")

collection = build_collection()

with st.sidebar:
    st.header("Filters")
    vegetarian_only = st.checkbox("Vegetarian only")
    max_time = st.slider("Maximum time (minutes)", 10, 1440, 60)
    difficulty = st.selectbox("Difficulty", ["any", "easy", "medium", "hard"])

# Build filter dict
filters = []
if vegetarian_only:
    filters.append({"vegetarian": {"$eq": True}})
filters.append({"time_minutes": {"$lte": max_time}})
if difficulty != "any":
    filters.append({"difficulty": {"$eq": difficulty}})

filter_dict = {"$and": filters} if len(filters) > 1 else filters[0]

query = st.text_input(
    "What are you looking for?",
    placeholder="e.g., something quick and healthy for tonight"
)

if st.button("Find Recipes", type="primary") and query:
    with st.spinner("Searching..."):
        results = search_recipes(collection, query, filters=filter_dict)
    
    if results:
        st.subheader("AI Recommendation")
        answer = generate_answer(query, results)
        st.info(answer)
        
        st.subheader("All Matching Recipes")
        for r in results:
            with st.expander(f"{r['name']} • {r['time_minutes']}min • {r['difficulty']}"):
                st.write(f"**Cuisine:** {r['cuisine']}")
                st.write(f"**Vegetarian:** {'Yes' if r['vegetarian'] else 'No'}")
                st.write(f"**Description:** {r['description']}")
                st.caption(f"Match confidence: {1 - r['distance']/2:.0%}")
    else:
        st.warning("No matching recipes found. Try relaxing your filters.")