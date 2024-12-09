from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from flask import Flask, jsonify, make_response, Response, request

from weather.weather_collection.models import location_model
from weather.weather_collection.models.favorites_model import FavoritesModel
from weather_collection.utils.sql_utils import check_database_connection, check_table_exists
import requests
from flask_bcrypt import Bcrypt
import os


# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

favorites_model = FavoritesModel()

####################################################
#
# User Model
####################################################

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///weather_api.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Columnn(db.String(80), unique=True, nullable=False)
    salt = db.Column(db.String(80), nullable=False)
    hashed_password = db.Column(db.String(120), nullable=False)
    
with app.app_context():
    db.create_all()
    
@app.route('/api/create-account', methods=['POST'])
def create_account():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400
    
    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'Username already exists'}), 400
    
    salt = bcrypt.generate_password_hash(username).decode('utf-8')
    hashed_password = bcrypt.generate_password_hash(password + salt).decode('utf-8')
    new_user = User(username=username, salt=salt, hashed_password=hashed_password)

    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message': 'Account created successfully'}), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400

    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({'error': 'Invalid credentials'}), 401

    if bcrypt.check_password_hash(user.hashed_password, password + user.salt):
        return jsonify({'message': 'Login successful'}), 200
    else:
        return jsonify({'error': 'Invalid credentials'}), 401
    
@app.route('/api/update-password', methods=['POST'])
def update_password():
    data = request.get_json()
    username = data.get('username')
    old_password = data.get('old_password')
    new_password = data.get('new_password')
    
    if not username or not old_password or not new_password:
        return jsonify({'error': 'All fields are required'}), 400
    
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({'error': 'Invalud credentials'}), 401
    
    if bcrypt.check_password_hash(user.hashed_password, old_password + user.salt):
        new_hashed_password = bcrypt.generate_password_hash(new_password + user.salt).decode('utf-8')
        user.hashed_password = new_hashed_password
        db.session.commit()
        return jsonify({'message': 'Password updated successfully'}), 200
    else:
        return jsonify({'error': 'Invalid credentials'}), 401

    
    
####################################################
#
# Healthchecks
#
####################################################

@app.route('/api/health', methods=['GET'])
def healthcheck() -> Response:
    """
    Health check route to verify the service is running.

    Returns:
        JSON response indicating the health status of the service.
    """
    app.logger.info('Health check')
    return make_response(jsonify({'status': 'healthy'}), 200)


@app.route('/api/db-check', methods=['GET'])
def db_check() -> Response:
    """
    Route to check if the database connection and songs table are functional.

    Returns:
        JSON response indicating the database health status.
    Raises:
        404 error if there is an issue with the database.
    """
    try:
        app.logger.info("Checking database connection...")
        check_database_connection()
        app.logger.info("Database connection is OK.")
        app.logger.info("Checking if songs table exists...")
        check_table_exists("songs")
        app.logger.info("songs table exists.")
        return make_response(jsonify({'database_status': 'healthy'}), 200)
    except Exception as e:
        return make_response(jsonify({'error': str(e)}), 404)


##########################################################
#
# Favorites Management
#
##########################################################

@app.route('/api/create-location', methods=['POST'])
def add_location() -> Response:
    """
    Route to add a new location to the catlog.

    Expected JSON Input:
        - name (str): The location's name.
    Returns:
        JSON response indicating the success of the location addition.
    Raises:
        400 error if input validation fails.
        500 error if there is an issue adding the song to the playlist.
    """
    app.logger.info('Adding a new location to the catalog')
    try:
        data = request.get_json()

        name = data.get('name')

        if  name is None:
            return make_response(jsonify({'error': 'Invalid input, all fields are required with valid values'}), 400)

        # Add the song to the playlist
        app.logger.info('Adding location: %s', name)
        location_model.create_location(name=name)
        app.logger.info("Location added to catlog: %s", name)
        return make_response(jsonify({'status': 'success', 'location': name}), 201)
    except Exception as e:
        app.logger.error("Failed to add location: %s", str(e))
        return make_response(jsonify({'error': str(e)}), 500)

@app.route('/api/clear-catalog', methods=['DELETE'])
def clear_catalog() -> Response:
    """
    Route to clear the entire location catalog (recreates the table).

    Returns:
        JSON response indicating success of the operation or error message.
    """
    try:
        app.logger.info("Clearing the location catalog")
        location_model.clear_catalog()
        return make_response(jsonify({'status': 'success'}), 200)
    except Exception as e:
        app.logger.error(f"Error clearing catalog: {e}")
        return make_response(jsonify({'error': str(e)}), 500)

@app.route('/api/delete-location/<int:location_id>', methods=['DELETE'])
def delete_location(location_id: int) -> Response:
    """
    Route to delete a location by its ID (soft delete).

    Path Parameter:
        - location_id (int): The ID of the location to delete.

    Returns:
        JSON response indicating success of the operation or error message.
    """
    try:
        app.logger.info(f"Deleting location by ID: {location_id}")
        location_model.delete_location(location_id)
        return make_response(jsonify({'status': 'success'}), 200)
    except Exception as e:
        app.logger.error(f"Error deleting location: {e}")
        return make_response(jsonify({'error': str(e)}), 500)


@app.route('/api/get-all-locations-from-catalog', methods=['GET'])
def get_all_locations() -> Response:
    """
    Route to retrieve all locations in the catalog (non-deleted).

    Returns:
        JSON response with the list of locations or error message.
    """
    try:
       
        app.logger.info("Retrieving all locations from the catalog")
        locations = location_model.get_all_locations()

        return make_response(jsonify({'status': 'success', 'locations': locations}), 200)
    except Exception as e:
        app.logger.error(f"Error retrieving locations: {e}")
        return make_response(jsonify({'error': str(e)}), 500)


@app.route('/api/get-location-from-catalog-by-id/<int:location_id>', methods=['GET'])
def get_locations_by_id(location_id: int) -> Response:
    """
    Route to retrieve a location by its ID.

    Path Parameter:
        - location_id (int): The ID of the location.

    Returns:
        JSON response with the location details or error message.
    """
    try:
        app.logger.info(f"Retrieving location by ID: {location_id}")
        location = location_model.get_location_by_id(location_id)
        return make_response(jsonify({'status': 'success', 'location': location}), 200)
    except Exception as e:
        app.logger.error(f"Error retrieving location by ID: {e}")
        return make_response(jsonify({'error': str(e)}), 500)


@app.route('/api/get-random-location', methods=['GET'])
def get_random_location() -> Response:
    """
    Route to retrieve a random location from the catalog.

    Returns:
        JSON response with the details of a random location or error message.
    """
    try:
        app.logger.info("Retrieving a random location from the catalog")
        location = location_model.get_random_location()
        return make_response(jsonify({'status': 'success', 'location': location}), 200)
    except Exception as e:
        app.logger.error(f"Error retrieving a random location: {e}")
        return make_response(jsonify({'error': str(e)}), 500)


############################################################
#
#Favorites Management
#
############################################################

@app.route('/api/add-location-to-favorites', methods=['POST'])
def add_location_to_favorites() -> Response:
    """
    Route to add a location to the favorite by the key (name).

    Expected JSON Input:
        - name (str): The location's name.
    
    Returns:
        JSON response indicating success of the addition or error message.
    """
    try:
        data = request.get_json()

        name = data.get('name')
        
        if not name:
            return make_response(jsonify({'error': 'Invalid input. Name is required.'}), 400)

        # Lookup the song by compound key
        location = location_model.get_location_by_name(name)

        # Add location to favorites
        favorites_model.add_location_to_favorites(location)

        app.logger.info(f"Location added to favorites: {name} )")
        return make_response(jsonify({'status': 'success', 'message': 'Location added to favorite'}), 201)

    except Exception as e:
        app.logger.error(f"Error adding location to favorites: {e}")
        return make_response(jsonify({'error': str(e)}), 500)

@app.route('/api/remove-favorites-from-favorites', methods=['DELETE'])
def remove_location_by_location_name() -> Response:
    """
    Route to remove a location from the favorites by the key (name).

    Expected JSON Input:
        - name (str): The location's name.
    Returns:
        JSON response indicating success of the removal or error message.
    """
    try:
        data = request.get_json()

        name = data.get('name')

        if not name:
            return make_response(jsonify({'error': 'Invalid input. Name is required.'}), 400)

        # Remove location from favorites
        favorites_model.remove_location_by_name(name)

        app.logger.info(f"Location removed from favorites: {name})")
        return make_response(jsonify({'status': 'success', 'message': 'Name removed from favorites'}), 200)

    except Exception as e:
        app.logger.error(f"Error removing location from favorites: {e}")
        return make_response(jsonify({'error': str(e)}), 500)


@app.route('/api/clear-favorites', methods=['POST'])
def clear_favorites() -> Response:
    """
    Route to clear all locations from the favorites.

    Returns:
        JSON response indicating success of the operation or an error message.
    """
    try:
        app.logger.info('Clearing the favorites')

        # Clear the entire favorites
        favorites_model.clear_favorites()

        return make_response(jsonify({'status': 'success', 'message': 'Favorites cleared'}), 200)

    except Exception as e:
        app.logger.error(f"Error clearing the favorites: {e}")
        return make_response(jsonify({'error': str(e)}), 500)

############################################################
#
# Get data for favorites
#
############################################################


@app.route('/api/get-current-weather-for-favorite/<str:location_name>',methods=['GET'])
def get_current_weather_for_favorite(name)-> Response:
    """
    get the current weather for a favorite using name
    Args:
        Name(str):The name of the favorite location to get weather.
    Returns:
        JSON response with the weather of the favorite location.
    Raises:
        500 error if there is an issue getting current weather for the favorite location.
    """
    try:
        app.logger.info('Getting current weather for %s',name)
        favorites_model.get_location_by_name_in_favorites(name)
        pos=requests.get('http://api.openweathermap.org/geo/1.0/direct',params={'appid':os.getenv('OPENWEATHER_APIKEY'),'q':name})
        data=pos.json()
        if len(data) == 0:
            return make_response(jsonify({'error': "Name is not a valid location"}),500)
        lat = data[0]["lat"]
        lon = data[0]["lon"]
        req=request.get('https://api.openweathermap.org/data/2.5/weather',params={'appid':os.getenv('OPENWEATHER_APIKEY'),'lon':lon,'lat':lat})
        data=req.json()
        return make_response(data,200)
    except Exception as e:
        app.logger.error(f"Error getting weather for favorites: {e}")
        return make_response(jsonify({'error': str(e)}), 500)

@app.route('/api/get-history-for-favorites/<str:location_name>',methods=['GET'])
def get_history_for_favorites(name)-> Response:
    """
    get the history for favorite locations.
    Args:
        Name(str):The name of the favorite location to get its weather history.
    Returns:
        JSON response with the weather history of the favorite location.
    Raises:
        500 error if there is an issue getting history of current weather for the favorite location.
    """
    try:
        app.logger.info('Getting history for %s',name)
        favorites_model.get_location_by_name_in_favorites(name)
        pos=requests.get('http://api.openweathermap.org/geo/1.0/direct',params={'appid':os.getenv('OPENWEATHER_APIKEY'),'q':name})
        data=pos.json()
        if len(data) == 0:
            return make_response(jsonify({'error': "Name is not a valid location"}),500)
        lat = data[0]["lat"]
        lon = data[0]["lon"]
        req=request.get('https://history.openweathermap.org/data/2.5/history/city',params={'appid':os.getenv('OPENWEATHER_APIKEY'),'lon':lon,'lat':lat,'type':'hour'})
        data=req.json()
        return make_response(data,200)
    except Exception as e:
        app.logger.error(f"Error getting history for favorites: {e}")
        return make_response(jsonify({'error': str(e)}), 500)

@app.route('/api/get-forecast-for-favorites/<str:location_name>',methods=['GET'])
def get_forecast_for_favorites(name)-> Response:
    """
    get weather forecast for favorite locations.
    Args:
        Name(str):The name of the favorite location to get its weather forecast.
    Returns:
        JSON response with the weather forecast of the favorite location.
    Raises:
        500 error if there is an issue getting forecast of  weather for the favorite location.
    """
    try:
        app.logger.info('Getting forecast for %s',name)
        favorites_model.get_location_by_name_in_favorites(name)
        pos=requests.get('http://api.openweathermap.org/geo/1.0/direct',params={'appid':os.getenv('OPENWEATHER_APIKEY'),'q':name})
        data=pos.json()
        if len(data) == 0:
            return make_response(jsonify({'error': "Name is not a valid location"}),500)
        lat = data[0]["lat"]
        lon = data[0]["lon"]
        req=request.get('https://pro.openweathermap.org/data/2.5/forecast/hourly',params={'appid':os.getenv('OPENWEATHER_APIKEY'),'lon':lon,'lat':lat,'type':'hour'})
        data=req.json()
        return make_response(data,200)
    except Exception as e:
        app.logger.error(f"Error getting forecasts for favorites: {e}")
        return make_response(jsonify({'error': str(e)}), 500)
 
@app.route('/api/get-weather-for-all-favorites/',methods=['GET'])
def get_weather_for_all_favorites()-> Response:
    """
    get weather for all favorite locations.
    Args:
        Name(str):The name of all favorite locations to get thier weather.
    Returns:
        JSON response with the weather of all the favorite weathers.
    Raises:
        500 error if there is an issue getting  weather for all the favorite locations.
    """
    try:
        app.logger.info('Getting weather for all favorites')
        favorites= favorites_model.get_all_favorites()
        ret=[]
        for name in favorites:
            pos=requests.get('http://api.openweathermap.org/geo/1.0/direct',params={'appid':os.getenv('OPENWEATHER_APIKEY'),'q':name})
            data=pos.json()
            if len(data) == 0:
                return make_response(jsonify({'error': "Name is not a valid location"}),500)
            lat = data[0]["lat"]
            lon = data[0]["lon"]
            req=request.get('https://pro.openweathermap.org/data/2.5/forecast/hourly',params={'appid':os.getenv('OPENWEATHER_APIKEY'),'lon':lon,'lat':lat,'type':'hour'})
            data=req.json()
            ret.append(data)
        return make_response(ret,200)
    except Exception as e:
        app.logger.error(f"Error getting weather for all favorite locations: {e}")
        return make_response(jsonify({'error': str(e)}), 500)
    


@app.route('/api/get-all-locations-from-favorites', methods=['GET'])
def get_all_locations_from_favorites() -> Response:
    """
    Route to retrieve all locations in the favorites.

    Returns:
        JSON response with the list of locations or an error message.
    """
    try:
        app.logger.info("Retrieving all locations from favorites")

        # Get all songs from the playlist
        locations = favorites_model.get_all_favorites()

        return make_response(jsonify({'status': 'success', 'locations': locations}), 200)

    except Exception as e:
        app.logger.error(f"Error retrieving all locations from favorites: {e}")
        return make_response(jsonify({'error': str(e)}), 500)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
