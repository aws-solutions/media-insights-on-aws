# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
    
import os
import boto3
import urllib3
import json

region = os.environ['AWS_REGION']

from MediaInsightsEngineLambdaHelper import MediaInsightsOperationHelper
from MediaInsightsEngineLambdaHelper import MasExecutionError
from MediaInsightsEngineLambdaHelper import DataPlane

def video_sync_ok_lambda_handler(event, context):

    return test_lambda_handler(event, context, "video-test-sync", "Video", "Success", "Start")

def video_sync_fail_lambda_handler(event, context):

    return test_lambda_handler(event, context, "video-test-sync-fail", "Video", "Fail", "Start")

def video_async_ok_lambda_handler(event, context):

    return test_lambda_handler(event, context, "video-test-async", "Video", "Success", "Start")

def video_async_ok_monitor_lambda_handler(event, context):

    return test_lambda_handler(event, context, "video-test-async", "Video", "Success", "Monitor")

def video_async_fail_monitor_lambda_handler(event, context):

    return test_lambda_handler(event, context, "video-test-async", "Video", "Success", "Monitor")

def audio_sync_ok_lambda_handler(event, context):

    return test_lambda_handler(event, context, "audio-test-sync", "Audio", "Success", "Start")

def audio_async_ok_lambda_handler(event, context):

    return test_lambda_handler(event, context, "audio-test-async", "Audio", "Success", "Start")

def audio_async_ok_monitor_lambda_handler(event, context):

    return test_lambda_handler(event, context, "audio-test-async", "Audio", "Success", "Monitor")

def image_sync_ok_lambda_handler(event, context):

    return test_lambda_handler(event, context, "image-test-sync", "Image", "Success", "Start")

def image_async_ok_lambda_handler(event, context):

    return test_lambda_handler(event, context, "image-test-async", "Image", "Success", "Start")

def image_async_ok_monitor_lambda_handler(event, context):

    return test_lambda_handler(event, context, "image-test-async", "Image", "Success", "Monitor")

def text_sync_ok_lambda_handler(event, context):

    return test_lambda_handler(event, context, "text-test-sync", "Text", "Success", "Start")

def text_async_ok_lambda_handler(event, context):

    return test_lambda_handler(event, context, "text-test-async", "Text", "Success", "Start")

def text_async_ok_monitor_lambda_handler(event, context):

    return test_lambda_handler(event, context, "text-test-async", "Text", "Success", "Monitor")


def test_lambda_handler(event, context, operator_name, mediaType, status, type):

    try:
        print(json.dumps(event))
        # set output status, media, and metatdata for workflow - these get passed to other
        # stages of the workflow through the control plane
        dataplane = DataPlane()

        operator_object = MediaInsightsOperationHelper(event)
        operator_object.update_workflow_status("Complete")
        metadata = {}
        metadata[operator_object.name] = {"Meta": "Workflow metadata for "+operator_object.name}
        
        if "TestCustomConfig" in operator_object.configuration:
            metadata[operator_object.name]["TestCustomConfig"] = operator_object.configuration["TestCustomConfig"]
            

        operator_object.add_workflow_metadata_json(
                metadata
            )

        if "OutputMediaType" in operator_object.configuration:
            mediaType = operator_object.configuration["OutputMediaType"]

        if mediaType == "Video":
            operator_object.add_media_object(
                    "Video", "S3BucketFrom{}".format(operator_object.name), "S3/Key/From/{}/video".format(operator_object.name)
            )
        elif mediaType == "Audio":
            operator_object.add_media_object(
                    "Audio", "S3BucketFrom{}".format(operator_object.name), "S3/Key/From/{}/audio".format(operator_object.name)
            )
        elif mediaType == "Image":
            operator_object.add_media_object(
                    "Text", "S3BucketFrom{}".format(operator_object.name), "S3/Key/From/{}/image".format(operator_object.name)
            )
        elif mediaType == "Text":
            operator_object.add_media_object(
                    "Text", "S3BucketFrom{}".format(operator_object.name), "S3/Key/From/{}/text".format(operator_object.name)
            )
        
    except Exception as e:
        operator_object.update_workflow_status("Error")
        operator_object.add_workflow_metadata(Message="Oh no! Something went wrong: {}".format(str(e)))
        raise MasExecutionError(operator_object.return_output_object())
    else:
        if status == "Fail":
            operator_object.update_workflow_status("Error")
        else:
            operator_object.update_workflow_status("Complete")
        return operator_object.return_output_object()




# def text_test_async_lambda_handler(event, context):
#     '''
#     This lambda is stub used to test data exchange between operators within a workflow.
#     MediaType: video
#     '''

#     return test_lambda_handler(event, context, "text-test-async", "Start")

# def text_test_async_monitor_lambda_handler(event, context):
#     '''
#     This lambda is stub used to test data exchange between operators within a workflow.
#     '''

#     return test_lambda_handler(event, context, "text-test-async", "Monitor")



# def audio_test_sync_lambda_handler(event, context):
#     '''
#     This lambda is stub used to test data exchange between operators within a workflow.
#     MediaType: video
#     '''

#     return test_lambda_handler(event, context, "audio-test-sync", "Start")

# def text_test_sync_lambda_handler(event, context):
#     '''
#     This lambda is stub used to test data exchange between operators within a workflow.
#     MediaType: video
#     '''

#     return test_lambda_handler(event, context, "text-test-sync", "Start")
