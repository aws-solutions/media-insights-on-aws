# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

###############################################################################
# PURPOSE:
#   Lambda function to recognize celebrities in an image or video file
#
###############################################################################

import os
import json
from botocore import config
import urllib
import boto3
from MediaInsightsEngineLambdaHelper import OutputHelper
from MediaInsightsEngineLambdaHelper import MasExecutionError
from MediaInsightsEngineLambdaHelper import DataPlane


operator_name = os.environ['OPERATOR_NAME']
output_object = OutputHelper(operator_name)

mie_config = json.loads(os.environ['botoConfig'])
config = config.Config(**mie_config)
rek = boto3.client('rekognition', config=config)


# Recognizes labels in an image
def recognize_celebrities(bucket, key):
    try:
        response = rek.recognize_celebrities(Image={'S3Object':{'Bucket':bucket, 'Name':key}})
    except Exception as e:
        output_object.update_workflow_status("Error")
        output_object.add_workflow_metadata(CelebrityRecognitionError=str(e))
        raise MasExecutionError(output_object.return_output_object())
    return response

# Recognizes celebrities in a video
def start_celebrity_recognition(bucket, key):
    try:
        response = rek.start_celebrity_recognition(
            Video={
                'S3Object': {
                    'Bucket': bucket,
                    'Name': key
                }
            },
            NotificationChannel={
                'SNSTopicArn': os.environ['REKOGNITION_SNS_TOPIC_ARN'],
                'RoleArn': os.environ['REKOGNITION_ROLE_ARN']
            }
        )
        print('Job Id (celebrity recognition): ' + response['JobId'])
        return response['JobId']
    except Exception as e:
        output_object.update_workflow_status("Error")
        output_object.add_workflow_metadata(CelebrityRecognitionError=str(e))
        raise MasExecutionError(output_object.return_output_object())


# Lambda function entrypoint:
def lambda_handler(event, context):
    try:
        if "Video" in event["Input"]["Media"]:
            s3bucket = event["Input"]["Media"]["Video"]["S3Bucket"]
            s3key = event["Input"]["Media"]["Video"]["S3Key"]
        elif "Image" in event["Input"]["Media"]:
            s3bucket = event["Input"]["Media"]["Image"]["S3Bucket"]
            s3key = event["Input"]["Media"]["Image"]["S3Key"]
        workflow_id = str(event["WorkflowExecutionId"])
        asset_id = event['AssetId']
    except Exception:
        output_object.update_workflow_status("Error")
        output_object.add_workflow_metadata(CelebrityRecognitionError="No valid inputs")
        raise MasExecutionError(output_object.return_output_object())
    print("Processing s3://"+s3bucket+"/"+s3key)
    valid_video_types = [".avi", ".mp4", ".mov"]
    valid_image_types = [".png", ".jpg", ".jpeg"]
    file_type = os.path.splitext(s3key)[1]
    if file_type in valid_image_types:
        # Image processing is synchronous.
        response = recognize_celebrities(s3bucket, urllib.parse.unquote_plus(s3key))
        output_object.add_workflow_metadata(AssetId=asset_id, WorkflowExecutionId=workflow_id)
        dataplane = DataPlane()
        metadata_upload = dataplane.store_asset_metadata(asset_id, operator_name, workflow_id, response)
        if "Status" not in metadata_upload:
            output_object.update_workflow_status("Error")
            output_object.add_workflow_metadata(
                CelebrityRecognitionError="Unable to upload metadata for asset: {asset}".format(asset=asset_id))
            raise MasExecutionError(output_object.return_output_object())
        else:
            if metadata_upload["Status"] == "Success":
                print("Uploaded metadata for asset: {asset}".format(asset=asset_id))
                output_object.update_workflow_status("Complete")
                return output_object.return_output_object()
            elif metadata_upload["Status"] == "Failed":
                output_object.update_workflow_status("Error")
                output_object.add_workflow_metadata(
                    CelebrityRecognitionError="Unable to upload metadata for asset: {asset}".format(asset=asset_id))
                raise MasExecutionError(output_object.return_output_object())
            else:
                output_object.update_workflow_status("Error")
                output_object.add_workflow_metadata(
                    CelebrityRecognitionError="Unable to upload metadata for asset: {asset}".format(asset=asset_id))
                raise MasExecutionError(output_object.return_output_object())
    elif file_type in valid_video_types:
        job_id = start_celebrity_recognition(s3bucket, urllib.parse.unquote_plus(s3key))
        output_object.update_workflow_status("Executing")
        output_object.add_workflow_metadata(CelebrityRecognitionJobId=job_id, AssetId=asset_id, WorkflowExecutionId=workflow_id)
        return output_object.return_output_object()
    else:
        print("ERROR: invalid file type")
        output_object.update_workflow_status("Error")
        output_object.add_workflow_metadata(CelebrityRecognitionError="Not a valid file type")
        raise MasExecutionError(output_object.return_output_object())
