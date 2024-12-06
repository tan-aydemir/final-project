from dataclasses import dataclass
import logging
import os
import sqlite3

from weather_collection.utils.logger import configure_logger
from weather_collection.utils.random_utils import get_random
from weather_collection.utils.sql_utils import get_db_connection


logger = logging.getLogger(__name__)
configure_logger(logger)


@dataclass
class Location:
    id: int
    name: str
    
    def __post_init__(self):
        if not isinstance(self.name, str):
            raise ValueError(f"Name must be a string: {self.wind}")

def create_location(name: str) -> None:
    """
    Creates a new location in the locations table.
    Args:
        name (str): Create a new location by name

    Raises:
        ValueError: If location is invalid.
        sqlite3.IntegrityError: If a location with the same compound key (location) already exists.
        sqlite3.Error: For any other database errors.
    """
    # Validate the required fields
    if not name or not isinstance(name, str):
        raise ValueError("Invalid name provided. Name must be a non-empty string.")
    
    try:
        # Use the context manager to handle the database connection
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO locations (name)
                VALUES (?)
            """, (name))
            conn.commit()

            logger.info("Location created successfully: %s - %s (%d)", name)

    except sqlite3.IntegrityError as e:
        logger.error(f"Location [{name}] already exists")
        raise ValueError(f"Location [{name}] already exists") from e
    except sqlite3.Error as e:
        logger.error("Database error while creating Location: %s", str(e))
        raise sqlite3.Error(f"Database error: {str(e)}")

def clear_catalog() -> None:
    """
    Recreates the locations table, effectively deleting all locations.

    Raises:
        sqlite3.Error: If any database error occurs.
    """
    try:
        with open(os.getenv("SQL_CREATE_TABLE_PATH", "/app/sql/create_location_table.sql"), "r") as fh:
            create_table_script = fh.read()
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.executescript(create_table_script)
            conn.commit()

            logger.info("Location catalog cleared successfully.")

    except sqlite3.Error as e:
        logger.error("Database error while clearing catalog: %s", str(e))
        raise e

def delete_location(location_id: int) -> None:
    """
    Soft deletes a location from the catalog by marking it as deleted.

    Args:
        location_id (int): The name of the Location to delete.

    Raises:
        ValueError: If the location id in the table does not exist or is already marked as deleted.
        sqlite3.Error: If any database error occurs.
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Check if the location exists and if it's already deleted
            cursor.execute("SELECT deleted FROM locations WHERE id = ?", (location_id,))
            try:
                deleted = cursor.fetchone()[0]
                if deleted:
                    logger.info("Location with id: %s has already been deleted", location_id)
                    raise ValueError(f"Location with id: {location_id} has already been deleted")
            except TypeError:
                logger.info("Location with id: %s not found", location_id)
                raise ValueError(f"Location with id: {location_id} not found")

            # Perform the soft delete by setting 'deleted' to TRUE
            cursor.execute("UPDATE locations SET deleted = TRUE WHERE id = ?", (location_id,))
            conn.commit()

            logger.info("Location with id: %s marked as deleted.", location_id)

    except sqlite3.Error as e:
        logger.error("Database error while deleting location: %s", str(e))
        raise e

def get_location_by_id(location_id: int) -> Location:
    """
    Retrieves a location from the catalog by its location id.

    Args:
        location_id (int): The id for the location to receive 

    Returns:
        Location: The Location object corresponding to the location_id variable

    Raises:
        ValueError: If the location isnt found or is marked as deleted.
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            logger.info("Attempting to retrieve location with ID %s", location_id)
            cursor.execute("""
                SELECT id, name, deleted
                FROM locations
                WHERE id = ?
            """, (location_id,))
            row = cursor.fetchone()

            if row:
                if row[2]:  # deleted flag
                    logger.info("Location with ID %s has been deleted", location_id)
                    raise ValueError(f"Location with ID {location_id} has been deleted")
                logger.info("Location with ID %s found", location_id)
                return Location(id=row[0], name=row[1])
            else:
                logger.info("Location with ID %s not found", location_id)
                raise ValueError(f"Location with ID {location_id} not found")

    except sqlite3.Error as e:
        logger.error("Database error while retrieving location by ID %s: %s", location_id, str(e))
        raise e

def get_all_locations() -> list[dict]:
    """
    Retrieves all locations that are not marked as deleted from the catalog.

    Returns:
        list[dict]: A list of dictionaries representing all non-deleted locations.

    Logs:
        Warning: If the catalog is empty.
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            logger.info("Attempting to retrieve all non-deleted locations from the catalog")

            # Determine the sort order based on the 'sort_by_play_count' flag
            query = """
                SELECT id, name
                FROM locations
                WHERE deleted = FALSE
            """
            
            cursor.execute(query)
            rows = cursor.fetchall()

            if not rows:
                logger.warning("The location catalog is empty.")
                return []

            locations = [
                {
                    "id": row[0],
                    "name": row[1],
                }
                for row in rows
            ]
            logger.info("Retrieved %d locations from the catalog", len(locations))
            return locations

    except sqlite3.Error as e:
        logger.error("Database error while retrieving all locations: %s", str(e))
        raise e

def get_random_location() -> Location:
    """
    Retrieves a random location from the catalog - A Feature For Feeling Lucky

    Returns:
        Location: A randomly selected Location object.

    Raises:
        ValueError: If the catalog is empty.
    """
    try:
        all_locations = get_all_locations()

        if not all_locations:
            logger.info("Cannot retrieve random Location because the location catalog is empty.")
            raise ValueError("The location catalog is empty.")

        # Get a random index using the random.org API
        random_index = get_random(len(all_locations))
        logger.info("Random index selected: %d (total locations: %d)", random_index, len(all_locations))

        # Return the location at the random index, adjust for 0-based indexing
        location_data = all_locations[random_index - 1]
        return Location(
            id=location_data["id"],
            name=location_data["name"],
        )

    except Exception as e:
        logger.error("Error while retrieving random location: %s", str(e))
        raise e
