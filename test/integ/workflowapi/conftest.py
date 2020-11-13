# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0


import pytest
import boto3
import json
import requests
import logging
import re
import os
from requests_aws4auth import AWS4Auth


# Fixture for retrieving env variables


@pytest.fixture(scope='session')
def testing_env_variables():
    print('Setting variables for tests')
    try:
        test_env_vars = {
            'MEDIA_PATH': os.environ['TEST_MEDIA_PATH'],
            'SAMPLE_IMAGE': os.environ['TEST_IMAGE'],
            'SAMPLE_VIDEO': os.environ['TEST_VIDEO'],
            'SAMPLE_AUDIO': os.environ['TEST_AUDIO'],
            'SAMPLE_TEXT': os.environ['TEST_TEXT'],
            'SAMPLE_JSON': os.environ['TEST_JSON'],
            'SAMPLE_FACE_IMAGE': os.environ['TEST_FACE_IMAGE'],
            'REGION': os.environ['MIE_REGION'],
            'MIE_STACK_NAME': os.environ['MIE_STACK_NAME'],
            'FACE_COLLECTION_ID': os.environ['TEST_FACE_COLLECTION_ID'],
            'ACCESS_KEY': os.environ['AWS_ACCESS_KEY_ID'],
            'SECRET_KEY': os.environ['AWS_SECRET_ACCESS_KEY']
            }

    except KeyError as e:
        logging.error("ERROR: Missing a required environment variable for testing: {variable}".format(variable=e))
        raise Exception(e)
    else:
        return test_env_vars

# Fixture for stack resources


@pytest.fixture(scope='session')
def stack_resources(testing_env_variables):
    print('Validating Stack Resources')
    resources = {}
    # are the workflow api and testing stubs present?

    client = boto3.client('cloudformation', region_name=testing_env_variables['REGION'])
    response = client.describe_stacks(StackName=testing_env_variables['MIE_STACK_NAME'])
    outputs = response['Stacks'][0]['Outputs']

    for output in outputs:
        resources[output["OutputKey"]] = output["OutputValue"]

    assert "WorkflowApiEndpoint" in resources
    assert "TestStack" in resources

    api_endpoint_regex = ".*.execute-api."+testing_env_variables['REGION']+".amazonaws.com/api/.*"

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


# API Class

class API:
    def __init__(self, stack_resources, testing_env_variables):
        self.env_vars = testing_env_variables
        self.stack_resources = stack_resources
        self.auth = AWS4Auth(testing_env_variables['ACCESS_KEY'], testing_env_variables['SECRET_KEY'],
                             testing_env_variables['REGION'], 'execute-api')

    # System methods

    def set_max_concurrent_request(self, max_concurrent):

        headers = {"Content-Type": "application/json"}
        body = {
            "Name":"MaxConcurrentWorkflows",
            "Value": max_concurrent
        }

        print ("POST /system/configuration {}".format(json.dumps(body)))
        set_configuration_response = requests.post(self.stack_resources["WorkflowApiEndpoint"]+'/system/configuration', headers=headers, json=body, verify=False, auth=self.auth)

        return set_configuration_response

    def get_configuration_request(self):
        get_configuration_response = requests.get(self.stack_resources["WorkflowApiEndpoint"]+'/system/configuration', verify=False, auth=self.auth)

        return get_configuration_response

    # Operation methods

    def get_operation_request(self, operation):
        get_operation_response = requests.get(
            self.stack_resources["WorkflowApiEndpoint"] + '/workflow/operation/' + operation, verify=False,
            auth=self.auth)

        return get_operation_response

    def create_operation_request(self, body):
        headers = {"Content-Type": "application/json"}

        # Create the operation

        create_operation_response = requests.post(self.stack_resources["WorkflowApiEndpoint"] + '/workflow/operation',
                                                  headers=headers, json=body, verify=False, auth=self.auth)

        return create_operation_response

    def delete_operation_request(self, operation):
        client = boto3.client(service_name='stepfunctions', region_name=self.env_vars['REGION'])
        delete_operation_response = requests.delete(self.stack_resources["WorkflowApiEndpoint"]+'/workflow/operation/'+operation, verify=False, auth=self.auth)
        return delete_operation_response

    # Workflow Methods

    def create_workflow_request(self, body):
        headers = {"Content-Type": "application/json"}
        print ("POST /workflow {}".format(json.dumps(body)))
        create_workflow_response = requests.post(self.stack_resources["WorkflowApiEndpoint"]+'/workflow', headers=headers, json=body, verify=False, auth=self.auth)

        return create_workflow_response

    def delete_workflow_request(self, workflow):
        headers = {"Content-Type": "application/json"}
        print("DELETE /workflow {}".format(workflow))
        delete_workflow_response = requests.delete(self.stack_resources["WorkflowApiEndpoint"]+'/workflow/'+workflow, verify=False, auth=self.auth, headers=headers)
        return delete_workflow_response

    # Stage Methods

    def create_stage_request(self, body):
        headers = {"Content-Type": "application/json"}
        print ("POST /workflow/stage {}".format(json.dumps(body)))
        create_stage_response = requests.post(self.stack_resources["WorkflowApiEndpoint"]+'/workflow/stage', headers=headers, json=body, verify=False, auth=self.auth)

        return create_stage_response

    def get_stage_request(self, stage):
        get_stage_response = requests.get(self.stack_resources["WorkflowApiEndpoint"]+'/workflow/stage/'+stage, verify=False, auth=self.auth)

        return get_stage_response

    def delete_stage_request(self, stage):
        delete_stage_response = requests.delete(self.stack_resources["WorkflowApiEndpoint"]+'/workflow/stage/'+stage, verify=False, auth=self.auth)

        return delete_stage_response

    def get_workflow_configuration_request(self, workflow):
        headers = {"Content-Type": "application/json"}
        get_workflow_configuration_response = requests.get(self.stack_resources["WorkflowApiEndpoint"]+'/workflow/configuration/'+workflow, verify=False, auth=self.auth, headers=headers)

        return get_workflow_configuration_response

# API Fixture


@pytest.fixture(scope='session')
def workflow_api(stack_resources, testing_env_variables):
    def _gen_api():
        testing_api = API(stack_resources, testing_env_variables)
        return testing_api
    return _gen_api


@pytest.fixture(scope='session')
def api_schema():

    schema_dir = "../../source/workflowapi/chalicelib/apischema"

    schemata = {}
    for f in os.listdir(schema_dir):
        with open(schema_dir+"/"+f) as schema_file:
            schema = json.load(schema_file)
            schemata[schema['title']] = schema

    return schemata


@pytest.fixture(scope='session')
def operation_configs():
    return [
        {"Name":"video-test-async","Input":"Video", "Type":"Async", "Status":"OK"},
        {"Name": "video-test-sync", "Input": "Video", "Type": "Sync", "Status": "OK"}
]


@pytest.fixture(scope='session')
def stage_configs():
    return [
        {"Name": "video-sync", "Input": "Video", "Operations": ["video-test-sync"],
         "ExecutedOperations": [], "Outputs": [], "Status": "OK"},
        {"Name": "video-async", "Input": "Video", "Operations": ["video-test-async"],
         "ExecutedOperations": [], "Outputs": [], "Status": "OK"}
]


@pytest.fixture(scope='session')
def workflow_configs():
    return [
        {"Name": "2-stage-wf", "Input": "Video", "Stages": ["video-sync", "video-async"], "Outputs": [], "Status": "OK"}
]


@pytest.fixture(scope="session", autouse=True)
def cleanup(workflow_api, request, operation_configs, stage_configs, workflow_configs):
    """Cleanup any created resources"""
    api = workflow_api()

    def remove_workflow_configs():
        print('Removing test workflows')
        configs = workflow_configs
        for config in configs:
            resp = api.delete_workflow_request(config["Name"])
            print(resp.json)

    def remove_operation_configs():
        print('Removing test operations')
        configs = operation_configs
        for config in configs:
            resp = api.delete_operation_request(config["Name"])
            print(resp.json)

    def remove_stage_configs():
        print('Removing test stages')
        configs = stage_configs
        for config in configs:
            resp = api.delete_stage_request(config["Name"])
            print(resp.json)

    request.addfinalizer(remove_operation_configs)
    request.addfinalizer(remove_stage_configs)
    request.addfinalizer(remove_workflow_configs)
