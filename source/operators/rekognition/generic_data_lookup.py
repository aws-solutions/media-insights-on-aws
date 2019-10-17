# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

###############################################################################
# PURPOSE:
#   JSON datasets can be precomputed and uploaded along with their associated
#   media files to MIE. This lambda function is an operator that puts that
#   precomputed data into DynamoDB. Don't forget to extend the Elasticsearch
#   consumer (source/consumers/elastic/lambda_handler.py) if you want said data
#   to be added to Elasticsearch so it can be searched and rendered on the MIE
#   front-end.
#
# USAGE:
#   JSON datasets must have the same filename as the associated video file. For
#   example, "Demo Video 01.mp4" must have data file "Demo Video 01.json".
#   Upload both files to the MIE dataplane bucket then add
#   '"GenericDataLookup":{"Enabled":true}' to workflow configuration, like
#   this:
#
#   curl -k -X POST -H "Content-Type: application/json" --data '{"Name":"MieCompleteWorkflow","Configuration":{"defaultVideoStage":{"GenericDataLookup":{"Enabled":true}}},"Input":{"Media":{"Video":{"S3Bucket":"'$DATAPLANE_BUCKET'","S3Key":"My Video.mp4"}}}}'  $WORKFLOW_API_ENDPOINT/workflow/execution
#
###############################################################################

import os
import json
import urllib
import boto3
from MediaInsightsEngineLambdaHelper import OutputHelper
from MediaInsightsEngineLambdaHelper import MasExecutionError
from MediaInsightsEngineLambdaHelper import DataPlane

operator_name = os.environ['OPERATOR_NAME']
output_object = OutputHelper(operator_name)


# Lookup labels from data file in S3
def lookup_labels(bucket, key):
    s3 = boto3.client('s3')
    try:
        # TODO: Use an operator configuration parameter to pass in s3uri for JSON data
        media_filename = key.split("/")[-1]
        data_filename = '.'.join(media_filename.split(".")[:-1])+".json"
        print("Getting data from s3://"+bucket+"/"+data_filename)
        data = s3.get_object(Bucket=bucket, Key=data_filename)
        return json.loads(data['Body'].read().decode('utf-8'))
    except Exception as e:
        output_object.update_workflow_status("Error")
        output_object.add_workflow_metadata(DataLookupError=str(e))
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
        output_object.add_workflow_metadata(DataLookupError="No valid inputs")
        raise MasExecutionError(output_object.return_output_object())
    print("Processing s3://"+s3bucket+"/"+s3key)
    valid_file_types = [".avi", ".mp4", ".mov", ".png", ".jpg", ".jpeg"]
    file_type = os.path.splitext(s3key)[1]
    if file_type in valid_file_types:
        # Getting labels from S3 is a synchronous operation.
        response = lookup_labels(s3bucket, urllib.parse.unquote_plus(s3key))
        print("lookup response: " + str(response)[0:200] + "...")
        if (type(response) != dict):
            output_object.update_workflow_status("Error")
            output_object.add_workflow_metadata(
                DataLookupError="Metadata must be of type dict. Found " + str(type(response)) + " instead.")
            raise MasExecutionError(output_object.return_output_object())
        output_object.add_workflow_metadata(AssetId=asset_id,WorkflowExecutionId=workflow_id)
        dataplane = DataPlane()
        metadata_upload = dataplane.store_asset_metadata(asset_id, operator_name, workflow_id, response)
        if "Status" not in metadata_upload:
            output_object.update_workflow_status("Error")
            output_object.add_workflow_metadata(
                DataLookupError="Unable to upload metadata for asset: {asset}".format(asset=asset_id))
            raise MasExecutionError(output_object.return_output_object())
        else:
            if metadata_upload["Status"] == "Success":
                print("Uploaded metadata for asset: {asset}".format(asset=asset_id))
                output_object.update_workflow_status("Complete")
                return output_object.return_output_object()
            elif metadata_upload["Status"] == "Failed":
                output_object.update_workflow_status("Error")
                output_object.add_workflow_metadata(
                    DataLookupError="Unable to upload metadata for asset: {asset}".format(asset=asset_id))
                raise MasExecutionError(output_object.return_output_object())
            else:
                output_object.update_workflow_status("Error")
                output_object.add_workflow_metadata(
                    DataLookupError="Unable to upload metadata for asset: {asset}".format(asset=asset_id))
                raise MasExecutionError(output_object.return_output_object())
