# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import os
import boto3
from botocore import config
import json
from MediaInsightsEngineLambdaHelper import MediaInsightsOperationHelper
from MediaInsightsEngineLambdaHelper import MasExecutionError
from MediaInsightsEngineLambdaHelper import DataPlane

mie_config = json.loads(os.environ['botoConfig'])
config = config.Config(**mie_config)
comprehend = boto3.client('comprehend', config=config)
s3 = boto3.client('s3')
comprehend_role = os.environ['comprehendRole']
region = os.environ['AWS_REGION']
headers = {"Content-Type": "application/json"}


def lambda_handler(event, context):
    #print("We got this event:\n", event)

    operator_object = MediaInsightsOperationHelper(event)

    try:
        workflow_id = operator_object.workflow_execution_id
    except KeyError as e:
        operator_object.update_workflow_status("Error")
        operator_object.add_workflow_metadata(comprehend_error="Missing a required metadata key {e}".format(e=e))
        raise MasExecutionError(operator_object.return_output_object())

    try:
        bucket = operator_object.input["Media"]["Text"]["S3Bucket"]
        key = operator_object.input["Media"]["Text"]["S3Key"]

        file_ext = str(key.split('.')[-1])
        if file_ext == "json":
            s3 = boto3.client('s3')
            obj = s3.get_object(
                Bucket=bucket,
                Key=key
            )
            results = obj['Body'].read().decode('utf-8')
            results_json = json.loads(results)
            try:
                uri_data = results_json["TextTranscriptUri"]
            except KeyError:
                raise MasExecutionError("JSON can only be passed in from AWS transcribe")
            else:
                uri = "s3://" + uri_data['S3Bucket'] + '/' + uri_data['S3Key']
        else:
            uri = "s3://" + bucket + '/' + key

    except KeyError:
        operator_object.update_workflow_status("Error")
        operator_object.add_workflow_metadata(comprehend_error="No valid inputs")
        raise MasExecutionError(operator_object.return_output_object())

    try:
        asset_id = operator_object.asset_id
    except KeyError:
        print('No asset id for this workflow')
        asset_id = ''

    dataplane = DataPlane()

    output_uri_request = dataplane.generate_media_storage_path(asset_id, workflow_id)

    output_uri = "s3://{bucket}/{key}".format(bucket=output_uri_request["S3Bucket"],
                                              key=output_uri_request["S3Key"] + '/comprehend_entities')

    try:
        comprehend.start_entities_detection_job(
            InputDataConfig={
                "S3Uri": uri,
                "InputFormat": "ONE_DOC_PER_FILE"
            },
            OutputDataConfig={
                "S3Uri": output_uri
            },
            DataAccessRoleArn=comprehend_role,
            JobName=workflow_id,
            LanguageCode="en"
        )
    except Exception as e:
        operator_object.update_workflow_status("Error")
        operator_object.add_workflow_metadata(comprehend_error="Unable to get response from comprehend: {e}".format(e=str(e)))
        raise MasExecutionError(operator_object.return_output_object())
    else:
        comprehend_job_id = workflow_id
        operator_object.add_workflow_metadata(comprehend_entity_job_id=comprehend_job_id, entity_output_uri=output_uri)
        operator_object.update_workflow_status('Executing')
        return operator_object.return_output_object()
