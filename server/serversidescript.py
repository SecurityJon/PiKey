import datetime
import string
import fileinput
import subprocess
import sys
import os
from subprocess import STDOUT, check_output
import json
import uuid

#Define /dev/null to route unwanted output to
FNULL = open(os.devnull, 'w')

#Grab the input from the command line
inputhash = sys.argv[1]

#Define the file to write all incoming hashes to
allinputsFileLocation = "/home/pikeyuser/PiKey/PiKey_CapturedHashes.txt"

#Write the incoming hash to the global file
dataToWriteToAllinputsFile = str(datetime.datetime.now()) + ' ' + inputhash + '\n'
allinputsFile = open(allinputsFileLocation, 'a')
allinputsFile.write(dataToWriteToAllinputsFile)
allinputsFile.close()

#Create a random filename for john to parse
fileLocation = "/tmp/"
randomFileName = str(uuid.uuid4())
hashfileForJohn = fileLocation + randomFileName

#Write the hash to a file for john to parse
hashfile = open(hashfileForJohn, 'w+')
hashfile.write(inputhash)
hashfile.close()

#Define a JSON structure to be returned
jsonData = {}
jsonData['status'] = ''
jsonData['password'] = ''

try:
#   Run John against the file, with a timeout of 20 seconds
    johnoutput = subprocess.check_output(["/usr/sbin/john", hashfileForJohn], stderr=FNULL, timeout=20)

#   Check the result of john to grab any hashes presented
    johnresult = subprocess.check_output(["/usr/sbin/john", "--show", hashfileForJohn])

#   Check that john actually returned a result, not an error message
    johnStatusCodecheck1 = johnresult.decode().find('No password hashes loaded')
    johnStatusCodecheck2 = johnresult.decode().find('0 password hashes cracked, 0 left')
    johnStatusCodecheck3 = johnresult.decode().find('NO PASSWORD')

#   Check to see if john throws an error code to indicate it didn't crack the hash
    if (johnStatusCodecheck1 == -1 and johnStatusCodecheck2 == -1 and johnStatusCodecheck3 == -1):

#       Carve up the output of John to return just the password
        passwordToBeReturned = johnresult.decode().split(':')[1]

#       Set return status to success
        jsonData['status'] = 'success'
        jsonData['password'] = passwordToBeReturned
    else:
        jsonData['status'] = 'failure'
        passwordToBeReturned = ''

#except (subprocess.TimeoutExpired):
except:
    jsonData['status'] = 'failure'
    passwordToBeReturned = ''

# Serialise the JSON
jsonSerialised = json.dumps(jsonData)

# Delete the hash file
os.remove(hashfileForJohn)

#Output the JSON result
print (jsonSerialised)
