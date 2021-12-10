# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import json
import boto3
from botocore.client import ClientError
import urllib3
import math
import os
import ntpath
import html
import webvtt
from io import StringIO
from botocore import config
from urllib.parse import urlparse
from datetime import datetime

from MediaInsightsEngineLambdaHelper import MediaInsightsOperationHelper
from MediaInsightsEngineLambdaHelper import MasExecutionError
from MediaInsightsEngineLambdaHelper import DataPlane

mie_config = json.loads(os.environ['botoConfig'])
config = config.Config(**mie_config)

s3 = boto3.client('s3', config=config)
s3_resource = boto3.resource('s3')
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
headers = {"Content-Type": "application/json"}
dataplane = DataPlane()


translate_client = boto3.client('translate', config=config)
polly = boto3.client('polly', config=config)

class WebCaptions:
    def __init__(self, operator_object):
        """
        :param event: The event passed in to the operator

        """
        print("WebCaptions operator_object = {}".format(operator_object))
        self.operator_object = operator_object

        try:
            self.transcribe_operator_name = "TranscribeVideo"
            self.workflow_id = operator_object.workflow_execution_id
            self.asset_id = operator_object.asset_id
            self.marker = "<span>"
            self.contentType = "text/html"
            self.existing_subtitles = False
            if "SourceLanguageCode" in self.operator_object.configuration:
                self.source_language_code = self.operator_object.configuration["SourceLanguageCode"]
                self.operator_name_with_lang = self.operator_object.name+"_"+self.source_language_code
            if "TargetLanguageCode" in self.operator_object.configuration:
                self.target_language_code = self.operator_object.configuration["TargetLanguageCode"]
            if "ExistingSubtitlesObject" in self.operator_object.configuration:
                self.existing_subtitles_object = self.operator_object.configuration["ExistingSubtitlesObject"]
                self.existing_subtitles = True
        except KeyError as e:
            self.operator_object.update_workflow_status("Error")
            self.operator_object.add_workflow_metadata(WebCaptionsError="No valid inputs {e}".format(e=e))
            raise MasExecutionError(operator_object.return_output_object())

    def WebCaptionsOperatorName(self, language_code=None, source=""):

        # Shouldn't assume WebCaptions operator is WebCaptions, maybe pass it in the configuration?
        print("WebCaptionsOperatorName {}, {}".format(language_code, source))

        operator_name = "WebCaptions"+source

        if language_code != None:
            return operator_name+"_"+language_code

        try:
            name = operator_name+"_"+self.source_language_code
        except KeyError:
            self.operator_object.update_workflow_status("Error")
            self.operator_object.add_workflow_metadata(WebCaptionsError="Missing language code for WebCaptions {e}".format(e=e))
            raise MasExecutionError(self.operator_object.return_output_object())

        print("WebCaptionsOperatorName() Name {}".format(name))
        return name

    def CaptionsOperatorName(self, language_code=None):

        # Shouldn't assume WebCaptions operator is WebCaptions, maybe pass it in the configuration?
        operator_name = "Captions"

        if language_code != None:
            return operator_name+"_"+language_code

        try:
            name = operator_name+"_"+self.source_language_code
        except KeyError:
            self.operator_object.update_workflow_status("Error")
            self.operator_object.add_workflow_metadata(WebCaptionsError="Missing language code for WebCaptions {e}".format(e=e))
            raise MasExecutionError(self.operator_object.return_output_object())

        print("CaptionsOperatorName() Name {}".format(name))
        return name



    def GetTranscript(self):

        transcript = []

        response = dataplane.retrieve_asset_metadata(self.asset_id, operator_name=self.transcribe_operator_name)
        transcript.append(response["results"])

        while "cursor" in response:
            response = dataplane.retrieve_asset_metadata(self.asset_id, operator_name=self.transcribe_operator_name, cursor=response["cursor"])
            transcript.append(response["results"])

        return transcript

    def TranscribeToWebCaptions(self, transcripts):

        endTime = 0.0
        maxLength = 120
        wordCount = 0
        maxWords = 25
        maxSilence = 1.5

        captions = []
        caption = None

        for transcript in transcripts:
            for item in transcript["results"]["items"]:

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
                if (wordCount >= maxWords) or (len(caption["caption"]) >= maxLength) or isPunctuation and text in "...?!":
                    caption["end"] = endTime
                    captions.append(caption)
                    wordCount = 0
                    caption = None


        # Close the last caption if required

        if caption is not None:
            caption["end"] = endTime
            captions.append(caption)

        return captions

    def GetWebCaptions(self, language_code):
        webcaptions_operator_name = self.WebCaptionsOperatorName(language_code)
        print(webcaptions_operator_name)

        response = dataplane.retrieve_asset_metadata(self.asset_id, operator_name=webcaptions_operator_name)
        print(response)
        return response["results"]["WebCaptions"]

    def PutWebCaptions(self, webcaptions, language_code=None, source=""):

        webcaptions_operator_name = self.WebCaptionsOperatorName(language_code, source)

        WebCaptions = {"WebCaptions": webcaptions}
        response = dataplane.store_asset_metadata(asset_id=self.asset_id, operator_name=webcaptions_operator_name,
                     workflow_id=self.workflow_id, results=WebCaptions, paginate=False)

        if "Status" not in response:
            self.operator_object.update_workflow_status("Error")
            self.operator_object.add_workflow_metadata(WebCaptionsError="Unable to store captions {} {e}".format(webcaptions_operator_name ,e=response))
            raise MasExecutionError(self.operator_object.return_output_object())
        else:
            if response["Status"] == "Success":
                return self.operator_object.return_output_object()
            else:
                self.operator_object.update_workflow_status("Error")
                self.operator_object.add_workflow_metadata(
                    WebCaptionsError="Unable to store captions {} {e}".format(webcaptions_operator_name, e=response))
                raise MasExecutionError(self.operator_object.return_output_object())

        metadata = {
            "OperatorName": webcaptions_operator_name,
            "WorkflowId": self.workflow_id,
            "LanguageCode": language_code
        }

        return metadata

    def GetWebCaptionsCollection(self):
        webcaptions_collection_name = "TranslateWebCaptions"
        print(webcaptions_collection_name)

        response = dataplane.retrieve_asset_metadata(self.asset_id, operator_name=webcaptions_collection_name)
        print(response)
        return response["results"]["CaptionsCollection"]

    def GetTextOnlyTranscript(self, language_code):

        webcaptions = self.GetWebCaptions(language_code)
        transcript = self.WebCaptionsToTextTranscript(webcaptions)

        return transcript

        # Convert most recently saved WebCaptions to a text only transcript

    def WebCaptionsToTextTranscript(self, webcaptions):

        transcript = ""

        for caption in webcaptions:
            transcript = transcript + caption["caption"]


        return transcript

    def PutWebCaptionsCollection(self, operator, collection):

        collection_dict = {}
        collection_dict["CaptionsCollection"] = collection
        response = dataplane.store_asset_metadata(self.asset_id, self.operator_object.name, self.workflow_id,
                                collection_dict)

        if "Status" not in response:
            self.operator_object.update_workflow_status("Error")
            self.operator_object.add_workflow_metadata(WebCaptionsError="Unable to store captions collection metadata {e}".format(e=response))
            raise MasExecutionError(self.operator_object.return_output_object())
        else:
            if response["Status"] == "Success":
                self.operator_object.update_workflow_status("Complete")
                return self.operator_object.return_output_object()
            else:
                self.operator_object.update_workflow_status("Error")
                self.operator_object.add_workflow_metadata(
                    WebCaptionsError="Unable to store captions collection {e}".format(e=response))
                raise MasExecutionError(self.operator_object.return_output_object())

    def WebCaptionsToSRT(self, webcaptions):
        srt = ''

        index = 1

        for caption in webcaptions:

            srt += str(index) + '\n'
            srt += formatTimeSRT(float(caption["start"])) + ' --> ' + formatTimeSRT(float(caption["end"])) + '\n'
            srt += caption["caption"] + '\n\n'
            index += 1

        return srt

    def PutSRT(self, lang, srt):
        response = dataplane.generate_media_storage_path(self.asset_id, self.workflow_id)

        bucket = response["S3Bucket"]
        key = response["S3Key"]+self.CaptionsOperatorName(lang)+".srt"
        s3_object = s3_resource.Object(bucket, key)

        s3_object.put(Body=srt)

        metadata = {
            "OperatorName": self.CaptionsOperatorName(lang),
            "Results": {"S3Bucket": bucket, "S3Key": key},
            "WorkflowId": self.workflow_id,
            "LanguageCode": lang
        }

        return metadata

    def PutVTT(self, lang, vtt):
        response = dataplane.generate_media_storage_path(self.asset_id, self.workflow_id)

        bucket = response["S3Bucket"]
        key = response["S3Key"]+self.CaptionsOperatorName(lang)+".vtt"
        s3_object = s3_resource.Object(bucket, key)

        s3_object.put(Body=vtt)

        metadata = {
            "OperatorName": self.CaptionsOperatorName(lang),
            "Results": {"S3Bucket": bucket, "S3Key": key},
            "WorkflowId": self.workflow_id,
            "LanguageCode": lang
        }

        return metadata

    def WebCaptionsToVTT(self, webcaptions):
        vtt = 'WEBVTT\n\n'

        for caption in webcaptions:

            vtt += formatTimeVTT(float(caption["start"])) + ' --> ' + formatTimeVTT(float(caption["end"])) + '\n'
            vtt += caption["caption"] + '\n\n'

        return vtt

    # Converts a delimited file back to web captions format.
    # Uses the source web captions to get timestamps and source caption text (saved in sourceCaption field).
    def DelimitedToWebCaptions(self, sourceWebCaptions, delimitedCaptions, delimiter, maxCaptionLineLength):

        if self.contentType == 'text/html':
            delimitedCaptions = html.unescape(delimitedCaptions)

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

    def PutMediaCollection(self, operator, collection):
        response = dataplane.store_asset_metadata(self.asset_id, self.operator_object.name, self.workflow_id,
                                collection)

        if "Status" not in response:
            self.operator_object.update_workflow_status("Error")
            self.operator_object.add_workflow_metadata(WebCaptionsError="Unable to store captions collection metadata {e}".format(e=response))
            raise MasExecutionError(self.operator_object.return_output_object())
        else:
            if response["Status"] == "Success":
                self.operator_object.update_workflow_status("Complete")
                return self.operator_object.return_output_object()
            else:
                self.operator_object.update_workflow_status("Error")
                self.operator_object.add_workflow_metadata(
                    WebCaptionsError="Unable to store srt captions file {e}".format(e=response))
                raise MasExecutionError(self.operator_object.return_output_object())

    def TranslateWebCaptions(self, inputCaptions, sourceLanguageCode, targetLanguageCodes, terminology_names=[], parallel_data_names=[]):

        marker = self.marker

        try:

            translate_role = os.environ['translateRole']
            asset_id = self.operator_object.asset_id
            workflow_id = self.operator_object.workflow_execution_id
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

                terminology_name = []
                if len(terminology_names) > 0:
                    # Find a terminology in the list of custom terminologies
                    # that defines translations for targetLanguageCode.
                    # If there happens to be more than one terminology matching targetLanguageCode
                    # then just use the first one in the list.
                    for item in terminology_names:
                        if targetLanguageCode in item['TargetLanguageCodes']:
                            terminology_name.append(item['Name'])
                            break
                    if len(terminology_name) == 0:
                        print("No custom terminology specified.")
                    else:
                        print("Using custom terminology {}".format(terminology_name))

                parallel_data_name = []
                if len(parallel_data_names) > 0:
                    # Find a parallel data set in the list of
                    # that defines translations for targetLanguageCode.
                    # If there happens to be more than one  matching targetLanguageCode
                    # then just use the first one in the list.
                    for item in parallel_data_names:
                        if targetLanguageCode in item['TargetLanguageCodes']:
                            parallel_data_name.append(item['Name'])
                            break
                    if len(parallel_data_name) == 0:
                        print("No parallel data specified.")
                    else:
                        print("Using parallel data_names {}".format(parallel_data_name))

                # Save the delimited transcript text to S3
                response = translate_client.start_text_translation_job(
                    JobName=job_name,
                    InputDataConfig={
                        'S3Uri': translation_input_uri,
                        'ContentType': self.contentType
                    },
                    OutputDataConfig={
                        'S3Uri': translation_output_uri
                    },
                    DataAccessRoleArn=translate_role,
                    SourceLanguageCode=sourceLanguageCode,
                    TargetLanguageCodes=singletonTargetList,
                    TerminologyNames=terminology_name,
                    ParallelDataNames=parallel_data_name
                )
                jobinfo = {
                    "JobId": response["JobId"],
                    "TargetLanguageCode": targetLanguageCode
                }
                translate_jobs.append(jobinfo)

                self.operator_object.add_workflow_metadata(TextTranslateJobPropertiesList=translate_jobs)
        except Exception as e:
            self.operator_object.update_workflow_status("Error")
            self.operator_object.add_workflow_metadata(TranslateError="Unable to start translation WebCaptions job: {e}".format(e=str(e)))
            raise MasExecutionError(self.operator_object.return_output_object())

# Create web captions with line by line captions from the transcribe output
def web_captions(event, context):

    print("We got the following event:\n", event)
    operator_object = MediaInsightsOperationHelper(event)

    webcaptions_object = WebCaptions(operator_object)

    transcript = webcaptions_object.GetTranscript()
    webcaptions = webcaptions_object.TranscribeToWebCaptions(transcript)

    # Save the the original Transcribe generated captions to compare to any ground truth modifications
    # made later so we can calculate quality metrics of the machine translation
    webcaptions_object.PutWebCaptions(webcaptions, source="TranscribeVideo")

    # if a vtt file was input, use that as the most recent version of the webcaptions file
    if webcaptions_object.existing_subtitles:
        webcaptions = vttToWebCaptions(operator_object, webcaptions_object.existing_subtitles_object)

    webcaptions_object.PutWebCaptions(webcaptions)

    operator_object.update_workflow_status("Complete")
    return operator_object.return_output_object()


# Create a SRT captions file from the web captions
def create_srt(event, context):
    print("We got the following event:\n", event)

    operator_object = MediaInsightsOperationHelper(event)
    webcaptions_object = WebCaptions(operator_object)

    try:
        targetLanguageCodes = webcaptions_object.operator_object.configuration["TargetLanguageCodes"]
    except KeyError as e:
        webcaptions_object.operator_object.update_workflow_status("Error")
        operator_object.add_workflow_metadata(WebCaptionsError="Missing a required metadata key {e}".format(e=e))
        raise MasExecutionError(operator_object.return_output_object())

    captions_collection = []
    for lang in targetLanguageCodes:
        webcaptions = []
        captions_operator_name = webcaptions_object.WebCaptionsOperatorName(lang)

        webcaptions = webcaptions_object.GetWebCaptions(lang)

        #captions = get_webcaptions_json(self.operator_object, lang)

        srt = webcaptions_object.WebCaptionsToSRT(webcaptions)
        metadata = webcaptions_object.PutSRT(lang, srt)

        captions_collection.append(metadata)

    data = {}
    data["CaptionsCollection"] = captions_collection

    webcaptions_object.PutMediaCollection(operator_object.name, data)

    operator_object.update_workflow_status("Complete")
    return operator_object.return_output_object()


# Create a VTT captions file from the web captions
def create_vtt(event, context):
    print("We got the following event:\n", event)

    operator_object = MediaInsightsOperationHelper(event)
    webcaptions_object = WebCaptions(operator_object)

    try:
        targetLanguageCodes = webcaptions_object.operator_object.configuration["TargetLanguageCodes"]
    except KeyError as e:
        webcaptions_object.operator_object.update_workflow_status("Error")
        operator_object.add_workflow_metadata(WebCaptionsError="Missing a required metadata key {e}".format(e=e))
        raise MasExecutionError(operator_object.return_output_object())

    captions_collection = []
    for lang in targetLanguageCodes:
        webcaptions = []

        webcaptions = webcaptions_object.GetWebCaptions(lang)

        #captions = get_webcaptions_json(self.operator_object, lang)

        vtt = webcaptions_object.WebCaptionsToVTT(webcaptions)
        metadata = webcaptions_object.PutVTT(lang, vtt)

        captions_collection.append(metadata)

    data = {}
    data["CaptionsCollection"] = captions_collection

    webcaptions_object.PutMediaCollection(operator_object.name, data)

    operator_object.update_workflow_status("Complete")
    return operator_object.return_output_object()

def start_translate_webcaptions(event, context):
    print("We got the following event:\n", event)

    operator_object = MediaInsightsOperationHelper(event)
    webcaptions_object = WebCaptions(operator_object)

    try:
        source_lang = operator_object.configuration["SourceLanguageCode"]
        target_langs = operator_object.configuration["TargetLanguageCodes"]
    except KeyError:
        operator_object.update_workflow_status("Error")
        operator_object.add_workflow_metadata(TranslateError="Language codes are not defined")
        raise MasExecutionError(operator_object.return_output_object())
    try:
        terminology_names = operator_object.configuration["TerminologyNames"]
    except KeyError:
        terminology_names = []
    try:
        parallel_data_names = operator_object.configuration["ParallelDataNames"]
    except KeyError:
        parallel_data_names = []

    #webcaptions = get_webcaptions(operator_object, source_lang)
    webcaptions = webcaptions_object.GetWebCaptions(source_lang)

    # Translate takes a list of target languages, but it only allow one item in the list.  Too bad
    # life would be so much easier if it truely allowed many targets.
    webcaptions_object.TranslateWebCaptions(webcaptions, source_lang, target_langs, terminology_names, parallel_data_names)

    return operator_object.return_output_object()


def check_translate_webcaptions(event, context):

    print("We got this event:\n", event)
    operator_object = MediaInsightsOperationHelper(event)
    webcaptions_object = WebCaptions(operator_object)

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
                inputWebCaptions = webcaptions_object.GetWebCaptions(translateJobDescription["TextTranslationJobProperties"]["SourceLanguageCode"])
                outputWebCaptions = webcaptions_object.DelimitedToWebCaptions(inputWebCaptions, translateOutput, webcaptions_object.marker, 15)
                print(outputS3ObjectKey)
                (targetLanguageCode, basename, ext) = outputFilename.split(".")
                #put_webcaptions(operator_object, outputWebCaptions, targetLanguageCode)
                operator_metadata = webcaptions_object.PutWebCaptions(outputWebCaptions, targetLanguageCode)
                operator_metadata = webcaptions_object.PutWebCaptions(outputWebCaptions, targetLanguageCode, source="Translate")

                # Save a copy of the translation text without delimiters.  The translation
                # process may remove or add important whitespace around caption markers
                # Try to replace markers with correct spacing (biased toward Latin based languages)
                if webcaptions_object.contentType == 'text/html':
                    translateOutput = html.unescape(translateOutput)

                # - delimiter next to space keeps the space
                translation_text = translateOutput.replace(" "+webcaptions_object.marker, " ")
                # - delimiter next to contraction (some languages) has no space
                translation_text = translation_text.replace("'"+webcaptions_object.marker, "")
                # - all the rest are replaced with a space. This might add an extra space
                # - but that's proabably better than no space
                translation_text = translation_text.replace(webcaptions_object.marker, " ")

                translation_text_key = translation_path+"translation"+"_"+targetLanguageCode+".txt"
                s3_object = s3_resource.Object(bucket, translation_text_key)
                s3_object.put(Body=translation_text)

            metadata = {
                "OperatorName": "TranslateWebCaptions_"+translateJobLanguageCode,
                "TranslationText": {"S3Bucket": bucket, "S3Key": translation_text_key},
                #"WebCaptions": operator_metadata,
                "WorkflowId": workflow_id,
                "TargetLanguageCode": translateJobLanguageCode
            }
            print(json.dumps(metadata))

            webcaptions_collection.append(metadata)

        except Exception as e:
            operator_object.update_workflow_status("Error")
            operator_object.add_workflow_metadata(CaptionsError="Unable to construct path to translate output in S3: {e}".format(e=str(e)))
            raise MasExecutionError(operator_object.return_output_object())


    data = {}
    data["CaptionsCollection"] = webcaptions_collection
    webcaptions_object.PutMediaCollection(operator_object.name, data)

    return operator_object.return_output_object()

def translate_to_polly_language_code(translate_language_code):

    code_lookup = {
        "ar":"arb",
        "zh":"cmn-CN",
        "zh-TW":"cmn-CN",
        "da":"da-DK",
        "de":"de-DE",
        "en":"en-GB",
        "es":"es-ES",
        "es-MX":"es-MX",
        "fr":"fr-FR",
        "fr-CA":"fr-CA",
        "it":"it-IT",
        "ja":"ja-JP",
        "hi":"hi-IN",
        "ko":"ko-KR",
        "no":"nb-NO",
        "nl":"nl-NL",
        "pl":"pl-PL",
        "pt":"pt-PT",
        "ro":"ro-RO",
        "ru":"ru-RU",
        "sv":"sv-SE",
        "tr":"tr-TR"
    }

    if translate_language_code in code_lookup:
        return code_lookup[translate_language_code]
    else:
        return "not supported"

# Create a Polly track using the text only transcript for each language in the WebCaptions collection for this AssetId
# The pacing of this polly track is determined bu the Polly service
def start_polly_webcaptions (event, context):
    print("We got this event:\n", event)

    operator_object = MediaInsightsOperationHelper(event)
    webcaptions_object = WebCaptions(operator_object)

    captions_collection = webcaptions_object.GetWebCaptionsCollection()
    print("INPUT CAPTIONS COLLECTION")
    print(json.dumps(captions_collection))

    for caption in captions_collection:


        # Always start from WebCaptions data since these are the most recently edited version
        # Convert WebCaptions to a text only transcript
        transcript = webcaptions_object.GetTextOnlyTranscript(caption["TargetLanguageCode"])


        # If input text is empty then we're done.
        if len(transcript) < 1:
            operator_object.update_workflow_status("Complete")
            return operator_object.return_output_object()

        # Get language code of the transcript, we should just pass this along in the event later
        language_code = translate_to_polly_language_code(caption["TargetLanguageCode"])

        if language_code == "not supported":
            caption["PollyStatus"] = "not supported"
            caption["PollyMessage"] = "WARNING: Language code not supported by the Polly service"
        else:

            try:
                # set voice_id based on language
                response = polly.describe_voices(
                    #Engine='standard'|'neural',
                    LanguageCode=language_code
                    #IncludeAdditionalLanguageCodes=True|False,
                    #NextToken='string'
                )

            except Exception as e:
                operator_object.update_workflow_status("Error")
                operator_object.add_workflow_metadata(PollyCollectionError="Unable to get response from polly describe_voices: {e}".format(e=str(e)))
                raise MasExecutionError(operator_object.return_output_object())
            else:
                # just take the fisrt voice in the list.  Maybe later we can extend to choose voice based on other criteria such
                # as gender
                if len(response["Voices"]) > 0 :
                    voice_id = response["Voices"][0]["Id"]
                    caption["VoiceId"] = voice_id
                elif language_code == "hi-IN":
                    # FIXME: Hindi is supported but polly.describe_voices() doesn't return any voices
                    voice_id = "Aditi"
                    caption["VoiceId"] = voice_id
                else:
                    operator_object.add_workflow_metadata(PollyCollectionError="Unable to get a valid Polly voice for language: {code}".format(code=language_code))
                    raise MasExecutionError(operator_object.return_output_object())

            caption["PollyAudio"] = {}
            caption["PollyAudio"]["S3Key"] = 'private/assets/' + operator_object.asset_id + "/workflows/" + operator_object.workflow_execution_id + "/" + "audio_only" + "_" + caption["TargetLanguageCode"]
            caption["PollyAudio"]["S3Bucket"] = caption["TranslationText"]["S3Bucket"]

            try:
                polly_response = polly.start_speech_synthesis_task(
                    OutputFormat='mp3',
                    OutputS3BucketName=caption["PollyAudio"]["S3Bucket"],
                    OutputS3KeyPrefix=caption["PollyAudio"]["S3Key"],
                    Text=transcript,
                    TextType='text',
                    VoiceId=voice_id
                )
            except ClientError as e:
                # Ignore and skip Polly if we get the TextLengthExceededException, bubble up
                # other exceptions.
                if e.response['Error']['Code'] == 'TextLengthExceededException':
                    caption["PollyMessage"] = "WARNING: Polly.Client.exceptions.TextLengthExceededException"
                    caption["PollyStatus"] = "not supported"
                else:
                    raise
            except Exception as e:
                operator_object.update_workflow_status("Error")
                operator_object.add_workflow_metadata(PollyCollectionError="Unable to get response from polly: {e}".format(e=str(e)))
                raise MasExecutionError(operator_object.return_output_object())
            else:
                polly_job_id = polly_response['SynthesisTask']['TaskId']
                caption["PollyTaskId"] = polly_job_id
                caption["PollyStatus"] = "started"

                # Polly adds the polly task id to the S3 Key of the output
                caption["PollyAudio"]["S3Key"] = 'private/assets/' + operator_object.asset_id + "/workflows/" + operator_object.workflow_execution_id + "/" + "audio_only" + "_" + caption["TargetLanguageCode"] + "." + polly_job_id + ".mp3"


    operator_object.add_workflow_metadata(PollyCollection=captions_collection, WorkflowExecutionId=operator_object.workflow_execution_id, AssetId=operator_object.asset_id)
    operator_object.update_workflow_status('Executing')
    return operator_object.return_output_object()

def check_polly_webcaptions(event, context):
    print("We got this event:\n", event)

    operator_object = MediaInsightsOperationHelper(event)
    webcaptions_object = WebCaptions(operator_object)

    print("We got this event:\n", event)

    operator_object = MediaInsightsOperationHelper(event)

    try:
        polly_collection = operator_object.metadata["PollyCollection"]
    except KeyError as e:
        operator_object.update_workflow_status("Error")
        operator_object.add_workflow_metadata(PollyCollectionError="Missing a required metadata key {e}".format(e=e))
        raise MasExecutionError(operator_object.return_output_object())

    finished_tasks = 0
    for caption in polly_collection:
        if caption["PollyStatus"] in ["completed", "failed", "not supported"]:
            finished_tasks = finished_tasks +1
        else:
            try:
                polly_response = polly.get_speech_synthesis_task(
                    TaskId=caption["PollyTaskId"]

                )
            except Exception as e:
                operator_object.update_workflow_status("Error")
                operator_object.add_workflow_metadata(PollyCollectionError="Unable to get response from polly: {e}".format(e=str(e)))
                raise MasExecutionError(operator_object.return_output_object())
            else:
                polly_status = polly_response["SynthesisTask"]["TaskStatus"]
                print("The status from polly is:\n", polly_status)
                if polly_status in ["inProgress", "scheduled"]:
                    operator_object.update_workflow_status("Executing")
                elif polly_status == "completed":
                    # TODO: Store job details as metadata in dataplane
                    finished_tasks = finished_tasks +1

                    caption["PollyAudio"]["Uri"] = polly_response["SynthesisTask"]["OutputUri"]

                    operator_object.update_workflow_status("Executing")

                elif polly_status == "failed":
                    finished_tasks = finished_tasks +1
                    operator_object.update_workflow_status("Error")
                    operator_object.add_workflow_metadata(PollyCollectionError="Polly returned as failed: {e}".format(e=str(polly_response["SynthesisTask"]["TaskStatusReason"])))
                    raise MasExecutionError(operator_object.return_output_object())
                else:
                    operator_object.update_workflow_status("Error")
                    operator_object.add_workflow_metadata(PollyCollectionError="Polly returned as failed: {e}".format(e=str(polly_response["SynthesisTask"]["TaskStatusReason"])))
                    raise MasExecutionError(operator_object.return_output_object())

    # If all the Polly jobs are done then the operator is complete
    if finished_tasks == len(polly_collection):
        operator_object.update_workflow_status("Complete")
        webcaptions_object.PutWebCaptionsCollection("CaptionsCollection", polly_collection)

    operator_object.add_workflow_metadata(PollyCollection=polly_collection)

    return operator_object.return_output_object()

# Convert VTT to WebCaptions
def vttToWebCaptions(operator_object, vttObject):

    webcaptions = []

    # Get metadata
    s3 = boto3.client('s3', config=config)
    try:
        print("Getting data from s3://"+vttObject["Bucket"]+"/"+vttObject["Key"])
        data = s3.get_object(Bucket=vttObject["Bucket"], Key=vttObject["Key"])
        vtt = data['Body'].read().decode('utf-8')
    except Exception as e:
        operator_object.update_workflow_status("Error")
        operator_object.add_workflow_metadata(WebCaptionsError="Unable read VTT file. " + str(e))
        raise MasExecutionError(operator_object.return_output_object())

    buffer = StringIO(vtt)

    for caption in webvtt.read_buffer(buffer):
        webcaption = {}
        webcaption["start"] = formatTimeVTTtoSeconds(caption.start)
        webcaption["end"] = formatTimeVTTtoSeconds(caption.end)
        webcaption["caption"] = caption.text
        webcaptions.append(webcaption)

    return webcaptions

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


# Format a VTT timestamp in HH:MM:SS.mmm
def formatTimeVTTtoSeconds(timeHMSf):
    hours, minutes, seconds = (timeHMSf.split(":"))[-3:]
    hours = int(hours)
    minutes = int(minutes)
    seconds = float(seconds)
    timeSeconds = float(3600 * hours + 60 * minutes + seconds)
    return str(timeSeconds)
