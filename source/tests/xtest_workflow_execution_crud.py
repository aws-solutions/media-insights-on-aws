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


def test_workflow_execution_api(api, api_schema, workflow_configs):
    api = api()
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    print("Running /workflow/execution API tests")
    for config in workflow_configs:
        
        print("----------------------------------------")
        print("\nTEST WORKFLOW EXECUTION CONFIGURATION: {}".format(config))

        # Create the workflow
        # TODO: Add a check here to see if the workflow is in a deleting state (from a previous test run) and wait 
        create_workflow_response = api.create_workflow_request(config)
        workflow = create_workflow_response.json()

        assert create_workflow_response.status_code == 200
        
        #FIXME - validate create_workflow_response
        #validation.schema(workflow, api_schema["create_workflow_response"])

        # Execute the workflow and wait for it to complete
        create_workflow_execution_response = api.create_workflow_execution_request(workflow, config)
        workflow_execution = create_workflow_execution_response.json()
        assert create_workflow_execution_response.status_code == 200
        assert workflow_execution['Status'] == 'Queued'
        
        #FIXME - validate create_workflow_response
        #validation.schema(workflow_execution, api_schema["create_workflow_execution_response"])
        workflow_execution = api.wait_for_workflow_execution(workflow_execution, 120)
        if config["Status"] == "OK":
            assert workflow_execution["Status"] == "Complete"
            
            # Check output media for expected types
            for outputType in config["Outputs"]:
                if outputType != "None":
                    assert outputType in workflow_execution["Globals"]["Media"]
                     
        else:
            assert workflow_execution["Status"] == "Error"

        # validation.stage_execution(workflow_execution, config, stack_resources, api_schema)

        # Delete the workflow
        delete_workflow_response = api.delete_stage_workflow_request(workflow)
        assert delete_workflow_response.status_code == 200
        
        #Delete the workflow
        delete_stage_response = api.delete_stage_request(workflow)
        assert delete_stage_response.status_code == 200




#TODO: dynamoDB remove asset