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
    # is the workflow api and operator library present?

    client = boto3.client('cloudformation', region_name=testing_env_variables['REGION'])
    response = client.describe_stacks(StackName=testing_env_variables['MIE_STACK_NAME'])
    outputs = response['Stacks'][0]['Outputs']

    for output in outputs:
        resources[output["OutputKey"]] = output["OutputValue"]

    assert "WorkflowApiEndpoint" in resources
    assert "DataplaneApiEndpoint" in resources

    api_endpoint_regex = ".*.execute-api."+testing_env_variables['REGION']+".amazonaws.com/api/.*"

    assert re.match(api_endpoint_regex, resources["WorkflowApiEndpoint"])

    response = client.describe_stacks(StackName=resources["OperatorLibraryStack"])
    outputs = response['Stacks'][0]['Outputs']
    for output in outputs:
        resources[output["OutputKey"]] = output["OutputValue"]

    expected_resources = ['WorkflowApiRestID', 'DataplaneBucket', 'WorkflowCustomResourceArn', 'TestStack', 'MediaInsightsEnginePython38Layer', 'AnalyticsStreamArn', 'DataplaneApiEndpoint', 'WorkflowApiEndpoint', 'DataplaneApiRestID', 'OperatorLibraryStack', 'PollyOperation', 'ContentModerationOperationImage', 'GenericDataLookupOperation', 'comprehendEntitiesOperation', 'FaceSearch', 'FaceSearchOperationImage', 'MediainfoOperationImage', 'TextDetection', 'TextDetectionOperationImage', 'CreateSRTCaptionsOperation', 'ContentModeration', 'WebCaptionsOperation', 'WebToVTTCaptionsOperation', 'PollyWebCaptionsOperation', 'WaitOperation', 'TranslateWebCaptionsOperation', 'CelebRecognition', 'LabelDetection', 'FaceDetection', 'PersonTracking', 'MediaconvertOperation', 'FaceDetectionOperationImage', 'MediainfoOperation', 'ThumbnailOperation', 'TechnicalCueDetection', 'CreateVTTCaptionsOperation', 'CelebrityRecognitionOperationImage', 'TranslateOperation', 'comprehendPhrasesOperation', 'WebToSRTCaptionsOperation', 'shotDetection', 'LabelDetectionOperationImage', 'StackName', "Version", "TranscribeAudioOperation", "TranscribeVideoOperation"]

    assert set(resources.keys()) == set(expected_resources)

    return resources


# This fixture uploads the sample media objects for testing.


@pytest.fixture(scope='session', autouse=True)
def upload_media(testing_env_variables, stack_resources):
    print('Uploading Test Media')
    s3 = boto3.client('s3', region_name=testing_env_variables['REGION'])
    # Upload test media files
    # s3.upload_file(testing_env_variables['MEDIA_PATH'] + testing_env_variables['SAMPLE_TEXT'], stack_resources['DataplaneBucket'], 'upload/' + testing_env_variables['SAMPLE_TEXT'])
    # s3.upload_file(testing_env_variables['MEDIA_PATH'] + testing_env_variables['SAMPLE_JSON'], stack_resources['DataplaneBucket'], 'upload/' + testing_env_variables['SAMPLE_JSON'])
    # s3.upload_file(testing_env_variables['MEDIA_PATH'] + testing_env_variables['SAMPLE_AUDIO'], stack_resources['DataplaneBucket'], 'upload/' + testing_env_variables['SAMPLE_AUDIO'])
    # s3.upload_file(testing_env_variables['MEDIA_PATH'] + testing_env_variables['SAMPLE_IMAGE'], stack_resources['DataplaneBucket'], 'upload/' + testing_env_variables['SAMPLE_IMAGE'])
    # s3.upload_file(testing_env_variables['MEDIA_PATH'] + testing_env_variables['SAMPLE_FACE_IMAGE'], stack_resources['DataplaneBucket'], 'upload/' + testing_env_variables['SAMPLE_FACE_IMAGE'])
    s3.upload_file(testing_env_variables['MEDIA_PATH'] + testing_env_variables['SAMPLE_VIDEO'], stack_resources['DataplaneBucket'], 'upload/' + testing_env_variables['SAMPLE_VIDEO'])
    # Wait for fixture to go out of scope:
    yield upload_media


# Workflow API Class


@pytest.mark.usefixtures("upload_media")
class WorkflowAPI:
    def __init__(self, stack_resources, testing_env_variables):
        self.env_vars = testing_env_variables
        self.stack_resources = stack_resources
        self.auth = AWS4Auth(testing_env_variables['ACCESS_KEY'], testing_env_variables['SECRET_KEY'],
                             testing_env_variables['REGION'], 'execute-api')

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

    def delete_stage_request(self, stage):
        delete_stage_response = requests.delete(self.stack_resources["WorkflowApiEndpoint"]+'/workflow/stage/'+stage, verify=False, auth=self.auth)

        return delete_stage_response

    # Workflow execution methods

    def create_workflow_execution_request(self, body):
        headers = {"Content-Type": "application/json"}
        print("POST /workflow/execution")
        create_workflow_execution_response = requests.post(self.stack_resources["WorkflowApiEndpoint"]+'/workflow/execution', headers=headers, json=body, verify=False, auth=self.auth)

        return create_workflow_execution_response

    def get_workflow_execution_request(self, id):
        print("GET /workflow/execution/{}".format(id))
        get_workflow_execution_response = requests.get(self.stack_resources["WorkflowApiEndpoint"]+'/workflow/execution/' + id, verify=False, auth=self.auth)

        return get_workflow_execution_response

# Workflow API Fixture


@pytest.fixture(scope='session')
def workflow_api(stack_resources, testing_env_variables):
    def _gen_api():
        testing_api = WorkflowAPI(stack_resources, testing_env_variables)
        return testing_api
    return _gen_api


# Dataplane API Class


class DataplaneAPI:
    def __init__(self, stack_resources, testing_env_variables):
        self.env_vars = testing_env_variables
        self.stack_resources = stack_resources
        self.auth = AWS4Auth(testing_env_variables['ACCESS_KEY'], testing_env_variables['SECRET_KEY'],
                             testing_env_variables['REGION'], 'execute-api')

    # Dataplane methods

    def get_single_metadata_field(self, asset_id, operator):
        url = self.stack_resources["DataplaneApiEndpoint"] + 'metadata/' + asset_id + "/" + operator
        headers = {"Content-Type": "application/json"}
        print("GET /metadata/{asset}/{operator}".format(asset=asset_id, operator=operator))
        single_metadata_response = requests.get(url, headers=headers, verify=False, auth=self.auth)
        return single_metadata_response

    def delete_asset(self, asset_id):
        url = self.stack_resources["DataplaneApiEndpoint"] + 'metadata/' + asset_id
        headers = {"Content-Type": "application/json"}
        print("DELETE /metadata/{asset}".format(asset=asset_id))
        delete_asset_response = requests.delete(url, headers=headers, verify=False, auth=self.auth)
        return delete_asset_response

# Dataplane API Fixture


@pytest.fixture(scope='session')
def dataplane_api(stack_resources, testing_env_variables):
    def _gen_api():
        testing_api = DataplaneAPI(stack_resources, testing_env_variables)
        return testing_api
    return _gen_api
