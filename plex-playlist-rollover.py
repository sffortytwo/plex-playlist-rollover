import json
import requests
from datetime import datetime


PLEX_SERVER = "http://betelgeuse.lan:32400"
PLEX_SERVER_ID = "22a0c4174216fa20b2f466380ce894832d07e04a"
PLEX_TOKEN = "urt6NZrsfY2jkPUwvj7s"
PLEX_HEADERS = {"X-Plex-Token": PLEX_TOKEN, "Accept": "application/json"}
NUMBER_OF_SEASONS_TO_CHECK = 2
MANAGED_KEYWORD = "[managed]"


class Episode:
    """
    Represents an episode with its title, rating key, and original release date.
    """
    def __init__(self, title, rating_key, originally_available_at):
        """
        Initialize a Playlist object.

        Args:
            title (str): The title of the playlist.
            rating_key (int): The rating key of the playlist.
            originally_available_at (str): The original release date of the playlist.
        """
        self.title = title
        self.rating_key = rating_key
        self.originally_available_at = originally_available_at

    def __repr__(self):
        """
        Returns a string representation of the Episode object.

        The string representation includes the originally_available_at,
        title, and rating_key attributes of the Episode.

        Returns:
            str: A string representation of the Episode object.
        """
        return f"Episode(originally_available_at={self.originally_available_at}, title={self.title}, rating_key={self.rating_key})"


def log(message):
    """
    Logs the given message along with the current timestamp.

    Args:
        message (str): The message to be logged.
    """
    print(f"{datetime.now()}: {message}")


def get_managed_playlists():
    """
    Retrieves the managed playlists from the Plex server.

    Returns:
        list: A list of managed playlists.
    """
    data = requests.get(f"{PLEX_SERVER}/playlists", headers=PLEX_HEADERS).json()
    # Filter down to the playlists that have the summary "managed"
    return [p for p in data["MediaContainer"]["Metadata"] if MANAGED_KEYWORD in p["summary"]]


def get_playlist_contents(playlist_key):
    """
    Retrieves the contents of a playlist from the Plex server.

    Args:
        playlist_key (str): The key of the playlist to retrieve.

    Returns:
        list: A list of metadata for the items in the playlist.
    """
    data = requests.get(f"{PLEX_SERVER}/playlists/{playlist_key}/items", headers=PLEX_HEADERS).json()
    return data["MediaContainer"]["Metadata"]


def episode_has_been_watched(episode):
    """
    Check if an episode has been watched based on the "viewCount" attribute.

    Args:
        episode (dict): The episode object to check.

    Returns:
        bool: True if the episode has been watched, False otherwise.
    """
    return "viewCount" in episode and episode["viewCount"] > 0


def get_upcoming_episodes_for_show(season_keys):
    """
    Retrieves the upcoming episodes for a given show based on the provided season keys.

    Args:
        season_keys (list): A list of season keys.

    Returns:
        list: A sorted list of Episode objects representing the upcoming episodes.
    """
    episodes = []

    for season_id in season_keys:
        # For each season, get the latest unwatched episode
        unwatched_episodes = requests.get(
            f"{PLEX_SERVER}/library/metadata/{season_id}/children?unwatched=1&X-Plex-Container-Start=0&X-Plex-Container-Size=1",
            headers=PLEX_HEADERS).json()
        unwatched_episode = unwatched_episodes["MediaContainer"]["Metadata"][0]
        originally_available_at = unwatched_episodes["MediaContainer"]["Metadata"][0]["originallyAvailableAt"]
        episode = Episode(
            title=unwatched_episode["title"],
            rating_key=unwatched_episode["ratingKey"],
            originally_available_at=originally_available_at
        )
        episodes.append(episode)

    # Sort the episodes by their originally_available_at attribute.
    # In cases where there is a "specials" season, its latest episode will be
    # compared to the next season's next episode. If the special aired before
    # the regular season's next episode, the special will be sorted first.
    return sorted(episodes, key=lambda x: x.originally_available_at)


def find_next_episode(episode):
    """
    Finds the next episode to watch based on the given episode.

    Args:
        episode (dict): The current episode information.

    Returns:
        dict: The next episode to watch.
    """
    # The show's id is grandparentRatingKey
    show_id = episode["grandparentRatingKey"]
    # Limit the scope to the first two unwatched seasons.
    # Season 0 *could* be specials, but it's okay if it's not.
    unwatched_seasons = requests.get(
        f"{PLEX_SERVER}/library/metadata/{show_id}/children?unwatched=1&X-Plex-Container-Start=0&X-Plex-Container-Size={NUMBER_OF_SEASONS_TO_CHECK}",
        headers=PLEX_HEADERS).json()
    # I want to extract each season's ratingKey
    seasonKeys = [season["ratingKey"] for season in unwatched_seasons["MediaContainer"]["Metadata"]]
    upcoming_episodes = get_upcoming_episodes_for_show(seasonKeys)
    # The next episode is the first one in the list
    return upcoming_episodes[0]


def update_playlist(playlist, episodes):
    """
    Update the given playlist by clearing its items and adding new episodes.

    Args:
        playlist (dict): The playlist to be updated.
        episodes (list): The list of episodes to be added to the playlist.

    Returns:
        None
    """
    log(f"Clearing playlist {playlist['title']}")
    requests.delete(f"{PLEX_SERVER}/playlists/{playlist['ratingKey']}/items", headers=PLEX_HEADERS)

    # Now add each episode to the playlist
    for episode in episodes:
        log(f"- Adding {episode}")
        requests.put(
            f"{PLEX_SERVER}/playlists/{playlist['ratingKey']}/items?uri=server://{PLEX_SERVER_ID}/com.plexapp.plugins.library/library/metadata/{episode.rating_key}",
            headers=PLEX_HEADERS)


def main():
    # Get all the managed playlists
    playlists = get_managed_playlists()

    for playlist in playlists:
        log(f"Playlist name: {playlist['title']}")

        # The playlist's ratingKey is its ID
        playlist_key = playlist["ratingKey"]

        # Get the episodes in the playlist
        playlist_contents = get_playlist_contents(playlist_key)

        playlist_episodes = []

        for episode in playlist_contents:
            # If this episode has been watched ...
            if (episode_has_been_watched(episode)):
                # ... add the next episode
                log(f"- Finished: {episode['grandparentTitle']}:{episode['parentTitle']}:{episode['title']} (EP{episode['index']})")
                playlist_episodes.append(find_next_episode(episode))
            else:
                # ... otherwise just re-add the unwatched episode
                playlist_episodes.append(Episode(episode["title"], episode["ratingKey"], episode["originallyAvailableAt"]))

        for episode in playlist_episodes:
            log(f"- {episode}")

        update_playlist(playlist, playlist_episodes)


if __name__ == "__main__":
    main()
