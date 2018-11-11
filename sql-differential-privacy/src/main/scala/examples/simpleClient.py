# Author: Rohan
# Date: 11-11-2018

""" client.py pastes some data to a url and sends it to the server.
It also receives the parameters in the url extracted by the server
and prints them in JSON along with a HTTP response code
"""

import fnmatch
import glob
import json
import os
from threading import Timer

import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

# Static data in JSON for testing
# Client sends this data in url
data = {
    'query': 'SELECT count(account_id) FROM accounts'
}

# Localhost url
url = 'http://127.0.0.1:5890/data'

# Client sends Get request
# Retry connection attempts in case client is unable to connect with the server
# Each retry attempt will create a new Retry object with updated values, so they can be safely reused.
session = requests.Session()
retry = Retry(connect=3, backoff_factor=0.5)  # A backoff factor to apply between attempts after the second try
adapter = HTTPAdapter(max_retries=retry)
session.mount('http://', adapter)
session.mount('https://', adapter)

# Variable to store the result file count in Uber Tool directory
fileCount = 0

# Variable to store the query result generated by Uber Tool
queryResult = 0

# Exception handling in case exception occurs while connecting to server
try:
    resp = session.get(url, params=json.dumps(data))
    # Client prints the data returned by the server in JSON
    print(resp.json())

    # Client prints the response code
    print(resp)

except requests.ConnectionError as e:
    print("Connection Error. Make sure you are connected to Internet.")
    print(str(e))

except requests.Timeout as e:
    print("Timeout Error")
    print(str(e))

except requests.RequestException as e:
    print("General Error")
    print(str(e))

except KeyboardInterrupt:
    print("Program closed")


# Method to read .txt files generated by Uber Tool
def readFile():
    global fileCount
    global queryResult
    path = "<Enter path of Uber tool directory>\\sql-differential-privacy\\"
    tempFileCount = len(fnmatch.filter(os.listdir(path), '*.txt'))
    if (fileCount != tempFileCount):
        fileCount = tempFileCount
        list_of_files = glob.iglob(path + '*.txt')
        latest_file = max(list_of_files, key=os.path.getctime)
        print(latest_file)
        with open(latest_file, "r") as myfile:
            queryResult = myfile.readlines()
            print(queryResult)


# Timer to call the readFile method periodically
# duration is in seconds
t = Timer(10, readFile)
t.start()

# wait for time completion
t.join()
