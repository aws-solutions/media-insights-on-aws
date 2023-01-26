# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

###############################################################################
# PURPOSE:
#   Lambda function to perform Rekognition tasks on image and video files
#
###############################################################################

import os
import json
from botocore import config
import urllib
import boto3
from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.core import patch_all
from MediaInsightsEngineLambdaHelper import OutputHelper
from MediaInsightsEngineLambdaHelper import MasExecutionError
from MediaInsightsEngineLambdaHelper import DataPlane

patch_all()

operator_name = os.environ['OPERATOR_NAME']
output_object = OutputHelper(operator_name)

mie_config = json.loads(os.environ['botoConfig'])
config = config.Config(**mie_config)
rek = boto3.client('rekognition', config=config)

# Placeholder for an image processor function that is not implemented
NOT_IMPLEMENTED = True


# Process an image using the provided image_function
def process_image(bucket, key, image_function, metadata_error_key):
    try:
        response = image_function(Image={'S3Object': {'Bucket': bucket, 'Name': key}})
    except Exception as e:
        output_object.update_workflow_status("Error")
        output_object.add_workflow_metadata(**{metadata_error_key: str(e)})
        raise MasExecutionError(output_object.return_output_object())
    return response


# Start processing a video using the provided video_function
def start_processing_video(bucket, key, video_function, additional_video_args, operation, metadata_error_key):
    try:
        response = video_function(
            Video={
                'S3Object': {
                    'Bucket': bucket,
                    'Name': key
                }
            },
            NotificationChannel={
                'SNSTopicArn': os.environ['REKOGNITION_SNS_TOPIC_ARN'],
                'RoleArn': os.environ['REKOGNITION_ROLE_ARN']
            },
            **additional_video_args
        )
        print('Job Id ({}): {}'.format(operation, response['JobId']))
        return response['JobId']
    except Exception as e:
        output_object.update_workflow_status("Error")
        output_object.add_workflow_metadata(**{metadata_error_key: str(e)})
        raise MasExecutionError(output_object.return_output_object())


def shared_handler(event, video_function, image_function, operation, metadata_error_key, additional_video_args={}):
    """Handles requests to check rekognition status.

    Parameters:
        event (dict): The unmodified event from the lambda function handler.
        video_function ((**kwargs) => dict): rekognition method to start processing a video.
        image_function ((**kwargs) => dict): rekognition method to process an image.
            Use `None` if image processing is not supported or `NOT_IMPLEMENTED` if it is not implemented.
        operation (str): The rekognition operation to be performed.
        metadata_error_key (str): Key name used for errors reported via OutputHelper.add_workflow_metadata().
        additional_video_args (dict): Additional named arguments that must be passed to video_function.

    Raises:
        MasExecutionError: Something went wrong.

    Returns:
        dict: Result of OutputHelper.return_output_object()
    """
    print("We got the following event:\n", event)
    try:
        # We have three possible S3 location keys if image_function is supplied, otherwise only two.
        media_keys = ("ProxyEncode", "Video", "Image") if image_function else ("ProxyEncode", "Video")
        # Find the key that exists under Input.Media searching in the order given by media_keys.
        input_media = event["Input"]["Media"]
        for media in (input_media[k] for k in media_keys if k in input_media):
            s3bucket = media["S3Bucket"]
            s3key = media["S3Key"]
            break

        workflow_id = str(event["WorkflowExecutionId"])
        asset_id = event['AssetId']
    except Exception:
        output_object.update_workflow_status("Error")
        output_object.add_workflow_metadata(**{metadata_error_key: "No valid inputs"})
        raise MasExecutionError(output_object.return_output_object())

    print("Processing s3://" + s3bucket + "/" + s3key)
    valid_video_types = [".avi", ".mp4", ".mov"]
    valid_image_types = [".png", ".jpg", ".jpeg"]
    file_type = os.path.splitext(s3key)[1].lower()
    if image_function and file_type in valid_image_types:
        if image_function is NOT_IMPLEMENTED:
            # TODO: implement image handling
            output_object.update_workflow_status("Complete")
            output_object.add_workflow_metadata(WorkflowExecutionId=workflow_id)
            return output_object.return_output_object()

        # Image processing is synchronous.
        response = process_image(s3bucket, urllib.parse.unquote_plus(s3key), image_function, metadata_error_key)
        output_object.add_workflow_metadata(AssetId=asset_id, WorkflowExecutionId=workflow_id)
        dataplane = DataPlane()
        metadata_upload = dataplane.store_asset_metadata(asset_id, operator_name, workflow_id, response)
        if metadata_upload.get("Status", "Failed") != "Success":
            # Status is missing or anything other than "Success"
            output_object.update_workflow_status("Error")
            output_object.add_workflow_metadata(
                **{metadata_error_key: "Unable to upload metadata for asset: {asset}".format(asset=asset_id)})
            raise MasExecutionError(output_object.return_output_object())

        print("Uploaded metadata for asset: {asset}".format(asset=asset_id))
        output_object.update_workflow_status("Complete")
        return output_object.return_output_object()
    elif file_type in valid_video_types:
        # Video processing is asynchronous.
        job_id = start_processing_video(s3bucket, urllib.parse.unquote_plus(s3key), video_function, additional_video_args, operation, metadata_error_key)
        output_object.update_workflow_status("Executing")
        output_object.add_workflow_metadata(JobId=job_id, AssetId=asset_id, WorkflowExecutionId=workflow_id)
        return output_object.return_output_object()
    else:
        print("ERROR: invalid file type")
        output_object.update_workflow_status("Error")
        output_object.add_workflow_metadata(**{metadata_error_key: "Not a valid file type"})
        raise MasExecutionError(output_object.return_output_object())


###############################################################################
# AWS Lambda Handlers
###############################################################################

def start_celebrity_recognition(event, _context):
    """Lambda function handler for starting celebrity recognition."""
    # Recognizes celebrities in a video or an image
    return shared_handler(event,
                          rek.start_celebrity_recognition,
                          rek.recognize_celebrities,
                          'celebrity recognition',
                          'CelebrityRecognitionError')


def start_content_moderation(event, _context):
    """Lambda function handler for starting content moderation."""
    # Detect explicit or suggestive adult content in a video or an image
    return shared_handler(event,
                          rek.start_content_moderation,
                          rek.detect_moderation_labels,
                          'content moderation',
                          'ContentModerationError')


def start_face_detection(event, _context):
    """Lambda function handler for starting face detection."""
    # Detect faces in a video or an image
    return shared_handler(event,
                          rek.start_face_detection,
                          rek.detect_faces,
                          'face detection',
                          'FaceDetectionError',
                          additional_video_args={'FaceAttributes': 'ALL'}
                          )


def start_label_detection(event, _context):
    """Lambda function handler for starting label detection."""
    # Recognizes labels in a video or an image
    return shared_handler(event,
                          rek.start_label_detection,
                          rek.detect_labels,
                          'label_detection',
                          'LabelDetectionError')


def start_shot_detection(event, _context):
    """Lambda function handler for starting shot detection."""
    # Recognizes labels in a video or an image
    return shared_handler(event,
                          rek.start_segment_detection,
                          rek.detect_labels,
                          'shot_detection',
                          'LabelDetectionError',
                          additional_video_args={'SegmentTypes': ['SHOT']}
                          )


def start_technical_cue_detection(event, _context):
    """Lambda function handler for starting techncal cue detection."""
    return shared_handler(event,
                          rek.start_segment_detection,
                          None,
                          'techncal_cue_detection',
                          'TechnicalCueDetectionError',
                          additional_video_args={'SegmentTypes': ['TECHNICAL_CUE']}
                          )


def start_text_detection(event, _context):
    """Lambda function handler for starting text detection."""
    # Recognizes text in a video or an image
    return shared_handler(event,
                          rek.start_text_detection,
                          rek.detect_text,
                          'text_detection',
                          'TextDetectionError')


def start_person_tracking(event, _context):
    """Lambda function handler for starting person tracking."""
    # Detects persons in a video
    return shared_handler(event,
                          rek.start_person_tracking,
                          NOT_IMPLEMENTED,
                          'person_tracking',
                          'PersonTrackingError')
