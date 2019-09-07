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

# local imports
import api 
import validation

REGION = os.environ['REGION']
BUCKET_NAME = os.environ['BUCKET_NAME']
MIE_STACK_NAME = os.environ['MIE_STACK_NAME']
VIDEO_FILENAME = os.environ['VIDEO_FILENAME']
IMAGE_FILENAME = os.environ['IMAGE_FILENAME']
AUDIO_FILENAME = os.environ['AUDIO_FILENAME']
TEXT_FILENAME = os.environ['TEXT_FILENAME']

def test_operation_delete(udi_operations, stack_resources):
    
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    print("\nTesting operation deletes")
    
    print("Delete an operation that is not part of a workflow or stage")
    config = udi_operations[0]
    operation = {}
    operation["Name"] = config["Name"]
        
    print("\nOPERATION CONFIGURATION: {}".format(config))
    delete_operation_response = api.delete_operation_request(operation, stack_resources)
    assert delete_operation_response.status_code == 200
    old_operation = delete_operation_response.json()

    # give some time for the state machine to delete
    time.sleep(45)

    print("Re-create the operation that is not part of a workflow or stage")
    # Create the operation
    create_operation_response = api.create_operation_request(config, stack_resources)
    print(create_operation_response.json())
    assert create_operation_response.status_code == 200
    new_operation = create_operation_response.json()
        
    assert old_operation["Id"] != new_operation["Id"]


