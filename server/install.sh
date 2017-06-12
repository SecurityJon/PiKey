USER='pikeyuser'
KEYFILE="/home/$USER/.ssh/authorized_keys"


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

#Are we connected to the internet?
Out "OK" "Checking Network Connectivity"
if ! ping -W 1 -c 1 8.8.8.8 &> /dev/null; then Out "ERR" "Not connected to the internet"; exit 1; fi

#Dowload pre-req packages
Out "OK" "Downloading Prerequisites"
sudo apt-get update
sudo apt-get install python3 john

##Configure SSH
Out "OK" "Modifying SSH to prevent Root Login for Security"
sudo sed -i 's/PermitRootLogin prohibit-password/PermitRootLogin no/g' /etc/ssh/sshd_config
sudo service ssh restart

##Create user and folder structure
Out "OK" "Creating Required User"
getent passwd $USER  > /dev/null
if [ $? -eq 0 ]; then
    Out "WARN" "User $USER already exists, skipping"
else
    Out "OK" "Creating user $USER"
    sudo useradd -m $USER    
fi

##Creating SSH keys
Out "OK" "Creating Security Keys"
if [ -e $KEYFILE ]; then
    Out "WARN" "SSH Public Key already exists, deleting"    
    sudo rm $KEYFILE
fi

Out "OK" "Creating SSH Public Key"
if [ ! -e "/home/$USER/.ssh" ]; then
	sudo mkdir "/home/$USER/.ssh"
fi
sudo touch $KEYFILE

    

echo "Paste in the SSH Public Key generated during the client install > "
IFS= read -d '' -n 1 KEY   
while IFS= read -d '' -n 1 -t 1 c
do
    KEY+=$c
done

#Put the SSH Public key into the KeyFile
Out "OK" "Inserting Public Key into File"
echo "command=\"python3 /home/$USER/PiKey/serversidescript.py \${SSH_ORIGINAL_COMMAND#* }\" $KEY $USER" >> $KEYFILE 

#Permissions on key file
Out "OK" "Changing Permissions on Files"
sudo chmod 600 $KEYFILE
sudo chown -R $USER:$USER $KEYFILE

#Change permissions on /tmp
sudo chmod 777 /tmp

##Grab PiKey
Out "OK" "Downloading PiKey"
sudo git clone https://github.com/SecurityJon/PiKey.git /tmp/PiKey/

##Lets move the files to the correct locations
Out "OK" "Moving Files"
sudo mkdir /home/$USER/PiKey
sudo mv /tmp/PiKey/PiKey/server/serversidescript.py /home/$USER/PiKey/serversidescript.py && sudo chmod +x /home/$USER/PiKey/serversidescript.py
sudo chown -R $USER:$USER /home/$USER
sudo rm -rf /tmp/PiKey/


Out "OK" "Installation complete. Don't forget to forward SSH access from the internet to this machine"
