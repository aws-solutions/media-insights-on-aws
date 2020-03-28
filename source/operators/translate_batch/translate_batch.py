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
        key = operator_object.input["Media"]["Webcaptions"]["S3Key"]
    except KeyError as e:
        operator_object.update_workflow_status("Error")
        operator_object.add_workflow_metadata(TranslateError="No valid inputs {e}".format(e=e))
        raise MasExecutionError(operator_object.return_output_object()) 

    try:
        s3_response = s3.get_object(Bucket=bucket, Key=key)
        webcaptions = json.loads(s3_response["Body"].read().decode("utf-8"))
        
    except Exception as e:
        operator_object.update_workflow_status("Error")
        operator_object.add_workflow_metadata(TranslateError="Unable to read webcaptions from S3: {e}".format(e=str(e)))
        raise MasExecutionError(operator_object.return_output_object())

    try:
        source_lang = operator_object.configuration["SourceLanguageCode"]
        target_langs = operator_object.configuration["TargetLanguageCodes"]
    except KeyError:
        operator_object.update_workflow_status("Error")
        operator_object.add_workflow_metadata(TranslateError="Language codes are not defined")
        raise MasExecutionError(operator_object.return_output_object())

    # If input text is empty then we're done.
    if len(transcript) < 1:
        operator_object.update_workflow_status("Complete")
        return operator_object.return_output_object()

    for target_lang in target_langs:
        translate(operation_object, webcaptions, source_lang, target_lang)



def setup_nltk():
    
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

    return tokenizer

def webcaptions_to_marked_transcript(webcaptions):
    transcript = ""
    marker = "|"

    for caption in webcaptions:
        transcript = transcript + caption["caption"] + " " + marker + " "

    return transcript

def marked_transcript_to_webcaptions(source_webcaptions, transcript):

    webcaptions = []
    marker = "|"

    translated_captions = transcript.split(marker)

    for translated_caption, source_webcaption in zip(translated_captions, source_webcaptions):

        webcaption = {}
        webcaption["caption"] = translated_caption
        webcaption["start"] = source_webcaption["start"]
        webcaption["end"] = source_webcaption["end"]
        webcaptions.append(webcaption)

    return webcaptions

def translate(operation_object, webcaptions, source_lang, target_lang):

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

    
    
    tokenizer = setup_nltk()

    transcript = webcaptions_to_marked_transcript(webcaptions)

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
    
    translated_webcaptions = marked_transcript_to_webcaptions(source_webcaptions, transcript)


    # Put final result into a JSON object because the MIE dataplane requires it to be so.
    translation_result = {}
    translation_result["TranslatedText"] = translated_text
    translation_result["SourceLanguageCode"] = source_lang
    translation_result["TargetLanguageCode"] = target_lang
    print("Final translation text length: " + str(len(translated_text)))
    dataplane = DataPlane()
    metadata_upload = dataplane.store_asset_metadata(asset_id, operator_object.name+"_"+target_lang, workflow_id, translated_webcaptions)
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



def translateWebCaptions(inputCaptions, inputLanguageCode, outputLanguageCode):
	marker = "<123>"

	inputEntries = map(lambda c: c["caption"], inputCaptions)
	inputDelimited = marker.join(inputEntries)
	
	outputDelimited = translate_client.translate_text(Text=inputDelimited, SourceLanguageCode=inputLanguageCode, TargetLanguageCode=outputLanguageCode)
	outputEntries = outputDelimited["TranslatedText"].split(marker)

	outputCaptions = copy.deepcopy(inputCaptions)
	for idx, c in enumerate(outputCaptions):
		c["caption"] = outputEntries[idx]

	return outputCaptions

def translateBatchWebCaptions(operation_object, inputCaptions, inputLanguageCode, outputLanguageCodes, terminology_names):
    marker = "<123>"
    try: 
        translate_role = os.environ['translateRole']

        inputEntries = map(lambda c: c["caption"], inputCaptions)
        inputDelimited = marker.join(inputEntries)

        trancript_storage_path = dataplane.generate_media_storage_path(asset_id, workflow_id)

        bucket = transcript_storage_path['S3Bucket']
        translation_input_path = transcript_storage_path['S3Key']+"/batch_translate_input/"
        translation_output_path = transcript_storage_path['S3Key']+"/batch_translate_output/"
        key = translation_input_path+"transcript_with_caption_markers.txt"

        s3.put_object(Bucket=bucket, Key=key, Body=inputDelimited)

        response = translate_client.start_text_translation_job(
            outputDelimited = translate_client.start_translate_text(
                InputDataConfig={
                    'S3Uri': 's3://'+translation_input_path
                    'ContentType': 'text/plain'
                },
                OutputDataConfig={
                    'S3Uri': 's3://'+transcript_output_path
                },
                DataAccessRoleArn=translate_role,
                SourceLanguageCode=inputLanguageCode,
                TargetLanguageCodes=outputLanguageCodes,
                TerminologyNames=terminology_names
            )
            
        operator_object.add_workflow_metadata(TextTranslateJobProperties=response)
    except Exception as e:
        operator_object.update_workflow_status("Error")
        operator_object.add_workflow_metadata(TranslateError="Unable to start translation batch job: {e}".format(e=str(e)))
        raise MasExecutionError(operator_object.return_output_object())
        


def checkTranslateBatchWebcaptions(event, context):

    print("We got this event:\n", event)
    operator_object = MediaInsightsOperationHelper(event)
    
    try:
        job_id = operator_object.metadata["TextTranslateJobProperties"]["JobId"]
        workflow_id = operator_object.workflow_execution_id
        asset_id = operator_object.asset_id
    except KeyError as e:
        operator_object.update_workflow_status("Error")
        operator_object.add_workflow_metadata(TranslateError="Missing a required metadata key {e}".format(e=e))
        raise MasExecutionError(operator_object.return_output_object())
    try:
        response = translate_client.describe_text_translation_job(
           JobId=job_id
        )
        print(response)
    except Exception as e:
        operator_object.update_workflow_status("Error")
        operator_object.add_workflow_metadata(TranslateError=str(e), TranslateJobId=job_id)
        raise MasExecutionError(operator_object.return_output_object())
    else:
        if response["TextTranslationJobProperties"]["JobStatus"] in ["IN_PROGRESS", "SUBMITTED"]:
            operator_object.update_workflow_status("Executing")
            operator_object.add_workflow_metadata(TextTranslateJobProperties=response, AssetId=asset_id, WorkflowExecutionId=workflow_id)
            return operator_object.return_output_object()
        elif response["TextTranslationJobProperties"]["JobStatus"] in ["FAILED", "COMPLETED_WITH_ERROR", "STOP_REQUESTED", "STOPPED"]:
            operator_object.update_workflow_status("Error")
            operator_object.add_workflow_metadata(TextTranslateJobProperties=job_id,
                                          TranslateError=str(response["TextTranslationJobProperties"]["FailureReason"]))
            raise MasExecutionError(operator_object.return_output_object())
        elif response["TextTranslationJobProperties"]["JobStatus"] == "COMPLETED":
            
            # convert translated text to WebCaptions
            

def get_webcaptions(operation_object, lang):
    

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

    return captions

def store_captions(operation_object, lang, captions):

    for i in range(len(captions)):
        asset = captions[i]
        metadata = {
            "OperatorName": "WebCaptions"+"_"+lang,
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
    