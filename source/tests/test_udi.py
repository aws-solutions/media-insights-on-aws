###############################################################################
# Integration testing for the MIE workflow API - test update and delete of 
# operations, stages and workflows. 
#
# PRECONDITIONS:
# MIE base stack must be deployed in your AWS account
#
# Boto3 will raise a deprecation warning (known issue). It's safe to ignore.
#
# USAGE:
#   cd tests/
#   pytest -s -W ignore::DeprecationWarning -p no:cacheprovider
#
###############################################################################

import pytest
import boto3
import json
import time
import math
import requests
import urllib3
import logging
from botocore.exceptions import ClientError
import re
import os
from jsonschema import validate
import time
import threading

import validation

udi_operation_configs = [
    {"Name":"udi-video-to-video1", "Input":"Video", "Type":"Async", "Status":"OK", "OutputMediaType":"Video"},
    {"Name":"udi-video-to-video2", "Input":"Video", "Type":"Async", "Status":"OK", "OutputMediaType":"Video"},
    {"Name":"udi-video-to-video3", "Input":"Video", "Type":"Async", "Status":"OK", "OutputMediaType":"Video"},
    {"Name":"udi-video-to-text1", "Input":"Video", "Type":"Async", "Status":"OK", "OutputMediaType":"Text"}
    ]

@pytest.fixture
def udi_operations(api, api_schema):
    api = api()
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    print("Creating update/delete test operations")
    for config in udi_operation_configs:
        
        print("\nOPERATION CONFIGURATION: {}".format(config))

        # Create the operation
        create_operation_response = api.create_operation_request(config)
        operation = create_operation_response.json()
        
        assert create_operation_response.status_code == 200
        #validation.schema(operation, api_schema["create_operation_response"])
        validation.schema(operation, api_schema["create_operation_response"])

    yield udi_operation_configs

    for config in udi_operation_configs:
        #Delete the operation
        operation = {}
        operation["Name"] = config["Name"]
        
        delete_operation_response = api.delete_operation_request(operation)
        assert delete_operation_response.status_code == 200


def test_operation_delete(api, udi_operations):
    api = api()
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    print("\nTesting operation deletes")
    
    print("Delete an operation that is not part of a workflow or stage")
    config = udi_operations[0]
    operation = {}
    operation["Name"] = config["Name"]
        
    print("\nOPERATION CONFIGURATION: {}".format(config))
    delete_operation_response = api.delete_operation_request(operation)
    assert delete_operation_response.status_code == 200
    old_operation = delete_operation_response.json()

    # give some time for the state machine to delete
    time.sleep(45)

    print("Re-create the operation that is not part of a workflow or stage")
    # Create the operation
    create_operation_response = api.create_operation_request(config)
    print(create_operation_response.json())
    assert create_operation_response.status_code == 200
    new_operation = create_operation_response.json()
        
    assert old_operation["Id"] != new_operation["Id"]


