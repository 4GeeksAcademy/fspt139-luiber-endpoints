"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
import os
from flask import Flask, request, jsonify, url_for
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_cors import CORS
from utils import APIException, generate_sitemap
from admin import setup_admin
from models import db, User, People, Planet, FavoritePeople, FavoritePlanet
#from models import Person

app = Flask(__name__)
app.url_map.strict_slashes = False

db_url = os.getenv("DATABASE_URL")
if db_url is not None:
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace("postgres://", "postgresql://")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:////tmp/test.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

MIGRATE = Migrate(app, db)
db.init_app(app)
CORS(app)
setup_admin(app)

# Handle/serialize errors like a JSON object
@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

# generate sitemap with all your endpoints
@app.route('/')
def sitemap():
    return generate_sitemap(app)

@app.route('/user', methods=['GET'])
def handle_hello():

    response_body = {
        "msg": "Hello, this is your GET /user response "
    }

    return jsonify(response_body), 200

# [GET] /people - Listar todos los personajes
@app.route('/people', methods=['GET'])
def get_all_people():
    people_query = db.session.scalars(db.select(People)).all()
    results = [person.serialize() for person in people_query]
    return jsonify(results), 200

# [GET] /people/<int:people_id> - Obtener un personaje por ID
@app.route('/people/<int:people_id>', methods=['GET'])
def get_single_person(people_id):
    person = db.session.get(People, people_id)
    if person is None:
        return jsonify({"msg": f"Personaje con id {people_id} no encontrado"}), 404
    return jsonify(person.serialize()), 200

# [GET] /planets - Listar todos los planetas
@app.route('/planets', methods=['GET'])
def get_all_planets():
    planets_query = db.session.scalars(db.select(Planet)).all()
    results = [planet.serialize() for planet in planets_query]
    return jsonify(results), 200

# [GET] /planets/<int:planet_id> - Obtener un planeta por ID
@app.route('/planets/<int:planet_id>', methods=['GET'])
def get_single_planet(planet_id):
    planet = db.session.get(Planet, planet_id)
    if planet is None:
        return jsonify({"msg": f"Planeta con id {planet_id} no encontrado"}), 404
    return jsonify(planet.serialize()), 200

# [GET] /users - Listar todos los usuarios
@app.route('/users', methods=['GET'])
def get_all_users():
    users_query = db.session.scalars(db.select(User)).all()
    results = [user.serialize() for user in users_query]
    return jsonify(results), 200

# [GET] /users/favorites - Listar todos los favoritos del usuario actual
@app.route('/users/favorites', methods=['GET'])
def get_user_favorites():
    current_user_id = 1
    user = db.session.get(User, current_user_id)
    if user is None:
        return jsonify({"msg": "Usuario no encontrado"}), 404

    fav_people = [fav.serialize() for fav in user.favorite_people]
    fav_planets = [fav.serialize() for fav in user.favorite_planets]

    return jsonify({
        "favorite_people": fav_people,
        "favorite_planets": fav_planets
    }), 200


# [POST] /favorite/people/<int:people_id> - Añadir personaje favorito
@app.route('/favorite/people/<int:people_id>', methods=['POST'])
def add_favorite_person(people_id):
    current_user_id = 1
    
    person = db.session.get(People, people_id)
    if person is None:
        return jsonify({"msg": f"Personaje con id {people_id} no existe"}), 404

    existing_fav = db.session.scalar(
        db.select(FavoritePeople).filter_by(user_id=current_user_id, people_id=people_id)
    )
    if existing_fav:
        return jsonify({"msg": "El personaje ya está en tus favoritos"}), 400

    new_fav = FavoritePeople(user_id=current_user_id, people_id=people_id)
    db.session.add(new_fav)
    db.session.commit()
    return jsonify({"msg": "Personaje añadido a favoritos exitosamente", "favorite": new_fav.serialize()}), 201


# [POST] /favorite/planet/<int:planet_id> - Añadir planeta favorito
@app.route('/favorite/planet/<int:planet_id>', methods=['POST'])
def add_favorite_planet(planet_id):
    current_user_id = 1
    
    planet = db.session.get(Planet, planet_id)
    if planet is None:
        return jsonify({"msg": f"Planeta con id {planet_id} no existe"}), 404

    existing_fav = db.session.scalar(
        db.select(FavoritePlanet).filter_by(user_id=current_user_id, planet_id=planet_id)
    )
    if existing_fav:
        return jsonify({"msg": "El planeta ya está en tus favoritos"}), 400

    new_fav = FavoritePlanet(user_id=current_user_id, planet_id=planet_id)
    db.session.add(new_fav)
    db.session.commit()
    return jsonify({"msg": "Planeta añadido a favoritos exitosamente", "favorite": new_fav.serialize()}), 201


# [DELETE] /favorite/people/<int:people_id> - Eliminar personaje favorito
@app.route('/favorite/people/<int:people_id>', methods=['DELETE'])
def delete_favorite_person(people_id):
    current_user_id = 1
    
    favorite = db.session.scalar(
        db.select(FavoritePeople).filter_by(user_id=current_user_id, people_id=people_id)
    )
    if favorite is None:
        return jsonify({"msg": "Favorito no encontrado para este usuario"}), 404

    db.session.delete(favorite)
    db.session.commit()
    return jsonify({"msg": "Personaje favorito eliminado exitosamente"}), 200


# [DELETE] /favorite/planet/<int:planet_id> - Eliminar planeta favorito
@app.route('/favorite/planet/<int:planet_id>', methods=['DELETE'])
def delete_favorite_planet(planet_id):
    current_user_id = 1
    
    favorite = db.session.scalar(
        db.select(FavoritePlanet).filter_by(user_id=current_user_id, planet_id=planet_id)
    )
    if favorite is None:
        return jsonify({"msg": "Favorito no encontrado para este usuario"}), 404

    db.session.delete(favorite)
    db.session.commit()
    return jsonify({"msg": "Planeta favorito eliminado exitosamente"}), 200


# this only runs if `$ python src/app.py` is executed
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)
