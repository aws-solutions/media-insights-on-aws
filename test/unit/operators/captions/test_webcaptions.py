import pytest, json
from unittest.mock import MagicMock
from botocore.response import StreamingBody
from io import BytesIO

def mock_dataplane(lambda_function, mock_retrieve_response = {}, mock_store_response = {}, mock_generate_response = {}):
    retrieve_function = lambda_function.dataplane.retrieve_asset_metadata
    lambda_function.dataplane.retrieve_asset_metadata = MagicMock(return_value = mock_retrieve_response)

    store_function = lambda_function.dataplane.store_asset_metadata
    lambda_function.dataplane.store_asset_metadata = MagicMock(return_value = mock_store_response)

    generate_function = lambda_function.dataplane.generate_media_storage_path
    lambda_function.dataplane.generate_media_storage_path = MagicMock(return_value = mock_generate_response)

    return {
        'retrieve': retrieve_function,
        'store': store_function,
        'generate': generate_function
    }

def restore_mock(lambda_function, original_dataplane_functions):
    lambda_function.dataplane.retrieve_asset_metadata = original_dataplane_functions['retrieve']
    lambda_function.dataplane.store_asset_metadata = original_dataplane_functions['store']
    lambda_function.dataplane.generate_media_storage_path = original_dataplane_functions['generate']

def test_web_captions_empty_transcript():
    import captions.webcaptions as lambda_function
    import helper

    original_functions = mock_dataplane(
        lambda_function,
        {
            'results': {
                'results': {
                    'items': [{
                        'type': 'punctuation',
                    }, {
                        'type': 'not_punctuation',
                        'start_time': '2.0',
                        'end_time': '3.0',
                        'alternatives': [{
                            'content': 'transcribed text',
                            'confidence': '1.0'
                        }]
                    }]
                }
            }
        },
        {
            'Status': 'Success'
        }
    )

    input_parameter = helper.get_operator_parameter(
        input={
            'MetaData': {
                'TranscribeSourceLanguage': 'en'
            }
        }
    )

    response = lambda_function.web_captions(input_parameter, {})
    assert response['Status'] == 'Complete'
    assert lambda_function.dataplane.retrieve_asset_metadata.call_count == 1
    assert lambda_function.dataplane.retrieve_asset_metadata.call_args[0][0] == 'testAssetId'
    assert lambda_function.dataplane.retrieve_asset_metadata.call_args[1]['operator_name'] == 'TranscribeVideo'
    assert lambda_function.dataplane.store_asset_metadata.call_count == 2
    assert lambda_function.dataplane.store_asset_metadata.call_args[1]['asset_id'] == 'testAssetId'
    assert lambda_function.dataplane.store_asset_metadata.call_args[1]['operator_name'] == 'WebCaptions_en'
    assert lambda_function.dataplane.store_asset_metadata.call_args[1]['workflow_id'] == 'testWorkflowId'
    assert lambda_function.dataplane.store_asset_metadata.call_args[1]['results'] == {'WebCaptions': [{'start': 2.0, 'caption': 'transcribed text', 'wordConfidence': [{'w': 'transcribed text', 'c': 1.0}], 'end': 3.0}]}
    assert lambda_function.dataplane.store_asset_metadata.call_args[1]['paginate'] == False
    restore_mock(lambda_function, original_functions)

def test_create_srt_empty_target_language():
    import captions.webcaptions as lambda_function
    from MediaInsightsEngineLambdaHelper import MasExecutionError
    import helper

    input_parameter = helper.get_operator_parameter(
        input={
            'MetaData': {
                'TranscribeSourceLanguage': 'en'
            }
        }
    )
    del input_parameter['Configuration']['TargetLanguageCodes']
    
    with pytest.raises(MasExecutionError) as err:
        lambda_function.create_srt(input_parameter, {})

    assert err.value.args[0]['Status'] == 'Error'
    assert err.value.args[0]['MetaData']['WebCaptionsError'] == "Missing a required metadata key 'TargetLanguageCodes'"

def test_create_srt(s3_resource_stub):
    import captions.webcaptions as lambda_function
    from MediaInsightsEngineLambdaHelper import MasExecutionError
    import helper

    dataplane_functions = mock_dataplane(
        lambda_function=lambda_function,
        mock_retrieve_response={
            'results': {
                'WebCaptions': [{
                    'start': 2.0,
                    'end': 3.0,
                    'caption': 'transcribed text',
                    'wordConfidence': [{
                        'w': 'transcribed text',
                        'c': 1.0
                    }]
                }]
            }
        },
        mock_generate_response={
            'S3Bucket': 'test_bucket',
            'S3Key': 'test_key'
        },
        mock_store_response={
            'Status': 'Success'
        }
    )

    s3_resource_stub.add_response(
        'put_object',
        expected_params = {
            'Bucket': 'test_bucket',
            'Key': 'test_keyCaptions_en.srt',
            'Body': '1\n00:00:02,000 --> 00:00:03,000\ntranscribed text\n\n'
        },
        service_response = {}
    )

    input_parameter = helper.get_operator_parameter(
        input={
            'MetaData': {
                'TranscribeSourceLanguage': 'en'
            }
        }
    )
    
    response = lambda_function.create_srt(input_parameter, {})
    assert response['Status'] == 'Complete'
    assert lambda_function.dataplane.retrieve_asset_metadata.call_count == 1
    assert lambda_function.dataplane.retrieve_asset_metadata.call_args[0][0] == 'testAssetId'
    assert lambda_function.dataplane.retrieve_asset_metadata.call_args[1]['operator_name'] == 'WebCaptions_en'
    assert lambda_function.dataplane.store_asset_metadata.call_count == 1
    assert lambda_function.dataplane.store_asset_metadata.call_args[0][0] == 'testAssetId'
    assert lambda_function.dataplane.store_asset_metadata.call_args[0][1] == 'testName'
    assert lambda_function.dataplane.store_asset_metadata.call_args[0][2] == 'testWorkflowId'
    assert lambda_function.dataplane.store_asset_metadata.call_args[0][3] == {
        'CaptionsCollection': [{
            'OperatorName': 'Captions_en',
            'Results': {
                'S3Bucket': 'test_bucket',
                'S3Key': 'test_keyCaptions_en.srt'
            },
            'WorkflowId': 'testWorkflowId',
            'LanguageCode': 'en'
        }]
    }
    assert lambda_function.dataplane.generate_media_storage_path.call_count == 1
    assert lambda_function.dataplane.generate_media_storage_path.call_args[0][0] == 'testAssetId'
    assert lambda_function.dataplane.generate_media_storage_path.call_args[0][1] == 'testWorkflowId'
    restore_mock(lambda_function, dataplane_functions)

def test_create_vtt_empty_target_language():
    import captions.webcaptions as lambda_function
    from MediaInsightsEngineLambdaHelper import MasExecutionError
    import helper

    input_parameter = helper.get_operator_parameter(
        input={
            'MetaData': {
                'TranscribeSourceLanguage': 'en'
            }
        }
    )
    del input_parameter['Configuration']['TargetLanguageCodes']
    
    with pytest.raises(MasExecutionError) as err:
        lambda_function.create_vtt(input_parameter, {})

    assert err.value.args[0]['Status'] == 'Error'
    assert err.value.args[0]['MetaData']['WebCaptionsError'] == "Missing a required metadata key 'TargetLanguageCodes'"

def test_create_vtt(s3_resource_stub):
    import captions.webcaptions as lambda_function
    import helper

    dataplane_functions = mock_dataplane(
        lambda_function=lambda_function,
        mock_retrieve_response={
            'results': {
                'WebCaptions': [{
                    'start': 2.0,
                    'end': 3.0,
                    'caption': 'transcribed text',
                    'wordConfidence': [{
                        'w': 'transcribed text',
                        'c': 1.0
                    }]
                }]
            }
        },
        mock_generate_response={
            'S3Bucket': 'test_bucket',
            'S3Key': 'test_key'
        },
        mock_store_response={
            'Status': 'Success'
        }
    )

    s3_resource_stub.add_response(
        'put_object',
        expected_params = {
            'Bucket': 'test_bucket',
            'Key': 'test_keyCaptions_en.vtt',
            'Body': 'WEBVTT\n\n00:00:02.000 --> 00:00:03.000\ntranscribed text\n\n'
        },
        service_response = {}
    )

    input_parameter = helper.get_operator_parameter(
        input={
            'MetaData': {
                'TranscribeSourceLanguage': 'en'
            }
        }
    )
    
    response = lambda_function.create_vtt(input_parameter, {})
    assert response['Status'] == 'Complete'
    assert lambda_function.dataplane.retrieve_asset_metadata.call_count == 1
    assert lambda_function.dataplane.retrieve_asset_metadata.call_args[0][0] == 'testAssetId'
    assert lambda_function.dataplane.retrieve_asset_metadata.call_args[1]['operator_name'] == 'WebCaptions_en'
    assert lambda_function.dataplane.store_asset_metadata.call_count == 1
    assert lambda_function.dataplane.store_asset_metadata.call_args[0][0] == 'testAssetId'
    assert lambda_function.dataplane.store_asset_metadata.call_args[0][1] == 'testName'
    assert lambda_function.dataplane.store_asset_metadata.call_args[0][2] == 'testWorkflowId'
    assert lambda_function.dataplane.store_asset_metadata.call_args[0][3] == {
        'CaptionsCollection': [{
            'OperatorName': 'Captions_en',
            'Results': {
                'S3Bucket': 'test_bucket',
                'S3Key': 'test_keyCaptions_en.vtt'
            },
            'WorkflowId': 'testWorkflowId',
            'LanguageCode': 'en'
        }]
    }
    assert lambda_function.dataplane.generate_media_storage_path.call_count == 1
    assert lambda_function.dataplane.generate_media_storage_path.call_args[0][0] == 'testAssetId'
    assert lambda_function.dataplane.generate_media_storage_path.call_args[0][1] == 'testWorkflowId'
    restore_mock(lambda_function, dataplane_functions)

def test_start_translate_webcaptions(s3_client_stub, translate_client_stub):
    import captions.webcaptions as lambda_function
    import helper

    dataplane_functions = mock_dataplane(
        lambda_function=lambda_function,
        mock_retrieve_response={
            'results': {
                'WebCaptions': [{
                    'start': 2.0,
                    'end': 3.0,
                    'caption': 'transcribed text',
                    'wordConfidence': [{
                        'w': 'transcribed text',
                        'c': 1.0
                    }]
                }]
            }
        },
        mock_generate_response={
            'S3Bucket': 'test_bucket',
            'S3Key': 'test_key'
        },
        mock_store_response={
            'Status': 'Success'
        }
    )

    s3_client_stub.add_response(
        'put_object',
        expected_params = {
            'Bucket': 'test_bucket',
            'Key': 'test_keywebcaptions_translate_input/transcript_with_caption_markers.txt',
            'Body': 'transcribed text'
        },
        service_response = {}
    )

    s3_client_stub.add_response(
        'put_object',
        expected_params = {
            'Bucket': 'test_bucket',
            'Key': 'test_keywebcaptions_translate_output//foo',
            'Body': 'foo'
        },
        service_response = {}
    )
    
    translate_client_stub.add_response(
        'start_text_translation_job',
        expected_params = json.loads('''{
            "JobName": "MIE_testAssetId_testWorkflowId_en",
            "InputDataConfig": {
                "S3Uri": "s3://test_bucket/test_keywebcaptions_translate_input/",
                "ContentType": "text/html"
            },
            "OutputDataConfig": {
                "S3Uri": "s3://test_bucket/test_keywebcaptions_translate_output/"
            },
            "DataAccessRoleArn": "testTranslateRole007",
            "SourceLanguageCode": "es",
            "TargetLanguageCodes": ["en"],
            "TerminologyNames": ["testTerminologyName"],
            "ParallelDataNames": ["testParallelName"]
        }'''),
        service_response = {
            'JobId': 'testJobId'
        }
    )

    input_parameter = helper.get_operator_parameter(
        metadata={},
        input={
            'MetaData': {
                'TranscribeSourceLanguage': 'es'
            }
        }
    )
    
    response = lambda_function.start_translate_webcaptions(input_parameter, {})

    assert response['Status'] == 'testStatus'
    assert response['MetaData']['TextTranslateJobPropertiesList'] == [{'JobId': 'testJobId', 'TargetLanguageCode': 'en'}]
    assert response['MetaData']['TranslateSourceLanguage'] == 'es'
    assert lambda_function.dataplane.generate_media_storage_path.call_count == 1
    assert lambda_function.dataplane.generate_media_storage_path.call_args[0][0] == 'testAssetId'
    assert lambda_function.dataplane.generate_media_storage_path.call_args[0][1] == 'testWorkflowId'
    assert lambda_function.dataplane.store_asset_metadata.call_count == 0
    assert lambda_function.dataplane.retrieve_asset_metadata.call_count == 1
    assert lambda_function.dataplane.retrieve_asset_metadata.call_args[0][0] == 'testAssetId'
    assert lambda_function.dataplane.retrieve_asset_metadata.call_args[1]['operator_name'] == 'WebCaptions_es'
    restore_mock(lambda_function, dataplane_functions)

def test_check_translate_webcaptions_same_source_and_target():
    import captions.webcaptions as lambda_function
    import helper

    input_parameter = helper.get_operator_parameter(
        metadata={},
        input={
            'MetaData': {
                'TranscribeSourceLanguage': 'en'
            }
        }
    )
    
    response = lambda_function.check_translate_webcaptions(input_parameter, {})
    assert response['Status'] == 'Complete'

def test_check_translate_webcaptions(translate_client_stub, s3_resource_stub):
    import captions.webcaptions as lambda_function
    import helper

    dataplane_functions = mock_dataplane(
        lambda_function=lambda_function,
        mock_retrieve_response={
            'results': {
                'WebCaptions': [{
                    'start': 2.0,
                    'end': 3.0,
                    'caption': 'transcribed text',
                    'wordConfidence': [{
                        'w': 'transcribed text',
                        'c': 1.0
                    }]
                }]
            }
        },
        mock_generate_response={
            'S3Bucket': 'test_bucket',
            'S3Key': 'test_key'
        },
        mock_store_response={
            'Status': 'Success'
        }
    )

    translate_client_stub.add_response(
        'describe_text_translation_job',
        expected_params = {
            'JobId': 'testJobId'
        },
        service_response = {
            'TextTranslationJobProperties': {
                'JobStatus': 'COMPLETED'
            }
        }
    )

    translate_client_stub.add_response(
        'describe_text_translation_job',
        expected_params = {
            'JobId': 'testJobId'
        },
        service_response = {
            'TextTranslationJobProperties': {
                'OutputDataConfig': {
                    'S3Uri': 's3://test_bucket/test_key'
                },
                'TargetLanguageCodes': ['en'],
                'SourceLanguageCode': 'es'
            }
        }
    )

    s3_resource_stub.add_response(
        'list_objects',
        expected_params = {
            'Bucket': 'test_bucket',
            'Prefix': 'test_key/',
            'Delimiter': '/'
        },
        service_response = {
            'Contents': [
                { 'Key': 'en.test_key1.srt' }
            ]
        }
    )

    s3_resource_stub.add_response(
        'get_object',
        expected_params = {
            'Bucket': 'test_bucket',
            'Key': 'en.test_key1.srt',
        },
        service_response = {
            'Body': StreamingBody(
                BytesIO('testTranslationOutput'.encode('utf-8')),
                len('testTranslationOutput')
            )
        }
    )

    s3_resource_stub.add_response(
        'put_object',
        expected_params = {
            'Body': 'testTranslationOutput',
            'Bucket': 'test_bucket',
            'Key': 'test_keytranslation_en.txt'
        },
        service_response = {}
    )

    input_parameter = helper.get_operator_parameter(
        metadata={
            'TextTranslateJobPropertiesList': [{'JobId': 'testJobId', 'TargetLanguageCode': 'en'}]
        },
        input={
            'MetaData': {
                'TranscribeSourceLanguage': 'es'
            }
        }
    )
    
    response = lambda_function.check_translate_webcaptions(input_parameter, {})
    assert response['Status'] == 'Complete'
    assert response['MetaData']['AssetId'] == 'testAssetId'
    assert response['MetaData']['WorkflowExecutionId'] == 'testWorkflowId'
    assert lambda_function.dataplane.generate_media_storage_path.call_count == 2
    assert lambda_function.dataplane.generate_media_storage_path.call_args[0][0] == 'testAssetId'
    assert lambda_function.dataplane.generate_media_storage_path.call_args[0][1] == 'testWorkflowId'
    assert lambda_function.dataplane.retrieve_asset_metadata.call_count == 1
    assert lambda_function.dataplane.retrieve_asset_metadata.call_args[0][0] == 'testAssetId'
    assert lambda_function.dataplane.retrieve_asset_metadata.call_args[1]['operator_name'] == 'WebCaptions_es'
    assert lambda_function.dataplane.store_asset_metadata.call_count == 3
    assert lambda_function.dataplane.store_asset_metadata.call_args[0][0] == 'testAssetId'
    assert lambda_function.dataplane.store_asset_metadata.call_args[0][1] == 'testName'
    assert lambda_function.dataplane.store_asset_metadata.call_args[0][2] == 'testWorkflowId'
    assert lambda_function.dataplane.store_asset_metadata.call_args[0][3] == {
        'CaptionsCollection': [{
            'OperatorName': 'TranslateWebCaptions_en',
            'TranslationText': {'S3Bucket': 'test_bucket', 'S3Key': 'test_keytranslation_en.txt'},
            'WorkflowId': 'testWorkflowId',
            'TargetLanguageCode': 'en'
        }]
    }
    restore_mock(lambda_function, dataplane_functions)

def test_start_polly_webcaptions(polly_client_stub):
    import captions.webcaptions as lambda_function
    import helper

    dataplane_functions = mock_dataplane(
        lambda_function=lambda_function,
        mock_retrieve_response={
            'results': {
                'CaptionsCollection': [{
                    'TargetLanguageCode': 'en',
                    'TranslationText': {
                        'S3Bucket': 'test_bucket'
                    }
                }],
                'WebCaptions': [{
                    'start': 2.0,
                    'end': 3.0,
                    'caption': 'transcribed text',
                    'wordConfidence': [{
                        'w': 'transcribed text',
                        'c': 1.0
                    }]
                }]
            }
        },
        mock_generate_response={
            'S3Bucket': 'test_bucket',
            'S3Key': 'test_key'
        },
        mock_store_response={
            'Status': 'Success'
        }
    )

    polly_client_stub.add_response(
        'describe_voices',
        expected_params = {
            'LanguageCode': 'en-GB'
        },
        service_response = {
            'Voices': [{
                'Id': 'testVoiceId'
            }]
        }
    )

    polly_client_stub.add_response(
        'start_speech_synthesis_task',
        expected_params = {
            'OutputFormat': 'mp3',
            'OutputS3BucketName': 'test_bucket',
            'OutputS3KeyPrefix': 'private/assets/testAssetId/workflows/testWorkflowId/audio_only_en',
            'Text': 'transcribed text',
            'TextType': 'text',
            'VoiceId': 'testVoiceId'
        },
        service_response = {
            'SynthesisTask': {
                'TaskId': 'testTaskId'
            }
        }
    )

    input_parameter = helper.get_operator_parameter(
        metadata={
            'TextTranslateJobPropertiesList': [{'JobId': 'testJobId', 'TargetLanguageCode': 'en'}]
        },
        input={
            'MetaData': {
                'TranscribeSourceLanguage': 'es'
            }
        }
    )
    
    response = lambda_function.start_polly_webcaptions(input_parameter, {})
    assert response['Status'] == 'Executing'
    assert response['MetaData']['PollyCollection'][0]['TargetLanguageCode'] == 'en'
    assert response['MetaData']['PollyCollection'][0]['TranslationText'] == {'S3Bucket': 'test_bucket'}
    assert response['MetaData']['PollyCollection'][0]['VoiceId'] == 'testVoiceId'
    assert response['MetaData']['PollyCollection'][0]['PollyAudio'] == {
        'S3Key': 'private/assets/testAssetId/workflows/testWorkflowId/audio_only_en.testTaskId.mp3',
        'S3Bucket': 'test_bucket'
    }
    assert response['MetaData']['PollyCollection'][0]['PollyTaskId'] == 'testTaskId'
    assert response['MetaData']['PollyCollection'][0]['PollyStatus'] == 'started'
    assert lambda_function.dataplane.generate_media_storage_path.call_count == 0
    assert lambda_function.dataplane.store_asset_metadata.call_count == 0
    assert lambda_function.dataplane.retrieve_asset_metadata.call_count == 2
    assert lambda_function.dataplane.retrieve_asset_metadata.call_args[0][0] == 'testAssetId'
    assert lambda_function.dataplane.retrieve_asset_metadata.call_args[1]['operator_name'] == 'WebCaptions_en'
    restore_mock(lambda_function, dataplane_functions)

def test_check_polly_webcaptions_all_tasks_finished():
    import captions.webcaptions as lambda_function
    import helper

    dataplane_functions = mock_dataplane(
        lambda_function=lambda_function,
        mock_store_response={
            'Status': 'Success'
        }
    )

    input_parameter = helper.get_operator_parameter(
        metadata={
            'PollyCollection': [{
                'TargetLAnguageCode': 'en',
                'TranslationText': {'S3Bucket': 'test_bucket'},
                'VoiceId': 'testVoiceId',
                'PollyTaskId': 'testTaskId',
                'PollyStatus': 'completed',
                'PollyAudio': {
                    'S3Key': 'private/assets/testAssetId/workflows/testWorkflowId/audio_only_en.testTaskId.mp3',
                    'S3Bucket': 'test_bucket'
                }
            }]
        },
        input = {
            'MetaData': {
                'TranscribeSourceLanguage': 'es'
            }
        }
    )
    
    response = lambda_function.check_polly_webcaptions(input_parameter, {})
    assert response['Status'] == 'Complete'
    assert lambda_function.dataplane.retrieve_asset_metadata.call_count == 0
    assert lambda_function.dataplane.generate_media_storage_path.call_count == 0
    assert lambda_function.dataplane.store_asset_metadata.call_count == 1
    assert lambda_function.dataplane.store_asset_metadata.call_args[0][0] == 'testAssetId'
    assert lambda_function.dataplane.store_asset_metadata.call_args[0][1] == 'testName'
    assert lambda_function.dataplane.store_asset_metadata.call_args[0][2] == 'testWorkflowId'
    restore_mock(lambda_function, dataplane_functions)

def test_check_polly_webcaptions_empty_collection():
    import captions.webcaptions as lambda_function
    from MediaInsightsEngineLambdaHelper import MasExecutionError
    import helper

    dataplane_functions = mock_dataplane(
        lambda_function=lambda_function
    )

    input_parameter = helper.get_operator_parameter(
        metadata={},
        input = {
            'MetaData': {
                'TranscribeSourceLanguage': 'es'
            }
        }
    )
    with pytest.raises(MasExecutionError) as err:
        lambda_function.check_polly_webcaptions(input_parameter, {})
    assert err.value.args[0]['Status'] == 'Error'
    assert err.value.args[0]['MetaData']['PollyCollectionError'] == "Missing a required metadata key 'PollyCollection'"
    assert lambda_function.dataplane.retrieve_asset_metadata.call_count == 0
    assert lambda_function.dataplane.generate_media_storage_path.call_count == 0
    assert lambda_function.dataplane.store_asset_metadata.call_count == 0
    restore_mock(lambda_function, dataplane_functions)

def test_check_polly_webcaptions_error_handle(polly_client_stub):
    import captions.webcaptions as lambda_function
    from MediaInsightsEngineLambdaHelper import MasExecutionError
    import helper

    dataplane_functions = mock_dataplane(
        lambda_function=lambda_function,
        mock_store_response={
            'Status': 'Success'
        }
    )

    polly_client_stub.add_client_error('get_speech_synthesis_task')

    input_parameter = helper.get_operator_parameter(
        metadata={
            'PollyCollection': [{
                'TargetLAnguageCode': 'en',
                'TranslationText': {'S3Bucket': 'test_bucket'},
                'VoiceId': 'testVoiceId',
                'PollyTaskId': 'testTaskId',
                'PollyStatus': 'started',
                'PollyAudio': {
                    'S3Key': 'private/assets/testAssetId/workflows/testWorkflowId/audio_only_en.testTaskId.mp3',
                    'S3Bucket': 'test_bucket'
                }
            }]
        },
        input = {
            'MetaData': {
                'TranscribeSourceLanguage': 'es'
            }
        }
    )
    with pytest.raises(MasExecutionError) as err:
        lambda_function.check_polly_webcaptions(input_parameter, {})
    assert err.value.args[0]['Status'] == 'Error'
    assert err.value.args[0]['MetaData']['PollyCollectionError'] == 'Unable to get response from polly: An error occurred () when calling the GetSpeechSynthesisTask operation: '
    assert lambda_function.dataplane.retrieve_asset_metadata.call_count == 0
    assert lambda_function.dataplane.generate_media_storage_path.call_count == 0
    assert lambda_function.dataplane.store_asset_metadata.call_count == 0
    restore_mock(lambda_function, dataplane_functions)

def test_check_polly_webcaptions_failed(polly_client_stub):
    import captions.webcaptions as lambda_function
    from MediaInsightsEngineLambdaHelper import MasExecutionError
    import helper

    dataplane_functions = mock_dataplane(
        lambda_function=lambda_function,
        mock_store_response={
            'Status': 'Success'
        }
    )

    polly_client_stub.add_response(
        'get_speech_synthesis_task',
        expected_params = {
            'TaskId': 'testTaskId'
        },
        service_response = {
            'SynthesisTask': {
                'TaskStatus': 'failed',
                'TaskStatusReason': 'testFailedReason'
            }
        }
    )

    input_parameter = helper.get_operator_parameter(
        metadata={
            'PollyCollection': [{
                'TargetLAnguageCode': 'en',
                'TranslationText': {'S3Bucket': 'test_bucket'},
                'VoiceId': 'testVoiceId',
                'PollyTaskId': 'testTaskId',
                'PollyStatus': 'started',
                'PollyAudio': {
                    'S3Key': 'private/assets/testAssetId/workflows/testWorkflowId/audio_only_en.testTaskId.mp3',
                    'S3Bucket': 'test_bucket'
                }
            }]
        },
        input = {
            'MetaData': {
                'TranscribeSourceLanguage': 'es'
            }
        }
    )
    with pytest.raises(MasExecutionError) as err:
        lambda_function.check_polly_webcaptions(input_parameter, {})
    assert err.value.args[0]['Status'] == 'Error'
    assert err.value.args[0]['MetaData']['PollyCollectionError'] == 'Polly returned as failed: testFailedReason'
    assert lambda_function.dataplane.retrieve_asset_metadata.call_count == 0
    assert lambda_function.dataplane.generate_media_storage_path.call_count == 0
    assert lambda_function.dataplane.store_asset_metadata.call_count == 0
    restore_mock(lambda_function, dataplane_functions)

def test_check_polly_webcaptions_unknown_status(polly_client_stub):
    import captions.webcaptions as lambda_function
    from MediaInsightsEngineLambdaHelper import MasExecutionError
    import helper

    dataplane_functions = mock_dataplane(
        lambda_function=lambda_function,
        mock_store_response={
            'Status': 'Success'
        }
    )

    polly_client_stub.add_response(
        'get_speech_synthesis_task',
        expected_params = {
            'TaskId': 'testTaskId'
        },
        service_response = {
            'SynthesisTask': {
                'TaskStatus': 'unknown_status',
                'TaskStatusReason': 'testFailedReason'
            }
        }
    )

    input_parameter = helper.get_operator_parameter(
        metadata={
            'PollyCollection': [{
                'TargetLAnguageCode': 'en',
                'TranslationText': {'S3Bucket': 'test_bucket'},
                'VoiceId': 'testVoiceId',
                'PollyTaskId': 'testTaskId',
                'PollyStatus': 'started',
                'PollyAudio': {
                    'S3Key': 'private/assets/testAssetId/workflows/testWorkflowId/audio_only_en.testTaskId.mp3',
                    'S3Bucket': 'test_bucket'
                }
            }]
        },
        input = {
            'MetaData': {
                'TranscribeSourceLanguage': 'es'
            }
        }
    )
    with pytest.raises(MasExecutionError) as err:
        lambda_function.check_polly_webcaptions(input_parameter, {})
    assert err.value.args[0]['Status'] == 'Error'
    assert err.value.args[0]['MetaData']['PollyCollectionError'] == 'Polly returned as failed: testFailedReason'
    assert lambda_function.dataplane.retrieve_asset_metadata.call_count == 0
    assert lambda_function.dataplane.generate_media_storage_path.call_count == 0
    assert lambda_function.dataplane.store_asset_metadata.call_count == 0
    restore_mock(lambda_function, dataplane_functions)

def test_check_polly_webcaptions_failed(polly_client_stub):
    import captions.webcaptions as lambda_function
    from MediaInsightsEngineLambdaHelper import MasExecutionError
    import helper

    dataplane_functions = mock_dataplane(
        lambda_function=lambda_function,
        mock_store_response={
            'Status': 'Success'
        }
    )

    polly_client_stub.add_response(
        'get_speech_synthesis_task',
        expected_params = {
            'TaskId': 'testTaskId'
        },
        service_response = {
            'SynthesisTask': {
                'TaskStatus': 'failed',
                'TaskStatusReason': 'testFailedReason'
            }
        }
    )

    input_parameter = helper.get_operator_parameter(
        metadata={
            'PollyCollection': [{
                'TargetLAnguageCode': 'en',
                'TranslationText': {'S3Bucket': 'test_bucket'},
                'VoiceId': 'testVoiceId',
                'PollyTaskId': 'testTaskId',
                'PollyStatus': 'started',
                'PollyAudio': {
                    'S3Key': 'private/assets/testAssetId/workflows/testWorkflowId/audio_only_en.testTaskId.mp3',
                    'S3Bucket': 'test_bucket'
                }
            }]
        },
        input = {
            'MetaData': {
                'TranscribeSourceLanguage': 'es'
            }
        }
    )
    with pytest.raises(MasExecutionError) as err:
        lambda_function.check_polly_webcaptions(input_parameter, {})
    assert err.value.args[0]['Status'] == 'Error'
    assert err.value.args[0]['MetaData']['PollyCollectionError'] == 'Polly returned as failed: testFailedReason'
    assert lambda_function.dataplane.retrieve_asset_metadata.call_count == 0
    assert lambda_function.dataplane.generate_media_storage_path.call_count == 0
    assert lambda_function.dataplane.store_asset_metadata.call_count == 0
    restore_mock(lambda_function, dataplane_functions)

def test_check_polly_webcaptions(polly_client_stub):
    import captions.webcaptions as lambda_function
    import helper

    dataplane_functions = mock_dataplane(
        lambda_function=lambda_function,
        mock_store_response={
            'Status': 'Success'
        }
    )

    polly_client_stub.add_response(
        'get_speech_synthesis_task',
        expected_params = {
            'TaskId': 'testTaskId'
        },
        service_response = {
            'SynthesisTask': {
                'TaskStatus': 'completed',
                'OutputUri': 'testOutputUri'
            }
        }
    )

    input_parameter = helper.get_operator_parameter(
        metadata={
            'PollyCollection': [{
                'TargetLAnguageCode': 'en',
                'TranslationText': {'S3Bucket': 'test_bucket'},
                'VoiceId': 'testVoiceId',
                'PollyTaskId': 'testTaskId',
                'PollyStatus': 'started',
                'PollyAudio': {
                    'S3Key': 'private/assets/testAssetId/workflows/testWorkflowId/audio_only_en.testTaskId.mp3',
                    'S3Bucket': 'test_bucket'
                }
            }]
        },
        input = {
            'MetaData': {
                'TranscribeSourceLanguage': 'es'
            }
        }
    )
    
    response = lambda_function.check_polly_webcaptions(input_parameter, {})
    assert response['Status'] == 'Complete'
    assert lambda_function.dataplane.retrieve_asset_metadata.call_count == 0
    assert lambda_function.dataplane.generate_media_storage_path.call_count == 0
    assert lambda_function.dataplane.store_asset_metadata.call_count == 1
    assert lambda_function.dataplane.store_asset_metadata.call_args[0][0] == 'testAssetId'
    assert lambda_function.dataplane.store_asset_metadata.call_args[0][1] == 'testName'
    assert lambda_function.dataplane.store_asset_metadata.call_args[0][2] == 'testWorkflowId'
    restore_mock(lambda_function, dataplane_functions)

def test_vttToWebCaptions(s3_client_stub):
    import captions.webcaptions as lambda_function
    import helper

    s3_client_stub.add_response(
        'get_object',
        expected_params = {
            'Bucket': 'test_bucket',
            'Key': 'test_key'
        },
        service_response = {
            'Body': StreamingBody(
                BytesIO('WEBVTT\n\n00:00:02.000 --> 00:00:03.000\ntranscribed text\n\n'.encode('utf-8')),
                len('WEBVTT\n\n00:00:02.000 --> 00:00:03.000\ntranscribed text\n\n')
            )
        }
    )

    input_parameter = helper.get_operator_parameter(
        metadata={},
        input = {
            'MetaData': {
                'TranscribeSourceLanguage': 'es'
            }
        }
    )
    
    response = lambda_function.vttToWebCaptions(
        input_parameter,
        {
            'Bucket': 'test_bucket',
            'Key': 'test_key'
        }
    )
    assert response is not None
    assert len(response) == 1
    assert response[0]['start'] == '2.0'
    assert response[0]['end'] == '3.0'
    assert response[0]['caption'] == 'transcribed text'
