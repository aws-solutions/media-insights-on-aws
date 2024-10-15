# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import pytest, json
from botocore.response import StreamingBody
from io import BytesIO

def test_input_parameter():
    import polly.start_polly as lambda_function
    import helper
    
    operator_parameter = helper.get_operator_parameter()
    del operator_parameter['WorkflowExecutionId']
    
    with pytest.raises(KeyError) as err:
        lambda_function.lambda_handler(operator_parameter, {})
    assert err.value.args[0] == 'WorkflowExecutionId'

def test_invalid_s3_inputs():
    import polly.start_polly as lambda_function
    import MediaInsightsEngineLambdaHelper
    import helper
    
    operator_parameter = helper.get_operator_parameter(
        input = {
            'Media': {
                'Text': {
                    'S3Bucket': 'test_bucket',
                }
            }
        }
    )
    
    with pytest.raises(MediaInsightsEngineLambdaHelper.MasExecutionError) as err:
        lambda_function.lambda_handler(operator_parameter, {})
    assert err.value.args[0]['Status'] == 'Error'
    assert err.value.args[0]['MetaData']['PollyError'] == 'No valid inputs'


def test_no_translation_text(s3_start_stub):
    import polly.start_polly as lambda_function
    import helper
    
    operator_parameter = helper.get_operator_parameter(
        input = {
            'Media': {
                'Text': {
                    'S3Bucket': 'test_bucket',
                    'S3Key': 'test_key'
                }
            }
        }
    )

    s3_response = {
        'TranslatedText': ''
    }
    s3_start_stub.add_response(
        'get_object',
        expected_params = {
            'Bucket': 'test_bucket',
            'Key': 'test_key'
        },
        service_response = {
            'Body': StreamingBody(
                BytesIO(json.dumps(s3_response).encode('utf-8')),
                len(json.dumps(s3_response))
            )
        }
    )
    
    response = lambda_function.lambda_handler(operator_parameter, {})
    assert response['Status'] == 'Complete'

def test_s3_invalid_response(s3_start_stub):
    import polly.start_polly as lambda_function
    import MediaInsightsEngineLambdaHelper
    import helper
    
    operator_parameter = helper.get_operator_parameter(
        input = {
            'Media': {
                'Text': {
                    'S3Bucket': 'test_bucket',
                    'S3Key': 'test_key'
                }
            }
        }
    )

    s3_response = {
    }
    s3_start_stub.add_response(
        'get_object',
        expected_params = {
            'Bucket': 'test_bucket',
            'Key': 'test_key'
        },
        service_response = {
            'Body': StreamingBody(
                BytesIO(json.dumps(s3_response).encode('utf-8')),
                len(json.dumps(s3_response))
            )
        }
    )
    
    with pytest.raises(MediaInsightsEngineLambdaHelper.MasExecutionError) as err:
        lambda_function.lambda_handler(operator_parameter, {})
    assert err.value.args[0]['Status'] == 'Error'
    assert 'Unable to read translation from S3: ' in err.value.args[0]['MetaData']['PollyError']

def test_comprehend_error(s3_start_stub, comprehend_start_stub):
    import polly.start_polly as lambda_function
    import MediaInsightsEngineLambdaHelper
    import helper
    
    operator_parameter = helper.get_operator_parameter(
        input = {
            'Media': {
                'Text': {
                    'S3Bucket': 'test_bucket',
                    'S3Key': 'test_key'
                }
            }
        }
    )

    s3_response = {
        'TranslatedText': 'test_translated_text'
    }
    s3_start_stub.add_response(
        'get_object',
        expected_params = {
            'Bucket': 'test_bucket',
            'Key': 'test_key'
        },
        service_response = {
            'Body': StreamingBody(
                BytesIO(json.dumps(s3_response).encode('utf-8')),
                len(json.dumps(s3_response))
            )
        }
    )

    comprehend_start_stub.add_client_error('detect_dominant_language')
    
    with pytest.raises(MediaInsightsEngineLambdaHelper.MasExecutionError) as err:
        lambda_function.lambda_handler(operator_parameter, {})
    assert err.value.args[0]['Status'] == 'Error'
    assert 'Unable to determine the language with comprehend: ' in err.value.args[0]['MetaData']['PollyError']

def test_start_job_successfully(s3_start_stub, comprehend_start_stub, polly_start_stub):
    import polly.start_polly as lambda_function
    import helper
    
    operator_parameter = helper.get_operator_parameter(
        input = {
            'Media': {
                'Text': {
                    'S3Bucket': 'test_bucket',
                    'S3Key': 'test_key'
                }
            }
        }
    )

    s3_response = {
        'TranslatedText': 'test_translated_text'
    }
    s3_start_stub.add_response(
        'get_object',
        expected_params = {
            'Bucket': 'test_bucket',
            'Key': 'test_key'
        },
        service_response = {
            'Body': StreamingBody(
                BytesIO(json.dumps(s3_response).encode('utf-8')),
                len(json.dumps(s3_response))
            )
        }
    )

    comprehend_start_stub.add_response(
        'detect_dominant_language',
        expected_params = {
            'Text': 'test_translated_text'
        },
        service_response = {
            'Languages': [{
                'LanguageCode': 'en'
            }]
        }
    )

    polly_start_stub.add_response(
        'start_speech_synthesis_task',
        expected_params = {
            'OutputFormat': 'mp3',
            'OutputS3BucketName': 'test_bucket',
            'OutputS3KeyPrefix': '/private/assets/testAssetId/workflows/testWorkflowId/translation',
            'Text': 'test_translated_text',
            'TextType': 'text',
            'VoiceId': 'Kendra'
        },
        service_response = {
            'SynthesisTask': {
                'TaskId': 'testTaskId'
            }
        }
    )
    
    response = lambda_function.lambda_handler(operator_parameter, {})
    assert response['Status'] == 'Executing'
    assert response['MetaData']['PollyJobId'] == 'testTaskId'
    assert response['MetaData']['WorkflowExecutionId'] == 'testWorkflowId'
    assert response['MetaData']['AssetId'] == 'testAssetId'