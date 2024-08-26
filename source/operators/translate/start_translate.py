# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import boto3
import os
import json
from botocore import config
from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.core import patch_all
import tempfile
import nltk.data
import pickle
from nltk.tokenize.punkt import PunktSentenceTokenizer

from MediaInsightsEngineLambdaHelper import DataPlane
from MediaInsightsEngineLambdaHelper import MediaInsightsOperationHelper
from MediaInsightsEngineLambdaHelper import MasExecutionError

patch_all()

mie_config = json.loads(os.environ['botoConfig'])
config = config.Config(**mie_config)
translate_client = boto3.client('translate', config=config)
s3 = boto3.client('s3', config=config)

def _load_tokenizer(lang: str) -> PunktSentenceTokenizer:
    """
    Load a PunktSentenceTokenizer for a given language from pre-downloaded pickles.
    Pickles found at: https://raw.githubusercontent.com/nltk/nltk_data/gh-pages/packages/tokenizers/punkt.zip
    These pickles are downloaded and packaged during build. See deployment/nltk_download_functions.sh

    Args:
        lang (str): The language for which to load the tokenizer.

    Returns:
        PunktSentenceTokenizer: The tokenizer for the specified language.
    """
    try:
        # Get the directory of the current file
        current_directory = os.path.dirname(os.path.abspath(__file__))

        # Construct the path to the pickle file
        pickle_path = os.path.join(current_directory, 'nltk_data', 'tokenizers', 'punkt', f'{lang.lower()}.pickle')

        # Open the file and unpickle the tokenizer
        with open(pickle_path, 'rb') as f:
            tokenizer = pickle.load(f)

        return tokenizer

    except FileNotFoundError as e:
        print("Error: Tokenizer file for '%s' not found." % lang)
        raise e
    except pickle.UnpicklingError as e:
        print("Error: Failed to unpickle the tokenizer for '%s'." % lang)
        raise e
    except Exception as e:
        print("An error occurred while loading the tokenizer: %s" % e)
        raise e

def lambda_handler(event, _context):
    print("We got the following event:\n", event)

    operator_object = MediaInsightsOperationHelper(event)

    try:
        bucket = operator_object.input["Media"]["Text"]["S3Bucket"]
        key = operator_object.input["Media"]["Text"]["S3Key"]
    except KeyError as e:
        operator_object.update_workflow_status("Error")
        operator_object.add_workflow_metadata(TranslateError="No valid inputs {e}".format(e=e))
        raise MasExecutionError(operator_object.return_output_object())

    workflow_id = operator_object.workflow_execution_id

    asset_id = operator_object.asset_id

    try:
        # The source language may not have been known when the configuration for
        # this operator was created. In that case, this operator may have been
        # placed downstream from the Transcribe operator which can auto-detect
        # the source language. Transcribe will put the source language into the
        # TranscribeSourceLanguage field of the workflow metadata object. If the
        # TranscribeSourceLanguage field is present then we will use that source
        # language throughout this operator.
        if "TranscribeSourceLanguage" in operator_object.input['MetaData']:
            source_lang = operator_object.input['MetaData']['TranscribeSourceLanguage'].split('-')[0]
        else:
            # If TranscribeSourceLanguage is not available, then SourceLanguageCode
            # must be present in the operator Configuration block.
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

    # If input text is empty then we're done.
    if len(transcript) < 1:
        operator_object.update_workflow_status("Complete")
        return operator_object.return_output_object()

    # Create language tokenizer according to user-specified source language.
    # Default to English.
    lang_options = {
        'fr': 'French',
        'de': 'German',
        're': 'Russian',
        'it': 'Italian',
        'pt': 'Portuguese',
        'es': 'Spanish'
    }
    lang = lang_options.get(source_lang, 'English')
    print("Using {} dictionary to find sentence boundaries.".format(lang))

    tokenizer = _load_tokenizer(lang)

    # Split input text into a list of sentences
    sentences = tokenizer.tokenize(transcript)
    print("Input text length: " + str(len(transcript)))
    print("Number of sentences: " + str(len(sentences)))
    translated_text = ''
    transcript_chunk = ''
    for sentence in sentences:
        # Translate can handle 5000 unicode characters but we'll process no
        # more than 1000 just to be on the safe side.
        # Even by limiting input text to 3000 characters, we've still seen
        # translate throttling with a RateExceeded exception.
        # Reducing input text to 1000 characters seemed to fix this.
        if (len(sentence) + len(transcript_chunk) < 1000):
            transcript_chunk = transcript_chunk + ' ' + sentence
        else:
            try:
                print("Translation input text length: " + str(len(transcript_chunk)))
                translation_chunk = translate_client.translate_text(
                    Text=transcript_chunk,
                    SourceLanguageCode=source_lang,
                    TargetLanguageCode=target_lang)
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
        translation_chunk = translate_client.translate_text(
            Text=transcript_chunk,
            SourceLanguageCode=source_lang,
            TargetLanguageCode=target_lang)
        print("Translation output text length: " + str(len(translation_chunk)))
    except Exception as e:
        operator_object.update_workflow_status("Error")
        operator_object.add_workflow_metadata(TranslateError="Unable to get response from translate: {e}".format(e=str(e)))
        raise MasExecutionError(operator_object.return_output_object())
    translated_text = translated_text + ' ' + translation_chunk["TranslatedText"]
    # Put final result into a JSON object because the MI dataplane requires it to be so.
    translation_result = {}
    translation_result["TranslatedText"] = translated_text
    translation_result["SourceLanguageCode"] = source_lang
    translation_result["TargetLanguageCode"] = target_lang
    print("Final translation text length: " + str(len(translated_text)))
    dataplane = DataPlane()
    metadata_upload = dataplane.store_asset_metadata(asset_id, operator_object.name, workflow_id, translation_result)

    if metadata_upload.get('Status', '') == 'Success':
        operator_object.add_media_object('Text', metadata_upload['Bucket'], metadata_upload['Key'])
        operator_object.update_workflow_status("Complete")
        return operator_object.return_output_object()

    operator_object.add_workflow_metadata(
        TranslateError="Unable to upload metadata for asset: {asset}".format(asset=asset_id))
    operator_object.update_workflow_status("Error")
    raise MasExecutionError(operator_object.return_output_object())
