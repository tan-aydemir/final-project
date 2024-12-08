import pytest
from unittest.mock import MagicMock
from weather.weather_collection.models.favorites_model import FavoritesModel
from weather.weather_collection.models.location_model import Location


@pytest.fixture()
def favorites_model():
    """Fixture to provide a new instance of FavoritesModel for each test."""
    return FavoritesModel()

"""Fixtures providing sample Locations for the tests."""
@pytest.fixture
def sample_Location1():
    return Location(1, 'Boston')

@pytest.fixture
def sample_Location2():
    return Location(2, 'Seattle')

@pytest.fixture
def sample_favorites(sample_Location1, sample_Location2):
    return [sample_Location1, sample_Location2]


##################################################
# Add Location Management Test Cases
##################################################

def test_add_location_to_favorites(favorites_model, sample_Location1):
    """Test adding a Location to the favorites."""
    favorites_model.add_location_to_favorites(sample_Location1)
    assert len(favorites_model.favorites) == 1
    assert favorites_model.favorites[0].name == 'Boston'


def test_add_duplicate_location_to_favorites(favorites_model, sample_Location1):
    """Test error when adding a duplicate Location to the favorites by ID."""
    favorites_model.add_location_to_favorites(sample_Location1)
    # The model raises: "Location with ID 1 already exists in Favorites"
    with pytest.raises(ValueError, match="Location with ID 1 already exists in Favorites"):
        favorites_model.add_location_to_favorites(sample_Location1)


##################################################
# Remove Location Management Test Cases
##################################################

def test_remove_location_from_favorites_by_location_id(favorites_model, sample_favorites):
    """Test removing a Location from the favorites by Location_id."""
    favorites_model.favorites.extend(sample_favorites)
    assert len(favorites_model.favorites) == 2

    # Assuming remove_Location_by_Location_id exists in the model.
    favorites_model.remove_Location_by_Location_id(1)
    assert len(favorites_model.favorites) == 1, f"Expected 1 Location, but got {len(favorites_model.favorites)}"
    assert favorites_model.favorites[0].id == 2, "Expected Location with id 2 to remain"


def test_remove_location_by_name(favorites_model, sample_favorites):
    """Test removing a Location from the favorites by location name."""
    favorites_model.favorites.extend(sample_favorites)
    assert len(favorites_model.favorites) == 2

    # Remove 'Boston' by name instead of using an integer.
    favorites_model.remove_location_by_name("Boston")
    assert len(favorites_model.favorites) == 1, f"Expected 1 Location, but got {len(favorites_model.favorites)}"
    assert favorites_model.favorites[0].id == 2, "Expected Location with id 2 to remain"


def test_clear_favorites(favorites_model, sample_Location1):
    """Test clearing the entire favorites."""
    favorites_model.add_location_to_favorites(sample_Location1)

    favorites_model.clear_favorites()
    assert len(favorites_model.favorites) == 0, "favorites should be empty after clearing"


def test_clear_favorites_empty_favorites(favorites_model, caplog):
    """Test clearing the entire favorites when it's empty."""
    favorites_model.clear_favorites()
    assert len(favorites_model.favorites) == 0, "favorites should be empty after clearing"
    assert "Clearing an empty favorites" in caplog.text, "Expected warning message when clearing an empty favorites"


##################################################
# Location Retrieval Test Cases
##################################################

def test_get_all_favorites(favorites_model, sample_favorites):
    """Test successfully retrieving all locations in favorites."""
    favorites_model.favorites.extend(sample_favorites)
    all_favs = favorites_model.get_all_favorites()
    assert len(all_favs) == 2
    assert all_favs[0].name == 'Boston'
    assert all_favs[1].name == 'Seattle'


def test_get_location_by_id_in_favorites(favorites_model, sample_favorites):
    """Test successfully retrieving location in favorites by id."""
    favorites_model.favorites.extend(sample_favorites)
    loc = favorites_model.get_location_by_id_in_favorites(2)
    assert loc.name == 'Seattle'


def test_get_lcoation_by_name_in_favorites(favorites_model, sample_Location1):
    """Test successfully retrieving a Location from the favorites by Location name."""
    favorites_model.add_location_to_favorites(sample_Location1)
    loc = favorites_model.get_location_by_name_in_favorites("Boston")
    assert loc.id == 1


def test_get_current_Location(favorites_model, sample_favorites):
    """Test successfully retrieving the current Location from the favorites."""
    favorites_model.favorites.extend(sample_favorites)
    current = favorites_model.get_current_location()
    # By default: current_location_number=1 and if no current_location_name set,
    # current location is the first in favorites.
    assert current.id == 1
    assert current.name == 'Boston'


def test_get_favorites_length(favorites_model, sample_favorites):
    """Test getting the length of the favorites."""
    favorites_model.favorites.extend(sample_favorites)
    assert favorites_model.get_favorites_length() == 2


##################################################
# Favorites Movement functions
##################################################

def test_go_to_favorites_name(favorites_model, sample_favorites):
    """Test going to the favorites name"""
    favorites_model.favorites.extend(sample_favorites)
    favorites_model.go_to_favorites_name("Seattle")
    current = favorites_model.get_current_location()
    assert current.name == "Seattle"


def test_move_location_to_beginnning(favorites_model, sample_favorites):
    """Tests moving a location to the beginning of favorites"""
    favorites_model.favorites.extend(sample_favorites)
    favorites_model.move_location_to_beginning(2)
    assert favorites_model.favorites[0].id == 2
    assert favorites_model.favorites[1].id == 1


def test_move_location_to_end(favorites_model, sample_favorites):
    """Test moving location to end of favorites"""
    favorites_model.favorites.extend(sample_favorites)
    favorites_model.move_location_to_end(1)
    assert favorites_model.favorites[-1].id == 1


def test_swap_locations_in_favorites(favorites_model, sample_favorites):
    """test swapping two locations in favorites"""
    favorites_model.favorites.extend(sample_favorites)
    favorites_model.swap_locations_in_favorites(1, 2)
    assert favorites_model.favorites[0].id == 2
    assert favorites_model.favorites[1].id == 1


##################################################
# Utility Function Test Cases
##################################################

def test_check_if_empty_non_empty_favorites(favorites_model, sample_Location1):
    """Test check_if_empty does not raise error if favorites is not empty."""
    favorites_model.add_location_to_favorites(sample_Location1)
    try:
        favorites_model.check_if_empty()
    except ValueError:
        pytest.fail("check_if_empty raised ValueError unexpectedly on non-empty favorites")

def test_check_if_empty_empty_favorites(favorites_model):
    """Test check_if_empty raises error when favorites is empty."""
    favorites_model.clear_favorites()
    with pytest.raises(ValueError, match="favorites is empty"):
        favorites_model.check_if_empty()

def test_validate_Location_id(favorites_model, sample_Location1):
    """Test validate_Location_id does not raise error for valid Location ID."""
    favorites_model.add_location_to_favorites(sample_Location1)
    try:
        favorites_model.validate_location_id(1)
    except ValueError:
        pytest.fail("validate_location_id raised ValueError unexpectedly for valid Location ID")

def test_validate_Location_id_no_check_in_favorites(favorites_model):
    """Test validate_Location_id does not raise error for valid Location ID when the id isn't in the favorites."""
    try:
        favorites_model.validate_location_id(1, check_in_favorites=False)
    except ValueError:
        pytest.fail("validate_location_id raised ValueError unexpectedly for valid Location ID")

def test_validate_Location_id_invalid_id(favorites_model):
    """Test validate_Location_id raises error for invalid Location ID."""
    # Code raises "Invalid location id: -1" for negative or invalid integer
    with pytest.raises(ValueError, match="Invalid location id: -1"):
        favorites_model.validate_location_id(-1)

    with pytest.raises(ValueError, match="Invalid location id: invalid"):
        favorites_model.validate_location_id("invalid")

def test_validate_location_name(favorites_model, sample_Location1):
    """Test validate_location_name does not raise error for valid location."""
    favorites_model.add_location_to_favorites(sample_Location1)
    try:
        favorites_model.validate_location_name("Boston")
    except ValueError:
        pytest.fail("validate_location_name raised ValueError unexpectedly for valid location")

def test_validiate_location_name_invalid(favorites_model, sample_Location1):
    """Test validate_location_name raises error for invalid location."""
    favorites_model.add_location_to_favorites(sample_Location1)

    # Passing a non-string should raise "Invalid name: 0"
    with pytest.raises(ValueError, match="Invalid name: 0"):
        favorites_model.validate_location_name(0)

    # Passing another non-string integer should raise "Invalid name: 2"
    with pytest.raises(ValueError, match="Invalid name: 2"):
        favorites_model.validate_location_name(2)

    # Passing an empty string should raise "Invalid name: "
    with pytest.raises(ValueError, match="Invalid name: "):
        favorites_model.validate_location_name("")


##################################################
# Playback Test Cases
##################################################

@pytest.fixture
def mock_update_play_count(mocker):
    return mocker.patch("weather.weather_collection.models.favorites_model.mock_update_play_count", autospec=True)


def test_play_current_Location(favorites_model, sample_favorites, mock_update_play_count):
    """Test playing the current Location."""
    favorites_model.favorites.extend(sample_favorites)

    favorites_model.play_current_Location()

    # Assert that current_location_number is now 2
    assert favorites_model.current_location_number == 2, f"Expected location to be 2, but got {favorites_model.current_location_number}"

    # update_play_count called with first Location's id (1)
    mock_update_play_count.assert_called_once_with(1)

    # Play again, should wrap around
    favorites_model.play_current_Location()

    # Should now be back to 1
    assert favorites_model.current_location_number == 1, f"Expected location to be 1, but got {favorites_model.current_location_number}"

    # update_play_count should have also been called with (2)
    mock_update_play_count.assert_called_with(2)


def test_go_to_location_number(favorites_model, sample_favorites):
    """Test moving the iterator to a specific location in the favorites."""
    favorites_model.favorites.extend(sample_favorites)

    favorites_model.go_to_location_number(2)
    assert favorites_model.current_location_number == 2, "Expected to be at location 2 after moving"

    # Going beyond the number of favorites should wrap around
    favorites_model.go_to_location_number(3)
    assert favorites_model.current_location_number == 1, "Expected to loop back to the beginning of the favorites"
