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
s3 = boto3.client('s3')

# TODO: Move voiceid to a user configurable variable


def lambda_handler(event, context):
    print("We got this event:\n", event)

    operator_object = MediaInsightsOperationHelper(event) 

    try:
        workflow_id = operator_object.workflow_execution_id
    except KeyError as e:
        operator_object.update_workflow_status("Error")
        operator_object.add_workflow_metadata(PollyError="Missing a required metadata key {e}".format(e=e))
        raise MasExecutionError(operator_object.return_output_object())
    try:
        asset_id = operator_object.asset_id
    except KeyError:
        print('No asset id passed along with this workflow')
        asset_id = ''

    try:
        bucket = operator_object.input["Media"]["Text"]["S3Bucket"]
        key = operator_object.input["Media"]["Text"]["S3Key"]
    except KeyError:
        operator_object.update_workflow_status("Error")
        operator_object.add_workflow_metadata(PollyError="No valid inputs")
        raise MasExecutionError(operator_object.return_output_object())
    try:
        s3_response = s3.get_object(Bucket=bucket, Key=key)
        translate_metadata = json.loads(s3_response["Body"].read().decode("utf-8"))
        translation = translate_metadata["TranslatedText"]
    except Exception as e:
        operator_object.update_workflow_status("Error")
        operator_object.add_workflow_metadata(PollyError="Unable to read translation from S3: {e}".format(e=str(e)))
        raise MasExecutionError(operator_object.return_output_object())

    voices = {'en': 'Kendra', 'ru': 'Maxim', 'es': 'Lucia', 'fr': 'Mathieu'}

    # Get language code of the translation, we should just pass this along in the event later
    try:
        comprehend = boto3.client('comprehend')

        language = comprehend.detect_dominant_language(
            Text=translation
        )
    except Exception as e:
        operator_object.update_workflow_status("Error")
        operator_object.add_workflow_metadata(PollyError="Unable to determine the language with comprehend: {e}".format(e=str(e)))
        raise MasExecutionError(operator_object.return_output_object())

    else:
        language_code = language['Languages'][0]['LanguageCode']
        if language_code not in voices:
            operator_object.update_workflow_status("Error")
            operator_object.add_workflow_metadata(PollyError="The only supported languages are: {e}".format(e=voices.keys()))
            raise MasExecutionError(operator_object.return_output_object())
        else:
            voice_id = voices[language_code]

    print("Translation received from S3:\n", translation)

    output_key = '/private/assets/' + asset_id + "/workflows/" + workflow_id + "/" + "translation"

    try:
        polly_response = polly.start_speech_synthesis_task(
            OutputFormat='mp3',
            OutputS3BucketName=bucket,
            OutputS3KeyPrefix=output_key,
            Text=translation,
            TextType='text',
            VoiceId=voice_id
        )

    except Exception as e:
        operator_object.update_workflow_status("Error")
        operator_object.add_workflow_metadata(PollyError="Unable to get response from polly: {e}".format(e=str(e)))
        raise MasExecutionError(operator_object.return_output_object())
    else:
        polly_job_id = polly_response['SynthesisTask']['TaskId']
        operator_object.add_workflow_metadata(PollyJobId=polly_job_id, WorkflowExecutionId=workflow_id, AssetId=asset_id)
        operator_object.update_workflow_status('Executing')
        return operator_object.return_output_object()


