# Automatic CD ripper

This project was created to digitise a pile of CDs I have which aren't available on streaming services like Spotify. The goal was to have something without a screen that needed as little interaction as possible in order to take a CD, losslessly rip it and store the files on a local NAS drive. Then Sonos indexes the NAS folders and lets me play the music and Plex has the folders as part of it's library.

I have this installed on a headless Raspberry Pi connected to a USB CD/DVD drive. It's running a Raspberry Pi OS which only requires a terminal, no point wasting power on a desktop i'm not going to use.

## Setup

SSH in to your Raspberry Pi and follow along...

Install various required packages

```
sudo apt-get update
sudo apt-get install flac cifs-utils ripit eject
```

Alter the output format of `ripit`, by default music is stored in a folder called 'artist - album name' but we want separate folders for artist and album in order to satisfy [Plex](https://support.plex.tv/articles/200265296-adding-music-media-from-folders/): 

Edit `/etc/ripit/config` (e.g. `nano /etc/ripit/config`) and update the following line from...

```
dirtemplate="$artist - $album"
```

...to...

```
dirtemplate="$artist/$album"
```

Save and exit the file.

We're going to mount the network drive using `fstab`.
Make a folder for your mount point, I used `/mnt/workhorse_music`:

```
sudo mkdir /mnt/workhorse_music
```

Open `/etc/fstab` with a text editor (as root or with sudo):

```bash
sudo nano /etc/fstab
```

Add a line for your network drive:

```
//SERVER/Share /mnt/workhorse_music cifs username=your_username,password=your_password,uid=1000,gid=1000 0 0
```

Replace 1000 with your user and group IDs (find these with id command), and adjust username and password for the network share access.

Test the configuration by attempting to mount all entries:

```bash
sudo mount -a
```

This command will try to mount everything defined in fstab and is a good way to ensure there are no errors in your configuration.

