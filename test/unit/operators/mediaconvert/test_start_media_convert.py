import pytest

def test_input_parameter():
    import mediaconvert.start_media_convert as lambda_function
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
    assert "Missing a required metadata key 'S3Bucket'" in err.value.args[0]['MetaData']['MediaconvertError']

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
    assert "Missing a required metadata key 'S3Key'" in err.value.args[0]['MetaData']['MediaconvertError']

def test_create_mediaconvert_job(mediaconvert_start_stub):
    import mediaconvert.start_media_convert as lambda_function
    import helper

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
                    "Destination": "s3://" + "testDataplaneBucket" + "/" + 'private/assets/' + "testAssetId" + "/workflows/" + "testWorkflowId" + "/"
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
                "FileInput": "s3://" + "test_bucket" + "/" + "test_key"
              }]
            }
        },
        service_response = {
            'Job': {
                'Id': 'testResultJobId',
                'Role': 'testMediaconvertRole',
                'Settings': {}
            }
        }
    )
    response = lambda_function.lambda_handler(operator_parameter, {})
    assert response['Status'] == 'Executing'
    assert response['MetaData']['MediaconvertJobId'] == 'testResultJobId'
    assert response['MetaData']['MediaconvertInputFile'] == 'test_key'
    assert response['MetaData']['AssetId'] == 'testAssetId'
    assert response['MetaData']['WorkflowExecutionId'] == 'testWorkflowId'