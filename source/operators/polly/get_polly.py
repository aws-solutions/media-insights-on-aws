# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import boto3
import json
import os
from botocore import config
from MediaInsightsEngineLambdaHelper import MediaInsightsOperationHelper
from MediaInsightsEngineLambdaHelper import MasExecutionError

mie_config = json.loads(os.environ['botoConfig'])
config = config.Config(**mie_config)
polly = boto3.client('polly', config=config)
s3 = boto3.client("s3")


def lambda_handler(event, context):

    print("We got this event:\n", event)

    operator_object = MediaInsightsOperationHelper(event)

    try:
        task_id = operator_object.metadata["PollyJobId"]
        workflow_id = operator_object.workflow_execution_id
        asset_id = operator_object.asset_id
    except KeyError as e:
        operator_object.update_workflow_status("Error")
        operator_object.add_workflow_metadata(PollyError="Missing a required metadata key {e}".format(e=e))
        raise MasExecutionError(operator_object.return_output_object())
    try:
        polly_response = polly.get_speech_synthesis_task(
            TaskId=task_id
        )
    except Exception as e:
        operator_object.update_workflow_status("Error")
        operator_object.add_workflow_metadata(PollyError="Unable to get response from polly: {e}".format(e=str(e)))
        raise MasExecutionError(operator_object.return_output_object())
    else:
        polly_status = polly_response["SynthesisTask"]["TaskStatus"]
        print("The status from polly is:\n", polly_status)
        if polly_status == "inProgress":
            polly_job_id = polly_response["SynthesisTask"]["TaskId"]
            operator_object.add_workflow_metadata(PollyJobId=polly_job_id, AssetId=asset_id, WorkflowExecutionId=workflow_id)
            operator_object.update_workflow_status("Executing")
            return operator_object.return_output_object()
        elif polly_status == "completed":
            # TODO: Store job details as metadata in dataplane

            uri = polly_response["SynthesisTask"]["OutputUri"]
            file = uri.split("/")[5]
            folder = uri.split("/")[4]
            bucket = uri.split("/")[3]
            key = folder + "/" + file

            operator_object.add_workflow_metadata(PollyJobId=task_id)
            operator_object.add_media_object("Audio", bucket, key)
            operator_object.update_workflow_status("Complete")

            return operator_object.return_output_object()

        elif polly_status == "scheduled":
            operator_object.add_workflow_metadata(PollyJobId=task_id, AssetId=asset_id, WorkflowExecutionId=workflow_id)
            operator_object.update_workflow_status("Executing")
            return operator_object.return_output_object()

        elif polly_status == "failed":
            operator_object.update_workflow_status("Error")
            operator_object.add_workflow_metadata(PollyError="Polly returned as failed: {e}".format(e=str(polly_response["SynthesisTask"]["TaskStatusReason"])))
            raise MasExecutionError(operator_object.return_output_object())
        else:
            operator_object.update_workflow_status("Error")
            operator_object.add_workflow_metadata(PollyError="Polly returned as failed: {e}".format(e=str(polly_response["SynthesisTask"]["TaskStatusReason"])))
            raise MasExecutionError(operator_object.return_output_object())


