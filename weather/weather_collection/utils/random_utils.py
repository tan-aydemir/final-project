import logging
import requests

from weather_collection.utils.logger import configure_logger

logger = logging.getLogger(__name__)
configure_logger(logger)


def get_random(num_locations: int) -> int:
    """
    Fetches a random int between 1 and the number of locations in the favorites from random.org.

    Returns:
        int: The random number fetched from random.org.

    Raises:
        RuntimeError: If the request to random.org fails or returns an invalid response.
        ValueError: If the response from random.org is not a valid float.
    """
    url = f"https://www.random.org/integers/?num=1&min=1&max={num_locations}&col=1&base=10&format=plain&rnd=new"

    try:
        # Log the request to random.org
        logger.info("Fetching random number from %s", url)

        headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36'}

        response = requests.get(url, timeout=5, headers=headers)

        # Check if the request was successful
        response.raise_for_status()

        random_number_str = response.text.strip()

        try:
            random_number = int(random_number_str)
        except ValueError:
            raise ValueError("Invalid response from random.org: %s" % random_number_str)

        logger.info("Received random number: %.3f", random_number)
        return random_number

    except requests.exceptions.Timeout:
        logger.error("Request to random.org timed out.")
        raise RuntimeError("Request to random.org timed out.")

    except requests.exceptions.RequestException as e:
        logger.error("Request to random.org failed: %s", e)
        raise RuntimeError("Request to random.org failed: %s" % e)
