""" Test module """
import getopt
import json
import time
import requests
import sys

import igraph as ig

LOCAL_PATH = 'http://localhost:8000/api/v1/'
PROD_PATH = 'http://webservices.rbvi.ucsf.edu/rest/api/v1/'

def test_leiden(input_file:str, server:str, algorithm:str):

    # Read in our data
    f = open(input_file, "r")
    edges = []
    for line in f:
        line2 = line.strip()
        edges.append(line2.split(","))

    data = {"nodes":[], "edges":edges}
    json_data = json.dumps(data)

    if algorithm == "leiden":
        response = requests.post(
            server+'algorithm/leiden?objective_function=modularity&iterations=4',
            files=dict(data=json_data)
        )
    elif algorithm == "fastgreedy":
        response = requests.post(
            server+'algorithm/fastgreedy',
            files=dict(data=json_data)
        )
    elif algorithm == "infomap":
        response = requests.post(
            server+'algorithm/infomap',
            files=dict(data=json_data)
        )
    elif algorithm == "labelpropagation":
        response = requests.post(
            server+'algorithm/labelpropagation',
            files=dict(data=json_data)
        )
    elif algorithm == "leadingeigenvector":
        response = requests.post(
            server+'algorithm/leadingeigenvector',
            files=dict(data=json_data)
        )
    elif algorithm == "multilevel":
        response = requests.post(
            server+'algorithm/multilevel',
            files=dict(data=json_data)
        )
    else:
        print("Unknown algorithm: "+algorithm)
        sys.exit(2)

    print (response.text)
    resp = response.json()
    print ('uuid = '+resp['job_id'])
    uuid = resp['job_id']
    status = None

    while status != 'done':
        time.sleep(2)
        response = requests.get(server+'status/'+uuid)
        status = response.text

    response = requests.get(server+'fetch/'+uuid)
    print(response.text)

def usage():
    print("test_rest.py [-h][-i input][-s server][-a algorithm]")

def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hi:s:a:", ["help", "input=", "server=", "algorithm="])
    except getopt.GetoptError as err:
        print(err)
        usage()
        sys.exit(2)

    input_file = None
    server = PROD_PATH
    algorithm = "leiden"
    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
            sys.exit(0)
        elif o in ("-i", "--input"):
            input_file = a
        elif o in ("-s", "--server="):
            if a.startswith("http"):
                server = a
            elif a.startswith("local"):
                server = LOCAL_PATH
            else:
                server = PROD_PATH
        elif o in ("-a", "--algorithm"):
            algorithm = a

    if input_file == None:
        print("Input file must be specified")
        sys.exit(2)

    test_leiden(input_file, server, algorithm)

if __name__ == '__main__':
    main()

