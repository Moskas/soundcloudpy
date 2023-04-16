import time
from bs4 import BeautifulSoup
from selenium import webdriver
import argparse
import subprocess
import os
import json

CACHE_DIR = os.path.join(
    os.getenv("XDG_CONFIG_HOME", os.path.expanduser("~/.config")), "soundcloudpy"
)


def cache_data(data, filename):
    os.makedirs(CACHE_DIR, exist_ok=True)
    cache_file = os.path.join(CACHE_DIR, filename)
    with open(cache_file, "w") as f:
        json.dump(data, f)


def get_cached_data(filename):
    cache_file = os.path.join(CACHE_DIR, filename)
    if os.path.exists(cache_file):
        with open(cache_file, "r") as f:
            return json.load(f)
    else:
        return None


# Create an argument parser to handle the mode, username, and player flags
parser = argparse.ArgumentParser()
parser.add_argument(
    "-m",
    "--mode",
    choices=["likes", "tracks"],
    default="likes",
    help="Scraping mode: likes (default) or tracks",
)
parser.add_argument(
    "-u", "--username", required=True, help="SoundCloud username to scrape"
)
parser.add_argument(
    "-p", "--play", action="store_true", help="Play the scraped songs using mpv"
)
args = parser.parse_args()

# Set the SoundCloud username for the user whose tracks you want to scrape
username = args.username

# Set the mode to either 'likes' or 'tracks' to scrape the user's likes or their posted tracks, respectively
mode = args.mode

songs = []

# Retrieve the cached songs
cached_songs = get_cached_data("scraped_songs.json")
if cached_songs:
    # Use the cached songs instead of scraping again
    songs = cached_songs
else:
    # Set the number of times to scroll down the page to load all the elements (increase this number for longer pages)
    scroll_count = 10

    # Launch a new instance of the Chrome browser with Selenium
    driver = webdriver.Chrome()

    # Load the SoundCloud URL for the user's likes or tracks page in the browser
    if mode == "likes":
        url = f"https://soundcloud.com/{username}/likes"
    else:
        url = f"https://soundcloud.com/{username}"
        driver.get(url)

        # Scroll down the page to load all the elements dynamically
        for i in range(scroll_count):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)

            # Parse the HTML response using BeautifulSoup and lxml
            soup = BeautifulSoup(driver.page_source, "lxml")

            # Find all the song elements on the page, depending on the selected mode
            if mode == "likes":
                song_elems = soup.find_all("li", {"class": "soundList__item"})
            else:
                song_elems = soup.find_all("li", {"class": "soundList__item"})
        # Close the browser instance
        driver.quit()

    # Iterate over each song element and extract the artist, title, and URL for the track
    for song_elem in song_elems:
        if mode == "likes":
            title_elem = song_elem.find("a", {"class": "soundTitle__title"})
            artist_elem = song_elem.find("a", {"class": "soundTitle__username"})
        else:
            title_elem = song_elem.find("a", {"class": "soundItem__trackTitle"})
            artist_elem = song_elem.find("a", {"class": "soundItem__username"})
        title = title_elem.text.strip()
        artist = artist_elem.text.strip()
        url = f'https://soundcloud.com{title_elem["href"]}'
        song = {"artist": artist, "title": title, "url": url}
        songs.append(song)

    # Cache the scraped songs
    cache_data(songs, "scraped_songs.json")


# Print the list of scraped songs
# for song in songs:
#    print(f'Artist: {song["artist"]}')
#    print(f'Title: {song["title"]}')
#    print(f'URL: {song["url"]}')
#    print()

# Play the scraped songs using mpv, if the -p or --player flag is set
if args.player:
    for song in songs:
        print("Now playing: " + song["artist"] + " - " + song["title"])
        subprocess.run(["mpv", song["url"]])
