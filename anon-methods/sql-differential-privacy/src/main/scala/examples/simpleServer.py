
""" server.py listens for incoming requests from the client and extracts the parameters from the url sent by the client.
It then writes the extracted parameters to a file in JSON format and sends the extracted file back to the client.
"""

import fnmatch
import glob
import json
import os
import time
from random import randint

from flask import Flask, request
from flask_restful import Api, Resource

app = Flask(__name__)
api = Api(app)

# Variable to store the result file count in Uber Tool directory
file_count = 0

# Variable to store the query result generated by Uber Tool
query_result = []


# Method to read .txt files generated by Uber Tool
def read_file():
    global file_count
    global query_result

    # Give path where Uber Tool creates the result.txt files

    path = "/root/files/noisyres/"

    # Check if new 'result*.txt' has been generated by Uber Tool
    temp_file_count = len(fnmatch.filter(os.listdir(path), '*.txt'))
    if (file_count != temp_file_count):
        file_count = temp_file_count
        list_of_files = glob.iglob(path + '*.txt') # Get list of all files generated by Uber Tool
        latest_file = max(list_of_files, key=os.path.getctime) # Get the latest file by timestamp
        print("\nLast modified file: " + latest_file)
        with open(latest_file, "r") as myfile: # Read the latest file to get the query result and return it
            query_result = myfile.readlines()
            return query_result


# Method to write Client request (url parameters) in JSON to a file
def write_file(response, sid):
    global query_result

    # Write JSON to file
    # Give path to where simpleServer.py creates files containing JSON data

    with open('/root/files/jsonreq/data' + str(sid) + '.json', 'w') as outfile:
        json.dump(response, outfile)
    print("\nJSON File created!")

    # Calls read_file method continuously to check if query_result value has changed
    while True:

        qr = read_file()  # Store the returned query_result
        time.sleep(5)

        if qr is not None:  # Check if query result value is not None
            return qr  # Return the query result to get method


""" Server method to handle incoming data.
Calls writeFile method to write the url parameters in JSON to a file.
Returns the query result (Noisy Result) as response to Client.
"""


class GetParams(Resource):
    def get(self):

        client_request = json.loads(list(dict(request.args).keys())[0])  # Stores the request in JSON format
        print("JSON sent by Client: " + str(client_request)) # Print the JSON payload sent by Client

        # Extract the values from the JSON payload sent by Client
        query = client_request['query'] # Query
        budget = client_request['budget'] # Budget value
        epsilon = client_request['epsilon'] # Epsilon value
        sid = client_request['sid'] # Session ID
        dbname = client_request['dbname'] # Database name

        # If Session ID (sid) is not present in payload i.e., it is a new session then
        # start a new session and assign a randoly generated Session ID
        if not sid:
            print("New session started")
            used_budget = 0.0 # Initialize used_budget to 0.0
            used_budget += float(epsilon) # Add Epsilon vaue to used_budget
            sid = randint(0,1000000000)  # Generate Session ID for new session
            # Create new client request with used_budget
            create_client = {'query': query,'budget': budget,'epsilon': epsilon,'sid': sid, 'used_budget':used_budget, 'dbname':dbname}
            result = write_file(create_client,sid) # Write updated client request to a file
            return [result, sid] # Return the query result and Session ID to Client

        # If Session ID is already present in JSON payload then
        # open the existing file created from previous session by comparing 'sid'
        else:

            # Give path to where simpleServer.py creates files containing JSON data

            with open("/root/files/jsonreq/data" + str(sid) + ".json", "r") as f:
                data = json.load(f)

            # Extract the previous value of used_budget and
            # update the value by adding Epsilon value to it
            tmp_used_budget = data["used_budget"]
            data["used_budget"] = float(tmp_used_budget) + float(epsilon)
            updated_used_budget = data["used_budget"]

            # Extract the original budget and restrict the Client from changing the budget
            file_budget = data ['budget']

            # Update the Client request with used_budget
            update_client = {'query': query,'budget': file_budget,'epsilon': epsilon,'sid': sid, 'used_budget':updated_used_budget, 'dbname':dbname}

            # If used_budget is less than the budget process queries sent by Client
            # else return an error message
            if (float(updated_used_budget) <= float(budget)):
                result = write_file(update_client,sid)
                return [result, sid]
            else:
                error_message = "Budget Exceeded - Cannot process queries"
                return [error_message, sid]


api.add_resource(GetParams, '/data')  # Route for get()

if __name__ == '__main__':
    app.run(port='5890', threaded=True)
