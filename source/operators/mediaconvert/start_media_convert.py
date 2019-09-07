# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import os
import boto3

from MediaInsightsEngineLambdaHelper import MediaInsightsOperationHelper
from MediaInsightsEngineLambdaHelper import MasExecutionError

region = os.environ['AWS_REGION']
mediaconvert_role = os.environ['mediaconvertRole']
mediaconvert = boto3.client("mediaconvert", region_name=region)


def lambda_handler(event, context):
    print("We got the following event:\n", event)
    operator_object = MediaInsightsOperationHelper(event)

    try:
        workflow_id = str(operator_object.workflow_execution_id)
        bucket = operator_object.input["Media"]["Video"]["S3Bucket"]
        key = operator_object.input["Media"]["Video"]["S3Key"]
    except KeyError as e:
        operator_object.update_workflow_status("Error")
        operator_object.add_workflow_metadata(MediaconvertError="Missing a required metadata key {e}".format(e=e))
        raise MasExecutionError(operator_object.return_output_object())

    # Adding in exception block for now since we aren't guaranteed an asset id will be present, should remove later
    try:
        asset_id = operator_object.asset_id
    except KeyError as e:
        print("No asset id passed in with this workflow", e)
        asset_id = ''

    file_input = "s3://" + bucket + "/" + key
    destination = "s3://" + bucket + "/" + 'private/assets/' + asset_id + "/workflows/" + workflow_id + "/"
    thumbnail_destination = "s3://" + bucket + "/" + 'private/assets/' + asset_id + "/"

    try:
        response = mediaconvert.describe_endpoints()
    except Exception as e:
        print("Exception:\n", e)
        operator_object.update_workflow_status("Error")
        operator_object.add_workflow_metadata(MediaconvertError=str(e))
        raise MasExecutionError(operator_object.return_output_object())
    else:
        mediaconvert_endpoint = response["Endpoints"][0]["Url"]
        customer_mediaconvert = boto3.client("mediaconvert", region_name=region, endpoint_url=mediaconvert_endpoint)

    try:
        response = customer_mediaconvert.create_job(
            Role=mediaconvert_role,
            Settings={
              "OutputGroups": [{
                "Name": "File Group",
                "Outputs": [{
                  "ContainerSettings": {
                    "Container": "MP4",
                    "Mp4Settings": {
                      "CslgAtom": "INCLUDE",
                      "FreeSpaceBox": "EXCLUDE",
                      "MoovPlacement": "PROGRESSIVE_DOWNLOAD"
                    }
                  },
                  "AudioDescriptions": [{
                    "AudioTypeControl": "FOLLOW_INPUT",
                    "AudioSourceName": "Audio Selector 1",
                    "CodecSettings": {
                      "Codec": "AAC",
                      "AacSettings": {
                        "AudioDescriptionBroadcasterMix": "NORMAL",
                        "Bitrate": 96000,
                        "RateControlMode": "CBR",
                        "CodecProfile": "LC",
                        "CodingMode": "CODING_MODE_2_0",
                        "RawFormat": "NONE",
                        "SampleRate": 48000,
                        "Specification": "MPEG4"
                      }
                    },
                    "LanguageCodeControl": "FOLLOW_INPUT"
                  }],
                  "Extension": "mp4",
                  "NameModifier": "_audio"
                }],
                "OutputGroupSettings": {
                  "Type": "FILE_GROUP_SETTINGS",
                  "FileGroupSettings": {
                    "Destination": destination
                  }
                }
              },
              {
                  "CustomName": "thumbnail",
                  "Name": "File Group",
                  "Outputs": [
                      {
                          "ContainerSettings": {
                              "Container": "RAW"
                          },
                          "VideoDescription": {
                              "ScalingBehavior": "DEFAULT",
                              "TimecodeInsertion": "DISABLED",
                              "AntiAlias": "ENABLED",
                              "Sharpness": 50,
                              "CodecSettings": {
                                  "Codec": "FRAME_CAPTURE",
                                  "FrameCaptureSettings": {
                                      "FramerateNumerator": 1,
                                      "FramerateDenominator": 5,
                                      "MaxCaptures": 2,
                                      "Quality": 80
                                  }
                              },
                              "DropFrameTimecode": "ENABLED",
                              "ColorMetadata": "INSERT"
                          },
                          "NameModifier": "_thumbnail"
                      }
                  ],
                  "OutputGroupSettings": {
                      "Type": "FILE_GROUP_SETTINGS",
                      "FileGroupSettings": {
                          "Destination": thumbnail_destination
                      }
                  }
              }],
              "AdAvailOffset": 0,
              "Inputs": [{
                "AudioSelectors": {
                  "Audio Selector 1": {
                    "Offset": 0,
                    "DefaultSelection": "DEFAULT",
                    "ProgramSelection": 1
                  }
                },
                "VideoSelector": {
                  "ColorSpace": "FOLLOW"
                },
                "FilterEnable": "AUTO",
                "PsiControl": "USE_PSI",
                "FilterStrength": 0,
                "DeblockFilter": "DISABLED",
                "DenoiseFilter": "DISABLED",
                "TimecodeSource": "EMBEDDED",
                "FileInput": file_input
              }]
            }
        )
    # TODO: Add support for boto client error handling
    except Exception as e:
        print("Exception:\n", e)
        operator_object.update_workflow_status("Error")
        operator_object.add_workflow_metadata(MediaconvertError=str(e))
        raise MasExecutionError(operator_object.return_output_object())
    else:
        job_id = response['Job']['Id']
        operator_object.update_workflow_status("Executing")
        operator_object.add_workflow_metadata(MediaconvertJobId=job_id, MediaconvertInputFile=key, AssetId=asset_id,
                                      WorkflowExecutionId=workflow_id)
        return operator_object.return_output_object()

