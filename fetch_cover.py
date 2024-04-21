import requests
from dotenv import load_dotenv
import discogs_client
import os
import argparse

# Load environment variables
load_dotenv()

def download_cover_art(artist_name, album_title, target_path):
    # Get user token from environment variables
    user_token = os.getenv('DISCOGS_USER_TOKEN')
    if not user_token:
        print("DISCOGS_USER_TOKEN is not set in .env file.")
        return
    
    d = discogs_client.Client('automatic-cd-ripper-workshed/0.1', user_token=user_token)
    
    try:
        # Search for releases by artist name and album title
        results = d.search(artist=artist_name, release_title=album_title, type='release')
        releases = list(results.page(1))
        
        if releases:
            # Pick the first release matching the query
            release = releases[0]
            print(f"Found release: {release.title} by {release.artists[0].name}")
            
            # Try to get the primary image of the release
            if release.images:
                front_cover_url = release.images[0]['uri']
                response = requests.get(front_cover_url)
                # Delete the file if it already exists
                if os.path.exists(os.path.join(target_path, "cover.jpg")):
                    os.remove(os.path.join(target_path, "cover.jpg"))

                with open(os.path.join(target_path, "cover.jpg"), "wb") as img_file:
                    img_file.write(response.content)
                print("Downloaded front cover art")
            else:
                print("No image available for this release.")
        else:
            print("No releases found for the given artist and album title.")
    except Exception as e:
        print(f"Couldn't find album art: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Download cover art.')
    parser.add_argument('artist_name', type=str, help='The name of the artist.')
    parser.add_argument('album_title', type=str, help='The title of the album.')
    parser.add_argument('target_path', type=str, help='The target path to save the cover art.')
    
    args = parser.parse_args()
    
    download_cover_art(args.artist_name, args.album_title, args.target_path)