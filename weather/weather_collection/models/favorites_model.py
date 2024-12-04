import logging
from typing import List
from weather.weather_collection.models.location_model import Location, update_play_count
from weather_collection.utils.logger import configure_logger

logger = logging.getLogger(__name__)
configure_logger(logger)


class FavoritesModel:
    """
    A class to manage a list of locations.

    Attributes:
        current_location_number (int): The current location being shown.
        favorites (List[Location]): The list of Locations in the favorites list.

    """

    def __init__(self):
        """
        Initializes the FavoritesModel with an empty list and the current location set to 1.
        """
        self.current_location_number = 1
        self.favorites: List[Location] = []

    ##################################################
    # Location Management Functions
    ##################################################

    def add_location_to_favorites(self, location: Location) -> None:
        """
        Adds a location to the favorites.

        Args:
            location (Location): the location to add to the favorites.

        Raises:
            TypeError: If the location is not a valid Location instance.
            ValueError: If a location with the same 'id' already exists.
        """
        logger.info("Adding new location to favorites")
        if not isinstance(location, Location):
            logger.error("Location is not a valid location")
            raise TypeError("Location is not a valid location")

        location_id = self.validate_location_id(location.id, check_in_favorites=False)
        if location_id in [location_in_favorites.id for location_in_favorites in self.favorites]:
            logger.error("Location with ID %d already exists in Favorites", location.id)
            raise ValueError(f"Location with ID {location.id} already exists in Favorites")

        self.favorites.append(location)

    def remove_location_by_name(self, name: str) -> None:
        """
        Removes a location from the favorites by its name.

        Args:
            name (str): The name of the location to remove.

        Raises:
            ValueError: If favorites is empty or the name is invalid.
        """
        logger.info("Removing location by name: %s", name)
        self.check_if_empty()
        name = self.validate_favorites_name(name)
        location_to_remove = next((loc for loc in self.favorites if loc.title == name), None)

        if not location_to_remove:
            logger.error("Location with name '%s' not found in favorites", name)
            raise ValueError(f"Location with name '{name}' not found in favorites")

        self.favorites.remove(location_to_remove)
        logger.info("Location with name '%s' has been removed", name)


    def remove_location_by_name(self, name: str) -> None:
        """
        Removes a location from the favorites by its name (str).

        Args:
            name (str): The name of the location to remove.

        Raises:
            ValueError: If favorites is empty or the name is invalid.
        """
        logger.info("Removing location %d from favorites", favorites)
        self.check_if_empty()
        favorites = self.validate_favorites_name(favorites)
        favorites_index = favorites - 1
        logger.info("Removing location: %s", self.favorites[favorites_index].title)
        del self.favorites[favorites_index]

    def clear_favorites(self) -> None:
        """
        Clears all locations from the favorites. If favorites is already empty, logs a warning.
        """
        logger.info("Clearing favorites")
        if self.get_favorites_length() == 0:
            logger.warning("Clearing an empty favorites")
        self.favorites.clear()

    ##################################################
    # Favorites Retrieval Functions
    ##################################################

    def get_all_favorites(self) -> List[Location]:
        """
        Returns a list of all locations in the favorites.
        """
        self.check_if_empty()
        logger.info("Getting all locations in the favorites")
        return self.favorites

    def get_location_by_id(self, location_id: int) -> Location:
        """
        Retrieves a location from the favorites by its location ID.

        Args:
            location_id (int): The ID of the location to retrieve.

        Raises:
            ValueError: If favorites is empty or the location is not found.
        """
        self.check_if_empty()
        location_id = self.validate_location_id(location_id)
        logger.info("Getting location with id %d from favorites", location_id)
        return next((location for location in self.favorites if location.id == location_id), None)

    def get_location_by_name(self, name: str) -> Location:
        """
        Retrieves a location from the favorites by its name.

        Args:
            name (str): The name of the location to retrieve.

        Raises:
            ValueError: If favorites is empty or the name is invalid.
        """
        logger.info("Getting location by name: %s", name)
        self.check_if_empty()
        name = self.validate_favorites_name(name)
        location = next((loc for loc in self.favorites if loc.title == name), None)

        if not location:
            logger.error("Location with name '%s' not found in favorites", name)
            raise ValueError(f"Location with name '{name}' not found in favorites")

        return location


    def get_current_location(self) -> Location:
        """
        Returns the current location being played.
        """
        self.check_if_empty()
        return self.get_location_by_name(self.current_location_name)

    def get_favorites_length(self) -> int:
        """
        Returns the number of locations in the favorites.
        """
        return len(self.favorites)

    ##################################################
    # Favorites Movement Functions
    ##################################################

    def go_to_favorites_name(self, name: str) -> None:
        """
        Sets the current name to the specified name.

        Args:
            name (str): The name to set as the current location.
        """
        logger.info("Setting current location name to: %s", name)
        self.check_if_empty()
        name = self.validate_favorites_name(name)
        self.current_location_name = name

    def move_location_to_beginning(self, location_id: int) -> None:
        """
        Moves a location to the beginning of the favorites.

        Args:
            location_id (int): The ID of the location to move to the beginning.
        """
        logger.info("Moving location with ID %d to the beginning of the favorites", location_id)
        self.check_if_empty()
        location_id = self.validate_location_id(location_id)
        location = self.get_location_by_id(location_id)
        self.favorites.remove(location)
        self.favorites.insert(0, location)
        logger.info("Location with ID %d has been moved to the beginning", location_id)

    def move_location_to_end(self, location_id: int) -> None:
        """
        Moves a location to the end of the favorites.

        Args:
            location_id (int): The ID of the location to move to the end.
        """
        logger.info("Moving location with ID %d to the end of the favorites", location_id)
        self.check_if_empty()
        location_id = self.validate_location_id(location_id)
        location = self.get_location_by_id(location_id)
        self.favorites.remove(location)
        self.favorites.append(location)
        logger.info("Location with ID %d has been moved to the end", location_id)


    def swap_locations_in_favorites(self, location1_id: int, location2_id: int) -> None:
        """
        Swaps the positions of two locations in favorites.

        Args:
            location1_id (int): The ID of the first location to swap.
            location2_id (int): The ID of the second location to swap.

        Raises:
            ValueError: If you attempt to swap a location with itself.
        """
        logger.info("Swapping locations with IDs %d and %d", location1_id, location2_id)
        self.check_if_empty()
        location1_id = self.validate_location_id(location1_id)
        location2_id = self.validate_location_id(location2_id)

        if location1_id == location2_id:
            logger.error("Cannot swap a location with itself, both location IDs are the same: %d", location1_id)
            raise ValueError(f"Cannot swap a location with itself, both location IDs are the same: {location1_id}")

        song1 = self.get_location_by_id(location1_id)
        song2 = self.get_location_by_id(location2_id)
        index1 = self.favorites.index(song1)
        index2 = self.favorites.index(song2)
        self.favorites[index1], self.favorites[index2] = self.favorites[index2], self.favorites[index1]
        logger.info("Swapped locations with IDs %d and %d", location1_id, location2_id)

    ##################################################
    # Favorites Playback Functions
    ##################################################

    def show_current_location(self) -> None:
        """
        Logs and shows the current location.
        """
        self.check_if_empty()
        logger.info("Current location: %s", self.current_location_name)


    

    ##################################################
    # Utility Functions
    ##################################################

    def validate_location_id(self, location_id: int, check_in_favorites: bool = True) -> int:
        """
        Validates the given location ID, ensuring it is a non-negative integer.

        Args:
            location_id (int): The location ID to validate.
            check_in_favorites (bool, optional): If True, checks if the location ID exists in the favorites.
                                                If False, skips the check. Defaults to True.

        Raises:
            ValueError: If the location ID is not a valid non-negative integer.
        """
        try:
            location_id = int(location_id)
            if location_id < 0:
                logger.error("Invalid location id %d", location_id)
                raise ValueError(f"Invalid location id: {location_id}")
        except ValueError:
            logger.error("Invalid location id %s", location_id)
            raise ValueError(f"Invalid location id: {location_id}")

        if check_in_favorites and location_id not in [loc.id for loc in self.favorites]:
            logger.error("Location with id %d not found in favorites", location_id)
            raise ValueError(f"Location with id {location_id} not found in favorites")

        return location_id


    def validate_favorites_name(self, name: str) -> str:
        """
        Validates the given name, ensuring it is a non-empty string.

        Args:
            name (str): The name to validate.

        Raises:
            ValueError: If the name is not a valid string or is empty.

        Returns:
            str: The validated name.
        """
        if not isinstance(name, str) or not name.strip():
            logger.error("Invalid name: %s", name)
            raise ValueError(f"Invalid name: {name}")

        return name
    
    def check_if_empty(self) -> None:
        """
        Checks if the favorites is empty, logs an error, and raises a ValueError if it is.

        Raises:
            ValueError: If the favorites is empty.
        """
        if not self.favorites:
            logger.error("favorites is empty")
            raise ValueError("favorites is empty")