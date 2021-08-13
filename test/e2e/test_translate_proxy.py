# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

###############################################################################
# Integration testing for the MIE service proxy API for Amazon Translate
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

import urllib3
import time
import json


def test_parallel_data(workflow_api, testing_env_variables, parallel_data):
    workflow_api = workflow_api()
    
    # Create parallel data is done in parallel_data fixture

    # List parallel data

    list_parallel_data_response = workflow_api.list_parallel_data()
    assert list_parallel_data_response.status_code == 200
    response = list_parallel_data_response.json()
    assert testing_env_variables['SAMPLE_PARALLEL_DATA'] in json.dumps(response)

    # Download parallel data
    body = {'parallel_data_name': testing_env_variables['SAMPLE_PARALLEL_DATA']}
    download_parallel_data_response = workflow_api.download_parallel_data(body)
    assert download_parallel_data_response.status_code == 200

    response = download_parallel_data_response.json()
    assert "larger than Earth" in json.dumps(response)

    # Delete parallel data is done in parallel_data fixture
    

def test_terminology(workflow_api, testing_env_variables, terminology):
    workflow_api = workflow_api()
    
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
    



    