# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

##############################################################################
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

def test_runtime_configuration(operations, stages, stack_resources, api_schema):

    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    print("Testing stage['Configuration'][operator]['Enable'] with different combinations of enabled and diasbled operators within a single stage")

    stage = {}
    stage["Name"] = "no-custom-config2"
    config = next(item for item in stages if item["Name"] == "no-custom-config2")

    # Create a singleton workflow to test executing this stage
    create_workflow_response = api.create_stage_workflow_request(stage, stack_resources)
    workflow = create_workflow_response.json()
    assert create_workflow_response.status_code == 200

    # Get the current workflow configuration
    get_workflow_configuration_response = api.get_workflow_configuration_request(workflow, stack_resources)
    assert get_workflow_configuration_response.status_code == 200

    configuration = get_workflow_configuration_response.json()
    print("Default Workflow Configuration = {}".format(configuration))

    tests = [
        {
            'Description': 'No Default for runtime configuration parameter',
            'Configuration': {
                'no-custom-config2': {
                    'video-test-sync-as': {
                        'MediaType': 'Video', 'Enabled': True,
                        'NoDefaultParameter': 'No Default'
                        }, 
                    'video-to-text': {
                        'MediaType': 'Video', 'Enabled': True, 
                        'OutputMediaType': 'Text'
                        }
                    }
                }, 
            'Outputs': ['Video', 'Text']
        },
        {
            'Description': 'Overide default for configuration parameter',
            'Configuration': {
                'no-custom-config2': {
                    'video-test-sync-as': {
                        'MediaType': 'Video', 
                        'Enabled': False,
                        'NoDefaultParameter': 'No Default'
                        }, 
                    'video-to-text': {
                        'MediaType': 'Video', 'Enabled': True, 
                        'OutputMediaType': 'Text'
                        }
                    }
                }, 
            'Outputs': ['Text']
        },
        {
            'Description': 'Override a subset of the default parameters',
            'Configuration': {
                'no-custom-config2': {
                    'video-test-sync-as': {
                        'NoDefaultParameter': 'No Default'
                        }, 
                    'video-to-text': {
                        'MediaType': 'Video', 
                        'OutputMediaType': 'Text'
                        }
                    }
                }, 
            'Outputs': ['Text']
        }

    ]

    keys = {
            'no-custom-config2': {
                'video-test-sync-as': {
                    'MediaType': '', 
                    'Enabled': False,
                    'NoDefaultParameter': ''
                    }, 
                'video-to-text': {
                    'MediaType': '', 'Enabled': True, 
                    'OutputMediaType': ''
                    }
                }
        }

    for test in tests:
        print("----------------------------------------")
        print("CONFIGURATION = {}".format(test))
        config["WorkflowConfiguration"] = test["Configuration"]
        
        # Execute the stage and wait for it to complete
        create_workflow_execution_response = api.create_workflow_execution_request(workflow, config, stack_resources)
        workflow_execution = create_workflow_execution_response.json()
        assert create_workflow_execution_response.status_code == 200
        assert workflow_execution['Status'] == 'Queued'
        
        workflow_execution = api.wait_for_workflow_execution(workflow_execution, stack_resources, 120)
        assert workflow_execution["Status"] == "Complete"

        print("Check that expected configuration keys are in operator output")
        for stage_name, stage in keys.items():
            for operation_name, operation in stage.items():
                operation_output = list(filter(lambda operation: operation['Name'] == operation_name, workflow_execution["Workflow"]["Stages"][stage_name]["Outputs"]))[0]
                for k,v in operation.items():
                    assert k in operation_output["Configuration"]

        print("Check that only expected configuration keys are in operator output")
        for stage_name, stage in keys.items():
            for operation_name, operation in stage.items():
                operation_output = list(filter(lambda operation: operation['Name'] == operation_name, workflow_execution["Workflow"]["Stages"][stage_name]["Outputs"]))[0]
                for k,v in operation_output["Configuration"].items():
                    assert k in operation
        

    
    # Delete the workflow
    delete_workflow_response = api.delete_stage_workflow_request(workflow, stack_resources)
    assert delete_workflow_response.status_code == 200


