# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

###############################################################################
# White box testing for the base Media Insights Engine stack and wait operator
# which is often used for pausing workflows to get user input.
#
# PRECONDITIONS:
# MIE base stack must be deployed in your AWS account
#
# Boto3 will raise a deprecation warning (known issue). It's safe to ignore.
#
# USAGE:
#   cd test/e2e/
#   export MIE_REGION=...
#   export MIE_STACK_NAME=...
#   export AWS_ACCESS_KEY_ID=...
#   export AWS_SECRET_ACCESS_KEY=...
#   export TEST_MEDIA_PATH="../test-media/"
#   export TEST_VIDEO="sample-video.mp4"
#   pytest -s -W ignore::DeprecationWarning -p no:cacheprovider test_workflow_with_user_input.py
#
###############################################################################


import urllib3
import time


def test_workflow_execution(workflow_api, dataplane_api, stack_resources, testing_env_variables):
    workflow_api = workflow_api()
    dataplane_api = dataplane_api()

    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    test_preprocess_stage = {"Name": "TestPreprocess", "Operations": ["Mediainfo"]}
    test_wait_stage = {"Name": "TestWait4UserInput", "Operations": ["Wait"]}
    test_postprocess_stage = {"Name": "TestPostprocess", "Operations": ["Thumbnail"]}

    test_workflow = {
        "Name": "TestingWaitWF",
        "StartAt": "TestPreprocess",
        "Stages": {
            "TestPreprocess": {
                "Next": "TestWait4UserInput"
            },
            "TestWait4UserInput": {
                "Next": "TestPostprocess"
            },
            "TestPostprocess": {
                "End": True
            }
        }
    }

    test_execution = {
        "Name": "TestingWaitWF",
        "Input": {
            "Media": {
                "Video": {
                    "S3Bucket": stack_resources['DataplaneBucket'],
                    "S3Key": 'upload/' + testing_env_variables['SAMPLE_VIDEO']
                }
            }
        },
        "Configuration": {
            "TestWait4UserInput": {
                "Wait": {
                    "MediaType": "MetadataOnly",
                    "Enabled": True
                }
            }
        }
    }

    # clean up previously incomplete tests
    print("Cleaning up previously incomplete tests")

    delete_preprocess_stage_request = workflow_api.delete_stage_request(test_preprocess_stage["Name"])
    delete_wait_stage_request = workflow_api.delete_stage_request(test_wait_stage["Name"])
    test_postprocess_stage_request = workflow_api.delete_stage_request(test_postprocess_stage["Name"])

    if workflow_api.get_workflow_request(test_workflow["Name"]).status_code == 200:
        workflow_api.delete_workflow_request(test_workflow["Name"])
        # Wait for the workflow to delete. It can take several seconds.
        time.sleep(30)

    # create stages

    preprocess_stage_request = workflow_api.create_stage_request(test_preprocess_stage)
    assert preprocess_stage_request.status_code == 200

    wait_stage_request = workflow_api.create_stage_request(test_wait_stage)
    assert wait_stage_request.status_code == 200

    postprocess_stage_request = workflow_api.create_stage_request(test_postprocess_stage)
    assert postprocess_stage_request.status_code == 200

    # create workflow

    workflow_create_request = workflow_api.create_workflow_request(test_workflow)
    assert workflow_create_request.status_code == 200

    # create workflow execution

    workflow_execution_request = workflow_api.create_workflow_execution_request(test_execution)
    assert workflow_execution_request.status_code == 200

    workflow_execution_response = workflow_execution_request.json()
    workflow_execution_id = workflow_execution_response["Id"]
    asset_id = workflow_execution_response["AssetId"]

    time.sleep(5)

    # wait for workflow to complete

    workflow_processing = True

    # Wait for workflow to pause at the Wait operator
    while workflow_processing:
        get_workflow_execution_request = workflow_api.get_workflow_execution_request(workflow_execution_id)
        get_workflow_execution_response = get_workflow_execution_request.json()
        assert get_workflow_execution_request.status_code == 200

        workflow_status = get_workflow_execution_response["Status"]
        print("Workflow Status: {}".format(workflow_status))

        allowed_statuses = ["Started", "Queued", "Waiting"]
        assert workflow_status in allowed_statuses

        if workflow_status == "Waiting":
            workflow_processing = False
        else:
            print('Sleeping for 10 seconds before retrying')
            time.sleep(10)

    # Resume the workflow
    workflow_current_stage = get_workflow_execution_response["CurrentStage"]
    assert workflow_current_stage == test_wait_stage["Name"]
    body = {"WaitingStageName": workflow_current_stage}
    resume_workflow_execution_response = workflow_api.resume_workflow_request(body, workflow_execution_id)
    assert resume_workflow_execution_response.status_code == 200

    # Wait for workflow to complete
    while workflow_processing:
        get_workflow_execution_request = workflow_api.get_workflow_execution_request(workflow_execution_id)
        get_workflow_execution_response = get_workflow_execution_request.json()
        assert get_workflow_execution_request.status_code == 200

        workflow_status = get_workflow_execution_response["Status"]
        print("Workflow Status: {}".format(workflow_status))

        allowed_statuses = ["Resumed", "Complete"]
        assert workflow_status in allowed_statuses

        if workflow_status == "Complete":
            workflow_processing = False
        else:
            print('Sleeping for 10 seconds before retrying')
            time.sleep(10)

    # Get asset mediainfo from dataplane

    asset_mediainfo_request = dataplane_api.get_single_metadata_field(asset_id, "Mediainfo")
    assert asset_mediainfo_request.status_code == 200

    print(asset_mediainfo_request.json())

    # Delete asset

    delete_asset_request = dataplane_api.delete_asset(asset_id)
    assert delete_asset_request.status_code == 200

    # Delete workflow

    delete_workflow_request = workflow_api.delete_workflow_request(test_workflow["Name"])
    assert delete_workflow_request.status_code == 200
    # Wait for the workflow to delete. It can take several seconds.
    time.sleep(30)

    # Delete stages

    delete_preprocess_stage_request = workflow_api.delete_stage_request(test_preprocess_stage["Name"])
    assert delete_preprocess_stage_request.status_code == 200

    delete_wait_stage_request = workflow_api.delete_stage_request(test_wait_stage["Name"])
    assert delete_wait_stage_request.status_code == 200

    delete_postprocess_stage_request = workflow_api.delete_stage_request(test_postprocess_stage["Name"])
    assert delete_postprocess_stage_request.status_code == 200

