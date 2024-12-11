#!/bin/bash

# Define the base URL for the Flask API
BASE_URL="http://localhost:10001/api"

# Flag to control whether to echo JSON output
ECHO_JSON=false

# Parse command-line arguments
while [ "$#" -gt 0 ]; do
  case $1 in
    --echo-json) ECHO_JSON=true ;;
    *) echo "Unknown parameter passed: $1"; exit 1 ;;
  esac
  shift
done


###############################################
#
# Health checks
#
###############################################

# Function to check the health of the service
check_health() {
  echo "Checking health status..."
  curl -s -X GET "$BASE_URL/health" | grep -q '"status": "healthy"'
  if [ $? -eq 0 ]; then
    echo "Service is healthy."
  else
    echo "Health check failed."
    exit 1
  fi
}

# Function to check the database connection
check_db() {
  echo "Checking database connection..."
  curl -s -X GET "$BASE_URL/db-check" | grep -q '"database_status": "healthy"'
  if [ $? -eq 0 ]; then
    echo "Database connection is healthy."
  else
    echo "Database check failed."
    exit 1
  fi
}


##########################################################
#
# location Management
#
##########################################################

clear_catalog() {
  echo "Clearing Favorites..."
  curl -s -X DELETE "$BASE_URL/clear-catalog" | grep -q '"status": "success"'
}

create_location() { #jayden
  name=$1

  echo "Adding location ($name) to the catalog..."
  response=$(curl -s -X POST "$BASE_URL/api/create-location" \
    -H "Content-Type: application/json" \
    -d "{\"name\":\"$name\"}")

  if echo "$response" | grep -q '"status": "success"'; then
    echo "Location added successfully."
  else
    echo "Failed to add location. Response: $response"
    exit 1
  fi
}


###############
#
# Login tests
#
################
login() {
  username=$1
  password=$2

  echo "Attempting login for ($username)..."
  response=$(curl -s -X POST "$BASE_URL/api/login" \
    -H "Content-Type: application/json" \
    -d "{\"username\":\"$username\", \"password\":\"$password\"}")

  if echo "$response" | grep -q '"message": "Login successful"'; then
    echo "Login successful."
  else
    echo "Failed to login. Response: $response"
    exit 1
  fi
}

create_account() {
  username=$1
  password=$2

  echo "Creating account for ($username)..."
  response=$(curl -s -X POST "$BASE_URL/api/create-account" \
    -H "Content-Type: application/json" \
    -d "{\"username\":\"$username\", \"password\":\"$password\"}")

  if echo "$response" | grep -q '"message": "Account created successfully"'; then
    echo "Account created successfully."
  else
    echo "Failed to create account. Response: $response"
    exit 1
  fi
}

update_password() {
  username=$1
  old_password=$2
  new_password=$3

  echo "Updating password for ($username)..."
  response=$(curl -s -X POST "$BASE_URL/api/update-password" \
    -H "Content-Type: application/json" \
    -d "{\"username\":\"$username\", \"old_password\":\"$old_password\", \"new_password\":\"$new_password\"}")

  if echo "$response" | grep -q '"message": "Password updated successfully"'; then
    echo "Password updated successfully."
  else
    echo "Failed to update password. Response: $response"
    exit 1
  fi
}

#Management Cont.

delete_location_by_id() { #tan
  location_id=$1

  echo "Deleting location by ID ($location_id)..."
  response=$(curl -s -X DELETE "$BASE_URL/delete-location/$location_id")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "location deleted successfully by ID ($location_id)."
  else
    echo "Failed to delete location by ID ($location_id)."
    exit 1
  fi
}

get_all_locations() { #jayden
  echo "Retrieving all locations from the catalog..."
  response=$(curl -s -X GET "$BASE_URL/api/get-all-locations-from-catalog" \
    -H "Content-Type: application/json")

  if echo "$response" | grep -q '"status": "success"'; then
    echo "Successfully retrieved all locations."
    echo "Response: $response"
  else
    echo "Failed to retrieve locations. Response: $response"
    exit 1
  fi
}

get_location_by_id() { #tan
  location_id=$1

  echo "Getting location by ID ($location_id)..."
  response=$(curl -s -X GET "$BASE_URL/get-location-from-catalog-by-id/$location_id")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "location retrieved successfully by ID ($location_id)."
    if [ "$ECHO_JSON" = true ]; then
      echo "location JSON (ID $location_id):"
      echo "$response" | jq .
    fi
  else
    echo "Failed to get location by ID ($location_id)."
    exit 1
  fi
}


get_random_location() { #tan
  echo "Getting a random location from the catalog..."
  response=$(curl -s -X GET "$BASE_URL/get-random-location")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Random location retrieved successfully."
    if [ "$ECHO_JSON" = true ]; then
      echo "Random location JSON:"
      echo "$response" | jq .
    fi
  else
    echo "Failed to get a random location."
    exit 1
  fi
}


############################################################
#
# Favorites Management
#
############################################################

add_location_to_favorites() { #jayden
  name=$1

  echo "Adding location ($name) to favorites..."
  response=$(curl -s -X POST "$BASE_URL/api/add-location-to-favorites" \
    -H "Content-Type: application/json" \
    -d "{\"name\":\"$name\"}")

  if echo "$response" | grep -q '"status": "success"'; then
    echo "Location added to favorites successfully."
    if [ "$ECHO_JSON" = true ]; then
      echo "Response JSON:"
      echo "$response" | jq .
    fi
  else
    echo "Failed to add location to favorites. Response: $response"
    exit 1
  fi
}


remove_location_from_favorites_by_location_name() { #tan
  location_name=$1

  echo "Removing location from favorites: $location_name..."
  response=$(curl -s -X DELETE "$BASE_URL/remove-location-from-favorites" \
    -H "Content-Type: application/json" \
    -d "{\"LocationName\":\"$location_name}")

  if echo "$response" | grep -q '"status": "success"'; then
    echo "location removed from favorites successfully."
    if [ "$ECHO_JSON" = true ]; then
      echo "location JSON:"
      echo "$response" | jq .
    fi
  else
    echo "Failed to remove location from favorites."
    exit 1
  fi
}


clear_catalog() { #tan
  echo "Clearing favorites..."
  response=$(curl -s -X POST "$BASE_URL/clear-catalog")

  if echo "$response" | grep -q '"status": "success"'; then
    echo "Catalog cleared successfully."
  else
    echo "Failed to clear catalog."
    exit 1
  fi
}

############################################################
#
# Favorites
#
############################################################


get_current_weather_for_favorite() {
  name=$1
  echo "Getting current weather for favorite ($name)..."
  response=$(curl -s -X GET "$BASE_URL/api/get-current-weather-for-favorite/$name")

  # Check if the response is empty or contains an error
  if echo "$response" | grep -q '"error"'; then
    echo "Failed to get current weather for $name. Response: $response"
    exit 1
  else
    echo "Successfully retrieved current weather for $name."
    if [ "$ECHO_JSON" = true ]; then
      echo "$response" | jq .
    fi
  fi
}

get_history_for_favorites() {
  name=$1
  echo "Getting history for favorite ($name)..."
  response=$(curl -s -X GET "$BASE_URL/api/get-history-for-favorites/$name")

  if echo "$response" | grep -q '"error"'; then
    echo "Failed to get history for $name. Response: $response"
    exit 1
  else
    echo "Successfully retrieved history for $name."
    if [ "$ECHO_JSON" = true ]; then
      echo "$response" | jq .
    fi
  fi
}

get_forecast_for_favorites() {
  name=$1
  echo "Getting forecast for favorite ($name)..."
  response=$(curl -s -X GET "$BASE_URL/api/get-forecast-for-favorites/$name")

  if echo "$response" | grep -q '"error"'; then
    echo "Failed to get forecast for $name. Response: $response"
    exit 1
  else
    echo "Successfully retrieved forecast for $name."
    if [ "$ECHO_JSON" = true ]; then
      echo "$response" | jq .
    fi
  fi
}

get_weather_for_all_favorites() {
  echo "Getting weather for all favorites..."
  response=$(curl -s -X GET "$BASE_URL/api/get-weather-for-all-favorites/")

  if echo "$response" | grep -q '"error"'; then
    echo "Failed to get weather for all favorites. Response: $response"
    exit 1
  else
    echo "Successfully retrieved weather for all favorites."
    if [ "$ECHO_JSON" = true ]; then
      echo "$response" | jq .
    fi
  fi
}

get_all_locations_from_favorites() {
  echo "Getting all locations from favorites..."
  response=$(curl -s -X GET "$BASE_URL/api/get-all-locations-from-favorites")

  if echo "$response" | grep -q '"status": "success"'; then
    echo "All locations retrieved from favorites successfully."
    if [ "$ECHO_JSON" = true ]; then
      echo "locations JSON:"
      echo "$response" | jq .
    fi
  else
    echo "Failed to get locations from favorites. Response: $response"
    exit 1
  fi
}


# Health checks
check_health
check_db

# Create locations
# Create multiple locations in the catalog using only the 'name' parameter
create_location "Boston"
create_location "Seattle"
create_location "New York"
create_location "Los Angeles"
create_location "Chicago"

# Delete a location by its ID (e.g., Boston might be ID=1)
delete_location_by_id 1

# Get all locations from the catalog
get_all_locations_from_catalog

# Get a location by its ID (assuming Seattle is ID=2)
get_location_by_id 2

# Get a random location from the catalog
get_random_location

# Clear the entire catalog
clear_catalog

# Re-add some locations to the catalog before working with favorites
create_location "Miami"
create_location "London"
create_location "Paris"
create_location "Tokyo"

# Add these locations to favorites by name
add_location_to_favorites "Miami"
add_location_to_favorites "London"
add_location_to_favorites "Paris"
add_location_to_favorites "Tokyo"

# Remove a location from favorites by name
remove_location_from_favorites "Paris"

# Get all locations from favorites
get_all_locations_from_favorites

# Clear all favorites
clear_favorites


# Test Account Creation
create_account "testuser" "testpassword"

# Test Duplicate Account Creation (Should not create the same user again)
create_account "testuser" "testpassword"

# Test Login with Correct Credentials
login "testuser" "testpassword"

# Test Login with Incorrect Credentials
echo "Testing login with incorrect password..."
response=$(curl -s -X POST "$BASE_URL/login" \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"testuser\", \"password\":\"wrongpassword\"}")

if echo "$response" | grep -q '"error": "Invalid credentials"'; then
  echo "Login failed with incorrect password as expected."
else
  echo "Response: $response"
  exit_with_error "Login test with incorrect password did not behave as expected."
fi

# Test Password Update
update_password "testuser" "testpassword" "newpassword"

# Test Login with New Password
login "testuser" "newpassword"

# Test Login with Old Password (Should Fail)
echo "Testing login with old password after password update..."
response=$(curl -s -X POST "$BASE_URL/login" \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"testuser\", \"password\":\"testpassword\"}")

if echo "$response" | grep -q '"error": "Invalid credentials"'; then
  echo "Login with old password failed as expected after password update."
else
  echo "Response: $response"
  exit_with_error "Login test with old password did not behave as expected."
fi


echo "All tests passed successfully!"
