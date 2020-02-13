# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

##############################################################################
# Integration testing for the MIE Instant Translate Workflow
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


def test_instant_translate(api, testing_env_variables, stack_resources):
    api = api()
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    # InstantTranslate workflow must be deployed
    
    print("Testing InstantTranslate workflow.  BUCKET_NAME = "+testing_env_variables['BUCKET_NAME']+" SAMPLE_VIDEO = "+ testing_env_variables['SAMPLE_VIDEO'])

    body = {
        "Name":"InstantTranslateWorkflow",
        "Input": {
            "Media": {
                "Video": {
                    "S3Bucket": testing_env_variables['BUCKET_NAME'],
                    "S3Key": testing_env_variables['SAMPLE_VIDEO']
                    }
                }
            }
        }
    
    get_workflow_configuration_response = api.get_workflow_configuration_request(body)

    configuration = get_workflow_configuration_response.json()
    print("Default Workflow Configuration = {}".format(configuration))

    headers = {"Content-Type": "application/json", "Authorization": testing_env_variables['token']}
    start_request = requests.post(stack_resources["WorkflowApiEndpoint"]+'/workflow/execution', headers=headers, json=body, verify=False)
    assert start_request.status_code == 200
    assert start_request.json()['Status'] == 'Queued'
    
    workflow_execution = start_request.json()
    
    workflow_execution = api.wait_for_workflow_execution(workflow_execution, 600)
    assert workflow_execution["Status"] == "Complete"

    asset_id = workflow_execution["AssetId"]

    # print("Retrieving all metadata for the asset: {asset}".format(asset=asset_id))

    # cursor = None

    # more_results = True
    # while more_results:
    #     retrieve_metadata_response = api.get_all_metadata(stack_resources, asset_id, cursor)
    #     assert retrieve_metadata_response.status_code == 200
    #     retrieved_metadata = retrieve_metadata_response.json()
    #     print(retrieved_metadata)
    #     if "cursor" in retrieved_metadata:
    #         cursor = retrieved_metadata["cursor"]
    #     else:
    #         more_results = False
    # print("Successfully retrieved all metadata for asset: {asset}".format(asset=asset_id))
    
    print("Retrieving sample metadata for the asset: {asset}".format(asset=asset_id))

    for operator_name in ["Transcribe", "Translate"]:
        operator = {"OperatorName" : operator_name}

        retrieve_single_metadata_response = api.get_single_metadata_field(asset_id, operator)
        assert retrieve_single_metadata_response.status_code == 200

        retrieved_single_metadata = retrieve_single_metadata_response.json()
        print(
            "Retrieved {operator} results for asset: {asset}".format(operator=operator["OperatorName"],
                                                                    asset=asset_id))
        print(retrieved_single_metadata)