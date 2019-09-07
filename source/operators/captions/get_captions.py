# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import json
import boto3
import urllib3
import math

from MediaInsightsEngineLambdaHelper import MediaInsightsOperationHelper
from MediaInsightsEngineLambdaHelper import MasExecutionError
from MediaInsightsEngineLambdaHelper import DataPlane

s3 = boto3.client('s3')
s3_resource = boto3.resource('s3')
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
headers = {"Content-Type": "application/json"}
dataplane = DataPlane()


# Create web captions with line by line captions from the transcribe output
def web_captions(event, context):
    print("We got the following event:\n", event)

    operator_object = MediaInsightsOperationHelper(event)

    try:
        bucket = operator_object.input["Media"]["Text"]["S3Bucket"]
        key = operator_object.input["Media"]["Text"]["S3Key"]
    except KeyError as e:
        operator_object.update_workflow_status("Error")
        operator_object.add_workflow_metadata(CaptionsError="No valid inputs {e}".format(e=e))
        raise MasExecutionError(operator_object.return_output_object())

    try:
        workflow_id = operator_object.workflow_execution_id
    except KeyError as e:
        operator_object.update_workflow_status("Error")
        operator_object.add_workflow_metadata(CaptionsError="Missing a required metadata key {e}".format(e=e))
        raise MasExecutionError(operator_object.return_output_object())

    try:
        asset_id = operator_object.asset_id
    except KeyError:
        print('No asset id for this workflow')
        asset_id = ''

    try:
        s3_response = s3.get_object(Bucket=bucket, Key=key)
        transcribe_metadata = json.loads(s3_response["Body"].read().decode("utf-8"))
    except Exception as e:
        operator_object.update_workflow_status("Error")
        operator_object.add_workflow_metadata(CaptionsError="Unable to read transcription from S3: {e}".format(e=str(e)))
        raise MasExecutionError(operator_object.return_output_object())

    endTime = 0.0
    maxLength = 50
    wordCount = 0
    maxWords = 12
    maxSilence = 1.5

    captions = []
    caption = None

    for item in transcribe_metadata["results"]["items"]:

        isPunctuation = item["type"] == "punctuation"

        if caption is None:

            # Start of a line with punctuation, just skip it
            if isPunctuation:
                continue

            # Create a new caption line
            caption = {
                "start": float(item["start_time"]),
                "caption": "",
                "wordConfidence": []
            }

        if not isPunctuation:

            startTime = float(item["start_time"])

            # Check to see if there has been a long silence
            # between the last recorded word and start a new
            # caption if this is the case, ending the last time
            # as this one starts.

            if (len(caption["caption"]) > 0) and ((endTime + maxSilence) < startTime):

                caption["end"] = startTime
                captions.append(caption)

                caption = {
                    "start": float(startTime),
                    "caption": "",
                    "wordConfidence": []
                }

                wordCount = 0

            endTime = float(item["end_time"])

        requiresSpace = (not isPunctuation) and (len(caption["caption"]) > 0)

        if requiresSpace:
            caption["caption"] += " "

        # Process tweaks

        text = item["alternatives"][0]["content"]
        confidence = item["alternatives"][0]["confidence"]
        textLower = text.lower()

        caption["caption"] += text

        # Track raw word confidence
        if not isPunctuation:
            caption["wordConfidence"].append(
                {
                    "w": textLower,
                    "c": float(confidence)
                }
            )
            # Count words
            wordCount += 1

        # If we have reached a good amount of text finalize the caption

        if (wordCount >= maxWords) or (len(caption["caption"]) >= maxLength):
            caption["end"] = endTime
            captions.append(caption)
            wordCount = 0
            caption = None

    # Close the last caption if required

    if caption is not None:
        caption["end"] = endTime
        captions.append(caption)

    for i in range(len(captions)):
        asset = captions[i]
        metadata = {
            "OperatorName": "WebCaptions",
            "Results": asset,
            "WorkflowId": workflow_id
        }

        if i != len(captions) - 1:
            metadata_upload = dataplane.store_asset_metadata(asset_id, operator_object.name, workflow_id,
                                           json.dumps(metadata))
            if "Status" not in metadata_upload:
                operator_object.update_workflow_status("Error")
                operator_object.add_workflow_metadata(
                    CaptionsError="Unable to store web captions {e}".format(e=metadata_upload))
                raise MasExecutionError(operator_object.return_output_object())
            else:
                if metadata_upload["Status"] == "Success":
                    operator_object.update_workflow_status("Complete")
                    return operator_object.return_output_object()
                else:
                    operator_object.update_workflow_status("Error")
                    operator_object.add_workflow_metadata(
                        CaptionsError="Unable to store web captions {e}".format(e=metadata_upload))
                    raise MasExecutionError(operator_object.return_output_object())
        else:
            metadata_upload = dataplane.store_asset_metadata(asset_id, operator_object.name, workflow_id,
                                                             json.dumps(metadata))
            if "Status" not in metadata_upload:
                operator_object.update_workflow_status("Error")
                operator_object.add_workflow_metadata(
                    CaptionsError="Unable to store web captions {e}".format(e=metadata_upload))
                raise MasExecutionError(operator_object.return_output_object())
            else:
                if metadata_upload["Status"] == "Success":
                    response_json = json.loads(metadata_upload)
                    operator_object.add_workflow_metadata(WebCaptionsS3Bucket=response_json['Bucket'],
                                                          WebCaptionsS3Key=response_json['Key'])
                    operator_object.update_workflow_status("Complete")
                    return operator_object.return_output_object()
                else:
                    operator_object.update_workflow_status("Error")
                    operator_object.add_workflow_metadata(
                        CaptionsError="Unable to store web captions {e}".format(e=metadata_upload))
                    raise MasExecutionError(operator_object.return_output_object())

# Create a SRT captions file from the web captions
def web_to_srt(event, context):
    print("We got the following event:\n", event)

    operator_object = MediaInsightsOperationHelper(event)

    try:
        asset_id = operator_object.asset_id
    except KeyError:
        print('No asset id for this workflow')
        asset_id = ''

    try:
        workflow_id = operator_object.workflow_execution_id
    except KeyError as e:
        operator_object.update_workflow_status("Error")
        operator_object.add_workflow_metadata(CaptionsError="Missing a required metadata key {e}".format(e=e))
        raise MasExecutionError(operator_object.return_output_object())

    captions = []

    response = dataplane.retrieve_asset_metadata(asset_id, operator_name="WebCaptions")

    response_json = json.loads(response)
    captions.append(response_json["results"])

    while "cursor" in response_json:
        response = dataplane.retrieve_asset_metadata(asset_id, operator_name="WebCaptions")
        response_json = json.loads(response)
        captions.append(response_json["results"])

    srt = ''

    index = 1

    for i in range(len(captions)):

        caption = captions[i]

        srt += str(index) + '\n'
        srt += formatTimeSRT(float(caption["start"])) + ' --> ' + formatTimeSRT(float(caption["end"])) + '\n'
        srt += caption["caption"] + '\n\n'
        index += 1

    response = dataplane.generate_media_storage_path(asset_id, workflow_id)
    response_json = json.loads(response)
    bucket = response_json["S3Bucket"]
    key = response_json["S3Key"]+'Captions.srt'
    s3_object = s3_resource.Object(bucket, key)

    s3_object.put(Body=srt)

    metadata = {
        "OperatorName": "SRTCaptions",
        "Results": {"S3Bucket": bucket, "S3Key": key},
        "WorkflowId": workflow_id
    }

    metadata_upload = dataplane.store_asset_metadata(asset_id, operator_object.name, workflow_id,
                                   json.dumps(metadata))

    if "Status" not in metadata_upload:
        operator_object.update_workflow_status("Error")
        operator_object.add_workflow_metadata(CaptionsError="Unable to store srt captions file {e}".format(e=metadata_upload))
        raise MasExecutionError(operator_object.return_output_object())
    else:
        if metadata_upload["Status"] == "Success":
            operator_object.update_workflow_status("Complete")
            return operator_object.return_output_object()
        else:
            operator_object.update_workflow_status("Error")
            operator_object.add_workflow_metadata(
                CaptionsError="Unable to store srt captions file {e}".format(e=metadata_upload))
            raise MasExecutionError(operator_object.return_output_object())

# Create a VTT captions file from the web captions
def web_to_vtt(event, context):
    print("We got the following event:\n", event)

    operator_object = MediaInsightsOperationHelper(event)

    try:
        asset_id = operator_object.asset_id
    except KeyError:
        print('No asset id for this workflow')
        asset_id = ''

    try:
        workflow_id = operator_object.workflow_execution_id
    except KeyError as e:
        operator_object.update_workflow_status("Error")
        operator_object.add_workflow_metadata(CaptionsError="Missing a required metadata key {e}".format(e=e))
        raise MasExecutionError(operator_object.return_output_object())

    captions = []

    response = dataplane.retrieve_asset_metadata(asset_id, operator_name="WebCaptions")
    response_json = json.loads(response)
    captions.append(response_json["results"])

    while "cursor" in response_json:
        response = dataplane.retrieve_asset_metadata(asset_id, operator_name="WebCaptions")
        response_json = json.loads(response)
        captions.append(response_json["results"])

    vtt = 'WEBVTT\n\n'

    for i in range(len(captions)):

        caption = captions[i]

        vtt += formatTimeVTT(float(caption["start"])) + ' --> ' + formatTimeVTT(float(caption["end"])) + '\n'
        vtt += caption["caption"] + '\n\n'

    response = dataplane.generate_media_storage_path(asset_id, workflow_id)
    response_json = json.loads(response)
    bucket = response_json["S3Bucket"]
    key = response_json["S3Key"]+'Captions.vtt'
    s3_object = s3_resource.Object(bucket, key)

    s3_object.put(Body=vtt)

    metadata = {
        "OperatorName": "VTTCaptions",
        "Results": {"S3Bucket": bucket, "S3Key": key},
        "WorkflowId": workflow_id
    }

    metadata_upload = dataplane.store_asset_metadata(asset_id, operator_object.name, workflow_id,
                                   json.dumps(metadata))

    if "Status" not in metadata_upload:
        operator_object.update_workflow_status("Error")
        operator_object.add_workflow_metadata(CaptionsError="Unable to store srt captions file {e}".format(e=metadata_upload))
        raise MasExecutionError(operator_object.return_output_object())
    else:
        if metadata_upload["Status"] == "Success":
            operator_object.update_workflow_status("Complete")
            return operator_object.return_output_object()
        else:
            operator_object.update_workflow_status("Error")
            operator_object.add_workflow_metadata(
                CaptionsError="Unable to store srt captions file {e}".format(e=metadata_upload))
            raise MasExecutionError(operator_object.return_output_object())


# Create a SRT captions file from transcribe output
def create_srt(event, context):
    web_captions(event, context)
    web_to_srt(event, context)

# Create a VTT captions file from transcribe output
def create_vtt(event, context):
    web_captions(event, context)
    web_to_vtt(event, context)

# Format an SRT timestamp in HH:MM:SS,mmm
def formatTimeSRT(timeSeconds):

    ONE_HOUR = 60 * 60
    ONE_MINUTE = 60
    hours = math.floor(timeSeconds / ONE_HOUR)
    remainder = timeSeconds - (hours * ONE_HOUR)
    minutes = math.floor(remainder / 60)
    remainder = remainder - (minutes * ONE_MINUTE)
    seconds = math.floor(remainder)
    remainder = remainder - seconds
    millis = remainder

    return str(hours).zfill(2) + ':' + str(minutes).zfill(2) + ':' + str(seconds).zfill(2) + ',' + str(math.floor(millis * 1000)).zfill(3)

# Format a VTT timestamp in HH:MM:SS.mmm
def formatTimeVTT(timeSeconds):

    ONE_HOUR = 60 * 60
    ONE_MINUTE = 60
    hours = math.floor(timeSeconds / ONE_HOUR)
    remainder = timeSeconds - (hours * ONE_HOUR)
    minutes = math.floor(remainder / 60)
    remainder = remainder - (minutes * ONE_MINUTE)
    seconds = math.floor(remainder)
    remainder = remainder - seconds
    millis = remainder

    return str(hours).zfill(2) + ':' + str(minutes).zfill(2) + ':' + str(seconds).zfill(2) + '.' + str(math.floor(millis * 1000)).zfill(3)
