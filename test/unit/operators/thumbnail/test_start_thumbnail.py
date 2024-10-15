# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import pytest

def test_input_parameter():
    import thumbnail.start_thumbnail as lambda_function
    import MediaInsightsEngineLambdaHelper
    import helper
    
    # Empty workflow id
    operator_parameter = helper.get_operator_parameter()
    del operator_parameter['WorkflowExecutionId']
    
    with pytest.raises(KeyError) as err:
        lambda_function.lambda_handler(operator_parameter, {})
    assert err.value.args[0] == 'WorkflowExecutionId'

    # Empty S3Bucket
    operator_parameter = helper.get_operator_parameter(
        metadata={},
        input = {
            'Media': {
                'Video': {
                    'S3Bucket': 'test_bucket',
                    'S3Key': 'test_key'
                }
            }
        }
    )
    del operator_parameter['Input']['Media']['Video']['S3Bucket']
    
    with pytest.raises(MediaInsightsEngineLambdaHelper.MasExecutionError) as err:
        lambda_function.lambda_handler(operator_parameter, {})
    assert err.value.args[0]['Status'] == 'Error'
    assert "Missing a required metadata key 'S3Bucket'" in err.value.args[0]['MetaData']['ThumbnailError']

    # Empty S3Key
    operator_parameter = helper.get_operator_parameter(
        metadata={},
        input = {
            'Media': {
                'Video': {
                    'S3Bucket': 'test_bucket',
                    'S3Key': 'test_key'
                }
            }
        }
    )
    del operator_parameter['Input']['Media']['Video']['S3Key']
    
    with pytest.raises(MediaInsightsEngineLambdaHelper.MasExecutionError) as err:
        lambda_function.lambda_handler(operator_parameter, {})
    assert err.value.args[0]['Status'] == 'Error'
    assert "Missing a required metadata key 'S3Key'" in err.value.args[0]['MetaData']['ThumbnailError']

def test_create_job_error(mediaconvert_start_stub):
    import thumbnail.start_thumbnail as lambda_function
    import MediaInsightsEngineLambdaHelper
    import helper
    
    # Empty workflow id
    operator_parameter = helper.get_operator_parameter(
        metadata={},
        input = {
            'Media': {
                'Video': {
                    'S3Bucket': 'test_bucket',
                    'S3Key': 'test_key'
                }
            }
        }
    )

    mediaconvert_start_stub.add_client_error('create_job')
    
    with pytest.raises(MediaInsightsEngineLambdaHelper.MasExecutionError) as err:
        lambda_function.lambda_handler(operator_parameter, {})
    assert err.value.args[0]['Status'] == 'Error'
    assert err.value.args[0]['MetaData']['ThumbnailError'] == 'An error occurred () when calling the CreateJob operation: '

def test_create_job_success(mediaconvert_start_stub):
    import thumbnail.start_thumbnail as lambda_function
    import helper
    
    # Empty workflow id
    operator_parameter = helper.get_operator_parameter(
        metadata={},
        input = {
            'Media': {
                'Video': {
                    'S3Bucket': 'test_bucket',
                    'S3Key': 'test_key'
                }
            }
        }
    )

    mediaconvert_start_stub.add_response(
        'create_job',
        expected_params = {
            'Role': 'testMediaconvertRole',
            'Settings': {
                "OutputGroups": [
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
                                            "FramerateDenominator": 7,
                                            "MaxCaptures": 2,
                                            "Quality": 80
                                        }
                                    },
                                    "DropFrameTimecode": "ENABLED",
                                    "ColorMetadata": "INSERT"
                                },
                                "Extension": "jpg",
                                "NameModifier": "_thumbnail"
                            }
                        ],
                        "OutputGroupSettings": {
                            "Type": "FILE_GROUP_SETTINGS",
                            "FileGroupSettings": {
                                "Destination": "s3://testDataplaneBucket/private/assets/testAssetId/"
                            }
                        }
                    },
                    {
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
                                "Destination": "s3://testDataplaneBucket/private/assets/testAssetId/workflows/testWorkflowId/"
                            }
                        }
                    },
                    {
                        "CustomName": "proxy",
                        "Name": "File Group",
                        "Outputs": [
                            {
                                "VideoDescription": {
                                    "ScalingBehavior": "DEFAULT",
                                    "TimecodeInsertion": "DISABLED",
                                    "AntiAlias": "ENABLED",
                                    "Sharpness": 50,
                                    "CodecSettings": {
                                        "Codec": "H_264",
                                        "H264Settings": {
                                            "InterlaceMode": "PROGRESSIVE",
                                            "NumberReferenceFrames": 3,
                                            "Syntax": "DEFAULT",
                                            "Softness": 0,
                                            "GopClosedCadence": 1,
                                            "GopSize": 90,
                                            "Slices": 1,
                                            "GopBReference": "DISABLED",
                                            "SlowPal": "DISABLED",
                                            "SpatialAdaptiveQuantization": "ENABLED",
                                            "TemporalAdaptiveQuantization": "ENABLED",
                                            "FlickerAdaptiveQuantization": "DISABLED",
                                            "EntropyEncoding": "CABAC",
                                            "Bitrate": 1600000,
                                            "FramerateControl": "SPECIFIED",
                                            "RateControlMode": "CBR",
                                            "CodecProfile": "MAIN",
                                            "Telecine": "NONE",
                                            "MinIInterval": 0,
                                            "AdaptiveQuantization": "HIGH",
                                            "CodecLevel": "AUTO",
                                            "FieldEncoding": "PAFF",
                                            "SceneChangeDetect": "ENABLED",
                                            "QualityTuningLevel": "SINGLE_PASS",
                                            "FramerateConversionAlgorithm": "DUPLICATE_DROP",
                                            "UnregisteredSeiTimecode": "DISABLED",
                                            "GopSizeUnits": "FRAMES",
                                            "ParControl": "SPECIFIED",
                                            "NumberBFramesBetweenReferenceFrames": 2,
                                            "RepeatPps": "DISABLED",
                                            "FramerateNumerator": 30,
                                            "FramerateDenominator": 1,
                                            "ParNumerator": 1,
                                            "ParDenominator": 1
                                        }
                                    },
                                    "AfdSignaling": "NONE",
                                    "DropFrameTimecode": "ENABLED",
                                    "RespondToAfd": "NONE",
                                    "ColorMetadata": "INSERT"
                                },
                                "AudioDescriptions": [
                                    {
                                        "AudioTypeControl": "FOLLOW_INPUT",
                                        "CodecSettings": {
                                            "Codec": "AAC",
                                            "AacSettings": {
                                                "AudioDescriptionBroadcasterMix": "NORMAL",
                                                "RateControlMode": "CBR",
                                                "CodecProfile": "LC",
                                                "CodingMode": "CODING_MODE_2_0",
                                                "RawFormat": "NONE",
                                                "SampleRate": 48000,
                                                "Specification": "MPEG4",
                                                "Bitrate": 64000
                                            }
                                        },
                                        "LanguageCodeControl": "FOLLOW_INPUT",
                                        "AudioSourceName": "Audio Selector 1"
                                    }
                                ],
                                "ContainerSettings": {
                                    "Container": "MP4",
                                    "Mp4Settings": {
                                        "CslgAtom": "INCLUDE",
                                        "FreeSpaceBox": "EXCLUDE",
                                        "MoovPlacement": "PROGRESSIVE_DOWNLOAD"
                                    }
                                },
                                "Extension": "mp4",
                                "NameModifier": "_proxy"
                            }
                        ],
                        "OutputGroupSettings": {
                            "Type": "FILE_GROUP_SETTINGS",
                            "FileGroupSettings": {
                                "Destination": "s3://testDataplaneBucket/private/assets/testAssetId/"
                            }
                        }
                    }
                    ],
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
                    "FileInput": "s3://test_bucket/test_key"
                }]
            }
        },
        service_response = {
            'Job': {
                'Id': 'testJobId',
                'Role': 'testMediaconvertRole',
                'Settings': {}
            }
        }
    )
    
    response = lambda_function.lambda_handler(operator_parameter, {})
    assert response['Status'] == 'Executing'
    assert response['MetaData']['MediaconvertJobId'] == 'testJobId'
    assert response['MetaData']['MediaconvertInputFile'] == 's3://test_bucket/test_key'
    assert response['MetaData']['AssetId'] == 'testAssetId'
    assert response['MetaData']['WorkflowExecutionId'] == 'testWorkflowId'
    