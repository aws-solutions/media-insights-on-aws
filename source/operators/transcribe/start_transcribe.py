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


def get_media_location_from_event(event, operator_object):
    valid_types = ["mp3", "mp4", "wav", "flac"]
    try:
        media = event["Input"]["Media"]
        if "ProxyEncode" in media:
            location = media["ProxyEncode"]
        elif "Video" in media:
            location = media["Video"]
        else:
            location = media["Audio"]
        bucket = location["S3Bucket"]
        key = location["S3Key"]
    except Exception:
        operator_object.update_workflow_status("Error")
        operator_object.add_workflow_metadata(TranscribeError="No valid inputs")
        raise MasExecutionError(operator_object.return_output_object())

    file_type = key.split('.')[-1]

    if file_type not in valid_types:
        operator_object.update_workflow_status("Error")
        operator_object.add_workflow_metadata(TranscribeError="Not a valid file type")
        raise MasExecutionError(operator_object.return_output_object())

    return (bucket, key, file_type)


def copy_optional_setting(src, dst, name):
    if name in src:
        dst[name] = src[name]


def set_optional_setting_if_not_empty(dst, name, optional_setting):
    if len(optional_setting) > 0:
        dst[name] = optional_setting


def lambda_handler(event, _context):
    print("We got this event:\n", event)
    transcribe_job_config = {}
    optional_settings = {}
    model_settings = {}
    job_execution_settings = {}
    content_redaction_settings = {}
    operator_object = MediaInsightsOperationHelper(event)
    workflow_id = str(event["WorkflowExecutionId"])
    asset_id = event['AssetId']
    job_id = "transcribe" + "-" + workflow_id

    (bucket, key, file_type) = get_media_location_from_event(event, operator_object)

    try:
        custom_vocab = operator_object.configuration["VocabularyName"]
        optional_settings["VocabularyName"] = custom_vocab
    except KeyError:
        # No custom vocab
        pass

    # Language is automatically identified if not explicitly defined or defined as 'auto'
    language_code = operator_object.configuration.get("TranscribeLanguage", 'auto')
    identify_language = language_code == 'auto' or operator_object.configuration.get("IdentifyLanguage", False)

    media_file = 'https://s3.' + region + '.amazonaws.com/' + bucket + '/' + key

    # Read optional transcription job settings:
    copy_optional_setting(operator_object.configuration, optional_settings, "VocabularyName")
    copy_optional_setting(operator_object.configuration, optional_settings, "ShowSpeakerLabels")
    copy_optional_setting(operator_object.configuration, optional_settings, "MaxSpeakerLabels")
    copy_optional_setting(operator_object.configuration, optional_settings, "ChannelIdentification")
    copy_optional_setting(operator_object.configuration, optional_settings, "MaxAlternatives")
    copy_optional_setting(operator_object.configuration, optional_settings, "VocabularyFilterName")
    copy_optional_setting(operator_object.configuration, optional_settings, "VocabularyFilterMethod")
    copy_optional_setting(operator_object.configuration, model_settings, "LanguageModelName")
    copy_optional_setting(operator_object.configuration, job_execution_settings, "AllowDeferredExecution")
    copy_optional_setting(operator_object.configuration, job_execution_settings, "DataAccessRoleArn")
    copy_optional_setting(operator_object.configuration, content_redaction_settings, "RedactionType")
    copy_optional_setting(operator_object.configuration, content_redaction_settings, "RedactionOutput")
    language_options = operator_object.configuration.get("LanguageOptions", [])

    # Combine all the defined transcription job settings into a single dict:
    transcribe_job_config["TranscriptionJobName"] = job_id
    transcribe_job_config["Media"] = {"MediaFileUri": media_file}
    transcribe_job_config["MediaFormat"] = file_type
    if not identify_language:
        transcribe_job_config["LanguageCode"] = language_code
    transcribe_job_config["IdentifyLanguage"] = identify_language
    set_optional_setting_if_not_empty(transcribe_job_config, "Settings", optional_settings)
    set_optional_setting_if_not_empty(transcribe_job_config, "ModelSettings", model_settings)
    set_optional_setting_if_not_empty(transcribe_job_config, "JobExecutionSettings", job_execution_settings)
    set_optional_setting_if_not_empty(transcribe_job_config, "ContentRedaction", content_redaction_settings)
    set_optional_setting_if_not_empty(transcribe_job_config, "LanguageOptions", language_options)

    # If mediainfo data is available then use it to avoid transcribing silent videos.
    # Check to see if audio tracks were detected by mediainfo
    if event["Input"]["MetaData"].get("Mediainfo_num_audio_tracks", "0") == "0":
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

    if response["TranscriptionJob"]["TranscriptionJobStatus"] in ("IN_PROGRESS", "COMPLETE"):
        operator_object.update_workflow_status("Executing")
        operator_object.add_workflow_metadata(TranscribeJobId=job_id, AssetId=asset_id, WorkflowExecutionId=workflow_id)
        return operator_object.return_output_object()
    elif response["TranscriptionJob"]["TranscriptionJobStatus"] == "FAILED":
        operator_object.update_workflow_status("Error")
        operator_object.add_workflow_metadata(TranscribeJobId=job_id, TranscribeError=str(response["TranscriptionJob"]["FailureReason"]))
        raise MasExecutionError(operator_object.return_output_object())
    else:
        operator_object.update_workflow_status("Error")
        operator_object.add_workflow_metadata(TranscribeJobId=job_id, TranscribeError="Unhandled error for this job: {job_id}".format(
                                              job_id=job_id))
        raise MasExecutionError(operator_object.return_output_object())
