# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

###############################################################################
# White box testing for the base Media Insights Engine stack and Rekognition
# workflow.
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
import requests
import urllib3
import logging
from botocore.exceptions import ClientError
import re
import os
import time

# DEFAULT test environment.
# Override these with environment variables at runtime.
REGION = 'us-west-2'
SAMPLE_IMAGE = "sample-image.jpg"
SAMPLE_VIDEO = "sample-video.mp4"
SAMPLE_AUDIO = "sample-audio.m4a"
SAMPLE_TEXT = "sample-text.txt"
SAMPLE_FACE_IMAGE = "sample-face.jpg"
BUCKET_NAME = "mie-testing-bucket-" + str(int(round(time.time())))
MIE_STACK_NAME = ""
FACE_COLLECTION_ID = "temporary_face_collection"

# override default test env with the vars specified in pytest.ini
if 'REGION' in os.environ:
    REGION = str(os.environ['REGION'])
if 'SAMPLE_IMAGE' in os.environ:
    SAMPLE_IMAGE = str(os.environ['SAMPLE_IMAGE'])
if 'SAMPLE_VIDEO' in os.environ:
    SAMPLE_VIDEO = str(os.environ['SAMPLE_VIDEO'])
if 'SAMPLE_AUDIO' in os.environ:
    SAMPLE_AUDIO = str(os.environ['SAMPLE_AUDIO'])
if 'SAMPLE_TEXT' in os.environ:
    SAMPLE_TEXT = str(os.environ['SAMPLE_TEXT'])
if 'SAMPLE_FACE_IMAGE' in os.environ:
    SAMPLE_FACE_IMAGE = str(os.environ['SAMPLE_FACE_IMAGE'])
if 'BUCKET_NAME' in os.environ:
    BUCKET_NAME = str(os.environ['BUCKET_NAME'])
if 'MIE_STACK_NAME' in os.environ:
    MIE_STACK_NAME = str(os.environ['MIE_STACK_NAME'])
else:
    print("ERROR: Stack name must be in MIE_STACK_NAME environment variable.")
    logging.error("ERROR: Stack name must be in MIE_STACK_NAME environment variable.")
    exit(1)
if 'FACE_COLLECTION_ID' in os.environ:
    FACE_COLLECTION_ID = str(os.environ['FACE_COLLECTION_ID'])

print("ENVIRONMENT VARIABLES:")
print("\tREGION: "+REGION)
print("\tSAMPLE_IMAGE: "+SAMPLE_IMAGE)
print("\tSAMPLE_VIDEO: "+SAMPLE_VIDEO)
print("\tSAMPLE_AUDIO: "+SAMPLE_AUDIO)
print("\tSAMPLE_TEXT: "+SAMPLE_TEXT)
print("\tSAMPLE_FACE_IMAGE: "+SAMPLE_FACE_IMAGE)
print("\tFACE_COLLECTION_ID: "+FACE_COLLECTION_ID)
print("\tBUCKET_NAME: "+BUCKET_NAME)
print("\tMIE_STACK_NAME: "+MIE_STACK_NAME)

# This fixture creates a temporary S3 bucket with media objects for testing.
# When pytest completes this removes said bucket and media objects.
@pytest.fixture(scope='session')
def uploaded_media():
    # Create the bucket
    s3 = boto3.client('s3', region_name=REGION)
    try:
        if REGION != 'us-east-1':
          s3.create_bucket(Bucket=BUCKET_NAME, CreateBucketConfiguration={'LocationConstraint': REGION})
        else:
          # This workaround is needed to avoid an InvalidLocationConstraint error when region is us-east-1
          # see: https://github.com/boto/boto3/issues/125
          import subprocess
          subprocess.run(["aws", "s3", "mb", "s3://"+BUCKET_NAME, "--region", REGION])
    except ClientError as e:
        logging.error(e)
        return False
    # Upload test media files
    s3.upload_file(SAMPLE_TEXT, BUCKET_NAME, SAMPLE_TEXT)
    s3.upload_file(SAMPLE_AUDIO, BUCKET_NAME, SAMPLE_AUDIO)
    s3.upload_file(SAMPLE_IMAGE, BUCKET_NAME, SAMPLE_IMAGE)
    s3.upload_file(SAMPLE_FACE_IMAGE, BUCKET_NAME, SAMPLE_FACE_IMAGE)
    s3.upload_file(SAMPLE_VIDEO, BUCKET_NAME, SAMPLE_VIDEO)
    # Wait for fixture to go out of scope:
    yield uploaded_media
    # Delete the bucket
    s3 = boto3.resource('s3', region_name=REGION)
    bucket = s3.Bucket(BUCKET_NAME)
    for key in bucket.objects.all():
        key.delete()
    bucket.delete()


# This fixture creates a temporary face collection for testing Face Recognition.
# Returns the name of the face collection.
# When pytest completes this removes said face collection.
@pytest.fixture(scope='session')
def create_face_collection():
    client = boto3.client('rekognition', region_name=REGION)
    try:
        client.delete_collection(
            CollectionId=FACE_COLLECTION_ID
        )
    except ClientError:
        pass
    client.create_collection(
        CollectionId=FACE_COLLECTION_ID
    )
    client.index_faces(
        CollectionId=FACE_COLLECTION_ID,
        Image={
            'S3Object': {
                'Bucket': BUCKET_NAME,
                'Name': SAMPLE_FACE_IMAGE
            }
        }
    )
    yield create_face_collection
    client.delete_collection(
        CollectionId=FACE_COLLECTION_ID
    )

# This fixture obtains, validates, and returns endpoints for the workflow and dataplane APIs
@pytest.fixture(scope='session')
def test_api_endpoints():
    # are the workflow and dataplane api's present?
    dataplane_api_endpoint=""
    workflow_api_endpoint=""
    client = boto3.client('cloudformation', region_name=REGION)
    response = client.describe_stacks(StackName=MIE_STACK_NAME)
    outputs = response['Stacks'][0]['Outputs']
    for output in outputs:
        if output["OutputKey"] == "DataplaneApiEndpoint":
            dataplane_api_endpoint = output["OutputValue"]
        if output["OutputKey"] == "WorkflowApiEndpoint":
            workflow_api_endpoint = output["OutputValue"]
    api_endpoint_regex = ".*.execute-api."+REGION+".amazonaws.com/api/.*"
    assert re.match(api_endpoint_regex, dataplane_api_endpoint)
    assert re.match(api_endpoint_regex, workflow_api_endpoint)
    return {"dataplane_api_endpoint": dataplane_api_endpoint, "workflow_api_endpoint": workflow_api_endpoint}


# This fixture is used for testing the following workflow configurations:
#   1. Rekognition Workflow for images with all operators disabled
#   2. Rekognition Workflow for images with one operator enabled
#   3. Rekognition Workflow for images with all operators enabled
#   4. Rekognition Workflow for videos with all operators enabled
# Returns an array of values for the parameterized test.
@pytest.fixture
def workflow_configs(create_face_collection):
    return [
        ('{"Name":"ParallelRekognitionWorkflowImage","Configuration": {"parallelRekognitionStageImage": {"faceSearchImage": {"MediaType": "Image","Enabled": false, "CollectionId": "' + FACE_COLLECTION_ID + '"},"labelDetectionImage": {"MediaType": "Image","Enabled": false},"celebrityRecognitionImage": {"MediaType": "Image","Enabled": false},"contentModerationImage": {"MediaType": "Image","Enabled": false},"faceDetectionImage": {"MediaType": "Image","Enabled": false}}},"Input": {"Media": {"Image": {"S3Bucket":"' + BUCKET_NAME +'","S3Key":"' + SAMPLE_IMAGE + '"}}}}'),
        ('{"Name":"ParallelRekognitionWorkflowImage","Configuration": {"parallelRekognitionStageImage": {"faceSearchImage": {"MediaType": "Image","Enabled": true, "CollectionId": "' + FACE_COLLECTION_ID + '"},"labelDetectionImage": {"MediaType": "Image","Enabled": true},"celebrityRecognitionImage": {"MediaType": "Image","Enabled": true},"contentModerationImage": {"MediaType": "Image","Enabled": true},"faceDetectionImage": {"MediaType": "Image","Enabled": true}}},"Input": {"Media": {"Image": {"S3Bucket":"' + BUCKET_NAME +'","S3Key":"' + SAMPLE_IMAGE + '"}}}}'),
        ('{"Name":"ParallelRekognitionWorkflow","Configuration": {"parallelRekognitionStage": {"faceSearch": {"CollectionId":"'+ FACE_COLLECTION_ID + '","MediaType": "Video","Enabled": true},"labelDetection": {"MediaType": "Video","Enabled": true},"celebrityRecognition": {"MediaType": "Video","Enabled": true},"contentModeration": {"MediaType": "Video","Enabled": true},"faceDetection": {"MediaType": "Video","Enabled": true},"personTracking": {"MediaType": "Video","Enabled": true}}},"Input": {"Media": {"Video": {"S3Bucket":"' + BUCKET_NAME +'","S3Key":"' + SAMPLE_VIDEO + '"}}}}'),
    ]

# Parameterized test for Rekognition workflow
def test_rekognition_workflow_execution(uploaded_media, test_api_endpoints, workflow_configs):
    print("Running parameterized test for Rekognition workflow.")
    # disable unsigned HTTPS certificate warnings
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    for workflow_config in workflow_configs:
        # Start the workflow
        print('------------------------------------------')
        print('Test config: ' + workflow_config)
        workflow_api_endpoint = test_api_endpoints["workflow_api_endpoint"]
        headers = {"Content-Type": "application/json"}
        start_request = requests.post(workflow_api_endpoint+'/workflow/execution', headers=headers, data=workflow_config, verify=False)
        assert start_request.status_code == 200
        assert start_request.json()['Status'] == 'Queued'
        workflow_name = json.loads(workflow_config)["Name"]
        for stage_name in start_request.json()["Workflow"]["Stages"].keys():
            workflow_execution_id = start_request.json()["Workflow"]["Stages"][stage_name]["WorkflowExecutionId"]
            # workflow_execution_id = "835c92c8-59ec-4d2f-9eda-9140839dfc6c"
            # It might take a few seconds for the step function to start, so we'll try to get the execution arn a few times
            # before giving up
            retries=0
            retry_limit=4
            print("Starting workflow")
            while(retries<retry_limit):
                workflow_execution = requests.get(workflow_api_endpoint+'/workflow/execution/'+workflow_execution_id, headers=headers, verify=False)
                assert workflow_execution.status_code == 200
                if "StateMachineExecutionArn" in workflow_execution.json():
                    break
                else:
                    time.sleep(2)
                    retries=retries+1
                    print("sleep "+str(retries)+"/"+str(retry_limit))
            try:
                assert "StateMachineExecutionArn" in workflow_execution.json()
            except AssertionError:
                print("ERROR: Missing StateMachineExecutionArn in Workflow output. Did it start?")
                print(json.dumps(workflow_execution.json(), indent=2))

            # Validate the StateMachineExecutionArn
            step_function_execution_arn = workflow_execution.json()['StateMachineExecutionArn']
            asset_id = workflow_execution.json()['Workflow']['Stages'][stage_name]['AssetId']
            arn_regex='arn:aws:([a-zA-Z-]*):'+REGION+':(\d*):execution:([\w-]*):([\w-]*)'
            assert re.match(arn_regex, step_function_execution_arn)

            # Wait for the Step Function to complete
            print("Workflow is running...")
            client = boto3.client('stepfunctions', region_name=REGION)
            step_function_execution_status = client.describe_execution(executionArn=step_function_execution_arn)['status']
            while step_function_execution_status=="RUNNING":
                time.sleep(3)
                step_function_execution_status = client.describe_execution(executionArn=step_function_execution_arn)['status']

            # Validate that the Step Function completed successfully
            assert step_function_execution_status == "SUCCEEDED"

            # Validate that the workflow status is Complete
            workflow_execution = requests.get(workflow_api_endpoint+'/workflow/execution/'+workflow_execution_id, headers=headers, verify=False)
            assert workflow_execution.status_code == 200
            assert workflow_execution.json()['Status'] == "Complete"

            # Validate that every operator in the workflow is Complete
            for operator in workflow_execution.json()['Workflow']['Stages'][stage_name]['Outputs']:
                assert (operator['Status'] == "Complete" or operator['Status'] == "Skipped")

            # # Validate that a new record has been to dynamodb for the generated asset_id
            # dataplane_api_endpoint=test_api_endpoints["dataplane_api_endpoint"]
            # dataplane_request = requests.get(dataplane_api_endpoint+'/metadata/'+asset_id, headers=headers, verify=False)
            # assert dataplane_request.status_code == 200
            #
            # # Validate dynamoDB add
            # test_data = {
            #     "OperatorName": "testOperator",
            #     "Results": {"test_metric":"test_value"},
            #     "WorkflowId": workflow_execution_id
            #     }
            #
            # dataplane_request = requests.post(dataplane_api_endpoint+'/metadata/'+asset_id, headers=headers, data=json.dumps(test_data), verify=False)
            # assert dataplane_request.status_code == 200
            #
            # # Validate DynamoDB read
            # dataplane_request = requests.get(dataplane_api_endpoint+'/metadata/'+asset_id, headers=headers, verify=False)
            # assert dataplane_request.status_code == 200
            # assert re.match('.*"testOperator":".*', dataplane_request.text)

            print('Test complete')


#TODO: dynamoDB remove asset
