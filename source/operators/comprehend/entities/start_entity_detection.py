# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

###############################################################################
# PURPOSE:
#
#   Lambda function to perform Comprehend Entity detection on text.
#
# INPUT:
#
#   This operator recognizes the following field in the Configuration
#   block of the Lambda input:
#
#      KmsKeyId - KMS key ID to use for encryption in the
#        Comprehend service. If not specified, then encryption is not used in the
#        Comprehend job.
#
#   Sample configuration block:
#
#      "Configuration": {
#          "KmsKeyId": "abcd0123-0123-4567-0abc-12345678abc",
#      },
#
#   The IAM policy used for this Lambda function must include the following permissions in order to use KMS Encryption (reference https://docs.aws.amazon.com/comprehend/latest/dg/access-control-managing-permissions.html):
#
#        "kms:CreateGrant",
#        "kms:Decrypt",
#        "kms:GenerateDatakey"
#
###############################################################################

import os
import boto3
from botocore import config
import json
from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.core import patch_all
from MediaInsightsEngineLambdaHelper import MediaInsightsOperationHelper
from MediaInsightsEngineLambdaHelper import MasExecutionError
from MediaInsightsEngineLambdaHelper import DataPlane

patch_all()

mie_config = json.loads(os.environ['botoConfig'])
config = config.Config(**mie_config)
comprehend = boto3.client('comprehend', config=config)
s3 = boto3.client('s3', config=config)
comprehend_role = os.environ['comprehendRole']
region = os.environ['AWS_REGION']
headers = {"Content-Type": "application/json"}


def lambda_handler(event, context):
    print("We got this event:\n", event)
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
        # If operator_object.input["Media"]["Text"]["S3Key"] is a json file,
        # then we're working with metadata about the text file and need to
        # get the actual transcript text from the TextTranscriptUri field.
        # Otherwise we assume operator_object.input["Media"]["Text"]["S3Key"]
        # contains only the transcript text.
        file_ext = str(key.split('.')[-1])
        if file_ext == "json":
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
                bucket = uri_data['S3Bucket']
                key = uri_data['S3Key']
        uri = "s3://" + bucket + '/' + key
        # If input text is empty then we're done.
        response = s3.head_object(Bucket=bucket, Key=key)
        # If a KmsKey is specified as an input to this operator, then use that
        # to enable encryption in the Comprehend job.
        kms_key_id = ""
        if "KmsKeyId" in operator_object.configuration:
            kms_key_id = operator_object.configuration["KmsKeyId"]
            print("Found a KMS Key Id. Encryption will be enabled in the Comprehend job.")
        else:
            print("No KMS Key was specified. Encryption will not be enabled in the Comprehend job.")
        if response['ContentLength'] < 1:
            operator_object.update_workflow_status("Complete")
            operator_object.add_workflow_metadata(comprehend_entity_job_id="Empty input --> empty output.")
            return operator_object.return_output_object()
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
    output_uri = "s3://{bucket}/{key}".format(bucket=output_uri_request["S3Bucket"], key=output_uri_request["S3Key"] + '/comprehend_entities')
    try:
        if kms_key_id != '':
            # If the user specified a KMS key then enable comprehend job encryption.
            comprehend.start_entities_detection_job(
                InputDataConfig={
                    "S3Uri": uri,
                    "InputFormat": "ONE_DOC_PER_FILE"
                },
                OutputDataConfig={
                    "S3Uri": output_uri,
                    "KmsKeyId": kms_key_id
                },
                DataAccessRoleArn=comprehend_role,
                VolumeKmsKeyId=kms_key_id,
                JobName=workflow_id,
                LanguageCode="en"
            )
        else:
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
