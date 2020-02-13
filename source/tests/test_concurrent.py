# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

###############################################################################
# Integration testing for the MIE workflow API - test concurrency control
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
import time
import threading

# local imports
import validation


def start_frame_workflows(nframes, stack_resources, testing_env_variables):
    print("starting {} workflows".format(nframes))

    body = {
        "Name":"ImageWorkflow",
        "Configuration": {
            "RekognitionStage": {
                "faceSearchImage": {
                    "MediaType": "Image",
                    "Enabled": False,
                    "CollectionId": "FOO"
                    }
                }
            },
        "Input": {
            "Media": {
                "Image": {
                    "S3Bucket": testing_env_variables['BUCKET_NAME'],
                    "S3Key": testing_env_variables['SAMPLE_IMAGE']
                    }
                }
            }
        }

    # Start nframe workflows
    for i in range(1,nframes):
        headers = {"Content-Type": "application/json", "Authorization": testing_env_variables['token']}
        start_request = requests.post(stack_resources["WorkflowApiEndpoint"]+'/workflow/execution', headers=headers, json=body, verify=False)
        assert start_request.status_code == 200
        assert start_request.json()['Status'] == 'Queued'

def test_concurreny(api, stack_resources, api_schema, testing_env_variables):
    api = api()

    headers = {"Content-Type": "application/json", "Authorization": testing_env_variables['token']}

    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


    # Check the number of Error worklfow at start - we'll check again at the end to make sure
    # our workflows are sucessful
    get_workflows_by_status_response = requests.get(stack_resources["WorkflowApiEndpoint"]+'/workflow/execution/status/Error', headers=headers, verify=False)
    assert get_workflows_by_status_response.status_code == 200
    start_errors = len(get_workflows_by_status_response.json())

    # Make sure no workflows are running
    get_workflows_by_status_response = requests.get(stack_resources["WorkflowApiEndpoint"]+'/workflow/execution/status/Started', headers=headers, verify=False)
    num_started = len(get_workflows_by_status_response.json())
    while num_started > 0:
        get_workflows_by_status_response = requests.get(stack_resources["WorkflowApiEndpoint"]+'/workflow/execution/status/Started', headers=headers, verify=False)
        num_started = len(get_workflows_by_status_response.json())
        print("Wait for 0 workflows running: {}/{}".format(num_started, 0))
        assert get_workflows_by_status_response.status_code == 200
        time.sleep(1)

    for max in [1, 9, 10, 15, 20, 25]:
        print("\nTest setting MaxConcurrentWorkflows to {}\n".format(max))

        set_max_concurrent_response = api.set_max_concurrent_request(max)
        assert set_max_concurrent_response.status_code == 200
        # It can take up to one run of the lambda for a configuration change to take effect
        time.sleep(20)

        get_configuration_response = api.get_configuration_request()
        assert get_configuration_response.status_code == 200
        configs = get_configuration_response.json()
        config = next(config for config in configs if config["Name"] == "MaxConcurrentWorkflows")
        assert config["Value"] == max

        start_frame_workflows(20, stack_resources, testing_env_variables)

        # At most "max" workflow should run at a time
        get_workflows_by_status_response = requests.get(stack_resources["WorkflowApiEndpoint"]+'/workflow/execution/status/Started', headers=headers, verify=False)
        print(get_workflows_by_status_response.json())
        num_started = len(get_workflows_by_status_response.json())
        print("{} or less workflows should be running now: {}/{}".format(max, num_started, max))
        assert get_workflows_by_status_response.status_code == 200
        assert num_started <= max

        while num_started > 0:
            get_workflows_by_status_response = requests.get(stack_resources["WorkflowApiEndpoint"]+'/workflow/execution/status/Started', headers=headers, verify=False)
            num_started = len(get_workflows_by_status_response.json())
            print("{} or less workflows should be running now: {}/{}".format(max, num_started, max))
            assert get_workflows_by_status_response.status_code == 200
            assert num_started <= max
            time.sleep(1)

    # Check if there are more errored workflows at the start of the test than at the end.  The
    # check is not detrministic since the worklfow counts from the status API is eventually consistent.
    # The number of error reported may not be up to date.  Issue a printed warning as a clue if there are
    # other failures
    get_workflows_by_status_response = requests.get(stack_resources["WorkflowApiEndpoint"]+'/workflow/execution/status/Error', headers=headers, verify=False)
    assert get_workflows_by_status_response.status_code == 200
    end_errors = len(get_workflows_by_status_response.json())

    if (end_errors > start_errors):
        print ("WARNING: errored workflows at the start of the  are > start")



def test_frame_flood(api, stack_resources, api_schema, testing_env_variables):
    api = api()
    headers = {"Content-Type": "application/json", "Authorization": testing_env_variables['token']}

    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    # Maximum concurrent for this test
    max = 50

    # Check the number of Error worklfow at start - we'll check again at the end to make sure
    # our workflows are sucessful
    get_workflows_by_status_response = requests.get(stack_resources["WorkflowApiEndpoint"]+'/workflow/execution/status/Error', headers=headers, verify=False)
    assert get_workflows_by_status_response.status_code == 200
    start_errors = len(get_workflows_by_status_response.json())

    # Make sure no workflows are running
    get_workflows_by_status_response = requests.get(stack_resources["WorkflowApiEndpoint"]+'/workflow/execution/status/Started', headers=headers, verify=False)
    num_started = len(get_workflows_by_status_response.json())
    while num_started > 0:
        get_workflows_by_status_response = requests.get(stack_resources["WorkflowApiEndpoint"]+'/workflow/execution/status/Started', headers=headers, verify=False)
        num_started = len(get_workflows_by_status_response.json())
        print("Wait for 0 workflows running: {}/{}".format(num_started, max))
        assert get_workflows_by_status_response.status_code == 200
        time.sleep(1)

    for frames in [100, 200]:

        print("\nTest processing {} frames with MaxConcurrentWorkflow = {}\n".format(frames, max))

        set_max_concurrent_response = api.set_max_concurrent_request(max)
        assert set_max_concurrent_response.status_code == 200
        # It can take up to one run of the lambda for a configuration change to take effect
        time.sleep(20)

        get_configuration_response = api.get_configuration_request()
        assert get_configuration_response.status_code == 200
        configs = get_configuration_response.json()
        config = next(config for config in configs if config["Name"] == "MaxConcurrentWorkflows")
        assert config["Value"] == max

        threads = []
        num_threads = frames//2
        for i in range(num_threads):
            t = threading.Thread(target=start_frame_workflows, args=(2, stack_resources, testing_env_variables))
            threads.append(t)
            t.start()

        # At most "max" workflow sshould run at a time
        get_workflows_by_status_response = requests.get(stack_resources["WorkflowApiEndpoint"]+'/workflow/execution/status/Started', headers=headers, verify=False)
        print(get_workflows_by_status_response.json())
        num_started = len(get_workflows_by_status_response.json())
        print("{} or less workflows should be running now: {}/{}".format(max, num_started, max))
        assert get_workflows_by_status_response.status_code == 200
        assert num_started <= max

        while num_started > 0:
            get_workflows_by_status_response = requests.get(stack_resources["WorkflowApiEndpoint"]+'/workflow/execution/status/Started', headers=headers, verify=False)
            num_started = len(get_workflows_by_status_response.json())
            print("{} or less workflows should be running now: {}/{}".format(max, num_started, max))
            assert get_workflows_by_status_response.status_code == 200
            assert num_started <= max
            time.sleep(1)


    # Check the number of Error worklfow at end and compare to the start
    get_workflows_by_status_response = requests.get(stack_resources["WorkflowApiEndpoint"]+'/workflow/execution/status/Error', headers=headers, verify=False)
    assert get_workflows_by_status_response.status_code == 200
    end_errors = len(get_workflows_by_status_response.json())
    assert start_errors == end_errors



# set concurrency via API
# spin up > MAX_CONCURRENT workflows and verify that no more than
# MAX_CONCURRENT worklfows are Started at a given time

# set concurrency to unlimited via API
# spin up > MAX_CONCURRENT workflows and verify many workflows
# run concurrently

# compare time it takes to run a set of 100 workflows with concurrency set to 1 vs 100
# time should be at least 10x faster (heuristic sanity check for embarrassing overheads)

