# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

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
import subprocess
import validation

# Fixure for retrieving env variables

@pytest.fixture(scope='session')
def testing_env_variables():
    print('Setting environment variables for tests')
    try:
        test_env_vars = {
            'SAMPLE_IMAGE': os.environ['SAMPLE_IMAGE'],
            'SAMPLE_VIDEO': os.environ['SAMPLE_VIDEO'],
            'SAMPLE_AUDIO': os.environ['SAMPLE_AUDIO'],
            'SAMPLE_TEXT': os.environ['SAMPLE_TEXT'],
            'SAMPLE_JSON': os.environ['SAMPLE_JSON'],
            'SAMPLE_FACE_IMAGE': os.environ['SAMPLE_FACE_IMAGE'],
            'BUCKET_NAME': os.environ['BUCKET_NAME'],
            'REGION': os.environ['REGION'],
            'MIE_STACK_NAME': os.environ['MIE_STACK_NAME'],
            'token': os.environ["MIE_ACCESS_TOKEN"],
            'FACE_COLLECTION_ID': os.environ['FACE_COLLECTION_ID']
            }

    except KeyError as e:
        logging.error("ERROR: Missing a required environment variable for testing: {variable}".format(variable=e))
        raise Exception(e)
    else:
        return test_env_vars

# Fixture for stack resources

@pytest.fixture(scope='session')
def stack_resources(testing_env_variables):
    print('Generating Stack Resources')
    resources = {}
    # are the workflow and dataplane api's present?

    client = boto3.client('cloudformation', region_name=testing_env_variables['REGION'])
    response = client.describe_stacks(StackName=testing_env_variables['MIE_STACK_NAME'])
    outputs = response['Stacks'][0]['Outputs']

    for output in outputs:
        resources[output["OutputKey"]] = output["OutputValue"]

    assert "DataplaneApiEndpoint" in resources
    assert "WorkflowApiEndpoint" in resources
    assert "TestStack" in resources

    api_endpoint_regex = ".*.execute-api."+testing_env_variables['REGION']+".amazonaws.com/api/.*"

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

# This fixture uploads the sample media objects for testing.
@pytest.fixture(scope='session', autouse=True)
def upload_media(testing_env_variables):
    print('Uploading Test Media')
    s3 = boto3.client('s3', region_name=testing_env_variables['REGION'])
    # Upload test media files
    s3.upload_file(testing_env_variables['SAMPLE_TEXT'], testing_env_variables['BUCKET_NAME'], testing_env_variables['SAMPLE_TEXT'])
    s3.upload_file(testing_env_variables['SAMPLE_JSON'], testing_env_variables['BUCKET_NAME'], testing_env_variables['SAMPLE_JSON'])
    s3.upload_file(testing_env_variables['SAMPLE_AUDIO'], testing_env_variables['BUCKET_NAME'], testing_env_variables['SAMPLE_AUDIO'])
    s3.upload_file(testing_env_variables['SAMPLE_IMAGE'], testing_env_variables['BUCKET_NAME'], testing_env_variables['SAMPLE_IMAGE'])
    s3.upload_file(testing_env_variables['SAMPLE_FACE_IMAGE'], testing_env_variables['BUCKET_NAME'], testing_env_variables['SAMPLE_FACE_IMAGE'])
    s3.upload_file(testing_env_variables['SAMPLE_VIDEO'], testing_env_variables['BUCKET_NAME'], testing_env_variables['SAMPLE_VIDEO'])
    # Wait for fixture to go out of scope:
    yield upload_media

# This fixture creates a temporary face collection for testing Face Recognition.
# Returns the name of the face collection.
# When pytest completes this removes said face collection.
@pytest.fixture(scope='session')
def create_face_collection(testing_env_variables):
    print('Creating sample face collection')
    client = boto3.client('rekognition', region_name=testing_env_variables['REGION'])
    try:
        client.delete_collection(
            CollectionId=testing_env_variables['FACE_COLLECTION_ID']
        )
    except ClientError:
        pass
    client.create_collection(
        CollectionId=testing_env_variables['FACE_COLLECTION_ID']
    )
    client.index_faces(
        CollectionId=testing_env_variables['FACE_COLLECTION_ID'],
        Image={
            'S3Object': {
                'Bucket': testing_env_variables['BUCKET_NAME'],
                'Name': testing_env_variables['SAMPLE_FACE_IMAGE']
            }
        }
    )
    yield create_face_collection
    client.delete_collection(
        CollectionId=testing_env_variables['FACE_COLLECTION_ID']
    )

# API Class

@pytest.mark.usefixtures("upload_media")
class API:
    def __init__(self, stack_resources, testing_env_variables):
        self.env_vars = testing_env_variables
        self.stack_resources = stack_resources
    # control plane methods
    def set_max_concurrent_request(self, max_concurrent):

        headers = {"Content-Type": "application/json", "Authorization": self.env_vars['token']}
        body = {
            "Name":"MaxConcurrentWorkflows",
            "Value": max_concurrent
        }

        print ("POST /system/configuration {}".format(json.dumps(body)))
        set_configuration_response = requests.post(self.stack_resources["WorkflowApiEndpoint"]+'/system/configuration', headers=headers, json=body, verify=False)

        return set_configuration_response

    def get_configuration_request(self):
        headers = {"Authorization": self.env_vars['token']}

        get_configuration_response = requests.get(self.stack_resources["WorkflowApiEndpoint"]+'/system/configuration', verify=False, headers=headers)

        return get_configuration_response

    def create_duplicate_operation_request(self, config):

        start_lambda = config["Input"]+config["Type"]+config["Status"]+"Lambda"

        headers = {"Content-Type": "application/json", "Authorization": self.env_vars['token']}
        body = {
            "StartLambdaArn": self.stack_resources[start_lambda],
            "Configuration": {
                "MediaType": config["Input"],
                "Enabled": True
            },
            "StateMachineExecutionRoleArn": self.stack_resources["StepFunctionRole"],
            "Type": config["Type"],
            "Name": config["Name"]
        }

        if (config["Type"] == "Async"):
            monitor_lambda = config["Input"]+config["Type"]+config["Status"]+"MonitorLambda"
            body["MonitorLambdaArn"] = self.stack_resources[monitor_lambda]

        if "OutputMediaType" in config:
            body["Configuration"]["OutputMediaType"] = config["OutputMediaType"]

        if "TestCustomConfig" in config:
            body["Configuration"]["TestCustomConfig"] = config["TestCustomConfig"]

        print ("POST /workflow/operation {}".format(json.dumps(body)))
        create_operation_response = requests.post(self.stack_resources["WorkflowApiEndpoint"]+'/workflow/operation', headers=headers, json=body, verify=False)
        print(create_operation_response.text)
        return create_operation_response


    def get_operation_request(self, operation):
        headers = {"Authorization": self.env_vars['token']}
        get_operation_response = requests.get(self.stack_resources["WorkflowApiEndpoint"]+'/workflow/operation/'+operation["Name"], verify=False, headers=headers)

        return get_operation_response


    def create_operation_request(self, config):

        start_lambda = config["Input"]+config["Type"]+config["Status"]+"Lambda"

        headers = {"Content-Type": "application/json", "Authorization": self.env_vars['token']}
        body = {
            "StartLambdaArn": self.stack_resources[start_lambda],
            "Configuration": {
                "MediaType": config["Input"],
                "Enabled": True
            },
            "StateMachineExecutionRoleArn": self.stack_resources["StepFunctionRole"],
            "Type": config["Type"],
            "Name": config["Name"]
        }

        if (config["Type"] == "Async"):
            monitor_lambda = config["Input"]+config["Type"]+config["Status"]+"MonitorLambda"
            body["MonitorLambdaArn"] = self.stack_resources[monitor_lambda]

        if "OutputMediaType" in config:
            body["Configuration"]["OutputMediaType"] = config["OutputMediaType"]

        if "TestCustomConfig" in config:
            body["Configuration"]["TestCustomConfig"] = config["TestCustomConfig"]

        # Create the operation
        # HTTP 409 or 500 errors can happen if the previous test didn't
        # clean up properly. If we see those then we'll try to clean up
        # and restart a maximum of 10 times.
        client = boto3.client(service_name='stepfunctions', region_name=self.env_vars['REGION'])
        for i in range(1, 10):
            print ("CREATE REQUEST: /workflow/operation {}".format(json.dumps(body)))
            create_operation_response = requests.post(self.stack_resources["WorkflowApiEndpoint"]+'/workflow/operation', headers=headers, json=body, verify=False)
            print ("CREATE RESPONSE: " + create_operation_response.text)
            response_message = create_operation_response.json()
            if create_operation_response.status_code == 409:
                print('Operator already exists: ' + config["Name"])
                print('Deleting operator: ' + config["Name"])
                operation = {"Name": config["Name"]}
                self.delete_operation_request(operation)
                time.sleep(45)
                print('Trying again...')
            elif create_operation_response.status_code == 500 and \
                    (re.match('.*StateMachineAlreadyExists.*', response_message['Message']) is not None or
                     re.match('.*StateMachineDeleting.*', response_message['Message']) is not None):
                arn_pattern = re.compile('(arn:aws:states:.+:stateMachine:[a-zA-Z0-9-_]+)')
                statemachine_arn = arn_pattern.findall(response_message['Message'])[0]
                print('State machine already exists: ' + statemachine_arn)
                print('Deleting state machine: ' + statemachine_arn)
                client.delete_state_machine(stateMachineArn=statemachine_arn)
                # wait up to 15 minutes for StateMachineDeleting
                for x in range(1,90):
                    print('.', end='')
                    time.sleep(10)
                    try:
                        client.describe_state_machine(stateMachineArn=statemachine_arn)
                    except:
                        print('\nDeleted state machine: ' + statemachine_arn)
                        break
            # For all other HTTP status codes, break out of the for loop
            else:
                break
        return create_operation_response

    def get_operation_request(self, operation):
        headers = {"Authorization": self.env_vars['token']}
        get_operation_response = requests.get(self.stack_resources["WorkflowApiEndpoint"]+'/workflow/operation/'+operation["Name"], verify=False, headers=headers)

        return get_operation_response

    def delete_operation_request(self, operation):
        client = boto3.client(service_name='stepfunctions', region_name=self.env_vars['REGION'])
        headers = {"Authorization": self.env_vars['token']}
        delete_operation_response = requests.delete(self.stack_resources["WorkflowApiEndpoint"]+'/workflow/operation/'+operation["Name"], verify=False, headers=headers)
        print("DELETE RESPONSE: " + str(delete_operation_response))
        # Delete will fail if StateMachineDeleting, so retry up to 10 times
        for i in range(1, 10):
            if delete_operation_response.status_code == 500 and (re.match('.*StateMachineDeleting.*', delete_operation_response['Message']) is not None):
                arn_pattern = re.compile('(arn:aws:states:.+:stateMachine:[a-zA-Z0-9-_]+)')
                statemachine_arn = arn_pattern.findall(delete_operation_response['Message'])[0]
                print('Waiting for StateMachineDeleting to complete: ' + statemachine_arn)
                # wait up to 30 minutes
                for x in range(1,180):
                    print('.', end='')
                    time.sleep(10)
                    try:
                        client.describe_state_machine(stateMachineArn=statemachine_arn)
                    except:
                        print('\nStateMachineDeleting is complete: ' + statemachine_arn)
                        break
        return delete_operation_response

    def create_operation_workflow_request(self, operation):

        headers = {"Content-Type": "application/json", "Authorization": self.env_vars['token']}
        body = {
            "Name":"_testoperation"+operation["Name"],
            "StartAt": operation["StageName"],
            "Stages": {
                operation["StageName"]: {
                    "End": True

                }
            }
        }

        print ("POST /workflow {}".format(json.dumps(body)))
        create_workflow_response = requests.post(self.stack_resources["WorkflowApiEndpoint"]+'/workflow', headers=headers, json=body, verify=False)

        return create_workflow_response


    def delete_operation_workflow_request(self, workflow):
        headers = {"Authorization": self.env_vars['token']}
        delete_workflow_response = requests.delete(self.stack_resources["WorkflowApiEndpoint"]+'/workflow/'+workflow["Name"], verify=False, headers=headers)

        return delete_workflow_response

    def create_workflow_execution_request(self, workflow, config):

        headers = {"Content-Type": "application/json", "Authorization": self.env_vars['token']}
        body = {
            "Name": workflow["Name"],
            "Input": {
                "Media": {
                }
            }
        }

        if "WorkflowConfiguration" in config:
            body["Configuration"] = config["WorkflowConfiguration"]
        s3 = boto3.client('s3', region_name=self.env_vars['REGION'])
        if config["Input"] == "Video":
            body["Input"]["Media"]["Video"] = {}
            body["Input"]["Media"]["Video"]["S3Bucket"] = self.env_vars['BUCKET_NAME']
            body["Input"]["Media"]["Video"]["S3Key"] = self.env_vars['SAMPLE_VIDEO']
            s3.upload_file(self.env_vars['SAMPLE_VIDEO'], self.env_vars['BUCKET_NAME'], self.env_vars['SAMPLE_VIDEO'])
        elif config["Input"] == "Audio":
            body["Input"]["Media"]["Audio"] = {}
            body["Input"]["Media"]["Audio"]["S3Bucket"] = self.env_vars['BUCKET_NAME']
            body["Input"]["Media"]["Audio"]["S3Key"] = self.env_vars['SAMPLE_AUDIO']
            s3.upload_file(self.env_vars['SAMPLE_AUDIO'], self.env_vars['BUCKET_NAME'], self.env_vars['SAMPLE_AUDIO'])
        elif config["Input"] == "Image":
            body["Input"]["Media"]["Image"] = {}
            body["Input"]["Media"]["Image"]["S3Bucket"] = self.env_vars['BUCKET_NAME']
            body["Input"]["Media"]["Image"]["S3Key"] = self.env_vars['SAMPLE_IMAGE']
            s3.upload_file(self.env_vars['SAMPLE_IMAGE'], self.env_vars['BUCKET_NAME'], self.env_vars['SAMPLE_IMAGE'])
        elif config["Input"] == "Text":
            body["Input"]["Media"]["Text"] = {}
            body["Input"]["Media"]["Text"]["S3Bucket"] = self.env_vars['BUCKET_NAME']
            body["Input"]["Media"]["Text"]["S3Key"] = self.env_vars['SAMPLE_TEXT']
            s3.upload_file(self.env_vars['SAMPLE_TEXT'], self.env_vars['BUCKET_NAME'], self.env_vars['SAMPLE_TEXT'])

        print ("POST /workflow/execution {}".format(json.dumps(body)))

        create_workflow_execution_response = requests.post(self.stack_resources["WorkflowApiEndpoint"]+'/workflow/execution', headers=headers, json=body, verify=False)

        return create_workflow_execution_response

    def wait_for_workflow_execution(self, workflow_execution, wait_seconds):
        headers = {"Authorization": self.env_vars['token']}

        # disable unsigned HTTPS certificate warnings
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        workflow_id = workflow_execution['Id']

        # It might take a few seconds for the step function to start, so we'll try to get the execution arn a few times
        # before giving up
        retries=0
        # FIXME retry_limit = ceil(wait_seconds/5)
        retry_limit = 60
        while(retries<retry_limit):
            retries+=1
            print("Checking workflow execution status for workflow {}".format(workflow_id))
            workflow_execution_response = requests.get(self.stack_resources["WorkflowApiEndpoint"]+'/workflow/execution/'+workflow_id, verify=False, headers=headers)
            workflow_execution = workflow_execution_response.json()
            assert workflow_execution_response.status_code == 200
            if workflow_execution["Status"] in ["Complete", "Error"]:
                break
            time.sleep(5)

        return workflow_execution

    def create_stage_request(self, config):

        headers = {"Content-Type": "application/json", "Authorization": self.env_vars['token']}
        body = {
            "Name": config["Name"],
            "Operations": config["Operations"]
        }

        print ("POST /workflow/stage {}".format(json.dumps(body)))
        create_stage_response = requests.post(self.stack_resources["WorkflowApiEndpoint"]+'/workflow/stage', headers=headers, json=body, verify=False)

        return create_stage_response

    def get_stage_request(self, stage):
        headers = {"Authorization": self.env_vars['token']}

        get_stage_response = requests.get(self.stack_resources["WorkflowApiEndpoint"]+'/workflow/stage/'+stage["Name"], verify=False, headers=headers)

        return get_stage_response

    def delete_stage_request(self, stage):
        headers = {"Authorization": self.env_vars['token']}

        delete_stage_response = requests.delete(self.stack_resources["WorkflowApiEndpoint"]+'/workflow/stage/'+stage["Name"], verify=False, headers=headers)

        return delete_stage_response

    def create_stage_workflow_request(self, stage):

        headers = {"Content-Type": "application/json", "Authorization": self.env_vars['token']}
        body = {
            "Name":"_teststage"+stage["Name"],
            "StartAt": stage["Name"],
            "Stages": {
                stage["Name"]: {
                    "End": True

                }
            }
        }

        print ("POST /workflow {}".format(json.dumps(body)))
        create_workflow_response = requests.post(self.stack_resources["WorkflowApiEndpoint"]+'/workflow', headers=headers, json=body, verify=False)

        return create_workflow_response

    def create_workflow_request(self, workflow_config):

        stages = workflow_config["Stages"]
        headers = {"Content-Type": "application/json", "Authorization": self.env_vars['token']}
        body = {
            "Name": workflow_config["Name"],
            "StartAt": stages[0],
        }

        workflow_stages = {}
        num_stages = len(stages)
        i = 1
        for stage in stages:
            if i == num_stages:
                workflow_stages[stage] = {
                    "End": True
                    }
            else:
                workflow_stages[stage] = {
                    "Next": stages[i]
                    }
            i = i + 1

        body["Stages"] = workflow_stages

        print ("POST /workflow {}".format(json.dumps(body)))
        create_workflow_response = requests.post(self.stack_resources["WorkflowApiEndpoint"]+'/workflow', headers=headers, json=body, verify=False)

        return create_workflow_response

    def get_workflow_configuration_request(self, workflow):
        headers = {"Authorization": self.env_vars['token']}

        get_workflow_configuration_response = requests.get(self.stack_resources["WorkflowApiEndpoint"]+'/workflow/configuration/'+workflow["Name"], verify=False, headers=headers)

        return get_workflow_configuration_response

    def delete_stage_workflow_request(self, workflow):
        headers = {"Authorization": self.env_vars['token']}

        delete_workflow_response = requests.delete(self.stack_resources["WorkflowApiEndpoint"]+'/workflow/'+workflow["Name"], verify=False, headers=headers)

        return delete_workflow_response

    # dataplane methods

    def create_asset(self):
        headers = {"Content-Type": "application/json", "Authorization": self.env_vars['token']}
        body = {
            "Input": {
                "S3Bucket": self.env_vars['BUCKET_NAME'],
                "S3Key": self.env_vars['SAMPLE_IMAGE']
            }
        }

        print("POST /create")
        create_asset_response = requests.post(self.stack_resources["DataplaneApiEndpoint"] + '/create', headers=headers, json=body, verify=False)
        return create_asset_response

    def post_metadata(self, asset_id, metadata, paginate=False, end=False):
        if paginate is True and end is True:
            url = self.stack_resources["DataplaneApiEndpoint"] + 'metadata/' + asset_id + "?paginated=true&end=true"
        elif paginate is True and end is False:
            url = self.stack_resources["DataplaneApiEndpoint"] + 'metadata/' + asset_id + "?paginated=true"
        else:
            url = self.stack_resources["DataplaneApiEndpoint"] + 'metadata/' + asset_id

        headers = {"Content-Type": "application/json", "Authorization": self.env_vars['token']}
        body = metadata
        print("POST /metadata/{asset}".format(asset=asset_id))
        nonpaginated_metadata_response = requests.post(url, headers=headers, json=body, verify=False)
        return nonpaginated_metadata_response

    def get_all_metadata(self, asset_id, cursor=None):
        if cursor is None:
            url = self.stack_resources["DataplaneApiEndpoint"] + 'metadata/' + asset_id
        else:
            url = self.stack_resources["DataplaneApiEndpoint"] + 'metadata/' + asset_id + "?cursor=" + cursor
        headers = {"Content-Type": "application/json", "Authorization": self.env_vars['token']}
        print("GET /metadata/{asset}".format(asset=asset_id))
        metadata_response = requests.get(url, headers=headers, verify=False)
        return metadata_response


    def get_single_metadata_field(self, asset_id, operator):
        metadata_field = operator["OperatorName"]
        url = self.stack_resources["DataplaneApiEndpoint"] + 'metadata/' + asset_id + "/" + metadata_field
        headers = {"Content-Type": "application/json", "Authorization": self.env_vars['token']}
        print("GET /metadata/{asset}/{operator}".format(asset=asset_id, operator=operator["OperatorName"]))
        single_metadata_response = requests.get(url, headers=headers, verify=False)
        return single_metadata_response

    def delete_single_metadata_field(self, asset_id, operator):
        metadata_field = operator["OperatorName"]
        url = self.stack_resources["DataplaneApiEndpoint"] + 'metadata/' + asset_id + "/" + metadata_field
        headers = {"Content-Type": "application/json", "Authorization": self.env_vars['token']}
        print("DELETE /metadata/{asset}/{operator}".format(asset=asset_id, operator=operator["OperatorName"]))
        delete_single_metadata_response = requests.delete(url, headers=headers, verify=False)
        return delete_single_metadata_response

    def delete_asset(self, asset_id):
        url = self.stack_resources["DataplaneApiEndpoint"] + 'metadata/' + asset_id
        headers = {"Content-Type": "application/json", "Authorization": self.env_vars['token']}
        print("DELETE /metadata/{asset}".format(asset=asset_id))
        delete_asset_response = requests.delete(url, headers=headers, verify=False)
        return delete_asset_response

# API Fixture

@pytest.fixture(scope='session')
def api(stack_resources, testing_env_variables):
    def _gen_api():
        print('Generating an API object for testing')
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

@pytest.fixture(scope='session', autouse=True)
def operations(api, session_operation_configs, api_schema):
    api = api()
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    print("Creating test operations")
    for config in session_operation_configs:

        print("\nOPERATION CONFIGURATION: {}".format(config))

        # Create the operation
        create_operation_response = api.create_operation_request(config)
        operation = create_operation_response.json()
        assert create_operation_response.status_code == 200
        validation.schema(operation, api_schema["create_operation_response"])

    # yield session_operation_configs

    # for config in session_operation_configs:
    #     #Delete the operation
    #     operation = {}
    #     operation["Name"] = config["Name"]

    #     delete_operation_response = api.delete_operation_request(operation)
    #     assert delete_operation_response.status_code == 200

@pytest.fixture(scope='session', autouse=True)
def stages(api, operations, session_stage_configs, api_schema):
    api = api()
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    print("Creating test stages")
    for config in session_stage_configs:

        print("\nSTAGE CONFIGURATION: {}".format(config))

        # Create the stage
        create_stage_response = api.create_stage_request(config)
        stage = create_stage_response.json()

        assert create_stage_response.status_code == 200
        validation.schema(stage, api_schema["create_stage_response"])

    # yield session_stage_configs

    # for config in session_stage_configs:
    #     #Delete the stage
    #     stage = {}
    #     stage["Name"] = config["Name"]

    #     delete_stage_response = api.delete_stage_request(stage)
    #     assert delete_stage_response.status_code == 200

@pytest.fixture(scope='session')
def operation_configs():
    return [
        {"Name":"video-test-sync-a","Input":"Video", "Type":"Sync", "Status":"OK"},
        {"Name":"audio-test-async-a","Input":"Audio", "Type":"Async", "Status":"OK", "TestCustomConfig":"audio-test-async-a"},
        {"Name":"text-test-sync-a","Input":"Text", "Type":"Async", "Status":"OK"},
        {"Name":"video-test-sync-fail-a","Input":"Video", "Type":"Sync", "Status":"Fail"}
]

@pytest.fixture(scope='session')
def stage_configs():
    return [
        {"Name":"fail-op-1-a","Input":"Video", "Operations": ["video-test-sync-fail-as", "audio-test-async-as"], "ExecutedOperations": [], "Outputs":[], "Status":"Fail"},
        {"Name":"fail-op-2-a","Input":"Video", "Operations": ["video-test-sync-as", "video-test-sync-fail-as"], "ExecutedOperations": ["video-test-sync-as"], "Outputs":[], "Status":"Fail"},
        {"Name":"2-op-a","Input":"Audio", "Operations": ["audio-test-async-as", "text-test-sync-as"], "ExecutedOperations": ["audio-test-async-as"], "Outputs":["Audio"], "Status":"OK"},
        {"Name":"many-op-a","Input":"Audio", "Operations": ["audio-test-async-as", "text-test-sync-as", "video-test-sync-as"], "ExecutedOperations": ["audio-test-async-as"], "Outputs":["Audio"], "Status":"OK"},
        {"Name":"no-op","Input":"Audio", "Operations": ["text-test-sync-as", "video-test-sync-as"], "ExecutedOperations": [], "Outputs":[], "Status":"OK"}
]

@pytest.fixture(scope='session')
def workflow_configs():
    return [
        {"Name":"first-stage-fail","Input":"Audio", "Stages": ["fail-op-2-as", "2-op-as"], "Outputs":[], "Status":"Fail"},
        {"Name":"last-stage-fail","Input":"Audio", "Stages": ["many-op-as", "2-op-as", "fail-op-2-as"], "Outputs":["Audio"], "Status":"Fail"},
        {"Name":"2-stage","Input":"Audio", "Stages": ["many-op-as", "2-op-as"], "Outputs":["Audio"], "Status":"OK"}
]

@pytest.fixture(scope="session", autouse=True)
def cleanup(api, request, session_operation_configs, operation_configs, session_stage_configs, stage_configs, workflow_configs):
    """Cleanup any created resources"""
    api = api()
    def remove_workflow_configs():
        print('Removing test workflows')
        configs = workflow_configs
        for config in configs:
            workflow = {}
            workflow["Name"] = config["Name"]
            api.delete_operation_workflow_request(workflow)
    def remove_operation_configs():
        print('Removing test operations')
        configs = operation_configs+session_operation_configs
        for config in configs:
            workflow = {}
            workflow["Name"] = "_testoperation"+config["Name"]
            api.delete_operation_workflow_request(workflow)
            operation = {}
            operation["Name"] = config["Name"]
            api.delete_operation_request(operation)
    def remove_stage_configs():
        print('Removing test stages')
        configs = stage_configs+session_stage_configs
        for config in configs:
            workflow = {}
            workflow["Name"] = "_teststage"+config["Name"]
            api.delete_stage_workflow_request(workflow)
            stage = {}
            stage["Name"] = config["Name"]
            api.delete_stage_request(stage)
    def reset_max_concurrent():
        print('Resetting max concurrency')
        set_max_concurrent_response = api.set_max_concurrent_request(10)
        # It can take up to one run of the lambda for a configuration change to take effect
        time.sleep(20)
    request.addfinalizer(remove_operation_configs)
    request.addfinalizer(remove_stage_configs)
    request.addfinalizer(reset_max_concurrent)
    request.addfinalizer(remove_workflow_configs)
