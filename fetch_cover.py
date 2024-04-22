import requests
from dotenv import load_dotenv
import discogs_client
import os
import argparse
import sys

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
                headers = {'User-Agent': 'automatic-cd-ripper-workshed/0.1'}
                response = requests.get(url=front_cover_url, headers=headers)                
                #response = requests.get(front_cover_url)
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

def reconstruct_arguments(argv):
    """
    Reconstructs arguments from sys.argv by merging arguments that were split due to missing quotes.
    This function assumes that '-a' precedes the artist name, '-b' precedes the album title, 
    and '-t' precedes the target path. The album title may be split across multiple arguments.
    """
    # Initialize variables
    artist = None
    album = []
    target_path = None
    arg_iter = iter(argv[1:])  # Create an iterator, skip the script name
    
    while True:
        try:
            arg = next(arg_iter)
            if arg == '-a':
                artist = next(arg_iter)
            elif arg == '-b':
                # Start collecting album title parts until another flag is encountered
                while True:
                    next_arg = next(arg_iter)
                    if next_arg.startswith('-'):
                        # If it's a flag, push it back for the next iteration and break
                        argv.insert(1, next_arg)
                        break
                    album.append(next_arg)
            elif arg == '-t':
                target_path = next(arg_iter)
        except StopIteration:
            break  # Exit loop if there are no more arguments
    
    return artist, ' '.join(album), target_path

def reconstruct_arguments2(argv):
    """
    Reconstruct arguments from sys.argv to handle cases where the artist name, album title,
    and target path might be split due to missing quotes. Each segment continues until the next flag.
    """
    artist, album, target_path = [], [], None
    current_segment = None  # Points to the current segment being collected

    for arg in argv[1:]:  # Skip the script name
        if arg in ['-a', '-b', '-t']:
            if arg == '-a':
                current_segment = artist
            elif arg == '-b':
                current_segment = album
            elif arg == '-t':
                current_segment = None
                continue  # Skip the flag itself for target path processing
        elif current_segment is not None:
            current_segment.append(arg)
        else:  # This will execute after '-t' flag, capturing target path
            target_path = arg
            break  # Assuming the target path is the last item

    # Join segments that were split into lists
    artist_name = ' '.join(artist) if artist else None
    album_title = ' '.join(album) if album else None
    return artist_name, album_title, target_path

def main():
    artist, album, target_path = reconstruct_arguments2(sys.argv)
    print(f"Artist: {artist}, Album: {album}, Target Path: {target_path}")
    download_cover_art(artist, album, target_path)

if __name__ == "__main__":
    main()
    #print("Raw command-line arguments:", sys.argv)
    #parser = argparse.ArgumentParser(description='Download cover art.')
    #parser.add_argument('-a', '--artist', 'artist_name', type=str, help='The name of the artist.')
    #parser.add_argument('-b', '--album', 'album_title', type=str, help='The title of the album.')
    #parser.add_argument('-t', '--target', 'target_path', type=str, help='The target path to save the cover art.')
    
    #args = parser.parse_args()
    
    #download_cover_art(args.artist_name, args.album_title, args.target_path)
