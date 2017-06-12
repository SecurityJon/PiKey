Client Installation
------

The instructions below are used to configure the Pi Zero.

- Download the latest version of Jessie Lite (https://downloads.raspberrypi.org/raspbian_lite_latest)
		
- Follow the guidance here for step by step installation (https://www.raspberrypi.org/documentation/installation/installing-images/README.md) …but in short:
	- Extract the image file from the downloaded ZIP
	- Plug in the MicroSD card into your PC - for Windows, use Win32DiskImager to install the image file onto the card.
	- Done!
			
- Plug the MicroSD card into your Pi Zero. It also makes sense at this point to plug in a monitor and a keyboard. Apply some power and wait for it to boot.
		
- Login with username: pi and password: raspberry
		
- Now is a good time to connect to your wifi so you can download the rest of the pre-requisites. Steps for connecting to Wifi for the non-Linux savy amoung us are below.

	- Edit the network interfaces file
	
		```bash	
		sudo nano /etc/network/interfaces
		```
		
	- Find the entry for wlan0 and modifiy it with the text below. If it isn't there, then add the following to the bottom of 		the file (Ctrl+X) to exit
	
		```bash
		allow-hotplug wlan0
		iface wlan0 inet dhcp
			wpa-conf /etc/wpa_supplicant_wpa_supplicant.conf
			metric 10
		```

	- Edit the wpa_supplicant file
	
		```bash
		sudo nano /etc/wpa_supplicant/wpa_supplicant.conf
		```
		
	- Add the following to the bottom of the file (Ctrl+X) to exit
	
		```bash		
		network={
			ssid="your network name"
			psk="your network key"
			key_mgmt=WPA-PSK
		}
		```
	
	- At this point you can do the following to verify it connects to your Wifi ok.
		```bash
		sudo ifdown wlan0
		sudo ifup wlan0
		```

**!!NOTE!!** - After the intial install, it might be wise to change these setting to a wifi hotspot on your phone or similar, as this is typically what you will use away from home. If you forget this step, then no hashes will get cracked!!

- Configure SSH to startup on boot:
	
	```bash
	sudo touch /boot/ssh
	```

- Reboot (with the screen connected as this will print the DHCP IP address for the wireless adapter). Log back in via SSH.
			
- Run the setup script as the normal user.

	```bash
	bash <(curl -s https://raw.githubusercontent.com/SecurityJon/PiKey/master/client/install.sh)
	```
