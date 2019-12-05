# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import boto3
import os
import json
from botocore import config
import math
import nltk.data

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

    # Tell the NLTK data loader to look for files in /tmp/
    nltk.data.path.append("/tmp/")
    # Download NLTK tokenizers to /tmp/
    # We use /tmp because that's where AWS Lambda provides write access to the local file system.
    nltk.download('punkt', download_dir='/tmp/')
    # Create language tokenizer according to user-specified source language.
    # Default to English.
    if source_lang == 'fr':
        print("Using French dictionary to find sentence boundaries.")
        tokenizer = nltk.data.load('tokenizers/punkt/french.pickle')
    elif source_lang == 'de':
        print("Using German dictionary to find sentence boundaries.")
        tokenizer = nltk.data.load('tokenizers/punkt/german.pickle')
    elif source_lang == 're':
        print("Using Russian dictionary to find sentence boundaries.")
        tokenizer = nltk.data.load('tokenizers/punkt/russian.pickle')
    elif source_lang == 'it':
        print("Using Italian dictionary to find sentence boundaries.")
        tokenizer = nltk.data.load('tokenizers/punkt/italian.pickle')
    elif source_lang == 'pt':
        print("Using Portuguese dictionary to find sentence boundaries.")
        tokenizer = nltk.data.load('tokenizers/punkt/portuguese.pickle')
    elif source_lang == 'es':
        print("Using Spanish dictionary to find sentence boundaries.")
        tokenizer = nltk.data.load('tokenizers/punkt/spanish.pickle')
    else:
        print("Using English dictionary to find sentence boundaries.")
        tokenizer = nltk.data.load('tokenizers/punkt/english.pickle')

    # Split input text into a list of sentences
    sentences = tokenizer.tokenize(transcript)
    print("Input text length: " + str(len(transcript)))
    print("Number of sentences: " + str(len(sentences)))
    translated_text = ''
    transcript_chunk = ''
    for sentence in sentences:
        # Translate can handle 5000 unicode characters but we'll process no more than 4000
        # just to be on the safe side.
        if (len(sentence) + len(transcript_chunk) < 4000):
            transcript_chunk = transcript_chunk + ' ' + sentence
        else:
            try:
                print("Translation input text length: " + str(len(transcript_chunk)))
                translation_chunk = translate_client.translate_text(Text=transcript_chunk,SourceLanguageCode=source_lang,TargetLanguageCode=target_lang)
                print("Translation output text length: " + str(len(translation_chunk)))
            except Exception as e:
                operator_object.update_workflow_status("Error")
                operator_object.add_workflow_metadata(TranslateError="Unable to get response from translate: {e}".format(e=str(e)))
                raise MasExecutionError(operator_object.return_output_object())
            translated_text = translated_text + ' ' + translation_chunk["TranslatedText"]
            transcript_chunk = sentence
    print("Translating the final chunk of input text...")
    try:
        print("Translation input text length: " + str(len(transcript_chunk)))
        translation_chunk = translate_client.translate_text(Text=transcript_chunk,SourceLanguageCode=source_lang,TargetLanguageCode=target_lang)
        print("Translation output text length: " + str(len(translation_chunk)))
    except Exception as e:
        operator_object.update_workflow_status("Error")
        operator_object.add_workflow_metadata(TranslateError="Unable to get response from translate: {e}".format(e=str(e)))
        raise MasExecutionError(operator_object.return_output_object())
    translated_text = translated_text + ' ' + translation_chunk["TranslatedText"]
    # Put final result into a JSON object because the MIE dataplane requires it to be so.
    translation_result = {}
    translation_result["TranslatedText"] = translated_text
    translation_result["SourceLanguageCode"] = source_lang
    translation_result["TargetLanguageCode"] = target_lang
    print("Final translation text length: " + str(len(translated_text)))
    dataplane = DataPlane()
    metadata_upload = dataplane.store_asset_metadata(asset_id, operator_object.name, workflow_id, translation_result)
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
