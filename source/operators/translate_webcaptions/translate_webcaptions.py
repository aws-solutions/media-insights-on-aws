# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import boto3
import os
import json
from botocore import config
import math
import nltk.data
import ntpath
from datetime import datetime, timezone
from urllib.parse import urlparse

from MediaInsightsEngineLambdaHelper import DataPlane
from MediaInsightsEngineLambdaHelper import MediaInsightsOperationHelper
from MediaInsightsEngineLambdaHelper import MasExecutionError

mie_config = json.loads(os.environ['botoConfig'])
config = config.Config(**mie_config)
translate_client = boto3.client('translate', config=config)
s3 = boto3.client('s3')
s3_resource = boto3.resource("s3")
dataplane = DataPlane()

def start_translate_webcaptions(event, context):
    print("We got the following event:\n", event)

    operator_object = MediaInsightsOperationHelper(event)

    try:
        source_lang = operator_object.configuration["SourceLanguageCode"]
        target_langs = operator_object.configuration["TargetLanguageCodes"]
    except KeyError:
        operator_object.update_workflow_status("Error")
        operator_object.add_workflow_metadata(TranslateError="Language codes are not defined")
        raise MasExecutionError(operator_object.return_output_object())

    #webcaptions = get_webcaptions(operator_object, source_lang)
    webcaptions = get_webcaptions_json(operator_object, source_lang)

    # Translate takes a list of target languages, but it only allow on item in the list.  Too bad
    # life would be so much easier if it truely allowed many targets.
    translate_webcaptions(operator_object, webcaptions, source_lang, target_langs) 

    return operator_object.return_output_object()

    
def translate_webcaptions(operator_object, inputCaptions, sourceLanguageCodes, targetLanguageCodes, terminology_names=[]):
    
    marker = "<123>"

    try: 
        
        translate_role = os.environ['translateRole']
        asset_id = operator_object.asset_id
        workflow_id = operator_object.workflow_execution_id
        translate_job_name = "MIE_"+asset_id+"_"+workflow_id

        # Convert WebCaptions to text with marker between caption lines
        inputEntries = map(lambda c: c["caption"], inputCaptions)
        inputDelimited = marker.join(inputEntries)

        transcript_storage_path = dataplane.generate_media_storage_path(asset_id, workflow_id)
        bucket = transcript_storage_path['S3Bucket']
        translation_input_path = transcript_storage_path['S3Key']+"webcaptions_translate_input/"
        translation_input_uri = 's3://'+bucket+"/"+translation_input_path       
        translation_output_path = transcript_storage_path['S3Key']+"webcaptions_translate_output/"
        translation_output_uri = 's3://'+bucket+"/"+translation_output_path
        key = translation_input_path+"transcript_with_caption_markers.txt"
        

        print("put object {} {}".format(bucket, key))
        s3.put_object(Bucket=bucket, Key=key, Body=inputDelimited)

        print("create translate output folder if it doesn't exist")
        dummy_key = translation_output_path+"/"+"foo"
        s3.put_object(Bucket=bucket, Key=dummy_key, Body="foo")

        print("Translate inputs")
        print("translation_input_uri {}".format(translation_input_uri))
        print("translation_output_uri {}".format(translation_output_uri))
        print("translate_role {}".format(translate_role))
        
        # Kick off a job for each input language
        translate_jobs = []
        for targetLanguageCode in targetLanguageCodes:
            print("Starting translation to {}".format(targetLanguageCode))
            # Even though the API takes a list of targets, Translate only supports
            # a list of 1 or less

            # Set the job name to avoid creating the same job multiple time if
            # we retry due to an error.  
            singletonTargetList = []
            singletonTargetList.append(targetLanguageCode)  
            job_name = "MIE_"+asset_id+"_"+workflow_id+"_"+targetLanguageCode
            print("JobName: {}".format(job_name))

            # Save the delimited transcript text to S3
            response = translate_client.start_text_translation_job(
                JobName=job_name,
                InputDataConfig={
                    'S3Uri': translation_input_uri,
                    'ContentType': 'text/plain'
                },
                OutputDataConfig={
                    'S3Uri': translation_output_uri
                },
                DataAccessRoleArn=translate_role,
                SourceLanguageCode=sourceLanguageCodes,
                TargetLanguageCodes=singletonTargetList,
                TerminologyNames=terminology_names
            )    
            jobinfo = {
                "JobId": response["JobId"],
                "TargetLanguageCode": targetLanguageCode
            }
            translate_jobs.append(jobinfo)           
            
            operator_object.add_workflow_metadata(TextTranslateJobPropertiesList=translate_jobs)
    except Exception as e:
        operator_object.update_workflow_status("Error")
        operator_object.add_workflow_metadata(TranslateError="Unable to start translation WebCaptions job: {e}".format(e=str(e)))
        raise MasExecutionError(operator_object.return_output_object())
        

def check_translate_webcaptions(event, context):

    print("We got this event:\n", event)
    operator_object = MediaInsightsOperationHelper(event)

    try:
        translate_jobs = operator_object.metadata["TextTranslateJobPropertiesList"]
        workflow_id = operator_object.workflow_execution_id
        asset_id = operator_object.asset_id
        transcript_storage_path = dataplane.generate_media_storage_path(asset_id, workflow_id)
        bucket = transcript_storage_path['S3Bucket']
        translation_output_path = transcript_storage_path['S3Key']+"webcaptions_translate_output/"
        
    except KeyError as e:
        operator_object.update_workflow_status("Error")
        operator_object.add_workflow_metadata(TranslateError="Missing a required metadata key {e}".format(e=e))
        raise MasExecutionError(operator_object.return_output_object())
    
    # Check the status of each job
    # - IF ANY job has an error, we fail the workflow and return from the loop
    # - IF ANY job is still running, the workflow is still Executing 
    # - If ALL jobs are complete, we reach the end of the loop and the workflow is complete
    for job in translate_jobs:

        try:
            job_id = job["JobId"]
            job_status_list = []
            
        except KeyError as e:
            operator_object.update_workflow_status("Error")
            operator_object.add_workflow_metadata(TranslateError="Missing a required metadata key {e}".format(e=e))
            raise MasExecutionError(operator_object.return_output_object())
        try:
            response = translate_client.describe_text_translation_job(
            JobId=job_id
            )
            print(response)
            job_status = {
                "JobId": job_id,
                "Status": response["TextTranslationJobProperties"]["JobStatus"]
            }

        except Exception as e:
            operator_object.update_workflow_status("Error")
            operator_object.add_workflow_metadata(TranslateError=str(e), TranslateJobId=job_id)
            raise MasExecutionError(operator_object.return_output_object())
        else:
            if response["TextTranslationJobProperties"]["JobStatus"] in ["IN_PROGRESS", "SUBMITTED"]:
                operator_object.update_workflow_status("Executing")
                operator_object.add_workflow_metadata(TextTranslateJobStatusList=job_status_list, AssetId=asset_id, WorkflowExecutionId=workflow_id)
                return operator_object.return_output_object()
            elif response["TextTranslationJobProperties"]["JobStatus"] in ["FAILED", "COMPLETED_WITH_ERROR", "STOP_REQUESTED", "STOPPED"]:
                operator_object.update_workflow_status("Error")
                operator_object.add_workflow_metadata(TextTranslateJobStatusList=job_status_list, AssetId=asset_id, WorkflowExecutionId=workflow_id)
                raise MasExecutionError(operator_object.return_output_object())
            elif response["TextTranslationJobProperties"]["JobStatus"] == "COMPLETED":
                print("{} is complete".format(job_id))
                operator_object.add_workflow_metadata(TextTranslateJobStatusList=job_status_list, AssetId=asset_id, WorkflowExecutionId=workflow_id)

        
    # If we made it here, then all the translate jobs are complete.  
    # Convert the translations back to WebCaptions and write them out
    # to the dataplane 

    translation_storage_path = dataplane.generate_media_storage_path(asset_id, workflow_id)
    bucket = translation_storage_path['S3Bucket']
    translation_path = translation_storage_path['S3Key']

    webcaptions_collection = []
    for job in translate_jobs:
        try:
            print("Save translation for job {}".format(job["JobId"]))

            translateJobDescription = translate_client.describe_text_translation_job(JobId = job["JobId"])
            translateJobS3Uri = translateJobDescription["TextTranslationJobProperties"]["OutputDataConfig"]["S3Uri"]
            translateJobUrl = urlparse(translateJobS3Uri, allow_fragments = False)
            translateJobLanguageCode = translateJobDescription["TextTranslationJobProperties"]["TargetLanguageCodes"][0]

            translateJobS3Location = {
                "Uri": translateJobS3Uri,
                "Bucket": translateJobUrl.netloc,
                "Key": translateJobUrl.path.strip("/")
            }

            # use input web captions to convert translation output to web captions format
            for outputS3ObjectKey in map(lambda s: s.key, s3_resource.Bucket(translateJobS3Location["Bucket"]).objects.filter(Prefix=translateJobS3Location["Key"] + "/", Delimiter="/")):
                print("Save translation for each output of job {} output {}".format(job["JobId"], outputS3ObjectKey))
                
                outputFilename = ntpath.basename(outputS3ObjectKey)

                translateOutput = s3_resource.Object(translateJobS3Location["Bucket"], outputS3ObjectKey).get()["Body"].read().decode("utf-8")
                #inputWebCaptions = get_webcaptions(operator_object, translateJobDescription["TextTranslationJobProperties"]["SourceLanguageCode"])
                inputWebCaptions = get_webcaptions_json(operator_object, translateJobDescription["TextTranslationJobProperties"]["SourceLanguageCode"])
                outputWebCaptions = delimitedToWebCaptions(inputWebCaptions, translateOutput, "<123>", 15)
                print(outputS3ObjectKey)
                (targetLanguageCode, basename, ext) = outputFilename.split(".")
                #put_webcaptions(operator_object, outputWebCaptions, targetLanguageCode)  
                operator_metadata = put_webcaptions_json(operator_object, outputWebCaptions, targetLanguageCode) 

                # Save a copy of the translation text without delimiters
                translation_text = translateOutput.replace("<123>", "")
                translation_text_key = translation_path+"translation"+"_"+targetLanguageCode+".txt"
                s3_object = s3_resource.Object(bucket, translation_text_key)
                s3_object.put(Body=translation_text)

            metadata = {
                "OperatorName": "TranslateWebCaptions_"+translateJobLanguageCode,
                "TranslationText": {"S3Bucket": bucket, "S3Key": translation_text_key},
                "WebCaptions": operator_metadata,
                "WorkflowId": workflow_id,
                "TargetLanguageCode": translateJobLanguageCode
            }
            
            webcaptions_collection.append(metadata)

        
            # lang_code = job["TargetLanguageCode"]
            # translation_with_caption_markers = lang_code+"."+"transcript_with_caption_markers.txt"
            # translation_with_caption_markers_key = translation_output_path + translation_with_caption_markers
        except Exception as e:
            operator_object.update_workflow_status("Error")
            operator_object.add_workflow_metadata(CaptionsError="Unable to contruct path to translate output in S3: {e}".format(e=str(e)))
            raise MasExecutionError(operator_object.return_output_object())


    data = {}
    data["CaptionsCollection"] = webcaptions_collection
    metadata_upload = dataplane.store_asset_metadata(asset_id, "TranslateWebCaptions", workflow_id,
                            data)   

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
                CaptionsError="Unable to store webcaptions collection information {e}".format(e=metadata_upload))
            raise MasExecutionError(operator_object.return_output_object())

    return operator_object.return_output_object()  


    
def get_webcaptions(operator_object, lang):

    try:
        workflow_id = operator_object.workflow_execution_id
    except KeyError as e:
        operator_object.update_workflow_status("Error")
        operator_object.add_workflow_metadata(CaptionsError="Missing a required metadata key {e}".format(e=e))
        raise MasExecutionError(operator_object.return_output_object())

    webcaptions = []

    response = dataplane.retrieve_asset_metadata(asset_id, operator_name=webcaptions_lang)
    print(json.dumps(response))

    #FIXME Dataplane should only return WebCaptions data from this call, but it is returning everything
    if "operator" in response and response["operator"] == webcaptions_lang:
        webcaptions.append(response["results"])

    while "cursor" in response:
        response = dataplane.retrieve_asset_metadata(asset_id, operator_name=webcaptions_lang,cursor=response["cursor"])
        print(json.dumps(response))
        
        #FIXME Dataplane should only return WebCaptions data from this call, but it is returning everything
        if response["operator"] == webcaptions_lang:
            webcaptions.append(response["results"])

    return webcaptions



def put_webcaptions(operator_object, webcaptions, lang):
    
    try:
        print("put_webcaptions({}".format(lang))
        asset_id = operator_object.asset_id
        webcaptions_lang = "WebCaptions"+"_"+lang
        workflow_id = operator_object.workflow_execution_id
    except KeyError:
        operator_object.update_workflow_status("Error")
        operator_object.add_workflow_metadata(CaptionsError="Missing a required metadata key {e}".format(e=e))
        raise MasExecutionError(operator_object.return_output_object())
        
    try:
        for i,asset in enumerate(webcaptions, start=1):

            if i != len(webcaptions):
                metadata_upload = dataplane.store_asset_metadata(asset_id=asset_id, operator_name=webcaptions_lang, 
                                        workflow_id=workflow_id, results=asset, paginate=True, end=False)
                
                if "Status" not in metadata_upload:
                    operator_object.update_workflow_status("Error")
                    operator_object.add_workflow_metadata(
                        CaptionsError="Unable to store web captions {e}".format(e=metadata_upload))
                    raise MasExecutionError(operator_object.return_output_object())
                else:
                    if metadata_upload["Status"] == "Success":
                        pass
                    else:
                        operator_object.update_workflow_status("Error")
                        operator_object.add_workflow_metadata(
                            CaptionsError="Unable to store web captions {e}".format(e=metadata_upload))
                        raise MasExecutionError(operator_object.return_output_object())
            else:
                metadata_upload = dataplane.store_asset_metadata(asset_id=asset_id, operator_name=webcaptions_lang, 
                                        workflow_id=workflow_id, results=asset, paginate=True, end=True)
                if "Status" not in metadata_upload:
                    operator_object.update_workflow_status("Error")
                    operator_object.add_workflow_metadata(
                        CaptionsError="Unable to store web captions {e}".format(e=metadata_upload))
                    raise MasExecutionError(operator_object.return_output_object())
                else:
                    if metadata_upload["Status"] == "Success":
                        response_json = metadata_upload
                        operator_object.add_workflow_metadata(WebCaptionsS3Bucket=response_json['Bucket'],
                                                            WebCaptionsS3Key=response_json['Key'])
                        operator_object.update_workflow_status("Complete")
                        return operator_object.return_output_object()
                    else:
                        operator_object.update_workflow_status("Error")
                        operator_object.add_workflow_metadata(
                            CaptionsError="Unable to store web captions {e}".format(e=metadata_upload))
                        raise MasExecutionError(operator_object.return_output_object())
    except Exception as e:
        operator_object.update_workflow_status("Error")
        operator_object.add_workflow_metadata(TranslateError=str(e))
        raise MasExecutionError(operator_object.return_output_object())

    print("put_webcaptions():SUCCESSS")


# Converts a delimited file back to web captions format.
# Uses the source web captions to get timestamps and source caption text (saved in sourceCaption field).
def delimitedToWebCaptions(sourceWebCaptions, delimitedCaptions, delimiter, maxCaptionLineLength):
	entries = delimitedCaptions.split(delimiter)

	outputWebCaptions = []
	for i, c in enumerate(sourceWebCaptions):
		caption = {}
		caption["start"] = c["start"]
		caption["end"] = c["end"]
		caption["caption"] = entries[i]
		caption["sourceCaption"] = c["caption"]
		outputWebCaptions.append(caption)
	
	return outputWebCaptions

def get_webcaptions_json(operator_object, lang):
    try:
        print("get_webcaptions_json({}".format(lang))
        asset_id = operator_object.asset_id
        workflow_id = operator_object.workflow_execution_id
    except KeyError:
        operator_object.update_workflow_status("Error")
        operator_object.add_workflow_metadata(CaptionsError="Missing a required metadata key {e}".format(e=e))
        raise MasExecutionError(operator_object.return_output_object())

    try:
        webcaptions_storage_path = dataplane.generate_media_storage_path(asset_id, workflow_id)
        bucket = webcaptions_storage_path['S3Bucket'] 
        key = webcaptions_storage_path['S3Key']+"WebCaptions"+"_"+lang+".json"
            

        print("get object {} {}".format(bucket, key))
        data = s3.get_object(Bucket=bucket, Key=key)
        webcaptions = json.loads(data['Body'].read().decode('utf-8'))
        
    
    except Exception as e:
        operator_object.update_workflow_status("Error")
        operator_object.add_workflow_metadata(CaptionsError="Unable to get webcaptions from dataplane {e}".format(e=e))
        raise MasExecutionError(operator_object.return_output_object())

    return webcaptions

def put_webcaptions_json(operator_object, webcaptions, lang):
    try:
        print("put_webcaptions_json({}".format(lang))
        asset_id = operator_object.asset_id
        webcaptions_lang = "WebCaptions"+"_"+lang
        workflow_id = operator_object.workflow_execution_id
    except KeyError:
        operator_object.update_workflow_status("Error")
        operator_object.add_workflow_metadata(CaptionsError="Missing a required metadata key {e}".format(e=e))
        raise MasExecutionError(operator_object.return_output_object())

    webcaptions_storage_path = dataplane.generate_media_storage_path(asset_id, workflow_id)
    bucket = webcaptions_storage_path['S3Bucket'] 
    key = webcaptions_storage_path['S3Key']+"WebCaptions"+"_"+lang+".json"
        

    print("put object {} {}".format(bucket, key))
    s3.put_object(Bucket=bucket, Key=key, Body=json.dumps(webcaptions))

    operator_metadata = {"S3Bucket": bucket, "S3Key": key, "Operator": "WebCaptions"+"_"+lang}
    # metadata_upload = dataplane.store_asset_metadata(asset_id, "WebCaptions"+"_"+lang, workflow_id,
    #                             operator_metadata)

    # if "Status" not in metadata_upload:
    #     operator_object.update_workflow_status("Error")
    #     operator_object.add_workflow_metadata(CaptionsError="Unable to store webcaptions file {e}".format(e=metadata_upload))
    #     raise MasExecutionError(operator_object.return_output_object())
    # else:
    #     if metadata_upload["Status"] == "Success":
    #         operator_object.update_workflow_status("Complete")
    #         return operator_object.return_output_object()
    #     else:
    #         operator_object.update_workflow_status("Error")
    #         operator_object.add_workflow_metadata(
    #             CaptionsError="Unable to store webcaptions file {e}".format(e=metadata_upload))
    #         raise MasExecutionError(operator_object.return_output_object())

    return operator_metadata
