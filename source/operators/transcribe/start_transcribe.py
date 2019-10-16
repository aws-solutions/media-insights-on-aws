# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import os
import boto3
import json
from botocore import config
from MediaInsightsEngineLambdaHelper import MediaInsightsOperationHelper
from MediaInsightsEngineLambdaHelper import MasExecutionError

region = os.environ['AWS_REGION']

mie_config = json.loads(os.environ['botoConfig'])
config = config.Config(**mie_config)
transcribe = boto3.client("transcribe", config=config)

# TODO: More advanced exception handling, e.g. using boto clienterrors and narrowing exception scopes


def lambda_handler(event, context):
        
        
        valid_types = ["mp3", "mp4", "wav", "flac"]
        optional_settings = {}

        operator_object = MediaInsightsOperationHelper(event)
        workflow_id = str(operator_object.workflow_execution_id)
        job_id = "transcribe" + "-" + workflow_id

        # Adding in exception block for now since we aren't guaranteed an asset id will be present, should remove later
        try:
            asset_id = operator_object.asset_id
        except KeyError as e:
            print("No asset id passed in with this workflow", e)
            asset_id = ''

        try:
            bucket = operator_object.input["Media"]["Audio"]["S3Bucket"]
            key = operator_object.input["Media"]["Audio"]["S3Key"]
            file_type = key.split('.')[-1]
        # TODO: Do we want to add support for video?
        except KeyError:
            bucket = operator_object.input["Media"]["Video"]["S3Bucket"]
            key = operator_object.input["Media"]["Video"]["S3Key"]
            file_type = os.path.splitext(key)[1]
        except Exception:
            operator_object.update_workflow_status("Error")
            operator_object.add_workflow_metadata(TranscribeError="No valid inputs")
            raise MasExecutionError(operator_object.return_output_object())
        if file_type not in valid_types:
            operator_object.update_workflow_status("Error")
            operator_object.add_workflow_metadata(TranscribeError="Not a valid file type")
            raise MasExecutionError(operator_object.return_output_object())
        try:
            custom_vocab = operator_object.configuration["VocabularyName"]
            optional_settings["VocabularyName"] = custom_vocab
        except KeyError:
            # No custom vocab
            pass
        try:
            language_code = operator_object.configuration["TranscribeLanguage"]
        except KeyError:
            operator_object.update_workflow_status("Error")
            operator_object.add_workflow_metadata(TranscribeError="No language code defined")
            raise MasExecutionError(operator_object.return_output_object())

        media_file = 'https://s3.' + region + '.amazonaws.com/' + bucket + '/' + key

        try:
            response = transcribe.start_transcription_job(
                TranscriptionJobName=job_id,
                LanguageCode=language_code,
                Media={
                    "MediaFileUri": media_file
                },
                MediaFormat=file_type,
                Settings=optional_settings
            )
            print(response)
        except Exception as e:
            operator_object.update_workflow_status("Error")
            operator_object.add_workflow_metadata(transcribe_error=str(e))
            raise MasExecutionError(operator_object.return_output_object())
        else:
            if response["TranscriptionJob"]["TranscriptionJobStatus"] == "IN_PROGRESS":
                operator_object.update_workflow_status("Executing")
                operator_object.add_workflow_metadata(TranscribeJobId=job_id, AssetId=asset_id, WorkflowExecutionId=workflow_id)
                return operator_object.return_output_object()
            elif response["TranscriptionJob"]["TranscriptionJobStatus"] == "FAILED":
                operator_object.update_workflow_status("Error")
                operator_object.add_workflow_metadata(TranscribeJobId=job_id, TranscribeError=str(response["TranscriptionJob"]["FailureReason"]))
                raise MasExecutionError(operator_object.return_output_object())
            elif response["TranscriptionJob"]["TranscriptionJobStatus"] == "COMPLETE":
                operator_object.update_workflow_status("Executing")
                operator_object.add_workflow_metadata(TranscribeJobId=job_id, AssetId=asset_id, WorkflowExecutionId=workflow_id)
                return operator_object.return_output_object()
            else:
                operator_object.update_workflow_status("Error")
                operator_object.add_workflow_metadata(TranscribeJobId=job_id,
                                              TranscribeError="Unhandled error for this job: {job_id}".format(job_id=job_id))
                raise MasExecutionError(operator_object.return_output_object())
