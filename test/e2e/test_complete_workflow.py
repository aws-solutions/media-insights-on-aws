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


import urllib3
import time


def test_workflow_execution(workflow_api, dataplane_api, stack_resources, testing_env_variables):
    workflow_api = workflow_api()
    dataplane_api = dataplane_api()

    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    test_preprocess_stage = {"Name": "TestPreprocess", "Operations": ["Thumbnail"]}
    test_video_stage = {"Name": "TestVideo",
                        "Operations": ["Mediainfo", "celebrityRecognition", "contentModeration", "faceDetection", "labelDetection",
                                       "personTracking", "shotDetection", "textDetection", "Mediaconvert",
                                       "technicalCueDetection"]}
    test_audio_stage = {"Name": "TestAudio", "Operations": ["TranscribeAudio"]}
    test_text_stage = {"Name": "TestText", "Operations": ["Translate", "ComprehendKeyPhrases", "ComprehendEntities"]}

    test_workflow = {
        "Name": "TestingWF",
        "StartAt": "TestPreprocess",
        "Stages": {
            "TestPreprocess": {
                "Next": "TestVideo"
            },
            "TestVideo": {
                "Next": "TestAudio"
            },
            "TestAudio": {
                "Next": "TestText"
            },
            "TestText": {
                "End": True
            }
        }
    }

    test_execution = {
        "Name": "TestingWF",
        "Input": {
            "Media": {
                "Video": {
                    "S3Bucket": stack_resources['DataplaneBucket'],
                    "S3Key": 'upload/' + testing_env_variables['SAMPLE_VIDEO']
                }
            }
        }
    }

    # clean up previously incomplete tests
    print("Cleaning up previously incomplete tests")

    delete_preprocess_stage_request = workflow_api.delete_stage_request(test_preprocess_stage["Name"])
    delete_video_stage_request = workflow_api.delete_stage_request(test_video_stage["Name"])
    delete_audio_stage_request = workflow_api.delete_stage_request(test_audio_stage["Name"])
    delete_text_stage_request = workflow_api.delete_stage_request(test_text_stage["Name"])
    if workflow_api.get_workflow_request(test_workflow["Name"]).status_code == 200:
        workflow_api.delete_workflow_request(test_workflow["Name"])
        # Wait for the workflow to delete. It can take several seconds.
        time.sleep(30)

    # create stages

    preprocess_stage_request = workflow_api.create_stage_request(test_preprocess_stage)
    assert preprocess_stage_request.status_code == 200

    video_stage_request = workflow_api.create_stage_request(test_video_stage)
    assert video_stage_request.status_code == 200

    audio_stage_request = workflow_api.create_stage_request(test_audio_stage)
    assert audio_stage_request.status_code == 200

    text_stage_request = workflow_api.create_stage_request(test_text_stage)
    assert text_stage_request.status_code == 200

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

    while workflow_processing:
        get_workflow_execution_request = workflow_api.get_workflow_execution_request(workflow_execution_id)
        get_workflow_execution_response = get_workflow_execution_request.json()

        assert get_workflow_execution_request.status_code == 200


        workflow_status = get_workflow_execution_response["Status"]
        print("Workflow Status: {}".format(workflow_status))

        allowed_statuses = ["Started", "Queued", "Complete"]

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

    delete_video_stage_request = workflow_api.delete_stage_request(test_video_stage["Name"])
    assert delete_video_stage_request.status_code == 200

    delete_audio_stage_request = workflow_api.delete_stage_request(test_audio_stage["Name"])
    assert delete_audio_stage_request.status_code == 200

    delete_text_stage_request = workflow_api.delete_stage_request(test_text_stage["Name"])
    assert delete_text_stage_request.status_code == 200
