# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

###############################################################################
# PURPOSE:
#   Lambda function to perform Rekognition tasks on image and video files
#
###############################################################################

import os
import json
import urllib
import boto3
from botocore import config

from MediaInsightsEngineLambdaHelper import OutputHelper
from MediaInsightsEngineLambdaHelper import MasExecutionError
from MediaInsightsEngineLambdaHelper import DataPlane

operator_name = os.environ['OPERATOR_NAME']
output_object = OutputHelper(operator_name)

mie_config = json.loads(os.environ['botoConfig'])
config = config.Config(**mie_config)
rek = boto3.client('rekognition-segment-detection')


def start_technical_cue_detection(bucket, key):
    try:
        response = rek.start_segment_detection(
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
            SegmentTypes=['TECHNICAL_CUE']
        )
        print('Job Id (techncal_cue_detection): ' + response['JobId'])
        return response['JobId']
    except Exception as e:
        output_object.update_workflow_status("Error")
        output_object.add_workflow_metadata(TechnicalCueDetectionError=str(e))
        raise MasExecutionError(output_object.return_output_object())


# Lambda function entrypoint:
def lambda_handler(event, context):
    print("We got the following event:\n", event)
    try:
        s3bucket = event["Input"]["Media"]["ProxyEncode"]["S3Bucket"]
        s3key = event["Input"]["Media"]["ProxyEncode"]["S3Key"]
        workflow_id = str(event["WorkflowExecutionId"])
        asset_id = event['AssetId']
    except Exception:
        output_object.update_workflow_status("Error")
        output_object.add_workflow_metadata(TechnicalCueDetectionError="No valid inputs")
        raise MasExecutionError(output_object.return_output_object())
    print("Processing s3://" + s3bucket + "/" + s3key)
    valid_video_types = [".avi", ".mp4", ".mov"]
    file_type = os.path.splitext(s3key)[1].lower()
    if file_type in valid_video_types:
        # Video processing is asynchronous.
        job_id = start_technical_cue_detection(s3bucket, urllib.parse.unquote_plus(s3key))
        output_object.update_workflow_status("Executing")
        output_object.add_workflow_metadata(JobId=job_id, AssetId=asset_id, WorkflowExecutionId=workflow_id)
        return output_object.return_output_object()
    else:
        print("ERROR: invalid file type")
        output_object.update_workflow_status("Error")
        output_object.add_workflow_metadata(TechnicalCueDetectionError="Not a valid file type")
        raise MasExecutionError(output_object.return_output_object())
