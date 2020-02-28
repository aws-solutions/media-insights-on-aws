# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
###############################################################################
# PURPOSE:
#   Get MediaInfo output for a media file.
# USAGE:
#   Make sure the LD_LIBRARY_PATH environment variable points to a directory
#   holding MediaInfo ".so" library files
#
# SAMPLE INPUT:
#     {
#         "Name": "Mediainfo",
#         "AssetId": "16924c5f-2ac9-4a9b-993f-6904a2ea2bc0",
#         "WorkflowExecutionId": "93a3833b-facf-4989-af67-ddf134f88d8f",
#         "Input": {
#             "Media": {
#                 "Video": {
#                     "S3Bucket": "mie03-dataplane-19omj1cwr101y",
#                     "S3Key": "private/assets/16924c5f-2ac9-4a9b-993f-6904a2ea2bc0/input/my_video.mp4"
#                 }
#             },
#             "MetaData": {}
#         },
#         "Configuration": {
#             "MediaType": "Video",
#             "Enabled": "True"
#         },
#         "Status": "Started",
#         "MetaData": {},
#         "Media": {}
#     }
###############################################################################

import os
import json
import boto3
from pymediainfo import MediaInfo

from MediaInsightsEngineLambdaHelper import MediaInsightsOperationHelper
from MediaInsightsEngineLambdaHelper import MasExecutionError
from MediaInsightsEngineLambdaHelper import DataPlane
from botocore.config import Config

region = os.environ['AWS_REGION']

def get_signed_url(expires_in, bucket, obj):
    """
    Generate a signed URL
    :param expires_in:  URL Expiration time in seconds
    :param bucket:
    :param obj:         S3 Key name
    :return:            Signed URL
    """
    s3_cli = boto3.client("s3", region_name=region, config = Config(signature_version = 's3v4', s3={'addressing_style': 'virtual'}))
    presigned_url = s3_cli.generate_presigned_url('get_object', Params={'Bucket': bucket, 'Key': obj}, ExpiresIn=expires_in)
    return presigned_url

def lambda_handler(event, context):
    print("We got the following event:\n", event)
    operator_object = MediaInsightsOperationHelper(event)

    try:
        workflow_id = str(operator_object.workflow_execution_id)
        bucket = operator_object.input["Media"]["Video"]["S3Bucket"]
        key = operator_object.input["Media"]["Video"]["S3Key"]
    except KeyError as e:
        operator_object.update_workflow_status("Error")
        operator_object.add_workflow_metadata(MediaconvertError="Missing a required metadata key {e}".format(e=e))
        raise MasExecutionError(operator_object.return_output_object())

    # Adding in exception block for now since we aren't guaranteed an asset id will be present, should remove later
    try:
        asset_id = operator_object.asset_id
    except KeyError as e:
        print("No asset id passed in with this workflow", e)
        asset_id = ''

    # Get metadata
    try:
        # The number of seconds that the Signed URL is valid:
        signed_url_expiration = 300
        # Generate a signed URL for the uploaded asset
        signed_url = get_signed_url(signed_url_expiration, bucket, key)
        # Launch MediaInfo
        media_info = MediaInfo.parse(signed_url)
        # Save the result
        metadata_json = json.loads(media_info.to_json())
    except Exception as e:
        print("Exception:\n", e)
        operator_object.update_workflow_status("Error")
        operator_object.add_workflow_metadata(MediainfoError="Unable to get Mediainfo results. " + str(e))
        raise MasExecutionError(operator_object.return_output_object())

    # Verify that the metadata is a dict, as required by the dataplane
    if (type(metadata_json) != dict):
        operator_object.update_workflow_status("Error")
        operator_object.add_workflow_metadata(
            MediainfoError="Metadata must be of type dict. Found " + str(type(metadata_json)) + " instead.")
        raise MasExecutionError(operator_object.return_output_object())

    # Pass metadata to downstream operators
    # Number of audio tracks is used by the Transcribe operator
    num_audio_tracks = len(list(filter(lambda i: i['track_type'] == 'Audio', metadata_json['tracks'])))
    operator_object.add_workflow_metadata(Mediainfo_num_audio_tracks=str(num_audio_tracks))

    # Save metadata to dataplane
    operator_object.add_workflow_metadata(AssetId=asset_id,WorkflowExecutionId=workflow_id)
    dataplane = DataPlane()
    metadata_upload = dataplane.store_asset_metadata(asset_id, operator_object.name, workflow_id, metadata_json)

    # Validate that the metadata was saved to the dataplane
    if "Status" not in metadata_upload:
        operator_object.add_workflow_metadata(
            MediainfoError="Unable to upload metadata for asset: {asset}".format(asset=asset_id))
        operator_object.update_workflow_status("Error")
        raise MasExecutionError(operator_object.return_output_object())
    else:
        # Update the workflow status
        if metadata_upload["Status"] == "Success":
            print("Uploaded metadata for asset: {asset}".format(asset=asset_id))
            operator_object.update_workflow_status("Complete")
            return operator_object.return_output_object()
        else:
            operator_object.add_workflow_metadata(
                MediainfoError="Unable to upload metadata for asset: {asset}".format(asset=asset_id))
            operator_object.update_workflow_status("Error")
            raise MasExecutionError(operator_object.return_output_object())
