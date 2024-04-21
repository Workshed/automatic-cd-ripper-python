import os
import time
import subprocess
import shutil
import signal
import sys
import requests
from dotenv import load_dotenv
import discogs_client

# Load environment variables
load_dotenv()

# Setting up a simple signal handler to handle graceful shutdown requests
def signal_handler(sig, frame):
    print('Exiting gracefully')
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def wait_for_cd(drive_path='/dev/cdrom'):
    """Wait for a CD to be inserted into the drive."""
    while True:
        if os.path.exists(drive_path):
            try:
                with open(drive_path, 'rb') as f:
                    print("CD detected, proceeding to rip.")
                    return True
            except IOError:
                pass
        else:
            print("Drive not found, check the drive path.")
        time.sleep(30)  # Check every 30 seconds

def rip_cd(output_directory):
    print("Ripping the CD with metadata to", output_directory)
    subprocess.run([
        'ripit', '-c', '2', 
        '--outputdir', output_directory, 
        '--coverpath', 'cover.jpg',
        '--coverart', '1',
        '--precmd', '\'"python fetch_cover.py $artist $album ."\''
        '--nointeraction'
    ])

def mount_network_drive(network_path, mount_point):
    if not os.path.ismount(mount_point):
        print(f"Mounting the network drive: {network_path}")
        subprocess.run(['sudo', 'mount', '-t', 'cifs', network_path, mount_point, '-o', 'username=guest,password=r3]wZ1-2'])

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
                with open(os.path.join(target_path, "cover.jpg"), "wb") as img_file:
                    img_file.write(response.content)
                print("Downloaded front cover art")
            else:
                print("No image available for this release.")
        else:
            print("No releases found for the given artist and album title.")
    except Exception as e:
        print(f"Couldn't find album art: {e}")

def copy_to_network(output_directory, mount_point):
    """Copy the ripped album directories to the network drive while maintaining the artist/album structure."""
    # Ensure we only look at directories directly under the output directory
    for artist in os.listdir(output_directory):
        artist_path = os.path.join(output_directory, artist)
        if os.path.isdir(artist_path):  # Ensure it's a directory
            for album in os.listdir(artist_path):
                album_path = os.path.join(artist_path, album)
                # download_cover_art(artist, album, album_path)
                if os.path.isdir(album_path):  # Ensure it's a directory
                    # Construct the target path on the network drive
                    network_artist_path = os.path.join(mount_point, artist)
                    network_album_path = os.path.join(network_artist_path, album)
                    os.makedirs(network_album_path, exist_ok=True)
                    # Copy each file within the album directory
                    for track in os.listdir(album_path):
                        source_file = os.path.join(album_path, track)
                        target_file = os.path.join(network_album_path, track)
                        if os.path.isfile(source_file):  # Ensure it's a file
                            subprocess.run(['cp', source_file, target_file], check=True)
                            print(f"Copying {track} to {target_file}")
                    # Optionally delete the local album directory after copying
                    shutil.rmtree(album_path)
                    print(f"Deleted local directory {album_path}")

def eject():
    subprocess.call(["eject"])

def main():
    output_directory = '/home/workshed/ripped'
    network_path = '//Workhorse/MainShare/Media/Music'
    mount_point = '/mnt/workhorse_music'
    while True:  # Main loop to continuously check for CDs and process them
        if wait_for_cd():
            rip_cd(output_directory)
            mount_network_drive(network_path, mount_point)
            copy_to_network(output_directory, mount_point)
            eject()

if __name__ == "__main__":
    main()
