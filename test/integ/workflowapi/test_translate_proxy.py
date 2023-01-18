# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

###############################################################################
# Integration testing for the MI service proxy API for Amazon Translate
#
# PRECONDITIONS:
# MI base stack must be deployed in your AWS account
#
# Boto3 will raise a deprecation warning (known issue). It's safe to ignore.
#
# USAGE:
#   cd tests/
#   pytest -s -W ignore::DeprecationWarning -p no:cacheprovider
#
###############################################################################

import time
import json
import pytest
import os

@pytest.mark.skipif(os.environ['REGION'] not in ["us-west-2", "us-east-1", "eu-west-1"], reason="Parallel Data is not supported in this region")
def test_parallel_data(workflow_api, stack_resources, testing_env_variables):
    workflow_api = workflow_api()

    print("Running parallel data function tests")

    # Remove test parallel data if it already exists
    list_parallel_data_response = workflow_api.list_parallel_data()
    assert list_parallel_data_response.status_code == 200
    response = list_parallel_data_response.json()
    if testing_env_variables['TEST_PARALLEL_DATA_NAME'] in json.dumps(response):
        print("Removing " + testing_env_variables['TEST_PARALLEL_DATA_NAME'])
        request_payload = {'Name': testing_env_variables['TEST_PARALLEL_DATA_NAME']}
        delete_parallel_data_response = workflow_api.delete_parallel_data(request_payload)
        assert delete_parallel_data_response.status_code == 200

        # Wait until the test parallel data is not longer listed
        list_parallel_data_response = workflow_api.list_parallel_data()
        assert list_parallel_data_response.status_code == 200
        response = list_parallel_data_response.json()
        while testing_env_variables['TEST_PARALLEL_DATA_NAME'] in json.dumps(response):
            time.sleep(10)
            list_parallel_data_response = workflow_api.list_parallel_data()
            response = list_parallel_data_response.json()

    # Create parallel data
    request_payload = {"Name": testing_env_variables['TEST_PARALLEL_DATA_NAME'], "ParallelDataConfig":{"S3Uri":"s3://" + stack_resources['DataplaneBucket'] + "/" + testing_env_variables['TEST_PARALLEL_DATA'], "Format":"CSV"}}
    create_parallel_data_response = workflow_api.create_parallel_data(request_payload)
    assert create_parallel_data_response.status_code == 200

    # Wait for create to finish
    request_payload = {'Name': testing_env_variables['TEST_PARALLEL_DATA_NAME']}
    get_parallel_data_response = workflow_api.get_parallel_data(request_payload)
    assert get_parallel_data_response.status_code == 200
    response = get_parallel_data_response.json()
    print("create status: " + response["ParallelDataProperties"]["Status"])
    while (response["ParallelDataProperties"]["Status"] == "CREATING"):
        time.sleep(30)
        get_parallel_data_response = workflow_api.get_parallel_data(request_payload)
        assert get_parallel_data_response.status_code == 200
        response = get_parallel_data_response.json()
        print("create status: " + response["ParallelDataProperties"]["Status"])

    # List parallel data
    list_parallel_data_response = workflow_api.list_parallel_data()
    assert list_parallel_data_response.status_code == 200
    response = list_parallel_data_response.json()
    assert testing_env_variables['TEST_PARALLEL_DATA_NAME'] in json.dumps(response)

    # Download parallel data
    body = {'Name': testing_env_variables['TEST_PARALLEL_DATA_NAME']}
    download_parallel_data_response = workflow_api.download_parallel_data(body)
    assert download_parallel_data_response.status_code == 200

    print("Removing " + testing_env_variables['TEST_PARALLEL_DATA_NAME'])
    request_payload = {'Name': testing_env_variables['TEST_PARALLEL_DATA_NAME']}
    delete_parallel_data_response = workflow_api.delete_parallel_data(request_payload)
    assert delete_parallel_data_response.status_code == 200


def test_terminology(workflow_api, testing_env_variables, terminology):
    workflow_api = workflow_api()

    print("Running custom terminology function tests")

    # Create terminology is done in terminology fixture

    # List terminology
    list_terminologies_response = workflow_api.list_terminologies()
    assert list_terminologies_response.status_code == 200
    response = list_terminologies_response.json()
    assert testing_env_variables['SAMPLE_TERMINOLOGY'] in json.dumps(response)

    # Get terminology
    body = {'terminology_name': testing_env_variables['SAMPLE_TERMINOLOGY']}
    get_terminology_response = workflow_api.get_terminology(body)
    assert get_terminology_response.status_code == 200
    response = get_terminology_response.json()
    assert testing_env_variables['SAMPLE_TERMINOLOGY'] == response['TerminologyProperties']['Name']

    # Download terminology
    body = {'terminology_name': testing_env_variables['SAMPLE_TERMINOLOGY']}
    download_terminology_response = workflow_api.download_terminology(body)
    assert download_terminology_response.status_code == 200

    response = download_terminology_response.json()
    assert "STEEN" in json.dumps(response)

    # Delete terminology is done in terminology fixture
    



    
