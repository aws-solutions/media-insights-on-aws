# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import os
import boto3
import urllib3
import json
from botocore import config
from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.core import patch_all
from MediaInsightsEngineLambdaHelper import MediaInsightsOperationHelper
from MediaInsightsEngineLambdaHelper import MasExecutionError
from MediaInsightsEngineLambdaHelper import DataPlane

patch_all()

region = os.environ['AWS_REGION']

mie_config = json.loads(os.environ['botoConfig'])
config = config.Config(**mie_config)
transcribe = boto3.client("transcribe", config=config)


def lambda_handler(event, context):
    print("We got this event:\n", event)
    operator_object = MediaInsightsOperationHelper(event)
    # If Transcribe wasn't run due to silent audio, then we're done
    if "Mediainfo_num_audio_tracks" in event["Input"]["MetaData"] and event["Input"]["MetaData"]["Mediainfo_num_audio_tracks"] == "0":
        operator_object.update_workflow_status("Complete")
        return operator_object.return_output_object()
    try:
        job_id = operator_object.metadata["TranscribeJobId"]
        workflow_id = operator_object.workflow_execution_id
        asset_id = operator_object.asset_id
    except KeyError as e:
        operator_object.update_workflow_status("Error")
        operator_object.add_workflow_metadata(TranscribeError="Missing a required metadata key {e}".format(e=e))
        raise MasExecutionError(operator_object.return_output_object())
    try:
        response = transcribe.get_transcription_job(
            TranscriptionJobName=job_id
        )
        print(response)
    except Exception as e:
        operator_object.update_workflow_status("Error")
        operator_object.add_workflow_metadata(TranscribeError=str(e), TranscribeJobId=job_id)
        raise MasExecutionError(operator_object.return_output_object())
    else:
        if response["TranscriptionJob"]["TranscriptionJobStatus"] == "IN_PROGRESS":
            operator_object.update_workflow_status("Executing")
            operator_object.add_workflow_metadata(TranscribeJobId=job_id, AssetId=asset_id, WorkflowExecutionId=workflow_id)
            return operator_object.return_output_object()
        elif response["TranscriptionJob"]["TranscriptionJobStatus"] == "FAILED":
            operator_object.update_workflow_status("Error")
            operator_object.add_workflow_metadata(TranscribeJobId=job_id,
                                          TranscribeError=str(response["TranscriptionJob"]["FailureReason"]))
            raise MasExecutionError(operator_object.return_output_object())
        elif response["TranscriptionJob"]["TranscriptionJobStatus"] == "COMPLETED":
            transcribe_uri = response["TranscriptionJob"]["Transcript"]["TranscriptFileUri"]
            http = urllib3.PoolManager()
            transcription = http.request('GET', transcribe_uri)
            transcription_data = transcription.data.decode("utf-8")
            transcription_json = json.loads(transcription_data)

            text_only_transcript = ''

            for transcripts in transcription_json["results"]["transcripts"]:
                transcript = transcripts["transcript"]
                text_only_transcript = text_only_transcript.join(transcript)

            print(text_only_transcript)

            dataplane = DataPlane()
            s3 = boto3.client('s3', config=config)

            transcript_storage_path = dataplane.generate_media_storage_path(asset_id, workflow_id)

            key = transcript_storage_path['S3Key'] + "transcript.txt"
            bucket = transcript_storage_path['S3Bucket']

            s3.put_object(Bucket=bucket, Key=key, Body=text_only_transcript)

            transcription_json["TextTranscriptUri"] = {"S3Bucket": bucket, "S3Key": key}

            metadata_upload = dataplane.store_asset_metadata(asset_id, operator_object.name, workflow_id,
                                                             transcription_json)
            if "Status" not in metadata_upload:
                operator_object.add_workflow_metadata(
                    TranscribeError="Unable to upload metadata for asset: {asset}".format(asset=asset_id),
                    TranscribeJobId=job_id)
                operator_object.update_workflow_status("Error")
                raise MasExecutionError(operator_object.return_output_object())
            else:
                if metadata_upload['Status'] == 'Success':
                    operator_object.add_media_object('Text', metadata_upload['Bucket'], metadata_upload['Key'])
                    operator_object.add_workflow_metadata(TranscribeJobId=job_id)
                    operator_object.update_workflow_status("Complete")
                    return operator_object.return_output_object()
                else:
                    operator_object.add_workflow_metadata(
                        TranscribeError="Unable to upload metadata for asset: {asset}".format(asset=asset_id),
                        TranscribeJobId=job_id)
                    operator_object.update_workflow_status("Error")
                    raise MasExecutionError(operator_object.return_output_object())
        else:
            operator_object.update_workflow_status("Error")
            operator_object.add_workflow_metadata(TranscribeError="Unable to determine status")
            raise MasExecutionError(operator_object.return_output_object())
