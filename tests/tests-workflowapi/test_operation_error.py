# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

###############################################################################
# Integration testing for the MIE workflow API
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
token = os.environ["MIE_ACCESS_TOKEN"]


def test_duplicate_operation(operations,stack_resources, api_schema):

    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    print("\nTest creating a duplicate operation")

    config = operations[0]

    # Create the operation again
    create_operation_response = api.create_operation_request(config, stack_resources)
    assert create_operation_response.status_code == 409

def test_schema_errors(operations, stack_resources, api_schema):

    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    print("----------------------------------------")
    print("\nTest create operation schema errors\n")

    config = operations[0]
    start_lambda = config["Input"]+config["Type"]+config["Status"]+"Lambda"
    headers = {"Content-Type": "application/json", "Authorization": token}
    body = {
        "StartLambdaArn": stack_resources[start_lambda],
        "Configuration": {
            "MediaType": config["Input"],
            "Enabled": True
        },
        "StateMachineExecutionRoleArn": stack_resources["StepFunctionRole"],
        "Type": config["Type"],
        "Name": config["Name"]
    }   

    if (config["Type"] == "Async"):
        monitor_lambda = config["Input"]+config["Type"]+config["Status"]+"MonitorLambda"
        body["MonitorLambdaArn"] = stack_resources[monitor_lambda]

    # mess it up by removing required parameters
    for param_key in ["StartLambdaArn", "Configuration", "StateMachineExecutionRoleArn", "Type", "Name" ]:
        print ("Missing {}".format(param_key))
        bad_body = dict(body)
        bad_body.pop(param_key)
        create_operation_response = requests.post(stack_resources["WorkflowApiEndpoint"]+'/workflow/operation', headers=headers, json=bad_body, verify=False)
        assert create_operation_response.status_code == 400
    
    # mess it up by missing keys from the "Configuration" block
    for param_key in ["MediaType", "Enabled"]:
        print ("Missing {}".format(param_key))
        bad_body = dict(body)
        bad_body["Configuration"].pop(param_key)
        create_operation_response = requests.post(stack_resources["WorkflowApiEndpoint"]+'/workflow/operation', headers=headers, json=bad_body, verify=False)
        assert create_operation_response.status_code == 400

    # mess it up by musing the wrong type
    print ("Wrong type for StartLambdaArn")
    bad_body = dict(body)
    bad_body["StartLambdaArn"] = 10
    create_operation_response = requests.post(stack_resources["WorkflowApiEndpoint"]+'/workflow/operation', headers=headers, json=bad_body, verify=False)
    assert create_operation_response.status_code == 400

    print ("Wrong format for StartLambdaArn string")
    bad_body = dict(body)
    bad_body["StartLambdaArn"] = "this is not an ARN"
    create_operation_response = requests.post(stack_resources["WorkflowApiEndpoint"]+'/workflow/operation', headers=headers, json=bad_body, verify=False)
    assert create_operation_response.status_code == 400

    # mess it up by musing the wrong type
    print ("Wrong type for MediaType")
    bad_body = dict(body)
    bad_body["Configuration"]["MediaType"] = 10
    create_operation_response = requests.post(stack_resources["WorkflowApiEndpoint"]+'/workflow/operation', headers=headers, json=bad_body, verify=False)
    assert create_operation_response.status_code == 400

    # mess it up by musing the wrong type
    print ("Wrong type for Enabled")
    bad_body = dict(body)
    bad_body["Configuration"]["Enabled"] = "this is no boolean"
    create_operation_response = requests.post(stack_resources["WorkflowApiEndpoint"]+'/workflow/operation', headers=headers, json=bad_body, verify=False)
    assert create_operation_response.status_code == 400
    
    # mess it up by musing the wrong type
    print ("Wrong type for StateMachineExecutionRoleArn")
    bad_body = dict(body)
    bad_body["StateMachineExecutionRoleArn"] = 10
    create_operation_response = requests.post(stack_resources["WorkflowApiEndpoint"]+'/workflow/operation', headers=headers, json=bad_body, verify=False)
    assert create_operation_response.status_code == 400

    print ("Wrong format for StateMachineExecutionRoleArn string")
    bad_body = dict(body)
    bad_body["StateMachineExecutionRoleArn"] = "this is not an ARN"
    create_operation_response = requests.post(stack_resources["WorkflowApiEndpoint"]+'/workflow/operation', headers=headers, json=bad_body, verify=False)
    assert create_operation_response.status_code == 400

    # mess it up by musing the wrong type
    print ("Wrong type for Type")
    bad_body = dict(body)
    bad_body["Type"] = 10
    create_operation_response = requests.post(stack_resources["WorkflowApiEndpoint"]+'/workflow/operation', headers=headers, json=bad_body, verify=False)
    assert create_operation_response.status_code == 400

    print ("Wrong value for Type")
    bad_body = dict(body)
    bad_body["Type"] = "this is not Async or Sync"
    create_operation_response = requests.post(stack_resources["WorkflowApiEndpoint"]+'/workflow/operation', headers=headers, json=bad_body, verify=False)
    assert create_operation_response.status_code == 400

    # mess it up by musing the wrong type
    print ("Wrong type for Name")
    bad_body = dict(body)
    bad_body["Name"] = 10
    create_operation_response = requests.post(stack_resources["WorkflowApiEndpoint"]+'/workflow/operation', headers=headers, json=bad_body, verify=False)
    assert create_operation_response.status_code == 400



#TODO: dynamoDB remove asset