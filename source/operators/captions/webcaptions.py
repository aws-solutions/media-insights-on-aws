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

not_supported = "not supported"


class WebCaptions:
    def __init__(self, operator_object):
        """
        :param event: The event passed in to the operator

        """
        print("WebCaptions operator_object = {}".format(operator_object.return_output_object()))
        self.operator_object = operator_object

        try:
            self.transcribe_operator_name = "TranscribeVideo"
            self.workflow_id = operator_object.workflow_execution_id
            self.asset_id = operator_object.asset_id
            self.marker = "<span>"
            self.content_type = "text/html"
            self.existing_subtitles = False

            # The source language may not have been known when the configuration for
            # this operator was created. In that case, this operator may have been
            # placed downstream from the Transcribe operator which can auto-detect
            # the source language. Transcribe will put the source language into the
            # TranscribeSourceLanguage field of the workflow metadata object. If the
            # TranscribeSourceLanguage field is present then we will use that source
            # language throughout this operator.

            if "TranscribeSourceLanguage" in self.operator_object.input['MetaData']:
                self.source_language_code = self.operator_object.input['MetaData']['TranscribeSourceLanguage'].split('-')[0]
            elif "TranslateSourceLanguage" in self.operator_object.input['MetaData']:
                self.source_language_code = self.operator_object.input['MetaData']['TranslateSourceLanguage'].split('-')[0]
            else:
                # If TranscribeSourceLanguage is not available, then SourceLanguageCode
                # must be present in the operator Configuration block.
                self.source_language_code = self.operator_object.configuration["SourceLanguageCode"]

            if "TargetLanguageCodes" in self.operator_object.configuration:
                self.target_language_codes = self.operator_object.configuration["TargetLanguageCodes"]
            if "ExistingSubtitlesObject" in self.operator_object.configuration:
                self.existing_subtitles_object = self.operator_object.configuration["ExistingSubtitlesObject"]
                self.existing_subtitles = True
        except KeyError as e:
            self.operator_object.update_workflow_status("Error")
            self.operator_object.add_workflow_metadata(WebCaptionsError="No valid inputs {e}".format(e=e))
            raise MasExecutionError(operator_object.return_output_object())

    def web_captions_operator_name(self, language_code=None, source=""):
        # This function determines filenames using the pattern "WebCaptions_[language code]".

        print("WebCaptionsOperatorName {}, {}".format(language_code, source))

        operator_name = "WebCaptions" + source

        if language_code is not None:
            return operator_name + "_" + language_code

        try:
            name = operator_name + "_" + self.source_language_code
        except KeyError as e:
            self.operator_object.update_workflow_status("Error")
            self.operator_object.add_workflow_metadata(WebCaptionsError="Missing language code for WebCaptions {e}".format(e=e))
            raise MasExecutionError(self.operator_object.return_output_object())

        print("WebCaptionsOperatorName() Name {}".format(name))
        return name

    def captions_operator_name(self, language_code=None):
        # This function determines filenames using the pattern "Captions_[language code]".

        operator_name = "Captions"

        if language_code is not None:
            return operator_name + "_" + language_code

        try:
            name = operator_name + "_" + self.source_language_code
        except KeyError as e:
            self.operator_object.update_workflow_status("Error")
            self.operator_object.add_workflow_metadata(WebCaptionsError="Missing language code for WebCaptions {e}".format(e=e))
            raise MasExecutionError(self.operator_object.return_output_object())

        print("CaptionsOperatorName() Name {}".format(name))
        return name

    def get_transcript(self):

        transcript = []

        response = dataplane.retrieve_asset_metadata(self.asset_id, operator_name=self.transcribe_operator_name)
        transcript.append(response["results"])

        while "cursor" in response:
            response = dataplane.retrieve_asset_metadata(self.asset_id, operator_name=self.transcribe_operator_name, cursor=response["cursor"])
            transcript.append(response["results"])

        return transcript

    class TranscribeContext:
        end_time = 0.0
        word_count = 0
        captions = []
        caption = None

    def _transcribe(self, tc, item):
        max_length = 120
        max_words = 25
        max_silence = 1.5

        is_punctuation = item["type"] == "punctuation"

        if tc.caption is None:

            # Start of a line with punctuation, just skip it
            if is_punctuation:
                return

            # Create a new caption line
            tc.caption = {
                "start": float(item["start_time"]),
                "caption": "",
                "wordConfidence": []
            }

        if not is_punctuation:

            start_time = float(item["start_time"])

            # Check to see if there has been a long silence
            # between the last recorded word and start a new
            # caption if this is the case, ending the last time
            # as this one starts.

            if (len(tc.caption["caption"]) > 0) and ((tc.end_time + max_silence) < start_time):

                tc.caption["end"] = start_time
                tc.captions.append(tc.caption)

                tc.caption = {
                    "start": float(start_time),
                    "caption": "",
                    "wordConfidence": []
                }

                tc.word_count = 0

            tc.end_time = float(item["end_time"])

        requires_space = (not is_punctuation) and (len(tc.caption["caption"]) > 0)

        if requires_space:
            tc.caption["caption"] += " "

        # Process tweaks

        text = item["alternatives"][0]["content"]
        confidence = item["alternatives"][0]["confidence"]
        text_lower = text.lower()

        tc.caption["caption"] += text

        # Track raw word confidence
        if not is_punctuation:
            tc.caption["wordConfidence"].append(
                {
                    "w": text_lower,
                    "c": float(confidence)
                }
            )
            # Count words
            tc.word_count += 1

        # If we have reached a good amount of text finalize the caption
        if (tc.word_count >= max_words) or (len(tc.caption["caption"]) >= max_length) or is_punctuation and text in "...?!":
            tc.caption["end"] = tc.end_time
            tc.captions.append(tc.caption)
            tc.word_count = 0
            tc.caption = None

    def transcribe_to_web_captions(self, transcripts):

        tc = self.TranscribeContext()

        for item in (item for transcript in transcripts for item in transcript["results"]["items"]):
            self._transcribe(tc, item)

        # Close the last caption if required

        if tc.caption is not None:
            tc.caption["end"] = tc.end_time
            tc.captions.append(tc.caption)

        return tc.captions

    def get_web_captions(self, language_code):
        webcaptions_operator_name = self.web_captions_operator_name(language_code)
        print(webcaptions_operator_name)

        response = dataplane.retrieve_asset_metadata(self.asset_id, operator_name=webcaptions_operator_name)
        print(response)
        return response["results"]["WebCaptions"]

    def put_web_captions(self, webcaptions, language_code=None, source=""):
        webcaptions_operator_name = self.web_captions_operator_name(language_code, source)

        web_captions = {"WebCaptions": webcaptions}
        response = dataplane.store_asset_metadata(asset_id=self.asset_id, operator_name=webcaptions_operator_name, workflow_id=self.workflow_id, results=web_captions, paginate=False)

        if response.get("Status") == "Success":
            return self.operator_object.return_output_object()

        self.operator_object.update_workflow_status("Error")
        self.operator_object.add_workflow_metadata(WebCaptionsError="Unable to store captions {} {e}".format(webcaptions_operator_name, e=response))
        raise MasExecutionError(self.operator_object.return_output_object())

    def get_web_captions_collection(self):
        webcaptions_collection_name = "TranslateWebCaptions"
        print(webcaptions_collection_name)

        response = dataplane.retrieve_asset_metadata(self.asset_id, operator_name=webcaptions_collection_name)
        print(response)
        return response["results"]["CaptionsCollection"]

    def get_text_only_transcript(self, language_code):

        webcaptions = self.get_web_captions(language_code)
        transcript = self.web_captions_to_text_transcript(webcaptions)

        return transcript

    def web_captions_to_text_transcript(self, webcaptions):

        transcript = ""

        for caption in webcaptions:
            transcript = transcript + caption["caption"]

        return transcript

    def put_web_captions_collection(self, operator, collection):

        collection_dict = {operator: collection}
        response = dataplane.store_asset_metadata(self.asset_id, self.operator_object.name, self.workflow_id, collection_dict)

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

    def web_captions_to_srt(self, webcaptions):
        srt = ''

        index = 1

        for caption in webcaptions:

            srt += str(index) + '\n'
            srt += format_time_srt(float(caption["start"])) + ' --> ' + format_time_srt(float(caption["end"])) + '\n'
            srt += caption["caption"] + '\n\n'
            index += 1

        return srt

    def put_srt(self, lang, srt):
        response = dataplane.generate_media_storage_path(self.asset_id, self.workflow_id)

        bucket = response["S3Bucket"]
        key = response["S3Key"] + self.captions_operator_name(lang) + ".srt"
        s3_object = s3_resource.Object(bucket, key)

        s3_object.put(Body=srt)

        metadata = {
            "OperatorName": self.captions_operator_name(lang),
            "Results": {"S3Bucket": bucket, "S3Key": key},
            "WorkflowId": self.workflow_id,
            "LanguageCode": lang
        }

        return metadata

    def put_vtt(self, lang, vtt):
        response = dataplane.generate_media_storage_path(self.asset_id, self.workflow_id)

        bucket = response["S3Bucket"]
        key = response["S3Key"] + self.captions_operator_name(lang) + ".vtt"
        s3_object = s3_resource.Object(bucket, key)

        s3_object.put(Body=vtt)

        metadata = {
            "OperatorName": self.captions_operator_name(lang),
            "Results": {"S3Bucket": bucket, "S3Key": key},
            "WorkflowId": self.workflow_id,
            "LanguageCode": lang
        }

        return metadata

    def web_captions_to_vtt(self, webcaptions):
        vtt = 'WEBVTT\n\n'

        for caption in webcaptions:

            vtt += format_time_vtt(float(caption["start"])) + ' --> ' + format_time_vtt(float(caption["end"])) + '\n'
            vtt += caption["caption"] + '\n\n'

        return vtt

    # Converts a delimited file back to web captions format.
    # Uses the source web captions to get timestamps and source caption text (saved in sourceCaption field).
    def delimited_to_web_captions(self, source_web_captions, delimited_captions, delimiter):

        if self.content_type == 'text/html':
            delimited_captions = html.unescape(delimited_captions)

        entries = delimited_captions.split(delimiter)

        output_web_captions = []
        for i, c in enumerate(source_web_captions):
            caption = {}
            caption["start"] = c["start"]
            caption["end"] = c["end"]
            caption["caption"] = entries[i]
            caption["sourceCaption"] = c["caption"]
            output_web_captions.append(caption)

        return output_web_captions

    def put_media_collection(self, collection):
        response = dataplane.store_asset_metadata(self.asset_id, self.operator_object.name, self.workflow_id, collection)

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

    def translate_web_captions(self, input_captions, source_language_code, target_language_codes, terminology_names=[], parallel_data_names=[]):

        marker = self.marker

        try:

            translate_role = os.environ['translateRole']
            asset_id = self.operator_object.asset_id
            workflow_id = self.operator_object.workflow_execution_id

            # Convert WebCaptions to text with marker between caption lines
            input_entries = map(lambda c: c["caption"], input_captions)
            input_delimited = marker.join(input_entries)

            transcript_storage_path = dataplane.generate_media_storage_path(asset_id, workflow_id)
            bucket = transcript_storage_path['S3Bucket']
            translation_input_path = transcript_storage_path['S3Key'] + "webcaptions_translate_input/"
            translation_input_uri = 's3://' + bucket + "/" + translation_input_path
            translation_output_path = transcript_storage_path['S3Key'] + "webcaptions_translate_output/"
            translation_output_uri = 's3://' + bucket + "/" + translation_output_path
            key = translation_input_path + "transcript_with_caption_markers.txt"

            print("put object {} {}".format(bucket, key))
            s3.put_object(Bucket=bucket, Key=key, Body=input_delimited)

            print("create translate output folder if it doesn't exist")
            dummy_key = translation_output_path + "/" + "foo"
            s3.put_object(Bucket=bucket, Key=dummy_key, Body="foo")

            print("Translate inputs")
            print("translation_input_uri {}".format(translation_input_uri))
            print("translation_output_uri {}".format(translation_output_uri))
            print("translate_role {}".format(translate_role))

            # Kick off a job for each input language
            translate_jobs = []
            # Avoid translating to the same language as the source language
            filtered_target_language_codes = (targetLanguageCode
                                              for targetLanguageCode in target_language_codes
                                              if targetLanguageCode != source_language_code)
            for target_language_code in filtered_target_language_codes:
                print("Starting translation to {}".format(target_language_code))
                # Even though the API takes a list of targets, Translate only supports
                # a list of 1 or less

                # Set the job name to avoid creating the same job multiple time if
                # we retry due to an error.
                singleton_target_list = []
                singleton_target_list.append(target_language_code)
                job_name = "MIE_" + asset_id + "_" + workflow_id + "_" + target_language_code
                print("JobName: {}".format(job_name))

                terminology_name = []
                if len(terminology_names) > 0:
                    # Find a terminology in the list of custom terminologies
                    # that defines translations for targetLanguageCode.
                    # If there happens to be more than one terminology matching targetLanguageCode
                    # then just use the first one in the list.
                    terminology_name = [item['Name']
                                        for item in terminology_names
                                        if target_language_code in item['TargetLanguageCodes']
                                        ][0:1]
                    print("No custom terminology specified."
                          if len(terminology_name) == 0 else
                          "Using custom terminology {}".format(terminology_name))

                parallel_data_name = []
                if len(parallel_data_names) > 0:
                    # Find a parallel data set in the list of
                    # that defines translations for targetLanguageCode.
                    # If there happens to be more than one  matching targetLanguageCode
                    # then just use the first one in the list.
                    parallel_data_name = [item['Name']
                                          for item in parallel_data_names
                                          if target_language_code in item['TargetLanguageCodes']
                                          ][0:1]
                    print("No parallel data specified."
                          if len(parallel_data_name) == 0 else
                          "Using parallel data_names {}".format(parallel_data_name))

                translation_job_config = {
                    "JobName": job_name,
                    "InputDataConfig": {
                        'S3Uri': translation_input_uri,
                        'ContentType': self.content_type
                    },
                    "OutputDataConfig": {
                        'S3Uri': translation_output_uri
                    },
                    "DataAccessRoleArn": translate_role,
                    "SourceLanguageCode": source_language_code,
                    "TargetLanguageCodes": singleton_target_list,
                    "TerminologyNames": terminology_name,
                }
                current_region = os.environ['AWS_REGION']
                # Include Parallel Data configuration when running in a region where
                # Active Custom Translation is available. Reference:
                # https://docs.aws.amazon.com/translate/latest/dg/customizing-translations-parallel-data.html
                active_custom_translation_supported_regions = ['us-east-1', 'us-west-2', 'eu-west-1']
                if current_region in active_custom_translation_supported_regions:
                    translation_job_config["ParallelDataNames"] = parallel_data_name

                # Save the delimited transcript text to S3
                response = translate_client.start_text_translation_job(**translation_job_config)
                jobinfo = {
                    "JobId": response["JobId"],
                    "TargetLanguageCode": target_language_code
                }
                translate_jobs.append(jobinfo)

                self.operator_object.add_workflow_metadata(TextTranslateJobPropertiesList=translate_jobs, TranslateSourceLanguage=source_language_code)
        except Exception as e:
            self.operator_object.update_workflow_status("Error")
            self.operator_object.add_workflow_metadata(TranslateError="Unable to start translation WebCaptions job: {e}".format(e=str(e)))
            raise MasExecutionError(self.operator_object.return_output_object())


def print_event(event):
    print("We got the following event:\n", event)


def format_missing_metadata_key_error(error):
    return "Missing a required metadata key {e}".format(e=error)


# Create web captions with line by line captions from the transcribe output
def web_captions(event, _context):

    print_event(event)
    operator_object = MediaInsightsOperationHelper(event)

    webcaptions_object = WebCaptions(operator_object)

    transcript = webcaptions_object.get_transcript()
    webcaptions = webcaptions_object.transcribe_to_web_captions(transcript)

    # Save the the original Transcribe generated captions to compare to any ground truth modifications
    # made later so we can calculate quality metrics of the machine translation
    webcaptions_object.put_web_captions(webcaptions, source="TranscribeVideo")

    # if a vtt file was input, use that as the most recent version of the webcaptions file
    if webcaptions_object.existing_subtitles:
        webcaptions = vtt_to_web_captions(operator_object, webcaptions_object.existing_subtitles_object)

    webcaptions_object.put_web_captions(webcaptions)

    operator_object.update_workflow_status("Complete")
    return operator_object.return_output_object()


# Create a SRT captions file from the web captions
def create_srt(event, _context):
    print_event(event)

    operator_object = MediaInsightsOperationHelper(event)
    webcaptions_object = WebCaptions(operator_object)

    try:
        target_language_codes = webcaptions_object.operator_object.configuration["TargetLanguageCodes"]
        # This function is intended to generate SRT caption files for every translated
        # transcript, but we also want to provide an SRT caption file for the source
        # language, so here we append the source language to the target languages to
        # make sure that happens.
        if webcaptions_object.source_language_code not in target_language_codes:
            target_language_codes.append(webcaptions_object.source_language_code)
    except KeyError as e:
        webcaptions_object.operator_object.update_workflow_status("Error")
        operator_object.add_workflow_metadata(WebCaptionsError=format_missing_metadata_key_error(e))
        raise MasExecutionError(operator_object.return_output_object())

    captions_collection = []
    for lang in target_language_codes:
        webcaptions = []
        webcaptions_object.web_captions_operator_name(lang)

        webcaptions = webcaptions_object.get_web_captions(lang)

        srt = webcaptions_object.web_captions_to_srt(webcaptions)
        metadata = webcaptions_object.put_srt(lang, srt)

        captions_collection.append(metadata)

    data = {}
    data["CaptionsCollection"] = captions_collection

    webcaptions_object.put_media_collection(data)

    operator_object.update_workflow_status("Complete")
    return operator_object.return_output_object()


# Create a VTT captions file from the web captions
def create_vtt(event, _context):
    print_event(event)

    operator_object = MediaInsightsOperationHelper(event)
    webcaptions_object = WebCaptions(operator_object)

    try:
        target_language_codes = webcaptions_object.operator_object.configuration[
            "TargetLanguageCodes"]
        # This function is intended to generate VTT caption files for every translated
        # transcript, but we also want to provide an VTT caption file for the source
        # language, so here we append the source language to the target languages to
        # make sure that happens.
        if webcaptions_object.source_language_code not in target_language_codes:
            target_language_codes.append(webcaptions_object.source_language_code)
    except KeyError as e:
        webcaptions_object.operator_object.update_workflow_status("Error")
        operator_object.add_workflow_metadata(WebCaptionsError=format_missing_metadata_key_error(e))
        raise MasExecutionError(operator_object.return_output_object())

    captions_collection = []
    for lang in target_language_codes:
        webcaptions = []

        webcaptions = webcaptions_object.get_web_captions(lang)

        vtt = webcaptions_object.web_captions_to_vtt(webcaptions)
        metadata = webcaptions_object.put_vtt(lang, vtt)

        captions_collection.append(metadata)

    data = {}
    data["CaptionsCollection"] = captions_collection

    webcaptions_object.put_media_collection(data)

    operator_object.update_workflow_status("Complete")
    return operator_object.return_output_object()


def start_translate_webcaptions(event, _context):
    print_event(event)

    operator_object = MediaInsightsOperationHelper(event)
    webcaptions_object = WebCaptions(operator_object)

    try:
        source_lang = webcaptions_object.source_language_code
        target_langs = webcaptions_object.target_language_codes
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

    webcaptions = webcaptions_object.get_web_captions(source_lang)

    webcaptions_object.translate_web_captions(webcaptions, source_lang, target_langs, terminology_names, parallel_data_names)
    return operator_object.return_output_object()


# Describe a translation job for check_translate_webcaptions.
def describe_text_translate_job(operator_object, job):
    """
    Describe a translation job for check_translate_webcaptions.

    :param operator_object: The MediaInsightsOperationHelper object.
    :param job: A dict containing a "JobId" key.
    :return: The job ID and description of the text translation job: (job_id, response)
    :raises MasExecutionError: if an error is encountered.
    """
    try:
        job_id = job["JobId"]

    except KeyError as e:
        operator_object.update_workflow_status("Error")
        operator_object.add_workflow_metadata(TranslateError=format_missing_metadata_key_error(e))
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

    return (job_id, response)


def check_translate_webcaptions(event, _context):

    print_event(event)
    operator_object = MediaInsightsOperationHelper(event)
    webcaptions_object = WebCaptions(operator_object)

    # If the array of target languages only contains the source language
    # then we have nothing to do.
    if webcaptions_object.target_language_codes == [webcaptions_object.source_language_code]:
        print("Skipping check_translate_webcaptions because source language is same as target language")
        operator_object.update_workflow_status("Complete")
        return operator_object.return_output_object()

    try:
        translate_jobs = operator_object.metadata["TextTranslateJobPropertiesList"]
        workflow_id = operator_object.workflow_execution_id
        asset_id = operator_object.asset_id
        transcript_storage_path = dataplane.generate_media_storage_path(asset_id, workflow_id)
        bucket = transcript_storage_path['S3Bucket']

    except KeyError as e:
        operator_object.update_workflow_status("Error")
        operator_object.add_workflow_metadata(TranslateError=format_missing_metadata_key_error(e))
        raise MasExecutionError(operator_object.return_output_object())

    # Check the status of each job
    # - IF ANY job has an error, we fail the workflow and return from the loop
    # - IF ANY job is still running, the workflow is still Executing
    # - If ALL jobs are complete, we reach the end of the loop and the workflow is complete
    for job in translate_jobs:

        job_id, response = describe_text_translate_job(operator_object, job)
        job_status_list = []

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

            translate_job_description = translate_client.describe_text_translation_job(JobId=job["JobId"])
            translate_job_s3_uri = translate_job_description["TextTranslationJobProperties"]["OutputDataConfig"]["S3Uri"]
            translate_job_url = urlparse(translate_job_s3_uri, allow_fragments=False)
            translate_job_language_code = translate_job_description["TextTranslationJobProperties"]["TargetLanguageCodes"][0]

            translate_job_s3_location = {
                "Uri": translate_job_s3_uri,
                "Bucket": translate_job_url.netloc,
                "Key": translate_job_url.path.strip("/")
            }

            # use input web captions to convert translation output to web captions format
            for output_s3_object_key in map(lambda s: s.key, s3_resource.Bucket(translate_job_s3_location["Bucket"]).objects.filter(Prefix=translate_job_s3_location["Key"] + "/", Delimiter="/")):
                print("Save translation for each output of job {} output {}".format(job["JobId"], output_s3_object_key))

                output_filename = ntpath.basename(output_s3_object_key)

                translate_output = s3_resource.Object(translate_job_s3_location["Bucket"], output_s3_object_key).get()["Body"].read().decode("utf-8")
                input_web_captions = webcaptions_object.get_web_captions(translate_job_description["TextTranslationJobProperties"]["SourceLanguageCode"])
                output_web_captions = webcaptions_object.delimited_to_web_captions(input_web_captions, translate_output, webcaptions_object.marker)
                print(output_s3_object_key)
                (target_language_code, basename, ext) = output_filename.split(".")
                # put_webcaptions(operator_object, outputWebCaptions, targetLanguageCode)
                webcaptions_object.put_web_captions(output_web_captions, target_language_code)
                webcaptions_object.put_web_captions(output_web_captions, target_language_code, source="Translate")

                # Save a copy of the translation text without delimiters.  The translation
                # process may remove or add important whitespace around caption markers
                # Try to replace markers with correct spacing (biased toward Latin based languages)
                if webcaptions_object.content_type == 'text/html':
                    translate_output = html.unescape(translate_output)

                # - delimiter next to space keeps the space
                translation_text = translate_output.replace(" " + webcaptions_object.marker, " ")
                # - delimiter next to contraction (some languages) has no space
                translation_text = translation_text.replace("'" + webcaptions_object.marker, "")
                # - all the rest are replaced with a space. This might add an extra space
                # - but that's better than no space
                translation_text = translation_text.replace(webcaptions_object.marker, " ")

                translation_text_key = translation_path + "translation" + "_" + target_language_code + ".txt"
                s3_object = s3_resource.Object(bucket, translation_text_key)
                s3_object.put(Body=translation_text)

            metadata = {
                "OperatorName": "TranslateWebCaptions_" + translate_job_language_code,
                "TranslationText": {"S3Bucket": bucket, "S3Key": translation_text_key},
                # "WebCaptions": operator_metadata,
                "WorkflowId": workflow_id,
                "TargetLanguageCode": translate_job_language_code
            }
            print(json.dumps(metadata))

            webcaptions_collection.append(metadata)

        except Exception as e:
            operator_object.update_workflow_status("Error")
            operator_object.add_workflow_metadata(CaptionsError="Unable to construct path to translate output in S3: {e}".format(e=str(e)))
            raise MasExecutionError(operator_object.return_output_object())

    data = {"CaptionsCollection": webcaptions_collection}
    webcaptions_object.put_media_collection(data)

    return operator_object.return_output_object()


def translate_to_polly_language_code(translate_language_code):

    code_lookup = {
        "ar": "arb",
        "zh": "cmn-CN",
        "zh-TW": "cmn-CN",
        "da": "da-DK",
        "de": "de-DE",
        "en": "en-GB",
        "es": "es-ES",
        "es-MX": "es-MX",
        "fr": "fr-FR",
        "fr-CA": "fr-CA",
        "it": "it-IT",
        "ja": "ja-JP",
        "hi": "hi-IN",
        "ko": "ko-KR",
        "no": "nb-NO",
        "nl": "nl-NL",
        "pl": "pl-PL",
        "pt": "pt-PT",
        "ro": "ro-RO",
        "ru": "ru-RU",
        "sv": "sv-SE",
        "tr": "tr-TR"
    }

    return code_lookup.get(translate_language_code, not_supported)


# Called by start_polly_for_webcaptions to create a Polly track for a language
def start_polly_for_webcaption(operator_object, caption, transcript, language_code):
    try:
        # set voice_id based on language
        response = polly.describe_voices(
            LanguageCode=language_code
        )

    except Exception as e:
        operator_object.update_workflow_status("Error")
        operator_object.add_workflow_metadata(PollyCollectionError="Unable to get response from polly describe_voices: {e}".format(e=str(e)))
        raise MasExecutionError(operator_object.return_output_object())

    # just take the first voice in the list.  Maybe later we can extend to choose voice based on other criteria such
    # as gender
    if len(response["Voices"]) > 0:
        voice_id = response["Voices"][0]["Id"]
        caption["VoiceId"] = voice_id
    elif language_code == "hi-IN":
        # TODO: Hindi is supported but polly.describe_voices() doesn't return any voices
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
        if e.response['Error']['Code'] != 'TextLengthExceededException':
            raise

        caption["PollyMessage"] = "WARNING: Polly.Client.exceptions.TextLengthExceededException"
        caption["PollyStatus"] = not_supported
    except Exception as e:
        operator_object.update_workflow_status("Error")
        operator_object.add_workflow_metadata(PollyCollectionError="Unable to get response from polly: {e}".format(e=str(e)))
        raise MasExecutionError(operator_object.return_output_object())

    polly_job_id = polly_response['SynthesisTask']['TaskId']
    caption["PollyTaskId"] = polly_job_id
    caption["PollyStatus"] = "started"

    # Polly adds the polly task id to the S3 Key of the output
    caption["PollyAudio"]["S3Key"] = 'private/assets/' + operator_object.asset_id + "/workflows/" + operator_object.workflow_execution_id + "/" + "audio_only" + "_" + caption["TargetLanguageCode"] + "." + polly_job_id + ".mp3"


# Create a Polly track using the text only transcript for each language in the WebCaptions collection for this AssetId
# The pacing of this polly track is determined bu the Polly service
def start_polly_webcaptions(event, _context):
    print_event(event)

    operator_object = MediaInsightsOperationHelper(event)
    webcaptions_object = WebCaptions(operator_object)

    captions_collection = webcaptions_object.get_web_captions_collection()
    print("INPUT CAPTIONS COLLECTION")
    print(json.dumps(captions_collection))

    for caption in captions_collection:

        # Always start from WebCaptions data since these are the most recently edited version
        # Convert WebCaptions to a text only transcript
        transcript = webcaptions_object.get_text_only_transcript(caption["TargetLanguageCode"])

        # If input text is empty then we're done.
        if len(transcript) < 1:
            operator_object.update_workflow_status("Complete")
            return operator_object.return_output_object()

        # Get language code of the transcript, we should just pass this along in the event later
        language_code = translate_to_polly_language_code(caption["TargetLanguageCode"])

        if language_code == not_supported:
            caption["PollyStatus"] = not_supported
            caption["PollyMessage"] = "WARNING: Language code not supported by the Polly service"
            continue

        start_polly_for_webcaption(operator_object, caption, transcript, language_code)

    operator_object.add_workflow_metadata(PollyCollection=captions_collection, WorkflowExecutionId=operator_object.workflow_execution_id, AssetId=operator_object.asset_id)
    operator_object.update_workflow_status('Executing')
    return operator_object.return_output_object()


def check_polly_webcaptions(event, _context):
    print_event(event)

    operator_object = MediaInsightsOperationHelper(event)
    webcaptions_object = WebCaptions(operator_object)

    print_event(event)

    operator_object = MediaInsightsOperationHelper(event)

    try:
        polly_collection = operator_object.metadata["PollyCollection"]
    except KeyError as e:
        operator_object.update_workflow_status("Error")
        operator_object.add_workflow_metadata(PollyCollectionError=format_missing_metadata_key_error(e))
        raise MasExecutionError(operator_object.return_output_object())

    finished_tasks = 0
    for caption in polly_collection:
        if caption["PollyStatus"] in ["completed", "failed", not_supported]:
            finished_tasks = finished_tasks + 1
        else:
            try:
                polly_response = polly.get_speech_synthesis_task(
                    TaskId=caption["PollyTaskId"]

                )
            except Exception as e:
                operator_object.update_workflow_status("Error")
                operator_object.add_workflow_metadata(PollyCollectionError="Unable to get response from polly: {e}".format(e=str(e)))
                raise MasExecutionError(operator_object.return_output_object())

            polly_status = polly_response["SynthesisTask"]["TaskStatus"]
            print("The status from polly is:\n", polly_status)
            if polly_status in ["inProgress", "scheduled"]:
                operator_object.update_workflow_status("Executing")
            elif polly_status == "completed":
                # TODO: Store job details as metadata in dataplane
                finished_tasks = finished_tasks + 1

                caption["PollyAudio"]["Uri"] = polly_response["SynthesisTask"]["OutputUri"]

                operator_object.update_workflow_status("Executing")

            elif polly_status == "failed":
                finished_tasks = finished_tasks + 1
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
        webcaptions_object.put_web_captions_collection("CaptionsCollection", polly_collection)

    operator_object.add_workflow_metadata(PollyCollection=polly_collection)

    return operator_object.return_output_object()


# Convert VTT to WebCaptions
def vtt_to_web_captions(operator_object, vtt_object):

    webcaptions = []

    try:
        print("Getting data from s3://" + vtt_object["Bucket"] + "/" + vtt_object["Key"])
        data = s3.get_object(Bucket=vtt_object["Bucket"], Key=vtt_object["Key"])
        vtt = data['Body'].read().decode('utf-8')
    except Exception as e:
        operator_object.update_workflow_status("Error")
        operator_object.add_workflow_metadata(WebCaptionsError="Unable read VTT file. " + str(e))
        raise MasExecutionError(operator_object.return_output_object())

    buf = StringIO(vtt)

    for caption in webvtt.read_buffer(buf):
        webcaption = {}
        webcaption["start"] = format_time_vtt_to_seconds(caption.start)
        webcaption["end"] = format_time_vtt_to_seconds(caption.end)
        webcaption["caption"] = caption.text
        webcaptions.append(webcaption)

    return webcaptions


# Format an SRT timestamp in HH:MM:SS,mmm
def format_time_srt(time_seconds):

    ONE_HOUR = 60 * 60
    ONE_MINUTE = 60
    hours = math.floor(time_seconds / ONE_HOUR)
    remainder = time_seconds - (hours * ONE_HOUR)
    minutes = math.floor(remainder / 60)
    remainder = remainder - (minutes * ONE_MINUTE)
    seconds = math.floor(remainder)
    remainder = remainder - seconds
    millis = remainder

    return str(hours).zfill(2) + ':' + str(minutes).zfill(2) + ':' + str(seconds).zfill(2) + ',' + str(math.floor(millis * 1000)).zfill(3)


# Format a VTT timestamp in HH:MM:SS.mmm
def format_time_vtt(time_seconds):
    ONE_HOUR = 60 * 60
    ONE_MINUTE = 60
    hours = math.floor(time_seconds / ONE_HOUR)
    remainder = time_seconds - (hours * ONE_HOUR)
    minutes = math.floor(remainder / 60)
    remainder = remainder - (minutes * ONE_MINUTE)
    seconds = math.floor(remainder)
    remainder = remainder - seconds
    millis = remainder
    return str(hours).zfill(2) + ':' + str(minutes).zfill(2) + ':' + str(seconds).zfill(2) + '.' + str(math.floor(millis * 1000)).zfill(3)


# Parse a VTT timestamp in HH:MM:SS.mmm into seconds
def format_time_vtt_to_seconds(time_hours_minutes_seconds):
    hours, minutes, seconds = (time_hours_minutes_seconds.split(":"))[-3:]
    hours = int(hours)
    minutes = int(minutes)
    seconds = float(seconds)
    time_seconds = float(3600 * hours + 60 * minutes + seconds)
    return str(time_seconds)
