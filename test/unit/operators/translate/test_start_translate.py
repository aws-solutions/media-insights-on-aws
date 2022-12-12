import pytest, json
from botocore.response import StreamingBody
from io import BytesIO
from unittest.mock import MagicMock

def test_input_parameter():
    import translate.start_translate as lambda_function
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
                'Text': {
                    'S3Bucket': 'test_bucket',
                    'S3Key': 'test_key'
                }
            }
        }
    )
    del operator_parameter['Input']['Media']['Text']['S3Bucket']
    
    with pytest.raises(MediaInsightsEngineLambdaHelper.MasExecutionError) as err:
        lambda_function.lambda_handler(operator_parameter, {})
    assert err.value.args[0]['Status'] == 'Error'
    assert "No valid inputs 'S3Bucket'" in err.value.args[0]['MetaData']['TranslateError']

    # Empty S3Key
    operator_parameter = helper.get_operator_parameter(
        metadata={},
        input = {
            'Media': {
                'Text': {
                    'S3Bucket': 'test_bucket',
                    'S3Key': 'test_key'
                }
            }
        }
    )
    del operator_parameter['Input']['Media']['Text']['S3Key']
    
    with pytest.raises(MediaInsightsEngineLambdaHelper.MasExecutionError) as err:
        lambda_function.lambda_handler(operator_parameter, {})
    assert err.value.args[0]['Status'] == 'Error'
    assert "No valid inputs 'S3Key'" in err.value.args[0]['MetaData']['TranslateError']

def test_target_language_not_provided():
    import translate.start_translate as lambda_function
    import MediaInsightsEngineLambdaHelper
    import helper

    operator_parameter = helper.get_operator_parameter(
        input = {
            'Media': {
                'Text': {
                    'S3Bucket': 'test_bucket',
                    'S3Key': 'test_key'
                }
            },
            'MetaData': {
                'TranscribeSourceLanguage': 'en-US'
            }
        }
    )
    del operator_parameter['Configuration']['TargetLanguageCode']
    
    with pytest.raises(MediaInsightsEngineLambdaHelper.MasExecutionError) as err:
        lambda_function.lambda_handler(operator_parameter, {})
    assert err.value.args[0]['Status'] == 'Error'
    assert err.value.args[0]['MetaData']['TranslateError'] == 'Language codes are not defined'

def test_s3_client_error(s3_client_stub, translate_client_stub):
    import translate.start_translate as lambda_function
    import MediaInsightsEngineLambdaHelper
    import helper

    operator_parameter = helper.get_operator_parameter(
        input = {
            'Media': {
                'Text': {
                    'S3Bucket': 'test_bucket',
                    'S3Key': 'test_key'
                }
            },
            'MetaData': {
                'TranscribeSourceLanguage': 'en-US'
            }
        },
        metadata={}
    )

    s3_client_stub.add_client_error('get_object')
    
    with pytest.raises(MediaInsightsEngineLambdaHelper.MasExecutionError) as err:
        lambda_function.lambda_handler(operator_parameter, {})
    assert err.value.args[0]['Status'] == 'Error'
    assert 'Unable to read transcription from S3: An error occurred () when calling the GetObject operation: ' in err.value.args[0]['MetaData']['TranslateError']

def test_empty_transcript(s3_client_stub):
    import translate.start_translate as lambda_function
    import helper

    operator_parameter = helper.get_operator_parameter(
        input = {
            'Media': {
                'Text': {
                    'S3Bucket': 'test_bucket',
                    'S3Key': 'test_key'
                }
            },
            'MetaData': {
                'TranscribeSourceLanguage': 'en-US'
            }
        },
        metadata={}
    )

    s3_response = {
        'results': {
            'transcripts': [{
                'transcript': ''
            }]
        }
    }
    s3_client_stub.add_response(
        'get_object',
        expected_params = {
            'Bucket': 'test_bucket',
            'Key': 'test_key'
        },
        service_response = {
            'Body': StreamingBody(
                BytesIO(json.dumps(s3_response).encode('utf-8')),
                len(json.dumps(s3_response).encode('utf-8'))
            )
        }
    )
    
    response = lambda_function.lambda_handler(operator_parameter, {})
    assert response['Status'] == 'Complete'

def test_translate_job_dataplane_empty_status(s3_client_stub, translate_client_stub):
    import translate.start_translate as lambda_function
    import MediaInsightsEngineLambdaHelper
    import helper

    original_function = lambda_function.DataPlane.store_asset_metadata
    lambda_function.DataPlane.store_asset_metadata = MagicMock(
        return_value = {}
    )

    operator_parameter = helper.get_operator_parameter(
        input = {
            'Media': {
                'Text': {
                    'S3Bucket': 'test_bucket',
                    'S3Key': 'test_key'
                }
            },
            'MetaData': {
                'TranscribeSourceLanguage': 'en-US'
            }
        },
        metadata={}
    )
    s3_response = {
        'results': {
            'transcripts': [{
                'transcript': 'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Aliquam turpis justo, lobortis at fringilla eu, vestibulum eu sapien. Aenean fringilla eros lorem, vel efficitur magna lobortis at. Morbi vulputate sem justo, et scelerisque augue imperdiet nec. Vestibulum ante ipsum primis in faucibus orci luctus et ultrices posuere cubilia curae; Duis cursus, nisl porta ornare commodo, purus enim tincidunt tortor, et sodales ante leo et mi. Nunc vitae nulla commodo, ultricies arcu vitae, consectetur mauris. Donec lobortis vestibulum massa, quis aliquam quam elementum vulputate. Sed consequat tortor enim, vitae pharetra felis facilisis quis. Sed ut sem elit. Sed nibh erat, pharetra vel risus eget, mollis mollis nunc. Phasellus ut massa et lorem efficitur commodo. Quisque posuere, est eget finibus molestie, risus nisi imperdiet eros, a dictum arcu odio vel justo. Ut ultricies odio neque, sit amet feugiat dolor gravida eu. Sed feugiat augue tempus euismod tincidunt. Proin finibus malesuada ex, vitae ornare ligula lobortis id. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Morbi tristique diam vel risus mollis facilisis. Suspendisse scelerisque ipsum vel dolor semper, sed faucibus nibh suscipit. Maecenas rutrum sollicitudin viverra. Sed risus erat, fringilla ac placerat a, accumsan vel velit.'
            }]
        }
    }
    s3_client_stub.add_response(
        'get_object',
        expected_params = {
            'Bucket': 'test_bucket',
            'Key': 'test_key'
        },
        service_response = {
            'Body': StreamingBody(
                BytesIO(json.dumps(s3_response).encode('utf-8')),
                len(json.dumps(s3_response).encode('utf-8'))
            )
        }
    )
    translate_client_stub.add_response(
        'translate_text',
        expected_params = {
            'Text': ' Lorem ipsum dolor sit amet, consectetur adipiscing elit. Aliquam turpis justo, lobortis at fringilla eu, vestibulum eu sapien. Aenean fringilla eros lorem, vel efficitur magna lobortis at. Morbi vulputate sem justo, et scelerisque augue imperdiet nec. Vestibulum ante ipsum primis in faucibus orci luctus et ultrices posuere cubilia curae; Duis cursus, nisl porta ornare commodo, purus enim tincidunt tortor, et sodales ante leo et mi. Nunc vitae nulla commodo, ultricies arcu vitae, consectetur mauris. Donec lobortis vestibulum massa, quis aliquam quam elementum vulputate. Sed consequat tortor enim, vitae pharetra felis facilisis quis. Sed ut sem elit. Sed nibh erat, pharetra vel risus eget, mollis mollis nunc. Phasellus ut massa et lorem efficitur commodo. Quisque posuere, est eget finibus molestie, risus nisi imperdiet eros, a dictum arcu odio vel justo. Ut ultricies odio neque, sit amet feugiat dolor gravida eu. Sed feugiat augue tempus euismod tincidunt.',
            'SourceLanguageCode': 'en',
            'TargetLanguageCode': 'en'
        },
        service_response = {
            'TranslatedText': 'testTranslatedText',
            'SourceLanguageCode': 'en',
            'TargetLanguageCode': 'en'
        }
    )

    translate_client_stub.add_response(
        'translate_text',
        expected_params = {
            'Text': 'Proin finibus malesuada ex, vitae ornare ligula lobortis id. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Morbi tristique diam vel risus mollis facilisis. Suspendisse scelerisque ipsum vel dolor semper, sed faucibus nibh suscipit. Maecenas rutrum sollicitudin viverra. Sed risus erat, fringilla ac placerat a, accumsan vel velit.',
            'SourceLanguageCode': 'en',
            'TargetLanguageCode': 'en'
        },
        service_response = {
            'TranslatedText': 'testTranslatedText',
            'SourceLanguageCode': 'en',
            'TargetLanguageCode': 'en'
        }
    )
    with pytest.raises(MediaInsightsEngineLambdaHelper.MasExecutionError) as err:
        lambda_function.lambda_handler(operator_parameter, {})
    assert err.value.args[0]['Status'] == 'Error'
    assert err.value.args[0]['MetaData']['TranslateError'] == 'Unable to upload metadata for asset: testAssetId'
    assert lambda_function.DataPlane.store_asset_metadata.call_count == 1
    assert lambda_function.DataPlane.store_asset_metadata.call_args[0][0] == 'testAssetId'
    assert lambda_function.DataPlane.store_asset_metadata.call_args[0][1] == 'testName'
    assert lambda_function.DataPlane.store_asset_metadata.call_args[0][2] == 'testWorkflowId'
    assert lambda_function.DataPlane.store_asset_metadata.call_args[0][3] == {'TranslatedText': ' testTranslatedText testTranslatedText', 'SourceLanguageCode': 'en', 'TargetLanguageCode': 'en'}
    
    lambda_function.DataPlane.store_asset_metadata = original_function

def test_translate_client_error(s3_client_stub, translate_client_stub):
    import translate.start_translate as lambda_function
    import MediaInsightsEngineLambdaHelper
    import helper

    original_function = lambda_function.DataPlane.store_asset_metadata
    lambda_function.DataPlane.store_asset_metadata = MagicMock(
        return_value = {}
    )

    operator_parameter = helper.get_operator_parameter(
        input = {
            'Media': {
                'Text': {
                    'S3Bucket': 'test_bucket',
                    'S3Key': 'test_key'
                }
            },
            'MetaData': {
                'TranscribeSourceLanguage': 'en-US'
            }
        },
        metadata={}
    )
    s3_response = {
        'results': {
            'transcripts': [{
                'transcript': 'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Aliquam turpis justo, lobortis at fringilla eu, vestibulum eu sapien. Aenean fringilla eros lorem, vel efficitur magna lobortis at. Morbi vulputate sem justo, et scelerisque augue imperdiet nec. Vestibulum ante ipsum primis in faucibus orci luctus et ultrices posuere cubilia curae; Duis cursus, nisl porta ornare commodo, purus enim tincidunt tortor, et sodales ante leo et mi. Nunc vitae nulla commodo, ultricies arcu vitae, consectetur mauris. Donec lobortis vestibulum massa, quis aliquam quam elementum vulputate. Sed consequat tortor enim, vitae pharetra felis facilisis quis. Sed ut sem elit. Sed nibh erat, pharetra vel risus eget, mollis mollis nunc. Phasellus ut massa et lorem efficitur commodo. Quisque posuere, est eget finibus molestie, risus nisi imperdiet eros, a dictum arcu odio vel justo. Ut ultricies odio neque, sit amet feugiat dolor gravida eu. Sed feugiat augue tempus euismod tincidunt. Proin finibus malesuada ex, vitae ornare ligula lobortis id. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Morbi tristique diam vel risus mollis facilisis. Suspendisse scelerisque ipsum vel dolor semper, sed faucibus nibh suscipit. Maecenas rutrum sollicitudin viverra. Sed risus erat, fringilla ac placerat a, accumsan vel velit.'
            }]
        }
    }
    s3_client_stub.add_response(
        'get_object',
        expected_params = {
            'Bucket': 'test_bucket',
            'Key': 'test_key'
        },
        service_response = {
            'Body': StreamingBody(
                BytesIO(json.dumps(s3_response).encode('utf-8')),
                len(json.dumps(s3_response).encode('utf-8'))
            )
        }
    )
    translate_client_stub.add_client_error('translate_text')
    with pytest.raises(MediaInsightsEngineLambdaHelper.MasExecutionError) as err:
        lambda_function.lambda_handler(operator_parameter, {})
    assert err.value.args[0]['Status'] == 'Error'
    assert err.value.args[0]['MetaData']['TranslateError'] == 'Unable to get response from translate: An error occurred () when calling the TranslateText operation: '
    assert lambda_function.DataPlane.store_asset_metadata.call_count == 0
    
    lambda_function.DataPlane.store_asset_metadata = original_function

def test_translate_job_error(s3_client_stub, translate_client_stub):
    import translate.start_translate as lambda_function
    import MediaInsightsEngineLambdaHelper
    import helper

    original_function = lambda_function.DataPlane.store_asset_metadata
    lambda_function.DataPlane.store_asset_metadata = MagicMock(
        return_value = {
            'Status': 'Error',
            'Bucket': 'test_result_bucket',
            'Key': 'test_result_key'
        }
    )

    operator_parameter = helper.get_operator_parameter(
        input = {
            'Media': {
                'Text': {
                    'S3Bucket': 'test_bucket',
                    'S3Key': 'test_key'
                }
            },
            'MetaData': {
                'TranscribeSourceLanguage': 'en-US'
            }
        },
        metadata={}
    )
    s3_response = {
        'results': {
            'transcripts': [{
                'transcript': 'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Aliquam turpis justo, lobortis at fringilla eu, vestibulum eu sapien. Aenean fringilla eros lorem, vel efficitur magna lobortis at. Morbi vulputate sem justo, et scelerisque augue imperdiet nec. Vestibulum ante ipsum primis in faucibus orci luctus et ultrices posuere cubilia curae; Duis cursus, nisl porta ornare commodo, purus enim tincidunt tortor, et sodales ante leo et mi. Nunc vitae nulla commodo, ultricies arcu vitae, consectetur mauris. Donec lobortis vestibulum massa, quis aliquam quam elementum vulputate. Sed consequat tortor enim, vitae pharetra felis facilisis quis. Sed ut sem elit. Sed nibh erat, pharetra vel risus eget, mollis mollis nunc. Phasellus ut massa et lorem efficitur commodo. Quisque posuere, est eget finibus molestie, risus nisi imperdiet eros, a dictum arcu odio vel justo. Ut ultricies odio neque, sit amet feugiat dolor gravida eu. Sed feugiat augue tempus euismod tincidunt. Proin finibus malesuada ex, vitae ornare ligula lobortis id. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Morbi tristique diam vel risus mollis facilisis. Suspendisse scelerisque ipsum vel dolor semper, sed faucibus nibh suscipit. Maecenas rutrum sollicitudin viverra. Sed risus erat, fringilla ac placerat a, accumsan vel velit.'
            }]
        }
    }
    s3_client_stub.add_response(
        'get_object',
        expected_params = {
            'Bucket': 'test_bucket',
            'Key': 'test_key'
        },
        service_response = {
            'Body': StreamingBody(
                BytesIO(json.dumps(s3_response).encode('utf-8')),
                len(json.dumps(s3_response).encode('utf-8'))
            )
        }
    )
    translate_client_stub.add_response(
        'translate_text',
        expected_params = {
            'Text': ' Lorem ipsum dolor sit amet, consectetur adipiscing elit. Aliquam turpis justo, lobortis at fringilla eu, vestibulum eu sapien. Aenean fringilla eros lorem, vel efficitur magna lobortis at. Morbi vulputate sem justo, et scelerisque augue imperdiet nec. Vestibulum ante ipsum primis in faucibus orci luctus et ultrices posuere cubilia curae; Duis cursus, nisl porta ornare commodo, purus enim tincidunt tortor, et sodales ante leo et mi. Nunc vitae nulla commodo, ultricies arcu vitae, consectetur mauris. Donec lobortis vestibulum massa, quis aliquam quam elementum vulputate. Sed consequat tortor enim, vitae pharetra felis facilisis quis. Sed ut sem elit. Sed nibh erat, pharetra vel risus eget, mollis mollis nunc. Phasellus ut massa et lorem efficitur commodo. Quisque posuere, est eget finibus molestie, risus nisi imperdiet eros, a dictum arcu odio vel justo. Ut ultricies odio neque, sit amet feugiat dolor gravida eu. Sed feugiat augue tempus euismod tincidunt.',
            'SourceLanguageCode': 'en',
            'TargetLanguageCode': 'en'
        },
        service_response = {
            'TranslatedText': 'testTranslatedText',
            'SourceLanguageCode': 'en',
            'TargetLanguageCode': 'en'
        }
    )

    translate_client_stub.add_response(
        'translate_text',
        expected_params = {
            'Text': 'Proin finibus malesuada ex, vitae ornare ligula lobortis id. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Morbi tristique diam vel risus mollis facilisis. Suspendisse scelerisque ipsum vel dolor semper, sed faucibus nibh suscipit. Maecenas rutrum sollicitudin viverra. Sed risus erat, fringilla ac placerat a, accumsan vel velit.',
            'SourceLanguageCode': 'en',
            'TargetLanguageCode': 'en'
        },
        service_response = {
            'TranslatedText': 'testTranslatedText',
            'SourceLanguageCode': 'en',
            'TargetLanguageCode': 'en'
        }
    )
    with pytest.raises(MediaInsightsEngineLambdaHelper.MasExecutionError) as err:
        lambda_function.lambda_handler(operator_parameter, {})
    assert err.value.args[0]['Status'] == 'Error'
    assert err.value.args[0]['MetaData']['TranslateError'] == 'Unable to upload metadata for asset: testAssetId'
    assert lambda_function.DataPlane.store_asset_metadata.call_count == 1
    assert lambda_function.DataPlane.store_asset_metadata.call_args[0][0] == 'testAssetId'
    assert lambda_function.DataPlane.store_asset_metadata.call_args[0][1] == 'testName'
    assert lambda_function.DataPlane.store_asset_metadata.call_args[0][2] == 'testWorkflowId'
    assert lambda_function.DataPlane.store_asset_metadata.call_args[0][3] == {'TranslatedText': ' testTranslatedText testTranslatedText', 'SourceLanguageCode': 'en', 'TargetLanguageCode': 'en'}
    
    lambda_function.DataPlane.store_asset_metadata = original_function

def test_translate_job_success(s3_client_stub, translate_client_stub):
    import translate.start_translate as lambda_function
    import helper

    original_function = lambda_function.DataPlane.store_asset_metadata
    lambda_function.DataPlane.store_asset_metadata = MagicMock(
        return_value = {
            'Status': 'Success',
            'Bucket': 'test_result_bucket',
            'Key': 'test_result_key'
        }
    )

    operator_parameter = helper.get_operator_parameter(
        input = {
            'Media': {
                'Text': {
                    'S3Bucket': 'test_bucket',
                    'S3Key': 'test_key'
                }
            },
            'MetaData': {
                'TranscribeSourceLanguage': 'en-US'
            }
        },
        metadata={}
    )
    s3_response = {
        'results': {
            'transcripts': [{
                'transcript': 'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Aliquam turpis justo, lobortis at fringilla eu, vestibulum eu sapien. Aenean fringilla eros lorem, vel efficitur magna lobortis at. Morbi vulputate sem justo, et scelerisque augue imperdiet nec. Vestibulum ante ipsum primis in faucibus orci luctus et ultrices posuere cubilia curae; Duis cursus, nisl porta ornare commodo, purus enim tincidunt tortor, et sodales ante leo et mi. Nunc vitae nulla commodo, ultricies arcu vitae, consectetur mauris. Donec lobortis vestibulum massa, quis aliquam quam elementum vulputate. Sed consequat tortor enim, vitae pharetra felis facilisis quis. Sed ut sem elit. Sed nibh erat, pharetra vel risus eget, mollis mollis nunc. Phasellus ut massa et lorem efficitur commodo. Quisque posuere, est eget finibus molestie, risus nisi imperdiet eros, a dictum arcu odio vel justo. Ut ultricies odio neque, sit amet feugiat dolor gravida eu. Sed feugiat augue tempus euismod tincidunt. Proin finibus malesuada ex, vitae ornare ligula lobortis id. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Morbi tristique diam vel risus mollis facilisis. Suspendisse scelerisque ipsum vel dolor semper, sed faucibus nibh suscipit. Maecenas rutrum sollicitudin viverra. Sed risus erat, fringilla ac placerat a, accumsan vel velit.'
            }]
        }
    }
    s3_client_stub.add_response(
        'get_object',
        expected_params = {
            'Bucket': 'test_bucket',
            'Key': 'test_key'
        },
        service_response = {
            'Body': StreamingBody(
                BytesIO(json.dumps(s3_response).encode('utf-8')),
                len(json.dumps(s3_response).encode('utf-8'))
            )
        }
    )
    translate_client_stub.add_response(
        'translate_text',
        expected_params = {
            'Text': ' Lorem ipsum dolor sit amet, consectetur adipiscing elit. Aliquam turpis justo, lobortis at fringilla eu, vestibulum eu sapien. Aenean fringilla eros lorem, vel efficitur magna lobortis at. Morbi vulputate sem justo, et scelerisque augue imperdiet nec. Vestibulum ante ipsum primis in faucibus orci luctus et ultrices posuere cubilia curae; Duis cursus, nisl porta ornare commodo, purus enim tincidunt tortor, et sodales ante leo et mi. Nunc vitae nulla commodo, ultricies arcu vitae, consectetur mauris. Donec lobortis vestibulum massa, quis aliquam quam elementum vulputate. Sed consequat tortor enim, vitae pharetra felis facilisis quis. Sed ut sem elit. Sed nibh erat, pharetra vel risus eget, mollis mollis nunc. Phasellus ut massa et lorem efficitur commodo. Quisque posuere, est eget finibus molestie, risus nisi imperdiet eros, a dictum arcu odio vel justo. Ut ultricies odio neque, sit amet feugiat dolor gravida eu. Sed feugiat augue tempus euismod tincidunt.',
            'SourceLanguageCode': 'en',
            'TargetLanguageCode': 'en'
        },
        service_response = {
            'TranslatedText': 'testTranslatedText',
            'SourceLanguageCode': 'en',
            'TargetLanguageCode': 'en'
        }
    )

    translate_client_stub.add_response(
        'translate_text',
        expected_params = {
            'Text': 'Proin finibus malesuada ex, vitae ornare ligula lobortis id. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Morbi tristique diam vel risus mollis facilisis. Suspendisse scelerisque ipsum vel dolor semper, sed faucibus nibh suscipit. Maecenas rutrum sollicitudin viverra. Sed risus erat, fringilla ac placerat a, accumsan vel velit.',
            'SourceLanguageCode': 'en',
            'TargetLanguageCode': 'en'
        },
        service_response = {
            'TranslatedText': 'testTranslatedText',
            'SourceLanguageCode': 'en',
            'TargetLanguageCode': 'en'
        }
    )
    
    response = lambda_function.lambda_handler(operator_parameter, {})
    assert response['Status'] == 'Complete'
    assert response['Media']['Text'] == {'S3Bucket': 'test_result_bucket', 'S3Key': 'test_result_key'}
    assert lambda_function.DataPlane.store_asset_metadata.call_count == 1
    assert lambda_function.DataPlane.store_asset_metadata.call_args[0][0] == 'testAssetId'
    assert lambda_function.DataPlane.store_asset_metadata.call_args[0][1] == 'testName'
    assert lambda_function.DataPlane.store_asset_metadata.call_args[0][2] == 'testWorkflowId'
    assert lambda_function.DataPlane.store_asset_metadata.call_args[0][3] == {'TranslatedText': ' testTranslatedText testTranslatedText', 'SourceLanguageCode': 'en', 'TargetLanguageCode': 'en'}
    
    lambda_function.DataPlane.store_asset_metadata = original_function