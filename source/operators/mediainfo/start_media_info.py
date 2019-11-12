# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

###############################################################################
# PURPOSE:
#   This operator is designed to get a thumbnail for a video.
#   It will grab the frame from 7 seconds into the video. That position can be
#   configured with the "ThumbnailPosition" argument. This operation is performed by
#   Media Convert.
#
# OUTPUT:
#   Thumbnails will be saved to the following path:
#       s3://" + $DATAPLANE_BUCKET + "/" + 'private/assets/' + asset_id + "/"
#   The thumbnail filename will end with "_thumbnail.0000001.jpg".
#   If the user specifies a thumbnail position that exceeds the video duration
#   then a thumbnail will be created at time 0 and have a filename ending
#   with end with "_thumbnail.0000000.jpg".
#
# USAGE:
#   To run this operator add
#   '"MediaInfo":{"Position":7, "Enabled":true}'
#   to the workflow configuration, like this:
#
#   curl -k -X POST -H "Authorization: $MIE_ACCESS_TOKEN" -H "Content-Type: application/json" --data '{"Name":"MieCompleteWorkflow","Configuration":{"defaultVideoStage":{"MediaInfo":{"ThumbnailPosition":7, Enabled":true}}}},"Input":{"Media":{"Video":{"S3Bucket":"'$DATAPLANE_BUCKET'","S3Key":"My Video.mp4"}}}}'  $WORKFLOW_API_ENDPOINT/workflow/execution
#
#  For instructions on getting $MIE_ACCESS_TOKEN, see:
#  https://github.com/awslabs/aws-media-insights-engine/blob/master/IMPLEMENTATION_GUIDE.md#step-6-test-your-operator
#
###############################################################################

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
        operator_object.add_workflow_metadata(MediainfoError="Missing a required metadata key {e}".format(e=e))
        raise MasExecutionError(operator_object.return_output_object())

    # Adding in exception block for now since we aren't guaranteed an asset id will be present, should remove later
    try:
        asset_id = operator_object.asset_id
    except KeyError as e:
        print("No asset id passed in with this workflow", e)
        asset_id = ''
    file_input = "s3://" + bucket + "/" + key
    thumbnail_destination = "s3://" + bucket + "/" + 'private/assets/' + asset_id + "/"

    # Get user-defined location for generic data file
    if "ThumbnailPosition" in operator_object.configuration:
        thumbnail_position = operator_object.configuration["ThumbnailPosition"]
    else:
        thumbnail_position = 7

    try:
        response = mediaconvert.describe_endpoints()
    except Exception as e:
        print("Exception:\n", e)
        operator_object.update_workflow_status("Error")
        operator_object.add_workflow_metadata(MediainfoError=str(e))
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
                            "Destination": thumbnail_destination
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
                                            "FramerateDenominator": thumbnail_position,
                                            "MaxCaptures": 1,
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
                    "FileInput": file_input
                }]
            }
        )
    # TODO: Add support for boto client error handling
    except Exception as e:
        print("Exception:\n", e)
        operator_object.update_workflow_status("Error")
        operator_object.add_workflow_metadata(MediainfoError=str(e))
        raise MasExecutionError(operator_object.return_output_object())
    else:
        operator_object.update_workflow_status("Complete")
        return operator_object.return_output_object()
