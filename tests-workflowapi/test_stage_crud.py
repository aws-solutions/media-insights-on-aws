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



def test_stage_api(operations, stage_configs, stack_resources, api_schema):

    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    print("Running /workflow/stage API tests")
    for config in stage_configs:
        
        print("----------------------------------------")
        print("\nTEST STAGE CONFIGURATION: {}".format(config))

        # Create the stage
        create_stage_response = api.create_stage_request(config, stack_resources)
        stage = create_stage_response.json()
        
        assert create_stage_response.status_code == 200
        validation.schema(stage, api_schema["create_stage_response"])

        get_stage_response = api.get_stage_request(stage, stack_resources)
        stage = get_stage_response.json()
        assert get_stage_response.status_code == 200
        validation.schema(stage, api_schema["create_stage_response"])

        # Create a singleton workflow to test executing this stage
        create_workflow_response = api.create_stage_workflow_request(stage, stack_resources)
        workflow = create_workflow_response.json()
        assert create_workflow_response.status_code == 200
        #FIXME - validate create_workflow_response
        # validation.schema(workflow, api_schema["create_workflow_response"])

        # Execute the stage and wait for it to complete
        create_workflow_execution_response = api.create_workflow_execution_request(workflow, config, stack_resources)
        workflow_execution = create_workflow_execution_response.json()
        assert create_workflow_execution_response.status_code == 200
        assert workflow_execution['Status'] == 'Queued'
        
        #FIXME - validate create_workflow_response
        #validation.schema(workflow_execution, api_schema["create_workflow_execution_response"])
        workflow_execution = api.wait_for_workflow_execution(workflow_execution, stack_resources, 120)
        if config["Status"] == "OK":
            assert workflow_execution["Status"] == "Complete"
            
            # Check output media for expected types
            for outputType in config["Outputs"]:
                if outputType != "None":
                    assert outputType in workflow_execution["Globals"]["Media"]
                     
        else:
            assert workflow_execution["Status"] == "Error"

        # Check output metadata for expected keys - each test operation writes a key with its operation name
        for metadataKey in config["ExecutedOperations"]:
            assert metadataKey in workflow_execution["Globals"]["MetaData"]
            if "TestCustomConfig" in config:
                assert "TestCustomConfig" in workflow_execution["Globals"]["MetaData"][metadataKey]
                assert workflow_execution["Globals"]["MetaData"][metadataKey]["TestCustomConfig"] == config["TestCustomConfig"]

        #validation.stage_execution(workflow_execution, config, stack_resources, api_schema)

        # Delete the workflow
        delete_workflow_response = api.delete_stage_workflow_request(workflow, stack_resources)
        assert delete_workflow_response.status_code == 200
        
        #Delete the stage
        delete_stage_response = api.delete_stage_request(stage, stack_resources)
        assert delete_stage_response.status_code == 200




#TODO: dynamoDB remove asset