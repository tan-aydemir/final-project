from contextlib import contextmanager
import re
from unittest.mock import patch, MagicMock

import sqlite3
import pytest
from weather_collection.models.location_model import (
    Location,
    create_location,
    clear_catalog,
    delete_location,
    get_location_by_id,
    get_all_locations,
    get_random_location
)

# Helper function to normalize whitespace in SQL queries
def normalize_whitespace(sql_query: str) -> str:
    return re.sub(r'\s+', ' ', sql_query).strip()

# Mock database connection fixture
@pytest.fixture
def mock_cursor(mocker):
    mock_conn = mocker.Mock()
    mock_cursor = mocker.Mock()

    # Mock the connection's cursor
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchone.return_value = None
    mock_cursor.fetchall.return_value = []
    mock_conn.commit.return_value = None

    @contextmanager
    def mock_get_db_connection():
        yield mock_conn

    mocker.patch("weather_collection.models.location_model.get_db_connection", mock_get_db_connection)

    return mock_cursor

##################################################
# Tests for Add/Delete logic
##################################################

def test_create_location(mock_cursor):
    """Test creating a new location in the catalog."""
    create_location(name="Boston")
    
    expected_query = normalize_whitespace("""
        INSERT INTO locations (name)
        VALUES (?)
    """)
    
    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])
    assert actual_query == expected_query, "SQL structure mismatch in create_location"
    actual_arguments = mock_cursor.execute.call_args[0][1]
    assert actual_arguments == ("Boston",), f"Arguments did not match. Expected ('Boston',), got {actual_arguments}"


def test_create_location_duplicate(mock_cursor):
    """Test creating a location with a duplicate location."""
    mock_cursor.execute.side_effect = sqlite3.IntegrityError("UNIQUE constraint failed: locations.name")

    with pytest.raises(ValueError, match="Location with name Boston already exists."):
        create_location(name="Boston")


def test_delete_location(mock_cursor):
    """Test soft deleting a location from the catalog by location ID."""
    mock_cursor.fetchone.return_value = [False]  # Simulate location exists and not deleted

    delete_location(1)

    expected_select_sql = normalize_whitespace("SELECT deleted FROM locations WHERE id = ?")
    expected_update_sql = normalize_whitespace("UPDATE locations SET deleted = TRUE WHERE id = ?")
    
    actual_select_sql = normalize_whitespace(mock_cursor.execute.call_args_list[0][0][0])
    actual_update_sql = normalize_whitespace(mock_cursor.execute.call_args_list[1][0][0])
    
    assert actual_select_sql == expected_select_sql, "SELECT query mismatch"
    assert actual_update_sql == expected_update_sql, "UPDATE query mismatch"
    
    assert mock_cursor.execute.call_args_list[0][0][1] == (1,)
    assert mock_cursor.execute.call_args_list[1][0][1] == (1,)

def test_clear_catalog(mock_cursor, mocker):
    """Test clearing the entire Location catalog."""
    mocker.patch.dict('os.environ', {'SQL_CREATE_TABLE_PATH': 'sql/create_location_table.sql'})
    mock_open = mocker.patch('builtins.open', mocker.mock_open(read_data="The body of the create statement"))
    
    clear_catalog()

    mock_open.assert_called_once_with('sql/create_location_table.sql', 'r')
    mock_cursor.executescript.assert_called_once()

##################################################
# Tests for Location Retrieval
##################################################

def test_get_location_by_id(mock_cursor):
    """Test fetching a location by its ID."""
    # Mock the database's fetchone() response
    mock_cursor.fetchone.return_value = (1, "Boston")  # A tuple matching the table schema

    # Call the function under test
    result = get_location_by_id(1)

    # Define the expected result
    expected_result = Location(1, "Boston")

    # Assert the result matches the expected value
    assert result == expected_result, f"Expected: {expected_result}, got: {result}"



def test_get_location_by_id_bad_id(mock_cursor):
    mock_cursor.fetchone.return_value = None
    
    with pytest.raises(ValueError, match="Location with ID 999 not found"):
        get_location_by_id(999)


def test_get_all_locations(mock_cursor):
    mock_cursor.fetchall.return_value = [
        (1, "Boston", False),
        (2, "Istanbul", False),
        (3, "Bergen", False)
    ]
    
    result = get_all_locations()
    
    expected_result = [
        {"id": 1, "name": "Boston"},
        {"id": 2, "name": "Istanbul"},
        {"id": 3, "name": "Bergen"}
    ]
    
    assert result == expected_result



def test_get_random_location(mock_cursor, mocker):
    mock_cursor.fetchall.return_value = [
        (1, "Boston"),
        (2, "Istanbul"),
        (3, "Bergen")
    ]
    
    # Mock get_random to return 2 (matching Istanbul)
    mock_random = mocker.patch("weather_collection.models.location_model.get_random", return_value=2)
    
    result = get_random_location()
    
    expected_result = Location(2, "Istanbul")
    
    assert result == expected_result
    mock_random.assert_called_once_with(3)  # Ensures get_random was called with the length of locations



def test_get_random_location_empty_catalog(mock_cursor, mocker):
    mock_cursor.fetchall.return_value = []

    with pytest.raises(ValueError, match="The location catalog is empty"):
        get_random_location()
    
    mocker.patch("weather_collection.models.location_model.get_random").assert_not_called()