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
import subprocess


# This fixture obtains, validates, and returns endpoints for the workflow and dataplane APIs
def test_api_endpoints(testing_env_variables):
    # are the workflow and dataplane api's present?
    dataplane_api_endpoint=""
    workflow_api_endpoint=""
    client = boto3.client('cloudformation', region_name=testing_env_variables['REGION'])
    response = client.describe_stacks(StackName=testing_env_variables['MIE_STACK_NAME'])
    outputs = response['Stacks'][0]['Outputs']
    for output in outputs:
        if output["OutputKey"] == "DataplaneApiEndpoint":
            dataplane_api_endpoint = output["OutputValue"]
        if output["OutputKey"] == "WorkflowApiEndpoint":
            workflow_api_endpoint = output["OutputValue"]
    api_endpoint_regex = ".*.execute-api."+testing_env_variables['REGION']+".amazonaws.com/api/.*"
    assert re.match(api_endpoint_regex, dataplane_api_endpoint)
    assert re.match(api_endpoint_regex, workflow_api_endpoint)
    return {"dataplane_api_endpoint": dataplane_api_endpoint, "workflow_api_endpoint": workflow_api_endpoint}


# This fixture is used for testing the following workflow configurations:
#   1. Rekognition Workflow for images with all operators disabled
#   2. Rekognition Workflow for images with one operator enabled
#   3. Rekognition Workflow for images with all operators enabled
#   4. Rekognition Workflow for videos with all operators enabled
# Returns an array of values for the parameterized test.
def rek_workflow_configs(testing_env_variables):
    return [
        # Test image processing workflow with all operators disabled
        ('{"Name":"ImageWorkflow","Configuration": {"ValidationStage": {"MediainfoImage": {"Enabled": true}},"RekognitionStage": {"faceSearchImage": {"MediaType": "Image","Enabled": false, "CollectionId": "' + testing_env_variables['FACE_COLLECTION_ID'] + '"},"labelDetectionImage": {"MediaType": "Image","Enabled": false},"celebrityRecognitionImage": {"MediaType": "Image","Enabled": false},"contentModerationImage": {"MediaType": "Image","Enabled": false},"faceDetectionImage": {"MediaType": "Image","Enabled": false}}},"Input": {"Media": {"Image": {"S3Bucket":"' + testing_env_variables['BUCKET_NAME'] +'","S3Key":"' + testing_env_variables['SAMPLE_IMAGE'] + '"}}}}'),
        # Test image processing workflow with all operators enabled
        ('{"Name":"ImageWorkflow","Configuration": {"ValidationStage": {"MediainfoImage": {"Enabled": true}},"RekognitionStage": {"faceSearchImage": {"MediaType": "Image","Enabled": true, "CollectionId": "' + testing_env_variables['FACE_COLLECTION_ID'] + '"},"labelDetectionImage": {"MediaType": "Image","Enabled": true},"celebrityRecognitionImage": {"MediaType": "Image","Enabled": true},"contentModerationImage": {"MediaType": "Image","Enabled": true},"faceDetectionImage": {"MediaType": "Image","Enabled": true}}},"Input": {"Media": {"Image": {"S3Bucket":"' + testing_env_variables['BUCKET_NAME'] +'","S3Key":"' + testing_env_variables['SAMPLE_IMAGE'] + '"}}}}'),
        # Test video processing workflow with all operators disabled
        ('{"Name":"MieCompleteWorkflow","Configuration":{"defaultPrelimVideoStage":{"Thumbnail":{"ThumbnailPosition":"1","Enabled":true},"Mediainfo":{"Enabled":true}},"defaultVideoStage":{"faceDetection":{"Enabled":false},"celebrityRecognition":{"Enabled":false},"labelDetection":{"Enabled":false},"Mediaconvert":{"Enabled":false},"contentModeration":{"Enabled":false},"faceSearch":{"Enabled":false,"CollectionId":"undefined"},"GenericDataLookup":{"Enabled":false,"Bucket":"mie01-dataplane-5wwcvkog5khj","Key":"undefined"}},"defaultAudioStage":{"Transcribe":{"Enabled":false,"TranscribeLanguage":"en-US"}},"defaultTextStage":{"Translate":{"Enabled":false,"SourceLanguageCode":"en","TargetLanguageCode":"es"},"ComprehendEntities":{"Enabled":false},"ComprehendKeyPhrases":{"Enabled":false}},"defaultTextSynthesisStage":{"Polly":{"Enabled":false}}},"Input":{"Media":{"Video":{"S3Bucket":"' + testing_env_variables['BUCKET_NAME'] +'","S3Key":"' + testing_env_variables['SAMPLE_VIDEO'] + '"}}}}'),
        # Test generic data processing operator separately since it's not part of AWS Rekognition
        ('{"Name":"MieCompleteWorkflow","Configuration":{"defaultPrelimVideoStage": {"Thumbnail": {"ThumbnailPosition": "1","Enabled": true},"Mediainfo": {"Enabled": true}},"defaultVideoStage":{"faceDetection":{"Enabled":false},"celebrityRecognition":{"Enabled":false},"GenericDataLookup":{"Enabled":true, "Bucket":"' + testing_env_variables['BUCKET_NAME'] + '","Key":"' + testing_env_variables['SAMPLE_JSON'] + '"},"labelDetection":{"Enabled":false},"personTracking":{"Enabled":false},"Mediaconvert":{"Enabled":false},"contentModeration":{"Enabled":false},"faceSearch":{"Enabled":false}}},"Input": {"Media": {"Video": {"S3Bucket":"' + testing_env_variables['BUCKET_NAME'] +'","S3Key":"' + testing_env_variables['SAMPLE_VIDEO'] + '"}}}}'),
        # Test video processing workflow with all operators enabled
        ('{"Name":"MieCompleteWorkflow","Configuration": {"defaultPrelimVideoStage": {"Thumbnail": {"ThumbnailPosition": "1","Enabled": true},"Mediainfo": {"Enabled": true}},"defaultVideoStage": {"GenericDataLookup":{"Enabled":false},"faceSearch": {"CollectionId":"'+ testing_env_variables['FACE_COLLECTION_ID'] + '","MediaType": "Video","Enabled": true},"labelDetection": {"MediaType": "Video","Enabled": true},"celebrityRecognition": {"MediaType": "Video","Enabled": true},"contentModeration": {"MediaType": "Video","Enabled": true},"faceDetection": {"MediaType": "Video","Enabled": true},"personTracking": {"MediaType": "Video","Enabled": true}}},"Input": {"Media": {"Video": {"S3Bucket":"' + testing_env_variables['BUCKET_NAME'] +'","S3Key":"' + testing_env_variables['SAMPLE_VIDEO'] + '"}}}}'),
    ]

# Parameterized test for Rekognition workflow
def test_rekognition_workflow_execution(create_face_collection, upload_media, testing_env_variables):
    print("Running parameterized test for Rekognition workflow.")
    # disable unsigned HTTPS certificate warnings
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    workflow_configs = rek_workflow_configs(testing_env_variables)
    api_endpoints = test_api_endpoints(testing_env_variables)
    for workflow_config in workflow_configs:
        # Start the workflow
        print('------------------------------------------')
        print('uploading test media')
        s3 = boto3.client('s3', region_name=testing_env_variables['REGION'])
        s3.upload_file(testing_env_variables['SAMPLE_IMAGE'], testing_env_variables['BUCKET_NAME'], testing_env_variables['SAMPLE_IMAGE'])
        s3.upload_file(testing_env_variables['SAMPLE_VIDEO'], testing_env_variables['BUCKET_NAME'], testing_env_variables['SAMPLE_VIDEO'])
        workflow_api_endpoint = api_endpoints["workflow_api_endpoint"]
        headers = {"Content-Type": "application/json", "Authorization": testing_env_variables['token']}
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
            arn_regex='arn:aws:([a-zA-Z-]*):'+testing_env_variables['REGION']+':(\d*):execution:([\w-]*):([\w-]*)'
            assert re.match(arn_regex, step_function_execution_arn)

            # Wait for the Step Function to complete
            print("Workflow is running...")
            client = boto3.client('stepfunctions', region_name=testing_env_variables['REGION'])
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
