import pytest
#import fixtures.setup as setup

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
import api 
import validation

REGION = os.environ['REGION']
BUCKET_NAME = os.environ['BUCKET_NAME']
MIE_STACK_NAME = os.environ['MIE_STACK_NAME']

@pytest.fixture(scope='session')
def api_schema():

    schema_dir = "../source/workflowapi/chalicelib/apischema"
    
    schemata = {}
    for f in os.listdir(schema_dir):
        with open(schema_dir+"/"+f) as schema_file:  
            schema = json.load(schema_file)
            schemata[schema['title']] = schema
    
    return schemata

    
@pytest.fixture(scope='session')
def stack_resources():

    resources = {}
    # are the workflow and dataplane api's present?

    client = boto3.client('cloudformation', region_name=REGION)
    response = client.describe_stacks(StackName=MIE_STACK_NAME)
    outputs = response['Stacks'][0]['Outputs']

    for output in outputs:
        resources[output["OutputKey"]] = output["OutputValue"]

    assert "DataplaneApiEndpoint" in resources
    assert "WorkflowApiEndpoint" in resources
    assert "TestStack" in resources

    api_endpoint_regex = ".*.execute-api."+REGION+".amazonaws.com/api/.*"
    
    assert re.match(api_endpoint_regex, resources["DataplaneApiEndpoint"])
    assert re.match(api_endpoint_regex, resources["WorkflowApiEndpoint"])

    response = client.describe_stacks(StackName=resources["TestStack"])
    outputs = response['Stacks'][0]['Outputs']
    for output in outputs:
        resources[output["OutputKey"]] = output["OutputValue"]

    assert "VideoSyncOKLambda" in resources
    assert "VideoAsyncOKLambda" in resources
    assert "VideoAsyncOKMonitorLambda" in resources
    assert "VideoSyncFailLambda" in resources
    assert "AudioSyncOKLambda" in resources
    assert "AudioAsyncOKLambda" in resources
    assert "AudioAsyncOKMonitorLambda" in resources
    assert "ImageSyncOKLambda" in resources
    assert "ImageAsyncOKLambda" in resources
    assert "ImageAsyncOKMonitorLambda" in resources
    assert "TextSyncOKLambda" in resources
    assert "TextAsyncOKLambda" in resources
    assert "TextAsyncOKMonitorLambda" in resources
    
    return resources



# This fixture is used for testing various operation configurations.
# Returns an array of values for the parameterized test.
@pytest.fixture(scope='session')
def operation_configs():
    return [
    {"Name":"video-test-sync-a","Input":"Video", "Type":"Sync", "Status":"OK"},
    {"Name":"audio-test-async-a","Input":"Audio", "Type":"Async", "Status":"OK", "TestCustomConfig":"audio-test-async-a"},
    {"Name":"text-test-sync-a","Input":"Text", "Type":"Async", "Status":"OK"},
    {"Name":"video-test-sync-fail-a","Input":"Video", "Type":"Sync", "Status":"Fail"}
    ]

# This fixture is used for testing various operation configurations.
# Returns an array of values for the parameterized test.
@pytest.fixture(scope='session')
def session_operation_configs():
    return [
    {"Name":"video-test-sync-as", "Input":"Video", "Type":"Sync", "Status":"OK"},
    {"Name":"video-test-async-as", "Input":"Video", "Type":"Async", "Status":"OK"},
    {"Name":"video-test-sync-fail-as", "Input":"Video", "Type":"Sync", "Status":"Fail"},
    {"Name":"audio-test-async-as", "Input":"Audio", "Type":"Async", "Status":"OK", "TestCustomConfig":"audio-test-async-a"},
    {"Name":"text-test-sync-as", "Input":"Text", "Type":"Async", "Status":"OK"},
    {"Name":"video-to-audio", "Input":"Video", "Type":"Async", "Status":"OK", "OutputMediaType":"Audio"},
    {"Name":"video-to-text", "Input":"Video", "Type":"Async", "Status":"OK", "OutputMediaType":"Text"}
    ]

# This fixture is used for testing updating and deleting operations.
# Returns an array of values for the parameterized test.
@pytest.fixture(scope='session')
def udi_operation_configs():
    return [
    {"Name":"udi-video-to-video1", "Input":"Video", "Type":"Async", "Status":"OK", "OutputMediaType":"Video"},
    {"Name":"udi-video-to-video2", "Input":"Video", "Type":"Async", "Status":"OK", "OutputMediaType":"Video"},
    {"Name":"udi-video-to-video3", "Input":"Video", "Type":"Async", "Status":"OK", "OutputMediaType":"Video"},
    {"Name":"udi-video-to-text1", "Input":"Video", "Type":"Async", "Status":"OK", "OutputMediaType":"Text"}
    ]

# This fixture is used for testing various operation configurations.
# Returns an array of values for the parameterized test.
@pytest.fixture(scope='session')
def stage_configs():
    return [
    {"Name":"fail-op-1-a","Input":"Video", "Operations": ["video-test-sync-fail-as", "audio-test-async-as"], "ExecutedOperations": [], "Outputs":[], "Status":"Fail"},
    {"Name":"fail-op-2-a","Input":"Video", "Operations": ["video-test-sync-as", "video-test-sync-fail-as"], "ExecutedOperations": ["video-test-sync-as"], "Outputs":[], "Status":"Fail"},
    {"Name":"2-op-a","Input":"Audio", "Operations": ["audio-test-async-as", "text-test-sync-as"], "ExecutedOperations": ["audio-test-async-as"], "Outputs":["Audio"], "Status":"OK"},
    {"Name":"many-op-a","Input":"Audio", "Operations": ["audio-test-async-as", "text-test-sync-as", "video-test-sync-as"], "ExecutedOperations": ["audio-test-async-as"], "Outputs":["Audio"], "Status":"OK"},
    {"Name":"no-op","Input":"Audio", "Operations": ["text-test-sync-as", "video-test-sync-as"], "ExecutedOperations": [], "Outputs":[], "Status":"OK"}
    ]

# This fixture is used for testing various operation configurations.
# Returns an array of values for the parameterized test.
@pytest.fixture(scope='session')
def session_stage_configs():
    return [
    {"Name":"no-custom-config", "Input":"Video", "Operations": ["video-test-sync-as", "video-to-text", ], "Outputs":["Video", "Text"], "Status":"OK"},
    {"Name":"no-custom-config2", "Input":"Video", "Operations": ["video-test-sync-as", "video-to-text", ], "Outputs":["Video", "Text"], "Status":"OK"},
    {"Name":"fail-op-2-as", "Input":"Audio", "Operations": ["video-test-sync-as", "video-test-sync-fail-as"], "Outputs":[], "Status":"Fail"},
    {"Name":"2-op-as", "Input":"Audio", "Operations": ["audio-test-async-as", "text-test-sync-as"], "Outputs":["Audio"], "Status":"OK"},
    {"Name":"many-op-as", "Input":"Audio", "Operations": ["audio-test-async-as", "text-test-sync-as", "video-test-sync-as"], "Outputs":["Audio"], "Status":"OK"},
    {"Name":"no-op-s","Input":"Audio", "Operations": ["text-test-sync-as", "video-test-sync-as"], "ExecutedOperations": [], "Outputs":[], "Status":"OK"}
    ]

# This fixture is used for testing various stage configurations.
# Returns an array of values for the parameterized test.
@pytest.fixture(scope='session')
def udi_stage_configs():
    return [
    {"Name":"udi_stage1", "Input":"Video", "Operations": ["udi-video-to-video1", ], "Outputs":["Video"], "Status":"OK"},
    {"Name":"udi_stage2", "Input":"Video", "Operations": ["udi-video-to-video2" ], "Outputs":["Video"], "Status":"OK"},
    {"Name":"udi_stage3", "Input":"Audio", "Operations": ["udi-video-to-video2"], "Outputs":["Video"], "Status":"OK"},
    {"Name":"udi_stage4", "Input":"Audio", "Operations": ["udi-video-to-video3", "udi-video-to-text1"], "Outputs":["Video", "Text"], "Status":"OK"}
    ]

# This fixture is used for testing various operation configurations.
# Returns an array of values for the parameterized test.
@pytest.fixture(scope='session')
def workflow_configs():
    return [
    {"Name":"first-stage-fail","Input":"Audio", "Stages": ["fail-op-2-as", "2-op-as"], "Outputs":[], "Status":"Fail"},
    {"Name":"last-stage-fail","Input":"Audio", "Stages": ["many-op-as", "2-op-as", "fail-op-2-as"], "Outputs":["Audio"], "Status":"Fail"},
    {"Name":"2-stage","Input":"Audio", "Stages": ["many-op-as", "2-op-as"], "Outputs":["Audio"], "Status":"OK"}
    ]

@pytest.fixture(scope='session')
def operations(session_operation_configs, stack_resources, api_schema):

    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    print("Creating test operations")
    for config in session_operation_configs:

        
        
        print("\nOPERATION CONFIGURATION: {}".format(config))

        # Create the operation
        create_operation_response = api.create_operation_request(config, stack_resources)
        operation = create_operation_response.json()
        
        assert create_operation_response.status_code == 200
        #validation.schema(operation, api_schema["create_operation_response"])
        validation.schema(operation, api_schema["create_operation_response"])

    yield session_operation_configs

    for config in session_operation_configs:    
        #Delete the operation
        operation = {}
        operation["Name"] = config["Name"]
        
        delete_operation_response = api.delete_operation_request(operation, stack_resources)
        assert delete_operation_response.status_code == 200

@pytest.fixture(scope='session')
def stages(operations, session_stage_configs, stack_resources, api_schema):

    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    print("Creating test stages")
    for config in session_stage_configs:
        
        print("\nSTAGE CONFIGURATION: {}".format(config))

        # Create the stage
        create_stage_response = api.create_stage_request(config, stack_resources)
        stage = create_stage_response.json()
        
        assert create_stage_response.status_code == 200
        validation.schema(stage, api_schema["create_stage_response"])

    yield session_stage_configs

    for config in session_stage_configs:    
        #Delete the stage
        stage = {}
        stage["Name"] = config["Name"]
        
        delete_stage_response = api.delete_stage_request(stage, stack_resources)
        assert delete_stage_response.status_code == 200

@pytest.fixture(scope='session')
def udi_operations(udi_operation_configs, stack_resources, api_schema):

    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    print("Creating update/delete test operations")
    for config in udi_operation_configs:
        
        print("\nOPERATION CONFIGURATION: {}".format(config))

        # Create the operation
        create_operation_response = api.create_operation_request(config, stack_resources)
        operation = create_operation_response.json()
        
        assert create_operation_response.status_code == 200
        #validation.schema(operation, api_schema["create_operation_response"])
        validation.schema(operation, api_schema["create_operation_response"])

    yield udi_operation_configs

    for config in udi_operation_configs:    
        #Delete the operation
        operation = {}
        operation["Name"] = config["Name"]
        
        delete_operation_response = api.delete_operation_request(operation, stack_resources)
        assert delete_operation_response.status_code == 200

@pytest.fixture(scope='session')
def session_nonpaginated_results():
    return {
        "OperatorName": "samplenonpagresults",
        "WorkflowId": "test-123",
        "Results": {
            "Testing": "This is some test data"
        }
    }


@pytest.fixture(scope='session')
def session_paginated_results():
    return {
        "OperatorName": "samplepagresults",
        "WorkflowId": "test-123",
        "Results": {
            "Labels": [{
                "Timestamp": 0,
                "Label": {
                    "Name": "Purple",
                    "Confidence": 54.41469192504883,
                    "Instances": [],
                    "Parents": []
                }
            }
            ]
        }
    }


@pytest.fixture(scope="session", autouse=True)
def cleanup(request, session_operation_configs, operation_configs, udi_operation_configs, session_stage_configs, stage_configs, udi_stage_configs, stack_resources):
    """Cleanup any created resources"""
    def remove_operation_configs():
        configs = operation_configs+session_operation_configs+udi_operation_configs
        for config in configs:
            workflow = {}
            workflow["Name"] = "_testoperation"+config["Name"]
            api.delete_operation_workflow_request(workflow, stack_resources)
            operation = {}
            operation["Name"] = config["Name"]
            api.delete_operation_request(operation, stack_resources)
    def remove_stage_configs():
        configs = stage_configs+session_stage_configs+udi_stage_configs
        for config in configs:
            workflow = {}
            workflow["Name"] = "_teststage"+config["Name"]
            api.delete_stage_workflow_request(workflow, stack_resources)
            stage = {}
            stage["Name"] = config["Name"]
            api.delete_stage_request(stage, stack_resources)
    def reset_max_concurrent():
        set_max_concurrent_response = api.set_max_concurrent_request(stack_resources, 10)
        # It can take up to one run of the lambda for a configuration change to take effect
        time.sleep(20)
    request.addfinalizer(remove_operation_configs)
    request.addfinalizer(remove_stage_configs)
    request.addfinalizer(reset_max_concurrent)
