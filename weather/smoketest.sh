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
# Song Management
#
##########################################################

clear_catalog() {
  echo "Clearing the playlist..."
  curl -s -X DELETE "$BASE_URL/clear-catalog" | grep -q '"status": "success"'
}

create_location() {
  name=$1

  echo "Adding location ($name) to the catalog..."
  curl -s -X POST "$BASE_URL/create-song" -H "Content-Type: application/json" \
    -d "{\"name\": \"$1\"}" | grep -q '"status": "success"'

  if [ $? -eq 0 ]; then
    echo "Location added successfully."
  else
    echo "Failed to add location."
    exit 1
  fi
}

delete_location() {
  location_id=$1

  echo "Deleting location by ID ($location_id)..."
  response=$(curl -s -X DELETE "$BASE_URL/delete-location/$location_id")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Location deleted successfully by ID ($location_id)."
  else
    echo "Failed to delete location by ID ($location_id)."
    exit 1
  fi
}

get_all_locations() {
  echo "Getting all locations in the playlist..."
  response=$(curl -s -X GET "$BASE_URL/get-all-locations-from-catalog")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "All locations retrieved successfully."
    if [ "$ECHO_JSON" = true ]; then
      echo "Locations JSON:"
      echo "$response" | jq .
    fi
  else
    echo "Failed to get songs."
    exit 1
  fi
}

get_location_by_id() {
  location_id=$1

  echo "Getting location by ID ($location_id)..."
  response=$(curl -s -X GET "$BASE_URL/get-location-from-catalog-by-id/$location_id")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Location retrieved successfully by ID ($location_id)."
    if [ "$ECHO_JSON" = true ]; then
      echo "Location JSON (ID $location_id):"
      echo "$response" | jq .
    fi
  else
    echo "Failed to get location by ID ($location_id)."
    exit 1
  fi
}

get_song_by_compound_key() {
  artist=$1
  title=$2
  year=$3

  echo "Getting song by compound key (Artist: '$artist', Title: '$title', Year: $year)..."
  response=$(curl -s -X GET "$BASE_URL/get-song-from-catalog-by-compound-key?artist=$(echo $artist | sed 's/ /%20/g')&title=$(echo $title | sed 's/ /%20/g')&year=$year")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Song retrieved successfully by compound key."
    if [ "$ECHO_JSON" = true ]; then
      echo "Song JSON (by compound key):"
      echo "$response" | jq .
    fi
  else
    echo "Failed to get song by compound key."
    exit 1
  fi
}

get_random_song() {
  echo "Getting a random song from the catalog..."
  response=$(curl -s -X GET "$BASE_URL/get-random-song")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Random song retrieved successfully."
    if [ "$ECHO_JSON" = true ]; then
      echo "Random Song JSON:"
      echo "$response" | jq .
    fi
  else
    echo "Failed to get a random song."
    exit 1
  fi
}


############################################################
#
# Playlist Management
#
############################################################

add_song_to_playlist() {
  artist=$1
  title=$2
  year=$3

  echo "Adding song to playlist: $artist - $title ($year)..."
  response=$(curl -s -X POST "$BASE_URL/add-song-to-playlist" \
    -H "Content-Type: application/json" \
    -d "{\"artist\":\"$artist\", \"title\":\"$title\", \"year\":$year}")

  if echo "$response" | grep -q '"status": "success"'; then
    echo "Song added to playlist successfully."
    if [ "$ECHO_JSON" = true ]; then
      echo "Song JSON:"
      echo "$response" | jq .
    fi
  else
    echo "Failed to add song to playlist."
    exit 1
  fi
}

remove_song_from_playlist() {
  artist=$1
  title=$2
  year=$3

  echo "Removing song from playlist: $artist - $title ($year)..."
  response=$(curl -s -X DELETE "$BASE_URL/remove-song-from-playlist" \
    -H "Content-Type: application/json" \
    -d "{\"artist\":\"$artist\", \"title\":\"$title\", \"year\":$year}")

  if echo "$response" | grep -q '"status": "success"'; then
    echo "Song removed from playlist successfully."
    if [ "$ECHO_JSON" = true ]; then
      echo "Song JSON:"
      echo "$response" | jq .
    fi
  else
    echo "Failed to remove song from playlist."
    exit 1
  fi
}

remove_song_by_track_number() {
  track_number=$1

  echo "Removing song by track number: $track_number..."
  response=$(curl -s -X DELETE "$BASE_URL/remove-song-from-playlist-by-track-number/$track_number")

  if echo "$response" | grep -q '"status":'; then
    echo "Song removed from playlist by track number ($track_number) successfully."
  else
    echo "Failed to remove song from playlist by track number."
    exit 1
  fi
}

clear_playlist() {
  echo "Clearing playlist..."
  response=$(curl -s -X POST "$BASE_URL/clear-playlist")

  if echo "$response" | grep -q '"status": "success"'; then
    echo "Playlist cleared successfully."
  else
    echo "Failed to clear playlist."
    exit 1
  fi
}


############################################################
#
# Play Playlist
#
############################################################


get_all_songs_from_playlist() {
  echo "Retrieving all songs from playlist..."
  response=$(curl -s -X GET "$BASE_URL/get-all-songs-from-playlist")

  if echo "$response" | grep -q '"status": "success"'; then
    echo "All songs retrieved successfully."
    if [ "$ECHO_JSON" = true ]; then
      echo "Songs JSON:"
      echo "$response" | jq .
    fi
  else
    echo "Failed to retrieve all songs from playlist."
    exit 1
  fi
}


# Health checks
check_health
check_db

# Clear the catalog
clear_catalog

# Create songs
create_location "Boston"
create_location "Washington"
create_location "New York"

delete_location 1
get_all_locations

get_location_by_id 2
get_song_by_compound_key "The Beatles" "Let It Be" 1970
get_random_song

clear_playlist

add_song_to_playlist "The Rolling Stones" "Paint It Black" 1966
add_song_to_playlist "Queen" "Bohemian Rhapsody" 1975
add_song_to_playlist "Led Zeppelin" "Stairway to Heaven" 1971
add_song_to_playlist "The Beatles" "Let It Be" 1970

remove_song_from_playlist "The Beatles" "Let It Be" 1970
remove_song_by_track_number 2

get_all_songs_from_playlist

add_song_to_playlist "Queen" "Bohemian Rhapsody" 1975
add_song_to_playlist "The Beatles" "Let It Be" 1970

move_song_to_beginning "The Beatles" "Let It Be" 1970
move_song_to_end "Queen" "Bohemian Rhapsody" 1975
move_song_to_track_number "Led Zeppelin" "Stairway to Heaven" 1971 2
swap_songs_in_playlist 1 2

get_all_songs_from_playlist
get_song_from_playlist_by_track_number 1

get_playlist_length_duration

play_current_song
rewind_playlist

play_entire_playlist
play_current_song
play_rest_of_playlist

get_song_leaderboard

echo "All tests passed successfully!"
