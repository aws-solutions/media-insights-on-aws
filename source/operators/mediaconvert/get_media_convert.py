# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import os
import boto3

from MediaInsightsEngineLambdaHelper import MediaInsightsOperationHelper
from MediaInsightsEngineLambdaHelper import MasExecutionError

region = os.environ["AWS_REGION"]

mediaconvert = boto3.client("mediaconvert", region_name=region)


def lambda_handler(event, context):
    print("We got the following event:\n", event)
    
    operator_object = MediaInsightsOperationHelper(event)

    try:
        job_id = operator_object.metadata["MediaconvertJobId"]
        workflow_id = operator_object.workflow_execution_id
        input_file = operator_object.metadata["MediaconvertInputFile"]
    except KeyError as e:
        operator_object.update_workflow_status("Error")
        operator_object.add_workflow_metadata(MediaconvertError="Missing a required metadata key {e}".format(e=e))
        raise MasExecutionError(operator_object.return_output_object())

    try:
        asset_id = operator_object.asset_id
    except KeyError as e:
        print("No asset_id in this workflow")
        asset_id = ''

    try:
        response = mediaconvert.describe_endpoints()
    except Exception as e:
        print("Exception:\n", e)
        operator_object.update_workflow_status("Error")
        operator_object.add_workflow_metadata(MediaconvertError=str(e))
        raise MasExecutionError(operator_object.return_output_object())
    else:
        mediaconvert_endpoint = response["Endpoints"][0]["Url"]
        customer_mediaconvert = boto3.client("mediaconvert", region_name=region, endpoint_url=mediaconvert_endpoint)

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
            operator_object.add_workflow_metadata(MediaconvertJobId=job_id,
                                          MediaconvertInputFile=input_file,
                                          AssetId=asset_id, WorkflowExecutionId=workflow_id)
            return operator_object.return_output_object()
        elif response["Job"]["Status"] == 'COMPLETE':
            # TODO: Store job details as metadata in dataplane
            # TODO: Get output uri from dataplane
            output_uri = response["Job"]["Settings"]["OutputGroups"][0]["OutputGroupSettings"]["FileGroupSettings"][
                "Destination"]

            extension = response["Job"]["Settings"]["OutputGroups"][0]["Outputs"][0]["Extension"]
            modifier = response["Job"]["Settings"]["OutputGroups"][0]["Outputs"][0]["NameModifier"]

            bucket = output_uri.split("/")[2]
            folder = "/".join(output_uri.split("/")[3:-1])

            file_name = operator_object.metadata["MediaconvertInputFile"].split("/")[-1].split(".")[0]

            key = folder + "/" + file_name + modifier + "." + extension

            operator_object.add_media_object("Audio", bucket, key)
            operator_object.add_workflow_metadata(MediaconvertJobId=job_id)
            operator_object.update_workflow_status("Complete")

            return operator_object.return_output_object()
        else:
            operator_object.update_workflow_status("Error")
            operator_object.add_workflow_metadata(
                MediaconvertError="Unhandled exception, unable to get status from mediaconvert: {response}".format(
                    response=response),
                MediaconvertJobId=job_id)
            raise MasExecutionError(operator_object.return_output_object())

