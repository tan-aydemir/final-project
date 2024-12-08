#!/bin/bash

# Define the base URL for the Flask API
BASE_URL="http://localhost:5000/api"

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
  artist=$1
  title=$2
  year=$3
  genre=$4
  duration=$5

  echo "Adding location ($artist - $title, $year) to the favorites..."
  curl -s -X POST "$BASE_URL/create-location" -H "Content-Type: application/json" \
    -d "{\"artist\":\"$artist\", \"title\":\"$title\", \"year\":$year, \"genre\":\"$genre\", \"duration\":$duration}" | grep -q '"status": "success"'

  if [ $? -eq 0 ]; then
    echo "location added successfully."
  else
    echo "Failed to add location."
    exit 1
  fi
}

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
  echo "Getting all locations in the favorites..."
  response=$(curl -s -X GET "$BASE_URL/get-all-locations-from-catalog")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "All locations retrieved successfully."
    if [ "$ECHO_JSON" = true ]; then
      echo "locations JSON:"
      echo "$response" | jq .
    fi
  else
    echo "Failed to get locations."
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

get_location_by_compound_key() { #jayden
  artist=$1
  title=$2
  year=$3

  echo "Getting location by compound key (Artist: '$artist', Title: '$title', Year: $year)..."
  response=$(curl -s -X GET "$BASE_URL/get-location-from-catalog-by-compound-key?artist=$(echo $artist | sed 's/ /%20/g')&title=$(echo $title | sed 's/ /%20/g')&year=$year")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "location retrieved successfully by compound key."
    if [ "$ECHO_JSON" = true ]; then
      echo "location JSON (by compound key):"
      echo "$response" | jq .
    fi
  else
    echo "Failed to get location by compound key."
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
  artist=$1
  title=$2
  year=$3

  echo "Adding location to favorites: $artist - $title ($year)..."
  response=$(curl -s -X POST "$BASE_URL/add-location-to-favorites" \
    -H "Content-Type: application/json" \
    -d "{\"artist\":\"$artist\", \"title\":\"$title\", \"year\":$year}")

  if echo "$response" | grep -q '"status": "success"'; then
    echo "location added to favorites successfully."
    if [ "$ECHO_JSON" = true ]; then
      echo "location JSON:"
      echo "$response" | jq .
    fi
  else
    echo "Failed to add location to favorites."
    exit 1
  fi
}

remove_location_from_favorites() { #tan
  artist=$1
  title=$2
  year=$3

  echo "Removing location from favorites: $artist - $title ($year)..."
  response=$(curl -s -X DELETE "$BASE_URL/remove-location-from-favorites" \
    -H "Content-Type: application/json" \
    -d "{\"artist\":\"$artist\", \"title\":\"$title\", \"year\":$year}")

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

remove_location_by_name() { #jayden
  track_number=$1

  echo "Removing location by track number: $track_number..."
  response=$(curl -s -X DELETE "$BASE_URL/remove-location-from-favorites-by-track-number/$track_number")

  if echo "$response" | grep -q '"status":'; then
    echo "location removed from favorites by track number ($track_number) successfully."
  else
    echo "Failed to remove location from favorites by track number."
    exit 1
  fi
}

clear_playlist() { #tan
  echo "Clearing favorites..."
  response=$(curl -s -X POST "$BASE_URL/clear-favorites")

  if echo "$response" | grep -q '"status": "success"'; then
    echo "Favorites cleared successfully."
  else
    echo "Failed to clear favorites."
    exit 1
  fi
}


############################################################
#
# Favorites
#
############################################################


get_all_locations_from_playlist() { #jayden
  echo "Retrieving all locations from favorites..."
  response=$(curl -s -X GET "$BASE_URL/get-all-locations-from-favorites")

  if echo "$response" | grep -q '"status": "success"'; then
    echo "All locations retrieved successfully."
    if [ "$ECHO_JSON" = true ]; then
      echo "locations JSON:"
      echo "$response" | jq .
    fi
  else
    echo "Failed to retrieve all locations from favorites."
    exit 1
  fi
}


# Health checks
check_health
check_db

# Clear the catalog
clear_catalog

# Create locations
create_location "The Beatles" "Hey Jude" 1968 "Rock" 180
create_location "The Rolling Stones" "Paint It Black" 1966 "Rock" 180
create_location "The Beatles" "Let It Be" 1970 "Rock" 180
create_location "Queen" "Bohemian Rhapsody" 1975 "Rock" 180
create_location "Led Zeppelin" "Stairway to Heaven" 1971 "Rock" 180

delete_location_by_id 1
get_all_locations

get_location_by_id 2
get_location_by_compound_key "The Beatles" "Let It Be" 1970
get_random_location

clear_playlist

add_location_to_favorites "The Rolling Stones" "Paint It Black" 1966
add_location_to_favorites "Queen" "Bohemian Rhapsody" 1975
add_location_to_favorites "Led Zeppelin" "Stairway to Heaven" 1971
add_location_to_favorites "The Beatles" "Let It Be" 1970

remove_location_from_favorites "The Beatles" "Let It Be" 1970
remove_location_by_name 2

get_all_locations_from_playlist

add_location_to_favorites "Queen" "Bohemian Rhapsody" 1975
add_location_to_favorites "The Beatles" "Let It Be" 1970

move_location_to_beginning "The Beatles" "Let It Be" 1970
move_location_to_end "Queen" "Bohemian Rhapsody" 1975
move_location_to_track_number "Led Zeppelin" "Stairway to Heaven" 1971 2
swap_locations_in_playlist 1 2

get_all_locations_from_playlist
get_location_from_playlist_by_track_number 1


echo "All tests passed successfully!"
