Compiling a Kernel Module
------

As the g_hid.ko by default is missing some platform information, it needs to be recompiled for each Jessie release in order to work. 
  
The instructions below give a few pointers on how to achieve this should you need to use a release other than 4.4.50.
  
- Get the latest source for the release you are using on your Pi Zero.

	```bash
	sudo apt-get update
	sudo apt-get upgrade
	
	sudo apt-get install libncurses5-dev
	sudo apt-get install bc
	
	sudo wget https://raw.githubusercontent.com/notro/rpi-source/master/rpi-source -O /usr/bin/rpi-source && sudo chmod +x /usr/bin/rpi-source && /usr/bin/rpi-source -q --tag-update
	sudo /usr/bin/rpi-source --skip-gcc
	```
- This should create a folder with a uid in /root, called linux-uid
    	
	```bash
	cd /root/linux-<uid>/drivers/usb/gadget/legacy
	```
	
- Copy the hid.c and makefile file from the repo to this current directory (override the existing, or rename if you prefer). Then compile...

	```bash
	make
	```
	
- Grab the resulting g_hid.ko in the directory and copy here: /lib/modules/4.4.50+/kernel/drivers/usb/gadget/legacy (overrie the existing)
	
- Load the module to test (it shouldn't give you any errors, and if plugged into a PC, you should see he "USB HID" appear)

	```bash
	modprobe g_hid
	```


References:

https://hackaday.io/post/34383

http://stackoverflow.com/questions/20167411/how-to-compile-a-kernel-module-for-raspberry-pi

https://www.mjmwired.net/kernel/Documentation/usb/gadget_hid.txt
