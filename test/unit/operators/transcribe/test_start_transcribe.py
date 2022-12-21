import pytest

def test_parameter_validation():
    import transcribe.start_transcribe as lambda_function
    import MediaInsightsEngineLambdaHelper
    import helper

    input_parameter = {
        'Media': {
            'ProxyEncode': {
                'S3Bucket': 'test_bucket',
                'S3Key': 'test_key'
            },
            'Video': {
                'S3Bucket': 'test_bucket',
                'S3Key': 'test_key'
            },
            'Audio': {
                'S3Bucket': 'test_bucket',
                'S3Key': 'test_key'
            }
        }
    }

    inner_keys = ['S3Bucket', 'S3Key']
    test_parameters = [{
        'ProxyEncode': inner_keys
    }, {
        'Video': inner_keys
    }, {
        'Audio': inner_keys
    }]
    for test_parameter in test_parameters:
        for main_key, inner_keys in test_parameter.items():
            for inner_key in inner_keys:
                operator_parameter = helper.get_operator_parameter(
                    input = input_parameter,
                    metadata = {}
                )
                del operator_parameter['Input']['Media'][main_key][inner_key]
                with pytest.raises(MediaInsightsEngineLambdaHelper.MasExecutionError) as err:
                    lambda_function.lambda_handler(operator_parameter, {})
                err.value.args[0]['Status'] == 'Error'
                err.value.args[0]['MetaData']['TranscribeError'] == 'No valid inputs'

def test_invalid_file_type():
    import transcribe.start_transcribe as lambda_function
    import MediaInsightsEngineLambdaHelper
    import helper

    input_parameter = {
        'Media': {
            'ProxyEncode': {
                'S3Bucket': 'test_bucket',
                'S3Key': 'test_key.notvalid'
            }
        }
    }
    operator_parameter = helper.get_operator_parameter(
        input = input_parameter
    )
    with pytest.raises(MediaInsightsEngineLambdaHelper.MasExecutionError) as err:
        lambda_function.lambda_handler(operator_parameter, {})
    assert err.value.args[0]['Status'] == 'Error'
    assert err.value.args[0]['MetaData']['TranscribeError'] == 'Not a valid file type'

def test_transcribe_job_zero_audio_tracks(transcribe_start_stub):
    import transcribe.start_transcribe as lambda_function
    import helper

    input_parameter = {
        'Media': {
            'ProxyEncode': {
                'S3Bucket': 'test_bucket',
                'S3Key': 'test_key.mp4'
            }
        },
        'MetaData': {
            'Mediainfo_num_audio_tracks': '0'
        }
    }
    operator_parameter = helper.get_operator_parameter(
        input = input_parameter,
        metadata={}
    )

    response = lambda_function.lambda_handler(operator_parameter, {})
    assert response['Status'] == 'Complete'

def test_transcribe_job_error(transcribe_start_stub):
    import transcribe.start_transcribe as lambda_function
    import MediaInsightsEngineLambdaHelper
    import helper

    input_parameter = {
        'Media': {
            'ProxyEncode': {
                'S3Bucket': 'test_bucket',
                'S3Key': 'test_key.mp4'
            }
        },
        'MetaData': {
            'Mediainfo_num_audio_tracks': '1'
        }
    }
    operator_parameter = helper.get_operator_parameter(
        input = input_parameter,
        metadata={}
    )

    transcribe_start_stub.add_client_error('start_transcription_job')
    with pytest.raises(MediaInsightsEngineLambdaHelper.MasExecutionError) as err:
        lambda_function.lambda_handler(operator_parameter, {})
    assert err.value.args[0]['Status'] == 'Error'
    assert err.value.args[0]['MetaData']['transcribe_error'] == 'An error occurred () when calling the StartTranscriptionJob operation: '

def test_transcribe_job_in_progress(transcribe_start_stub):
    import transcribe.start_transcribe as lambda_function
    import helper

    input_parameter = {
        'Media': {
            'ProxyEncode': {
                'S3Bucket': 'test_bucket',
                'S3Key': 'test_key.mp4'
            }
        },
        'MetaData': {
            'Mediainfo_num_audio_tracks': '1'
        }
    }
    operator_parameter = helper.get_operator_parameter(
        input = input_parameter,
        metadata={}
    )

    transcribe_start_stub.add_response(
        'start_transcription_job',
        expected_params = {
            'TranscriptionJobName': 'transcribe-testWorkflowId',
            'Media': { 'MediaFileUri': 'https://s3.us-west-2.amazonaws.com/test_bucket/test_key.mp4'},
            'MediaFormat': 'mp4',
            'LanguageCode': 'en',
            'IdentifyLanguage': False,
            'Settings': {'VocabularyName': 'testVocabularyName'},
            'ModelSettings': {'LanguageModelName': 'testLanguageModelName'},
            'JobExecutionSettings': {'AllowDeferredExecution': False},
            'ContentRedaction': {
                'RedactionType': 'testRedactionType',
                'RedactionOutput': 'testRedactionOutput'
            },
            'LanguageOptions': ['en']
        },
        service_response = {
            'TranscriptionJob': {
                'TranscriptionJobStatus': 'IN_PROGRESS'
            }
        }
    )

    response = lambda_function.lambda_handler(operator_parameter, {})
    assert response['Status'] == 'Executing'
    assert response['MetaData']['TranscribeJobId'] == 'transcribe-testWorkflowId'
    assert response['MetaData']['AssetId'] == 'testAssetId'
    assert response['MetaData']['WorkflowExecutionId'] == 'testWorkflowId'

def test_transcribe_job_failed(transcribe_start_stub):
    import transcribe.start_transcribe as lambda_function
    import MediaInsightsEngineLambdaHelper
    import helper

    input_parameter = {
        'Media': {
            'ProxyEncode': {
                'S3Bucket': 'test_bucket',
                'S3Key': 'test_key.mp4'
            }
        },
        'MetaData': {
            'Mediainfo_num_audio_tracks': '1'
        }
    }
    operator_parameter = helper.get_operator_parameter(
        input = input_parameter,
        metadata={}
    )

    transcribe_start_stub.add_response(
        'start_transcription_job',
        expected_params = {
            'TranscriptionJobName': 'transcribe-testWorkflowId',
            'Media': { 'MediaFileUri': 'https://s3.us-west-2.amazonaws.com/test_bucket/test_key.mp4'},
            'MediaFormat': 'mp4',
            'LanguageCode': 'en',
            'IdentifyLanguage': False,
            'Settings': {'VocabularyName': 'testVocabularyName'},
            'ModelSettings': {'LanguageModelName': 'testLanguageModelName'},
            'JobExecutionSettings': {'AllowDeferredExecution': False},
            'ContentRedaction': {
                'RedactionType': 'testRedactionType',
                'RedactionOutput': 'testRedactionOutput'
            },
            'LanguageOptions': ['en']
        },
        service_response = {
            'TranscriptionJob': {
                'TranscriptionJobStatus': 'FAILED',
                'FailureReason': 'test_failed_reason'
            }
        }
    )
    with pytest.raises(MediaInsightsEngineLambdaHelper.MasExecutionError) as err:
        lambda_function.lambda_handler(operator_parameter, {})
    assert err.value.args[0]['Status'] == 'Error'
    assert err.value.args[0]['MetaData']['TranscribeJobId'] == 'transcribe-testWorkflowId'
    assert err.value.args[0]['MetaData']['TranscribeError'] == 'test_failed_reason'

def test_transcribe_job_with_unknown_status(transcribe_start_stub):
    import transcribe.start_transcribe as lambda_function
    import MediaInsightsEngineLambdaHelper
    import helper

    input_parameter = {
        'Media': {
            'ProxyEncode': {
                'S3Bucket': 'test_bucket',
                'S3Key': 'test_key.mp4'
            }
        },
        'MetaData': {
            'Mediainfo_num_audio_tracks': '1'
        }
    }
    operator_parameter = helper.get_operator_parameter(
        input = input_parameter,
        metadata={}
    )

    transcribe_start_stub.add_response(
        'start_transcription_job',
        expected_params = {
            'TranscriptionJobName': 'transcribe-testWorkflowId',
            'Media': { 'MediaFileUri': 'https://s3.us-west-2.amazonaws.com/test_bucket/test_key.mp4'},
            'MediaFormat': 'mp4',
            'LanguageCode': 'en',
            'IdentifyLanguage': False,
            'Settings': {'VocabularyName': 'testVocabularyName'},
            'ModelSettings': {'LanguageModelName': 'testLanguageModelName'},
            'JobExecutionSettings': {'AllowDeferredExecution': False},
            'ContentRedaction': {
                'RedactionType': 'testRedactionType',
                'RedactionOutput': 'testRedactionOutput'
            },
            'LanguageOptions': ['en']
        },
        service_response = {
            'TranscriptionJob': {
                'TranscriptionJobStatus': 'UNKNOWN_STATUS',
                'FailureReason': 'test_failed_reason'
            }
        }
    )
    with pytest.raises(MediaInsightsEngineLambdaHelper.MasExecutionError) as err:
        lambda_function.lambda_handler(operator_parameter, {})
    assert err.value.args[0]['Status'] == 'Error'
    assert err.value.args[0]['MetaData']['TranscribeJobId'] == 'transcribe-testWorkflowId'
    assert err.value.args[0]['MetaData']['TranscribeError'] == 'Unhandled error for this job: transcribe-testWorkflowId'

def test_transcribe_job_complete_status(transcribe_start_stub):
    import transcribe.start_transcribe as lambda_function
    import helper

    input_parameter = {
        'Media': {
            'ProxyEncode': {
                'S3Bucket': 'test_bucket',
                'S3Key': 'test_key.mp4'
            }
        },
        'MetaData': {
            'Mediainfo_num_audio_tracks': '1'
        }
    }
    operator_parameter = helper.get_operator_parameter(
        input = input_parameter,
        metadata={}
    )

    transcribe_start_stub.add_response(
        'start_transcription_job',
        expected_params = {
            'TranscriptionJobName': 'transcribe-testWorkflowId',
            'Media': { 'MediaFileUri': 'https://s3.us-west-2.amazonaws.com/test_bucket/test_key.mp4'},
            'MediaFormat': 'mp4',
            'LanguageCode': 'en',
            'IdentifyLanguage': False,
            'Settings': {'VocabularyName': 'testVocabularyName'},
            'ModelSettings': {'LanguageModelName': 'testLanguageModelName'},
            'JobExecutionSettings': {'AllowDeferredExecution': False},
            'ContentRedaction': {
                'RedactionType': 'testRedactionType',
                'RedactionOutput': 'testRedactionOutput'
            },
            'LanguageOptions': ['en']
        },
        service_response = {
            'TranscriptionJob': {
                'TranscriptionJobStatus': 'COMPLETE',
                'FailureReason': 'test_failed_reason'
            }
        }
    )
    response = lambda_function.lambda_handler(operator_parameter, {})
    assert response['Status'] == 'Executing'
    assert response['MetaData']['TranscribeJobId'] == 'transcribe-testWorkflowId'
    assert response['MetaData']['AssetId'] == 'testAssetId'
    assert response['MetaData']['WorkflowExecutionId'] == 'testWorkflowId'

def test_transcribe_job_with_auto_language(transcribe_start_stub):
    import transcribe.start_transcribe as lambda_function
    import helper

    input_parameter = {
        'Media': {
            'ProxyEncode': {
                'S3Bucket': 'test_bucket',
                'S3Key': 'test_key.mp4'
            }
        },
        'MetaData': {
            'Mediainfo_num_audio_tracks': '1'
        }
    }
    operator_parameter = helper.get_operator_parameter(
        input = input_parameter,
        metadata={}
    )

    operator_parameter['Configuration']['TranscribeLanguage'] = 'auto'

    transcribe_start_stub.add_response(
        'start_transcription_job',
        expected_params = {
            'TranscriptionJobName': 'transcribe-testWorkflowId',
            'Media': { 'MediaFileUri': 'https://s3.us-west-2.amazonaws.com/test_bucket/test_key.mp4'},
            'MediaFormat': 'mp4',
            'IdentifyLanguage': True,
            'Settings': {'VocabularyName': 'testVocabularyName'},
            'ModelSettings': {'LanguageModelName': 'testLanguageModelName'},
            'JobExecutionSettings': {'AllowDeferredExecution': False},
            'ContentRedaction': {
                'RedactionType': 'testRedactionType',
                'RedactionOutput': 'testRedactionOutput'
            },
            'LanguageOptions': ['en']
        },
        service_response = {
            'TranscriptionJob': {
                'TranscriptionJobStatus': 'COMPLETE',
                'FailureReason': 'test_failed_reason'
            }
        }
    )
    response = lambda_function.lambda_handler(operator_parameter, {})
    assert response['Status'] == 'Executing'
    assert response['MetaData']['TranscribeJobId'] == 'transcribe-testWorkflowId'
    assert response['MetaData']['AssetId'] == 'testAssetId'
    assert response['MetaData']['WorkflowExecutionId'] == 'testWorkflowId'