# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

###############################################################################
# PURPOSE:
#   Lambda function to check the status of a Rekognition job and save that job's
#   data to the MIE dataplane when the job is complete.
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
    print("We got the following event:\n", event)
    try:
        status = event["Status"]
        asset_id = event['MetaData']['AssetId']
    except KeyError as e:
        output_object.update_workflow_status("Error")
        output_object.add_workflow_metadata(FaceDetectionError="Missing key {e}".format(e=e))
        raise MasExecutionError(output_object.return_output_object())
    # Images will have already been processed, so return if job status is already set.
    if status == "Complete":
        print ("Marking workflow Complete")
        output_object.update_workflow_status("Complete")
        return output_object.return_output_object()
    try:
        job_id = event["MetaData"]["JobId"]
        workflow_id = event["MetaData"]["WorkflowExecutionId"]
    except KeyError as e:
        output_object.update_workflow_status("Error")
        output_object.add_workflow_metadata(FaceDetectionError="Missing a required metadata key {e}".format(e=e))
        raise MasExecutionError(output_object.return_output_object())
    # Check rekognition job status:
    dataplane = DataPlane()
    pagination_token = ''
    is_paginated = False
    # If pagination token is in event["MetaData"] then use that to start
    # reading reko results from where this Lambda's previous invocation left off.
    if ("PageToken" in event["MetaData"]):
        pagination_token = event["MetaData"]["PageToken"]
        is_paginated = True
    # Read and persist 10 reko pages per invocation of this Lambda
    for page_number in range(11):
        # Get reko results
        print("job id: " + job_id + " page token: " + pagination_token)
        try:
            response = rek.get_face_detection(JobId=job_id, NextToken=pagination_token)
        except rek.exceptions.InvalidPaginationTokenException as e:
            # Trying to reverse seek to the last valid pagination token would be difficult
            # to implement, so in the rare case that a pagination token expires we'll
            # just start over by reading from the first page.
            print(e)
            print("WARNING: Invalid pagination token found. Restarting read from first page.")
            pagination_token = ''
            continue
        # If the reko job is IN_PROGRESS then return. We'll check again after a step function wait.
        if response['JobStatus'] == "IN_PROGRESS":
            output_object.update_workflow_status("Executing")
            output_object.add_workflow_metadata(JobId=job_id, AssetId=asset_id, WorkflowExecutionId=workflow_id)
            return output_object.return_output_object()
        # If the reko job is FAILED then mark the workflow status as Error and return.
        elif response['JobStatus'] == "FAILED":
            output_object.update_workflow_status("Error")
            output_object.add_workflow_metadata(JobId=job_id, FaceDetectionError=str(response["StatusMessage"]))
            raise MasExecutionError(output_object.return_output_object())
        # If the reko job is SUCCEEDED then save this current reko page result
        # and continue to next page_number.
        elif response['JobStatus'] == "SUCCEEDED":
            # If reko results contain more pages then save this page and continue to the next page
            if 'NextToken' in response:
                is_paginated = True
                # Persist rekognition results (current page)
                metadata_upload = dataplane.store_asset_metadata(asset_id=asset_id, operator_name=operator_name, workflow_id=workflow_id, results=response, paginate=True, end=False)
                # If dataplane request succeeded then get the next pagination token and continue.
                if "Status" in metadata_upload and metadata_upload["Status"] == "Success":
                    # Log that this page has been successfully uploaded to the dataplane
                    print("Uploaded metadata for asset: {asset}, job {JobId}, page {page}".format(asset=asset_id, JobId=job_id, page=pagination_token))
                    # Get the next pagination token:
                    pagination_token = response['NextToken']
                    # In order to avoid Lambda timeouts, we're only going to persist 10 pages then
                    # pass the pagination token to the workflow metadata and let our step function
                    # invoker restart this Lambda. The pagination token allows this Lambda
                    # continue from where it left off.
                    if page_number == 10:
                        output_object.update_workflow_status("Executing")
                        output_object.add_workflow_metadata(PageToken=pagination_token, JobId=job_id, AssetId=asset_id, WorkflowExecutionId=workflow_id)
                        return output_object.return_output_object()
                # If dataplane request failed then mark workflow as failed
                else:
                    output_object.update_workflow_status("Error")
                    output_object.add_workflow_metadata(FaceDetectionError="Unable to upload metadata for asset: {asset}".format(asset=asset_id), JobId=job_id)
                    raise MasExecutionError(output_object.return_output_object())
            # If reko results contain no more pages then save this page and mark the stage complete
            else:
                # If we've been saving pages, then tell dataplane this is the last page
                if is_paginated:
                    metadata_upload = dataplane.store_asset_metadata(asset_id=asset_id, operator_name=operator_name, workflow_id=workflow_id, results=response, paginate=True, end=True)
                # If there is only one page then save to dataplane without dataplane options
                else:
                    metadata_upload = dataplane.store_asset_metadata(asset_id=asset_id, operator_name=operator_name, workflow_id=workflow_id, results=response)
                # If dataplane request succeeded then mark the stage complete
                if "Status" in metadata_upload and metadata_upload["Status"] == "Success":
                    print("Uploaded metadata for asset: {asset}".format(asset=asset_id))
                    output_object.add_workflow_metadata(JobId=job_id)
                    output_object.update_workflow_status("Complete")
                    return output_object.return_output_object()
                # If dataplane request failed then mark workflow as failed
                else:
                    output_object.update_workflow_status("Error")
                    output_object.add_workflow_metadata(FaceDetectionError="Unable to upload metadata for {asset}: {error}".format(asset=asset_id, error=metadata_upload))
                    output_object.add_workflow_metadata(JobId=job_id)
                    raise MasExecutionError(output_object.return_output_object())
        # If reko job failed then mark workflow as failed
        else:
            output_object.update_workflow_status("Error")
            output_object.add_workflow_metadata(FaceDetectionError="Unable to determine status")
            raise MasExecutionError(output_object.return_output_object())
