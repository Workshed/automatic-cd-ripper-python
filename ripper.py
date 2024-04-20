import os
import time
import subprocess
import shutil

def wait_for_cd(drive_path='/dev/cdrom'):
    while True:
        if os.path.exists(drive_path):
            try:
                with open(drive_path, 'rb') as f:
                    return
            except IOError:
                print("Waiting for CD...")
        time.sleep(5)

def rip_cd(output_directory):
    print("Ripping the CD with metadata to", output_directory)
    #subprocess.run(['ripit', '--encoder', 'flac', '--outputdir', output_directory])
    subprocess.run(['ripit', '-c', '2', '--outputdir', output_directory, '--nointeraction'])

def mount_network_drive(network_path, mount_point):
    if not os.path.ismount(mount_point):
        print(f"Mounting the network drive: {network_path}")
        subprocess.run(['sudo', 'mount', '-t', 'cifs', network_path, mount_point, '-o', 'username=guest,password=r3]wZ1-2'])

def copy_to_network(output_directory, mount_point):
    """Copy the ripped album directories to the network drive while maintaining the artist/album structure."""
    # Ensure we only look at directories directly under the output directory
    for artist in os.listdir(output_directory):
        artist_path = os.path.join(output_directory, artist)
        if os.path.isdir(artist_path):  # Ensure it's a directory
            for album in os.listdir(artist_path):
                album_path = os.path.join(artist_path, album)
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
    drive_path = '/dev/cdrom'
    output_directory = '/home/workshed/ripped'
    network_path = '//Workhorse/MainShare/Media/Music'
    mount_point = '/mnt/workhorse_music'
    wait_for_cd(drive_path)
    rip_cd(output_directory)
    mount_network_drive(network_path, mount_point)
    copy_to_network(output_directory, mount_point)
    eject()

if __name__ == "__main__":
    main()
