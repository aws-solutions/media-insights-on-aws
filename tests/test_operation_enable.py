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
import validation


def test_stage_enable(api, session_stage_configs):
    stages = session_stage_configs
    api = api()
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    print("\nTesting stage['Configuration'][operator]['Enable'] with different combinations of enabled and diasbled operators within a single stage")

    stage = {}
    stage["Name"] = "no-custom-config"
    config = next(item for item in stages if item["Name"] == "no-custom-config")

    # Create a singleton workflow to test executing this stage
    create_workflow_response = api.create_stage_workflow_request(stage)
    workflow = create_workflow_response.json()
    assert create_workflow_response.status_code == 200

    # Get the current workflow configuration
    get_workflow_configuration_response = api.get_workflow_configuration_request(workflow)
    assert get_workflow_configuration_response.status_code == 200

    configuration = get_workflow_configuration_response.json()
    print("Default Workflow Configuration = {}".format(configuration))

    tests = [
        {
            'Description': 'Default configuration: all operators enabled',
            'Configuration': {
                'no-custom-config': {
                    'video-test-sync-as': {
                        'MediaType': 'Video', 'Enabled': True
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
            'Description': 'First operation disabled',
            'Configuration': {
                'no-custom-config': {
                    'video-test-sync-as': {
                        'MediaType': 'Video', 'Enabled': False
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
            'Description': 'Last operation disabled',
            'Configuration': {
                'no-custom-config': {
                    'video-test-sync-as': {
                        'MediaType': 'Video', 'Enabled': True
                        }, 
                    'video-to-text': {
                        'MediaType': 'Video', 'Enabled': False, 
                        'OutputMediaType': 'Text'
                        }
                    }
                }, 
            'Outputs': ['Video']
        },
        {
            'Description': 'All operations disabled',
            'Configuration': {
                'no-custom-config': {
                    'video-test-sync-as': {
                        'MediaType': 'Video', 'Enabled': False
                        }, 
                    'video-to-text': {
                        'MediaType': 'Video', 'Enabled': False, 
                        'OutputMediaType': 'Text'
                        }
                    }
                }, 
            'Outputs': ['Video']
        }

    ]

    for test in tests:
        print("----------------------------------------")
        print("CONFIGURATION = {}".format(test))
        config["WorkflowConfiguration"] = test["Configuration"]
        
        # Execute the stage and wait for it to complete
        create_workflow_execution_response = api.create_workflow_execution_request(workflow, config)
        workflow_execution = create_workflow_execution_response.json()
        assert create_workflow_execution_response.status_code == 200
        assert workflow_execution['Status'] == 'Queued'
        
        workflow_execution = api.wait_for_workflow_execution(workflow_execution, 120)
        assert workflow_execution["Status"] == "Complete"
        
        # Check that disabled operations are skipped
        for stage_name, stage in workflow_execution["Workflow"]["Stages"].items():
            for operation_output in stage["Outputs"]:
                if test["Configuration"][stage_name][operation_output["Name"]]["Enabled"] == True:
                    assert operation_output["Status"] == "Complete"
                else:
                    assert operation_output["Status"] == "Skipped"
        
        # The single stage workflow should have the expected number of outputs for the stage.  
        # If the input video is not transformed by the stage, it will be included in the output
        if "Video" in test["Outputs"]: 
            expected_workflow_outputs = len(test["Outputs"])
        else: 
            expected_workflow_outputs = len(test["Outputs"])+1
        
        assert len(workflow_execution["Globals"]["Media"]) == expected_workflow_outputs

    
    # Delete the workflow
    delete_workflow_response = api.delete_stage_workflow_request(workflow)
    assert delete_workflow_response.status_code == 200

