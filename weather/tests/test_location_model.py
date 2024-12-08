from contextlib import contextmanager
import re
import sqlite3

import pytest

from weather.weather_collection.models.location_model import (
    Location,
    create_location,
    clear_catalog,
    delete_location,
    get_location_by_id,
    get_all_locations,
    get_random_location
)

######################################################
#
#    Fixtures
#
######################################################

def normalize_whitespace(sql_query: str) -> str:
    return re.sub(r'\s+', ' ', sql_query).strip()

# Mocking the database connection for tests
@pytest.fixture
def mock_cursor(mocker):
    mock_conn = mocker.Mock()
    mock_cursor = mocker.Mock()

    # Mock the connection's cursor
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchone.return_value = None  # Default return for queries
    mock_cursor.fetchall.return_value = []
    mock_conn.commit.return_value = None

    # Mock the get_db_connection context manager from sql_utils
    @contextmanager
    def mock_get_db_connection():
        yield mock_conn  # Yield the mocked connection object

    mocker.patch("weather_collection.models.location_model.get_db_connection", mock_get_db_connection)

    return mock_cursor  # Return the mock cursor so we can set expectations per test

######################################################
#
#    Add and delete
#
######################################################

def test_create_location(mock_cursor):
    """Test creating a new location in the catalog."""

    # Call the function to create a new location
    create_location(name="Boston")

    expected_query = normalize_whitespace("""
        INSERT INTO locations (name)
        VALUES (?)
    """)

    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])

    # Assert that the SQL query was correct
    assert actual_query == expected_query, "The SQL query did not match the expected structure."

    # Extract the arguments used in the SQL call (second element of call_args)
    actual_arguments = mock_cursor.execute.call_args[0][1]

    # Assert that the SQL query was executed with the correct arguments
    expected_arguments = ("Boston")
    assert actual_arguments == expected_arguments, f"The SQL query arguments did not match. Expected {expected_arguments}, got {actual_arguments}."

def test_create_location_duplicate(mock_cursor):
    """Test creating a location with a duplicate location (should raise an error)."""

    # Simulate that the database will raise an IntegrityError due to a duplicate entry
    mock_cursor.execute.side_effect = sqlite3.IntegrityError("UNIQUE constraint failed: locations.name")

    # Expect the function to raise a ValueError with a specific message when handling the IntegrityError
    with pytest.raises(ValueError, match="Location with name Boston already exists."):
        create_location(name="Boston")

def test_delete_location(mock_cursor):
    """Test soft deleting a location from the catalog by location ID."""

    # Simulate that the location exists (id = 1)
    mock_cursor.fetchone.return_value = ([False])

    # Call the delete_location function
    delete_location(1)

    # Normalize the SQL for both queries (SELECT and UPDATE)
    expected_select_sql = normalize_whitespace("SELECT deleted FROM locations WHERE id = ?")
    expected_update_sql = normalize_whitespace("UPDATE locations SET deleted = TRUE WHERE id = ?")

    # Access both calls to `execute()` using `call_args_list`
    actual_select_sql = normalize_whitespace(mock_cursor.execute.call_args_list[0][0][0])
    actual_update_sql = normalize_whitespace(mock_cursor.execute.call_args_list[1][0][0])

    # Ensure the correct SQL queries were executed
    assert actual_select_sql == expected_select_sql, "The SELECT query did not match the expected structure."
    assert actual_update_sql == expected_update_sql, "The UPDATE query did not match the expected structure."

    # Ensure the correct arguments were used in both SQL queries
    expected_select_args = (1,)
    expected_update_args = (1,)

    actual_select_args = mock_cursor.execute.call_args_list[0][0][1]
    actual_update_args = mock_cursor.execute.call_args_list[1][0][1]

    assert actual_select_args == expected_select_args, f"The SELECT query arguments did not match. Expected {expected_select_args}, got {actual_select_args}."
    assert actual_update_args == expected_update_args, f"The UPDATE query arguments did not match. Expected {expected_update_args}, got {actual_update_args}."

def test_delete_location_bad_id(mock_cursor):
    """Test error when trying to delete a non-existent location."""

    # Simulate that no location exists with the given ID
    mock_cursor.fetchone.return_value = None

    # Expect a ValueError when attempting to delete a non-existent location
    with pytest.raises(ValueError, match="Location with ID 999 not found"):
        delete_location(999)

def test_delete_location_already_deleted(mock_cursor):
    """Test error when trying to delete a location that's already marked as deleted."""

    # Simulate that the location exists but is already marked as deleted
    mock_cursor.fetchone.return_value = ([True])

    # Expect a ValueError when attempting to delete a location that's already been deleted
    with pytest.raises(ValueError, match="Location with ID 999 has already been deleted"):
        delete_location(999)

def test_clear_catalog(mock_cursor, mocker):
    """Test clearing the entire Location catalog (removes all locations)."""

    # Mock the file reading
    mocker.patch.dict('os.environ', {'SQL_CREATE_TABLE_PATH': 'sql/create_location_table.sql'})
    mock_open = mocker.patch('builtins.open', mocker.mock_open(read_data="The body of the create statement"))

    # Call the clear_database function
    clear_catalog()

    # Ensure the file was opened using the environment variable's path
    mock_open.assert_called_once_with('sql/create_location_table.sql', 'r')

    # Verify that the correct SQL script was executed
    mock_cursor.executescript.assert_called_once()


######################################################
#
#    Get location
#
######################################################

def test_get_location_by_id(mock_cursor):
    # Simulate that the location exists (id = 1)
    mock_cursor.fetchone.return_value = (1, "Boston")

    # Call the function and check the result
    result = get_location_by_id(1)

    # Expected result based on the simulated fetchone return value
    expected_result = Location(1, "Boston")

    # Ensure the result matches the expected output
    assert result == expected_result, f"Expected {expected_result}, got {result}"

    # Ensure the SQL query was executed correctly
    expected_query = normalize_whitespace("SELECT id, name, deleted FROM locations WHERE id = ?")
    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])

    # Assert that the SQL query was correct
    assert actual_query == expected_query, "The SQL query did not match the expected structure."

    # Extract the arguments used in the SQL call
    actual_arguments = mock_cursor.execute.call_args[0][1]

    # Assert that the SQL query was executed with the correct arguments
    expected_arguments = (1,)
    assert actual_arguments == expected_arguments, f"The SQL query arguments did not match. Expected {expected_arguments}, got {actual_arguments}."

def test_get_location_by_id_bad_id(mock_cursor):
    # Simulate that no location exists for the given ID
    mock_cursor.fetchone.return_value = None

    # Expect a ValueError when the location is not found
    with pytest.raises(ValueError, match="Location with ID 999 not found"):
        get_location_by_id(999)

def test_get_all_locations(mock_cursor):
    """Test retrieving all locations that are not marked as deleted."""

    # Simulate that there are multiple locations in the database
    mock_cursor.fetchall.return_value = [
        (1, "Boston", False),
        (2, "Istanbul", False),
        (3, "Bergen", False)
    ]

    # Call the get_all_locations function
    locations = get_all_locations()

    # Ensure the results match the expected output
    expected_result = [
        {"id": 1, "Location": "Boston"},
        {"id": 2, "Location": "Istanbul"},
        {"id": 3, "Location": "Bergen"}
    ]

    assert locations == expected_result, f"Expected {expected_result}, but got {locations}"

    # Ensure the SQL query was executed correctly
    expected_query = normalize_whitespace("""
        SELECT id, name
        FROM locations
        WHERE deleted = FALSE
    """)
    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])

    assert actual_query == expected_query, "The SQL query did not match the expected structure."

def test_get_all_locations_empty_catalog(mock_cursor, caplog):
    """Test that retrieving all locations returns an empty list when the catalog is empty and logs a warning."""

    # Simulate that the catalog is empty (no locations found)
    mock_cursor.fetchall.return_value = []

    # Call the get_all_locations function
    result = get_all_locations()

    # Ensure the result is an empty list
    assert result == [], f"Expected empty list, but got {result}"

    # Ensure that a warning was logged
    assert "The locations catalog is empty." in caplog.text, "Expected warning about empty catalog not found in logs."

    # Ensure the SQL query was executed correctly
    expected_query = normalize_whitespace("SELECT id, name FROM locations WHERE deleted = FALSE")
    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])

    # Assert that the SQL query was correct
    assert actual_query == expected_query, "The SQL query did not match the expected structure."

def test_get_random_location(mock_cursor, mocker):
    """Test retrieving a random location from the catalog."""

    # Simulate that there are multiple locations in the database
    mock_cursor.fetchall.return_value = [
        (1, "Boston"),
        (2, "Istanbul"),
        (3, "Bergen")
    ]

    # Mock random number generation to return the 2nd location
    mock_random = mocker.patch("weather_collection.models.location_model.get_random", return_value=2)

    # Call the get_random_location method
    result = get_random_location()

    # Expected result based on the mock random number and fetchall return value
    expected_result = Location(2, "Istanbul")

    # Ensure the result matches the expected output
    assert result == expected_result, f"Expected {expected_result}, got {result}"

    # Ensure that the random number was called with the correct number of locations
    mock_random.assert_called_once_with(3)

    # Ensure the SQL query was executed correctly
    expected_query = normalize_whitespace("SELECT id, name FROM locations WHERE deleted = FALSE")
    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])

    # Assert that the SQL query was correct
    assert actual_query == expected_query, "The SQL query did not match the expected structure."

def test_get_random_location_empty_catalog(mock_cursor, mocker):
    """Test retrieving a random location when the catalog is empty."""

    # Simulate that the catalog is empty
    mock_cursor.fetchall.return_value = []

    # Expect a ValueError to be raised when calling a random location with an empty catalog
    with pytest.raises(ValueError, match="The location catalog is empty"):
        get_random_location()

    # Ensure that the random number was not called since there are no locations. 
    mocker.patch("weather_collection.models.location_model.get_random").assert_not_called()

    # Ensure the SQL query was executed correctly
    expected_query = normalize_whitespace("SELECT id, name FROM locations WHERE deleted = FALSE")
    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])

    # Assert that the SQL query was correct
    assert actual_query == expected_query, "The SQL query did not match the expected structure."