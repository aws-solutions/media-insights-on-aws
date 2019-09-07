# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

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

def schema(instance, schema):
    valid = True
    try:
        validate(instance=instance, schema=schema)
    except Exception as e:
        pytest.fail("Schema validation failed {}".format(e))

    return valid

def operation_execution(workflow_execution, operation_config, stack_resources, api_schema):

    print(workflow_execution)

    globals = workflow_execution["Globals"]
    media_type = operation_config["Input"]
    name = operation_config["Name"]
    stage_name = "_"+name
    
    if operation_config["Status"] == "OK":
        expected_status = "Complete" 
    else:
        expected_status = "Error"

    # Check the outputs published by the operator to the workflow
    assert media_type in globals["Media"]
    assert "MetaData" in globals
    assert name in globals["MetaData"]
    assert globals["MetaData"][name]["Meta"] == "Workflow metadata for {}".format(name)
    
    # Check that the TestCustomConfig was set for the operator
    if "TestCustomConfig" in operation_config:
        assert "TestCustomConfig" in globals["MetaData"][name]

    # Check the status of the stage
    assert stage_name in workflow_execution["Workflow"]["Stages"]
    stage_status = workflow_execution["Workflow"]["Stages"][stage_name]["Status"]
    assert stage_status == expected_status

    # Check the operator status
    operator_output = workflow_execution["Workflow"]["Stages"][stage_name]["Outputs"][0]
    assert media_type in operator_output["Media"]
    assert "MetaData" in operator_output
    assert operator_output["MetaData"][name]["Meta"] == "Workflow metadata for {}".format(name)
    
    # Check that the TestCustomConfig was set for the operator
    if "TestCustomConfig" in operation_config:
        assert "TestCustomConfig" in operator_output["MetaData"][name]

    # FIXME - Check the asset

def stage_execution(workflow_execution, stage_config, stack_resources, api_schema):

    print(workflow_execution)

    globals = workflow_execution["Globals"]
    name = stage_config["Name"]
    stage_name = stage_config["Name"]
    
    if stage_config["Status"] == "OK":
        expected_status = "Complete" 
    else:
        expected_status = "Error"

    # Check the outputs published by the operator to the workflow
    for media_type in stage_config["Ouputs"]:
        assert media_type in globals["Media"]
    
    assert "MetaData" in globals
    for operation in stage_config["Operations"]:
        # FIXME- for now check the need to update the step function to pass in operation 
        # name as a parameter 
        assert operation in globals["MetaData"]
        assert globals["MetaData"][operation]["Meta"] == "Workflow metadata for {}".format(name)

    # Check the status of the stage
    assert stage_name in workflow_execution["Workflow"]["Stages"]
    stage_status = workflow_execution["Workflow"]["Stages"][stage_name]["Status"]
    assert stage_status == expected_status
