# Automatic CD ripper

This project was created to digitise a pile of CDs I have which aren't available on streaming services like Spotify. The goal was to have something without a screen that needed as little interaction as possible in order to take a CD, losslessly rip it and store the files on a local NAS drive. Then Sonos indexes the NAS folders and lets me play the music and Plex has the folders as part of it's library.

I have this installed on a headless Raspberry Pi connected to a USB CD/DVD drive. It's running a Raspberry Pi OS which only requires a terminal, no point wasting power on a desktop i'm not going to use.

## Setup

SSH in to your Raspberry Pi and follow along...

### Prerequisites

Install various required dependencies

```
sudo apt-get update
sudo apt-get install flac cifs-utils ripit eject
```

### Ripit output directory

Alter the output path/structure of `ripit`, by default music is stored in a folder called 'artist - album name' but we want separate folders for artist and album in order to satisfy [Plex](https://support.plex.tv/articles/200265296-adding-music-media-from-folders/): 

Edit `/etc/ripit/config` (e.g. `nano /etc/ripit/config`) and update the following line from...

```
dirtemplate="$artist - $album"
```

...to...

```
dirtemplate="$artist/$album"
```

Save and exit the file.

### Mounting the network drive automatically

We're going to mount the network drive using `fstab`.
Make a folder for your mount point, I used `/mnt/workhorse_music`:

```
sudo mkdir /mnt/workhorse_music
```

Create a new file to store your credentials, such as `/etc/cifs-credentials`.
Add the username and password to the file:

```
username=myusername
password=mypassword
```

Secure the file by restricting its access to root only:

```
sudo chown root:root /etc/cifs-credentials
sudo chmod 600 /etc/cifs-credentials
```

Open `/etc/fstab` with a text editor (as root or with sudo):

```bash
sudo nano /etc/fstab
```

Add a line for your network drive:

```
//SERVER/Share /mnt/workhorse_music cifs credentials=/etc/cifs-credentials,uid=1000,gid=1000 0 0
```

Replace 1000 with your user and group IDs (find these with id command), and adjust username and password for the network share access.

Test the configuration by attempting to mount all entries:

```bash
sudo mount -a
```

This command will try to mount everything defined in fstab and is a good way to ensure there are no errors in your configuration.

### Creating a `systemd` service

Create a service file:

```
sudo nano /etc/systemd/system/rip_and_transfer.service
```

Add the following:

```
[Unit]
Description=Python CD Ripping and Transfer Script
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 /path/to/your/script/ripper.py
Restart=on-failure
User=pi
Group=pi
Environment="PATH=/usr/bin:/usr/local/bin"
StandardOutput=append:/var/log/rip_and_transfer.log
StandardError=inherit

[Install]
WantedBy=multi-user.target
```

Create and set permissions for a log file for the service:

```
sudo touch /var/log/rip_and_transfer.log
sudo chown root: /var/log/rip_and_transfer.log
sudo chmod 664 /var/log/rip_and_transfer.log
```

Reload and restart the service:

```
sudo systemctl daemon-reload
sudo systemctl enable rip_and_transfer.service
sudo systemctl start rip_and_transfer.service
```

Check the status of the service:

```
sudo systemctl status rip_and_transfer.service
```

Setup log rotation:

```
sudo nano /etc/logrotate.d/rip_and_transfer
```

And add:

```
/var/log/rip_and_transfer.log {
    weekly
    rotate 4
    compress
    delaycompress
    missingok
    notifempty
    create 0644 pi pi
    postrotate
        systemctl restart rip_and_transfer.service > /dev/null
    endscript
}
```

### Debugging the script

To check for problems with `ripper.py` I would recommend stopping your service and just running `python3 /path/to/ripper.py`, give it a CD and watch the output. Is it all working as it should? Have you set the right paths etc in `ripper.py`?
