import os
from flask import Flask, jsonify, request
from pymongo import MongoClient
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
app.debug = True

connected_to_database = "DATABASE_CONNECTION_STRING" in os.environ

if connected_to_database:
    client = MongoClient(os.environ["DATABASE_CONNECTION_STRING"])

def get_ratings_collection():
    db = client["rateron"]
    return db["ratings"]

# Store ratings in memory
ratings_in_memory = {}

@app.route("/rating", methods=["POST"])
def rate_image():
    # Get the image name and rating from the request
    image = request.json['image']
    rating = request.json['rating']

    # Validate the rating
    if int(rating) < 1 or int(rating) > 5:
        return jsonify({"error": "Invalid rating"}), 400

    # Save the rating
    if connected_to_database:
        ratings = get_ratings_collection()
        ratings.update_one({"image": image}, {"$push": {"ratings": int(rating)}}, upsert=True)
    else:
        if image not in ratings_in_memory:
            ratings_in_memory[image] = []
        ratings_in_memory[image].append(int(rating))

    response = jsonify({"success": True})
    return response

@app.route("/rating", methods=["GET"])
def get_rating():
    # Get the image name from the request
    image = request.args.get("image")

    # Get the ratings for the image
    if connected_to_database:
        ratings = get_ratings_collection()
        result = ratings.find_one({"image": image})
        if result:
            ratings_list = result["ratings"]
        else:
            ratings_list = []
    else:
        ratings_list = ratings_in_memory.get(image, [])

    # Calculate the average rating
    if ratings_list:
        avg_rating = sum(ratings_list) / len(ratings_list)
    else:
        avg_rating = None
    
    response = jsonify({"image": image, "average_rating": avg_rating})
    return response

@app.route('/ratings', methods=['GET'])
def get_ratings():
    if connected_to_database:
        image_ratings = {}
        ratings_collection = get_ratings_collection()
        all_images = ratings_collection.find()
        for image in all_images:
            image_ratings[image['image']] = image['ratings']
        image_ratings = image_ratings.items()
    else:
        image_ratings = ratings_in_memory.items()
    
    average_ratings = []
    for image_name, ratings in image_ratings:
        average_rating = sum(ratings) / len(ratings)
        average_ratings.append({"image_name": image_name, "rating": average_rating})
    average_ratings.sort(key=lambda x: x['rating'], reverse=True)
    response = jsonify(average_ratings)
    return response
    