""" Test module """
import getopt
import json
import time
import requests
import sys

import igraph as ig

LOCAL_PATH = 'http://localhost:8000/'
PROD_PATH = 'http://webservices.rbvi.ucsf.edu/rest/api/v1/'

def test_service(input_file:str, server:str, service:str):

    # Read in our data
    f = open(input_file, "r")
    edges = []
    for line in f:
        line2 = line.strip()
        edges.append(line2.split(","))

    data = {"nodes":[], "edges":edges}
    json_data = json.dumps(data)

    if service == "leiden":
        response = requests.post(
            server+'service/leiden?objective_function=modularity&iterations=4',
            files=dict(data=json_data)
        )
    elif service == "fastgreedy":
        response = requests.post(
            server+'service/fastgreedy',
            files=dict(data=json_data)
        )
    elif service == "infomap":
        response = requests.post(
            server+'service/infomap',
            files=dict(data=json_data)
        )
    elif service == "labelpropagation":
        response = requests.post(
            server+'service/labelpropagation',
            files=dict(data=json_data)
        )
    elif service == "leadingeigenvector":
        response = requests.post(
            server+'service/leadingeigenvector',
            files=dict(data=json_data)
        )
    elif service == "multilevel":
        response = requests.post(
            server+'service/multilevel',
            files=dict(data=json_data)
        )
    else:
        print("Unknown service: "+service)
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
    print("test_rest.py [-h][-i input][-s server][-a service]")

def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hi:s:a:", ["help", "input=", "server=", "service="])
    except getopt.GetoptError as err:
        print(err)
        usage()
        sys.exit(2)

    input_file = None
    server = PROD_PATH
    service = "leiden"
    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
            sys.exit(0)
        elif o in ("-i", "--input"):
            input_file = a
        elif o in ("-s", "--server"):
            if a.startswith("http"):
                server = a
            elif a.startswith("local"):
                server = LOCAL_PATH
            else:
                server = PROD_PATH
        elif o in ("-a", "--service"):
            service = a

    if input_file == None:
        print("Input file must be specified")
        sys.exit(2)

    test_service(input_file, server, service)

if __name__ == '__main__':
    main()

