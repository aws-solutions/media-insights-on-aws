# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

###############################################################################
# PURPOSE:
#   Lambda function to check the status of a Rekognition job processing a media object
#
# REFERENCE:
# https://github.com/awsdocs/amazon-rekognition-developer-guide/blob/master/code_examples/python_examples/stored_video/python-rek-video.py
###############################################################################

import os
import boto3
import json
from botocore import config
from MediaInsightsEngineLambdaHelper import OutputHelper
from MediaInsightsEngineLambdaHelper import MasExecutionError
from MediaInsightsEngineLambdaHelper import DataPlane

operator_name = os.environ['OPERATOR_NAME']
output_object = OutputHelper(operator_name)

mie_config = json.loads(os.environ['botoConfig'])
config = config.Config(**mie_config)
rek = boto3.client('rekognition', config=config)


def lambda_handler(event, context):
    try:
        status = event["Status"]
        asset_id = event['MetaData']['AssetId']
    except KeyError as e:
        output_object.update_workflow_status("Error")
        output_object.add_workflow_metadata(PersonTrackingError="Missing key {e}".format(e=e))
        raise MasExecutionError(output_object.return_output_object())
    # Images will have already been processed, so return if job status is already set.
    if status == "Complete":
        # TODO: Persist rekognition output
        output_object.update_workflow_status("Complete")
        return output_object.return_output_object()

    try:
        job_id = event["MetaData"]["PersonTrackingJobId"]
        workflow_id = event["MetaData"]["WorkflowExecutionId"]
    except KeyError as e:
        output_object.update_workflow_status("Error")
        output_object.add_workflow_metadata(PersonTrackingError="Missing a required metadata key {e}".format(e=e))
        raise MasExecutionError(output_object.return_output_object())

    # Check rekognition job status:
    dataplane = DataPlane()
    max_results = 1000
    pagination_token = ''
    finished = False
    # Pagination starts on 1001th result. This while loops through each page.
    while not finished:
        response = rek.get_person_tracking(JobId=job_id,
                                           MaxResults=max_results,
                                           NextToken=pagination_token)

        if response['JobStatus'] == "IN_PROGRESS":
            finished = True
            output_object.update_workflow_status("Executing")
            output_object.add_workflow_metadata(PersonTrackingJobId=job_id, AssetId=asset_id, WorkflowExecutionId=workflow_id)
            return output_object.return_output_object()
        elif response['JobStatus'] == "FAILED":
            finished = True
            output_object.update_workflow_status("Error")
            output_object.add_workflow_metadata(PersonTrackingJobId=job_id,
                                          PersonTrackingError=str(response["StatusMessage"]))
            raise MasExecutionError(output_object.return_output_object())
        elif response['JobStatus'] == "SUCCEEDED":
            if 'NextToken' in response:
                pagination_token = response['NextToken']
                # Persist rekognition results (current page)
                metadata_upload = dataplane.store_asset_metadata(asset_id, operator_name, workflow_id, response)
                if "Status" not in metadata_upload:
                    output_object.update_workflow_status("Error")
                    output_object.add_workflow_metadata(
                        PersonTrackingError="Unable to upload metadata for asset: {asset}".format(asset=asset_id))
                    raise MasExecutionError(output_object.return_output_object())
                else:
                    if metadata_upload["Status"] == "Success":
                        print("Uploaded metadata for asset: {asset}".format(asset=asset_id))
                    elif metadata_upload["Status"] == "Failed":
                        output_object.update_workflow_status("Error")
                        output_object.add_workflow_metadata(
                            PersonTrackingError="Unable to upload metadata for asset: {asset}".format(asset=asset_id))
                        raise MasExecutionError(output_object.return_output_object())
                    else:
                        output_object.update_workflow_status("Error")
                        output_object.add_workflow_metadata(
                            PersonTrackingError="Unable to upload metadata for asset: {asset}".format(asset=asset_id))
                        raise MasExecutionError(output_object.return_output_object())
            else:
                finished = True
                # Persist rekognition results
                metadata_upload = dataplane.store_asset_metadata(asset_id, operator_name, workflow_id, response)
                if "Status" not in metadata_upload:
                    output_object.update_workflow_status("Error")
                    output_object.add_workflow_metadata(
                        PersonTrackingError="Unable to upload metadata for asset: {asset}".format(asset=asset_id))
                    raise MasExecutionError(output_object.return_output_object())
                else:
                    if metadata_upload["Status"] == "Success":
                        print("Uploaded metadata for asset: {asset}".format(asset=asset_id))
                        output_object.update_workflow_status("Complete")
                        return output_object.return_output_object()
                    elif metadata_upload["Status"] == "Failed":
                        output_object.update_workflow_status("Error")
                        output_object.add_workflow_metadata(
                            PersonTrackingError="Unable to upload metadata for asset: {asset}".format(asset=asset_id))
                        raise MasExecutionError(output_object.return_output_object())
                    else:
                        output_object.update_workflow_status("Error")
                        output_object.add_workflow_metadata(
                            PersonTrackingError="Unable to upload metadata for asset: {asset}".format(asset=asset_id))
                        output_object.add_workflow_metadata(PersonTrackingJobId=job_id)
                        raise MasExecutionError(output_object.return_output_object())
        else:
            output_object.update_workflow_status("Error")
            output_object.add_workflow_metadata(PersonTrackingError="Unable to determine status")
            raise MasExecutionError(output_object.return_output_object())
