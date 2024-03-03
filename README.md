# Plex Playlist Rollover

A script that updates managed playlists in Plex to the next unwatched episode of each show.

## How to use

In Plex, create one or more playlists and add the next individual episodes you want to watch for each show. In the Summary of the playlists, write whatever you want, but add the keyword "[managed]" (including the brackets). This will tell the script to include these playlists in the rollover.

Set up a cron job to run the script at a time of your choosing (once a day should be fine). The script will then update the playlist so that watched episode of each show roll over to the next episode.

> Note: Only completed episodes advance to the next one in the series. Unwatched episodes are left alone.

## How the script works

### 1. Retrieve all managed playlists

The default keyword is "[managed]". Just add that to the summary of the playlist and it will be included in the rollover.

### 2. For each playlist, extract its episodes

If an episode has not been watched, it will get re-added to the playlist as-is. If it has been watched, the code searches for the next chronological episode in the series and adds that to the playlist.

### 3. Save the updated playlist

The code then clears the playlist and re-adds the episode in the original order.

## A note on "special" seasons

Since seasons that have been completed are excluded from the search, the code wil grab the next available unwatched seasons (something like season five and six or, if there's a "specials" season, it will grab it and something like season five). The next unwatched episode from each season is extracted and sorted according to the broadcast date. This way, if a special was broadcast between seasons, it becomes the next one to watch.

## Limitations

This script only works with TV shows. Since it uses broadcast dates to determine the next episode, make sure the metadata of your episodes are set correctly.

This script assumes each show has normal, sequential seasons and is capable of handling one "specials" season (this usually comes up first). If you have any other configuration of seasons (somehow you have two "specials" seasons), where the normal sequential season would come third or later in the list, try increasing the value of the `NUMBER_OF_SEASONS_TO_CHECK` variable so it encompasses all the special seasons and the first availabe regular one.
