import os
import time
import subprocess
import shutil
import signal
import sys
import requests
from dotenv import load_dotenv
import discogs_client
import shlex

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
    subprocess.run(
        f'ripit -c 2 --verbose 3 --outputdir {output_directory} --coverart 1 --coverpath {os.path.join(output_directory, "cover.jpg")} --precmd \'"python /home/workshed/ripper/fetch_cover.py -a $artist -b $album -t {output_directory}"\' --nointeraction',
        shell=True
    )

def fancy_rip_cd(output_directory):
    artist_var = '$artist'  # Shell variables should be escaped manually if needed
    album_var = '$album'
    script_path = '/home/workshed/ripper/fetch_cover.py'
    cover_path = os.path.join(output_directory, "cover.jpg")

    # Prepare the command string with proper escaping
    precmd_command = f'python {shlex.quote(script_path)} {artist_var} {album_var} {shlex.quote(output_directory)}'
    precmd_escaped = f"\\'{precmd_command}\\'"  # Escape single quotes for shell

    # Full command to run
    command = (
        f'ripit -c 2 --verbose 3 --outputdir {shlex.quote(output_directory)} '
        f'--coverart 1 --coverpath {shlex.quote(cover_path)} '
        f'--precmd {precmd_escaped} --nointeraction'
    )

    # Execute the command
    subprocess.run(command, shell=True)

def old_rip_cd(output_directory):
    subprocess.run([
        'ripit', '-c', '2', 
        '--outputdir', output_directory, 
        '--coverpath', 'cover.jpg',
        '--coverart', '1',
        '--nointeraction',
        '--precmd', '\'"python fetch_cover.py \'$artist\' \'$album\' ."\''
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

def copy_file_if_exists(source_directory, destination_directory, filename="cover.jpg"):
    """Copy a file from source to destination directory if it exists."""
    source_file = os.path.join(source_directory, filename)
    destination_file = os.path.join(destination_directory, filename)

    # Check if the source file exists
    if os.path.exists(source_file):
        try:
            # Attempt to copy the file
            subprocess.run(['cp', source_file, destination_file], check=True)
            print(f"Successfully copied {filename} to {destination_directory}.")
        except subprocess.CalledProcessError as e:
            # Handle errors during the copy process
            print(f"Failed to copy {filename}: {e}")
    else:
        print(f"No file found to copy: {source_file}")

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
                    # Copy the cover art to the album directory
                    copy_file_if_exists(output_directory, album_path, "cover.jpg")
                    #subprocess.run(['cp', os.path.join(output_directory, "cover.jpg"), os.path.join(album_path, "cover.jpg")], check=True)
                    #print(f"Copying cover art from {os.path.join(output_directory, "cover.jpg")} to {os.path.join(album_path, "cover.jpg")}")
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
            # Check if the artist directory is empty after deleting all album directories
            if not os.listdir(artist_path):  # This checks if the list is empty
                shutil.rmtree(artist_path)
                print(f"Deleted empty artist directory {artist_path}")

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
