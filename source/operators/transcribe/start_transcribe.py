# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import os
import boto3
import json
from botocore import config
from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.core import patch_all
from MediaInsightsEngineLambdaHelper import MediaInsightsOperationHelper
from MediaInsightsEngineLambdaHelper import MasExecutionError
from MediaInsightsEngineLambdaHelper import OutputHelper

patch_all()

region = os.environ['AWS_REGION']

mie_config = json.loads(os.environ['botoConfig'])
config = config.Config(**mie_config)
transcribe = boto3.client("transcribe", config=config)

# TODO: More advanced exception handling, e.g. using boto clienterrors and narrowing exception scopes

def lambda_handler(event, context):
    print("We got this event:\n", event)
    valid_types = ["mp3", "mp4", "wav", "flac"]
    transcribe_job_config = {}
    optional_settings = {}
    model_settings = {}
    job_execution_settings = {}
    content_redaction_settings = {}
    identify_language = False
    language_options = []
    operator_object = MediaInsightsOperationHelper(event)
    workflow_id = str(event["WorkflowExecutionId"])
    asset_id = event['AssetId']
    job_id = "transcribe" + "-" + workflow_id

    try:
        if "ProxyEncode" in event["Input"]["Media"]:
            bucket = event["Input"]["Media"]["ProxyEncode"]["S3Bucket"]
            key = event["Input"]["Media"]["ProxyEncode"]["S3Key"]
        elif "Video" in event["Input"]["Media"]:
            bucket = event["Input"]["Media"]["Video"]["S3Bucket"]
            key = event["Input"]["Media"]["Video"]["S3Key"]
        elif "Audio" in event["Input"]["Media"]:
            bucket = event["Input"]["Media"]["Audio"]["S3Bucket"]
            key = event["Input"]["Media"]["Audio"]["S3Key"]
        file_type = key.split('.')[-1]
    except Exception:
        operator_object.update_workflow_status("Error")
        operator_object.add_workflow_metadata(TranscribeError="No valid inputs")
        raise MasExecutionError(operator_object.return_output_object())

    if file_type not in valid_types:
        operator_object.update_workflow_status("Error")
        operator_object.add_workflow_metadata(TranscribeError="Not a valid file type")
        raise MasExecutionError(operator_object.return_output_object())
    try:
        language_code = operator_object.configuration["TranscribeLanguage"]
    except KeyError:
        operator_object.update_workflow_status("Error")
        operator_object.add_workflow_metadata(TranscribeError="No language code defined")
        raise MasExecutionError(operator_object.return_output_object())

    media_file = 'https://s3.' + region + '.amazonaws.com/' + bucket + '/' + key

    # Read optional transcription job settings:
    if "VocabularyName" in operator_object.configuration:
        option_value = operator_object.configuration["VocabularyName"]
        optional_settings["VocabularyName"] = option_value
    if "ShowSpeakerLabels" in operator_object.configuration:
        option_value = operator_object.configuration["ShowSpeakerLabels"]
        optional_settings["ShowSpeakerLabels"] = option_value
    if "MaxSpeakerLabels" in operator_object.configuration:
        option_value = operator_object.configuration["MaxSpeakerLabels"]
        optional_settings["MaxSpeakerLabels"] = option_value
    if "ChannelIdentification" in operator_object.configuration:
        option_value = operator_object.configuration["ChannelIdentification"]
        optional_settings["ChannelIdentification"] = option_value
    if "MaxAlternatives" in operator_object.configuration:
        option_value = operator_object.configuration["MaxAlternatives"]
        optional_settings["MaxAlternatives"] = option_value
    if "VocabularyFilterName" in operator_object.configuration:
        option_value = operator_object.configuration["VocabularyFilterName"]
        optional_settings["VocabularyFilterName"] = option_value
    if "VocabularyFilterMethod" in operator_object.configuration:
        option_value = operator_object.configuration["VocabularyFilterMethod"]
        optional_settings["VocabularyFilterMethod"] = option_value
    if "LanguageModelName" in operator_object.configuration:
        option_value = operator_object.configuration["LanguageModelName"]
        model_settings["LanguageModelName"] = option_value
    if "AllowDeferredExecution" in operator_object.configuration:
        option_value = operator_object.configuration["AllowDeferredExecution"]
        job_execution_settings["AllowDeferredExecution"] = option_value
    if "DataAccessRoleArn" in operator_object.configuration:
        option_value = operator_object.configuration["DataAccessRoleArn"]
        job_execution_settings["DataAccessRoleArn"] = option_value
    if "RedactionType" in operator_object.configuration:
        option_value = operator_object.configuration["RedactionType"]
        content_redaction_settings["RedactionType"] = option_value
    if "RedactionOutput" in operator_object.configuration:
        option_value = operator_object.configuration["RedactionOutput"]
        content_redaction_settings["RedactionOutput"] = option_value
    if "IdentifyLanguage" in operator_object.configuration:
        option_value = operator_object.configuration["IdentifyLanguage"]
        identify_language = option_value
    if "LanguageOptions" in operator_object.configuration:
        option_value = operator_object.configuration["LanguageOptions"]
        language_options = option_value

    # Combine all the defined transcription job settings into a single dict:
    transcribe_job_config["TranscriptionJobName"] = job_id
    transcribe_job_config["Media"] = {"MediaFileUri": media_file}
    transcribe_job_config["MediaFormat"] = file_type
    transcribe_job_config["LanguageCode"] = language_code
    transcribe_job_config["IdentifyLanguage"] = identify_language
    if len(optional_settings) > 0:
        transcribe_job_config["Settings"] = optional_settings
    if len(model_settings) > 0:
        transcribe_job_config["ModelSettings"] = model_settings
    if len(job_execution_settings) > 0:
        transcribe_job_config["JobExecutionSettings"] = job_execution_settings
    if len(content_redaction_settings) > 0:
        transcribe_job_config["ContentRedaction"] = content_redaction_settings
    if len(language_options) > 0:
        transcribe_job_config["LanguageOptions"] = language_options

    # If mediainfo data is available then use it to avoid transcribing silent videos.
    if "Mediainfo_num_audio_tracks" in event["Input"]["MetaData"]:
        num_audio_tracks = event["Input"]["MetaData"]["Mediainfo_num_audio_tracks"]
        # Check to see if audio tracks were detected by mediainfo
        if num_audio_tracks == "0":
            # If there is no input audio then we're done.
            operator_object.update_workflow_status("Complete")
            return operator_object.return_output_object()

    try:
        # Run the transcribe job.
        # The ** operator converts the job config dict to keyword arguments.
        response = transcribe.start_transcription_job(**transcribe_job_config)
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
            operator_object.add_workflow_metadata(TranscribeJobId=job_id, TranscribeError="Unhandled error for this job: {job_id}".format(
                                                      job_id=job_id))
            raise MasExecutionError(operator_object.return_output_object())
