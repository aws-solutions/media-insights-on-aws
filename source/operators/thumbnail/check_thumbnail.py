# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

###############################################################################
# PURPOSE:
#   Add thumbnail, audio track, and proxy encode outputs from mediaconvert to
#   workflow metadata so downstream operators can use them as inputs.
###############################################################################

import os
import boto3

from MediaInsightsEngineLambdaHelper import MediaInsightsOperationHelper
from MediaInsightsEngineLambdaHelper import MasExecutionError

region = os.environ["AWS_REGION"]
mediaconvert = boto3.client("mediaconvert", region_name=region)

def lambda_handler(event, context):
    print("We got the following event:\n", event)
    operator_object = MediaInsightsOperationHelper(event)
    # Get MediaConvert job id
    try:
        job_id = operator_object.metadata["MediaconvertJobId"]
        workflow_id = operator_object.workflow_execution_id
        input_file = operator_object.metadata["MediaconvertInputFile"]
    except KeyError as e:
        operator_object.update_workflow_status("Error")
        operator_object.add_workflow_metadata(MediaconvertError="Missing a required metadata key {e}".format(e=e))
        raise MasExecutionError(operator_object.return_output_object())
    # Get asset id
    try:
        asset_id = operator_object.asset_id
    except KeyError as e:
        print("No asset_id in this workflow")
        asset_id = ''

    # Get mediaconvert endpoint from cache if available
    if ("MEDIACONVERT_ENDPOINT" in os.environ):
        mediaconvert_endpoint = os.environ["MEDIACONVERT_ENDPOINT"]
        customer_mediaconvert = boto3.client("mediaconvert", region_name=region, endpoint_url=mediaconvert_endpoint)
    else:
        try:
            response = mediaconvert.describe_endpoints()
        except Exception as e:
            print("Exception:\n", e)
            operator_object.update_workflow_status("Error")
            operator_object.add_workflow_metadata(MediaconvertError=str(e))
            raise MasExecutionError(operator_object.return_output_object())
        else:
            mediaconvert_endpoint = response["Endpoints"][0]["Url"]
            # Cache the mediaconvert endpoint in order to avoid getting throttled on
            # the DescribeEndpoints API.
            os.environ["MEDIACONVERT_ENDPOINT"] = mediaconvert_endpoint
            customer_mediaconvert = boto3.client("mediaconvert", region_name=region, endpoint_url=mediaconvert_endpoint)

    # Get MediaConvert job results
    try:
        response = customer_mediaconvert.get_job(Id=job_id)
    except Exception as e:
        print("Exception:\n", e)
        operator_object.update_workflow_status("Error")
        operator_object.add_workflow_metadata(MediaconvertError=e, MediaconvertJobId=job_id)
        raise MasExecutionError(operator_object.return_output_object())
    else:
        if response["Job"]["Status"] == 'IN_PROGRESS' or response["Job"]["Status"] == 'PROGRESSING':
            operator_object.update_workflow_status("Executing")
            operator_object.add_workflow_metadata(MediaconvertJobId=job_id, MediaconvertInputFile=input_file, AssetId=asset_id, WorkflowExecutionId=workflow_id)
            return operator_object.return_output_object()
        elif response["Job"]["Status"] == 'COMPLETE':
            input_filename = os.path.splitext(operator_object.metadata["MediaconvertInputFile"].split("/")[-1])[0]
            # Get Thumbnail object
            thumbnail_output_uri = response["Job"]["Settings"]["OutputGroups"][0]["OutputGroupSettings"]["FileGroupSettings"]["Destination"]
            thumbnail_extension = response["Job"]["Settings"]["OutputGroups"][0]["Outputs"][0]["Extension"]
            thumbnail_modifier = response["Job"]["Settings"]["OutputGroups"][0]["Outputs"][0]["NameModifier"]
            thumbnail_bucket = thumbnail_output_uri.split("/")[2]
            thumbnail_folder = "/".join(thumbnail_output_uri.split("/")[3:-1])
            thumbnail_key = thumbnail_folder + "/" + input_filename + thumbnail_modifier + "." + thumbnail_extension
            operator_object.add_media_object("Thumbnail", thumbnail_bucket, thumbnail_key)
            # Get audio object
            audio_output_uri = response["Job"]["Settings"]["OutputGroups"][1]["OutputGroupSettings"]["FileGroupSettings"]["Destination"]
            audio_extension = response["Job"]["Settings"]["OutputGroups"][1]["Outputs"][0]["Extension"]
            audio_modifier = response["Job"]["Settings"]["OutputGroups"][1]["Outputs"][0]["NameModifier"]
            audio_bucket = audio_output_uri.split("/")[2]
            audio_folder = "/".join(audio_output_uri.split("/")[3:-1])
            audio_key = audio_folder + "/" + input_filename + audio_modifier + "." + audio_extension
            operator_object.add_media_object("Audio", audio_bucket, audio_key)
            operator_object.add_workflow_metadata(MediaconvertJobId=job_id)
            # Get mp4 proxy encode object
            proxy_encode_output_uri = response["Job"]["Settings"]["OutputGroups"][2]["OutputGroupSettings"]["FileGroupSettings"]["Destination"]
            proxy_encode_extension = response["Job"]["Settings"]["OutputGroups"][2]["Outputs"][0]["Extension"]
            proxy_encode_modifier = response["Job"]["Settings"]["OutputGroups"][2]["Outputs"][0]["NameModifier"]
            proxy_encode_bucket = proxy_encode_output_uri.split("/")[2]
            proxy_encode_folder = "/".join(proxy_encode_output_uri.split("/")[3:-1])
            proxy_encode_key = proxy_encode_folder + "/" + input_filename + proxy_encode_modifier + "." + proxy_encode_extension
            operator_object.add_media_object("ProxyEncode", proxy_encode_bucket, proxy_encode_key)
            # Set workflow status complete
            operator_object.update_workflow_status("Complete")
            return operator_object.return_output_object()
        else:
            operator_object.update_workflow_status("Error")
            operator_object.add_workflow_metadata(
                MediaconvertError="Unhandled exception, unable to get status from mediaconvert: {response}".format(response=response), MediaconvertJobId=job_id)
            raise MasExecutionError(operator_object.return_output_object())

