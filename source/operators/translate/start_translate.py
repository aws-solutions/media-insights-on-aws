# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import boto3
import os
import json
from botocore import config
import math

from MediaInsightsEngineLambdaHelper import DataPlane
from MediaInsightsEngineLambdaHelper import MediaInsightsOperationHelper
from MediaInsightsEngineLambdaHelper import MasExecutionError

mie_config = json.loads(os.environ['botoConfig'])
config = config.Config(**mie_config)
translate_client = boto3.client('translate', config=config)
s3 = boto3.client('s3')


def lambda_handler(event, context):
    print("We got the following event:\n", event)

    operator_object = MediaInsightsOperationHelper(event)

    try:
        bucket = operator_object.input["Media"]["Text"]["S3Bucket"]
        key = operator_object.input["Media"]["Text"]["S3Key"]
    except KeyError as e:
        operator_object.update_workflow_status("Error")
        operator_object.add_workflow_metadata(TranslateError="No valid inputs {e}".format(e=e))
        raise MasExecutionError(operator_object.return_output_object())

    try:
        workflow_id = operator_object.workflow_execution_id
    except KeyError as e:
        operator_object.update_workflow_status("Error")
        operator_object.add_workflow_metadata(TranslateError="Missing a required metadata key {e}".format(e=e))
        raise MasExecutionError(operator_object.return_output_object())

    try:
        asset_id = operator_object.asset_id
    except KeyError:
        print('No asset id for this workflow')
        asset_id = ''

    try:
        source_lang = operator_object.configuration["SourceLanguageCode"]
        target_lang = operator_object.configuration["TargetLanguageCode"]
    except KeyError:
        operator_object.update_workflow_status("Error")
        operator_object.add_workflow_metadata(TranslateError="Language codes are not defined")
        raise MasExecutionError(operator_object.return_output_object())

    try:
        s3_response = s3.get_object(Bucket=bucket, Key=key)
        transcribe_metadata = json.loads(s3_response["Body"].read().decode("utf-8"))
        transcript = transcribe_metadata["results"]["transcripts"][0]["transcript"]
    except Exception as e:
        operator_object.update_workflow_status("Error")
        operator_object.add_workflow_metadata(TranslateError="Unable to read transcription from S3: {e}".format(e=str(e)))
        raise MasExecutionError(operator_object.return_output_object())


    # TODO: This transcript splitter will fragment words and sentences, which will lead to
    #  less accurate translations. The python nltk package could be used to avoid this
    #  problem, like this:
    #  Tokenize transcript into sentences with nltk
    #  for each sentence
    #    if a sentence is > 5000 length, print error and bail.
    #    append sentences but don't exceed 5000 characters
    #    process translate on that appended chunk

    try:
        # process transcript in blocks of 5000 characters
        translated_text = ''
        print("Input text length: " + str(len(transcript)))
        for i in range(math.ceil(len(transcript)/5000)):
            transcript_chunk = transcript[i*5000:i*5000+4999]
            print("Processing transcript characters " + str(i*5000) + " through " + str(i*5000+4999))
            translation_chunk = translate_client.translate_text(Text=transcript_chunk,SourceLanguageCode=source_lang,TargetLanguageCode=target_lang)
            translated_text = translated_text + ' ' + translation_chunk["TranslatedText"]
    except Exception as e:
        operator_object.update_workflow_status("Error")
        operator_object.add_workflow_metadata(TranslateError="Unable to get response from translate: {e}".format(e=str(e)))
        raise MasExecutionError(operator_object.return_output_object())
    else:
        print("Translated text length: " + str(len(transcript)))
        dataplane = DataPlane()
        translation_chunk["TranslatedText"] = translated_text
        translation = translation_chunk
        metadata_upload = dataplane.store_asset_metadata(asset_id, operator_object.name, workflow_id, translation)
        if "Status" not in metadata_upload:
            operator_object.add_workflow_metadata(
                TranslateError="Unable to upload metadata for asset: {asset}".format(asset=asset_id))
            operator_object.update_workflow_status("Error")
            raise MasExecutionError(operator_object.return_output_object())
        else:
            if metadata_upload['Status'] == 'Success':
                operator_object.add_media_object('Text', metadata_upload['Bucket'], metadata_upload['Key'])
                operator_object.update_workflow_status("Complete")
                return operator_object.return_output_object()
            else:
                operator_object.add_workflow_metadata(
                    TranslateError="Unable to upload metadata for asset: {asset}".format(asset=asset_id))
                operator_object.update_workflow_status("Error")
                raise MasExecutionError(operator_object.return_output_object())
