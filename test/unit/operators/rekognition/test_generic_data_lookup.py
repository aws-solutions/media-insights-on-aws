# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import pytest, json
from unittest.mock import MagicMock
from botocore.stub import Stubber
from botocore.response import StreamingBody
from io import BytesIO

def test_empty_event_status():
    import rekognition.generic_data_lookup as lambda_function
    import MediaInsightsEngineLambdaHelper
    import helper

    input_parameter = helper.get_operator_parameter(metadata={})

    with pytest.raises(MediaInsightsEngineLambdaHelper.MasExecutionError) as err:
        lambda_function.lambda_handler(input_parameter,{})
    assert err.value.args[0]['Status'] == 'Error'
    assert err.value.args[0]['MetaData']['GenericDataLookupError'] == 'No valid inputs'

def test_empty_key_configuration():
    import rekognition.generic_data_lookup as lambda_function
    import MediaInsightsEngineLambdaHelper
    import helper

    input_parameter = helper.get_operator_parameter(
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
    del input_parameter['Configuration']['Key']

    with pytest.raises(MediaInsightsEngineLambdaHelper.MasExecutionError) as err:
        lambda_function.lambda_handler(input_parameter,{})
    assert err.value.args[0]['Status'] == 'Error'
    assert err.value.args[0]['MetaData']['GenericDataLookupError'] == 'Missing S3 key for data file.'

def test_empty_bucket_configuration():
    import rekognition.generic_data_lookup as lambda_function
    import MediaInsightsEngineLambdaHelper
    import helper

    input_parameter = helper.get_operator_parameter(
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
    del input_parameter['Configuration']['Bucket']

    with pytest.raises(MediaInsightsEngineLambdaHelper.MasExecutionError) as err:
        lambda_function.lambda_handler(input_parameter,{})
    assert err.value.args[0]['Status'] == 'Error'
    assert err.value.args[0]['MetaData']['GenericDataLookupError'] == 'Missing S3 bucket for data file.'

def test_empty_bucket_configuration():
    import rekognition.generic_data_lookup as lambda_function
    import MediaInsightsEngineLambdaHelper
    import helper

    input_parameter = helper.get_operator_parameter(
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
    del input_parameter['Configuration']['Bucket']

    with pytest.raises(MediaInsightsEngineLambdaHelper.MasExecutionError) as err:
        lambda_function.lambda_handler(input_parameter,{})
    assert err.value.args[0]['Status'] == 'Error'
    assert err.value.args[0]['MetaData']['GenericDataLookupError'] == 'Missing S3 bucket for data file.'

def test_s3_error():
    import rekognition.generic_data_lookup as lambda_function
    import MediaInsightsEngineLambdaHelper
    import helper

    input_parameter = helper.get_operator_parameter(
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

    with Stubber(lambda_function.s3) as stubber:
        stubber.assert_no_pending_responses()
        stubber.add_client_error('get_object')

        with pytest.raises(MediaInsightsEngineLambdaHelper.MasExecutionError) as err:
            lambda_function.lambda_handler(input_parameter,{})
        assert err.value.args[0]['Status'] == 'Error'
        assert err.value.args[0]['MetaData']['GenericDataLookupError'] == 'Unable read datafile. An error occurred () when calling the GetObject operation: '

def test_s3_invalid_response():
    import rekognition.generic_data_lookup as lambda_function
    import MediaInsightsEngineLambdaHelper
    import helper

    input_parameter = helper.get_operator_parameter(
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

    with Stubber(lambda_function.s3) as stubber:
        stubber.assert_no_pending_responses()
        stubber.add_response(
            'get_object',
            expected_params = {
                'Bucket': 'testBucket',
                'Key': 'testKey'
            },
            service_response = {
                'Body': StreamingBody(
                    BytesIO(json.dumps('invalid response').encode('utf-8')),
                    len(json.dumps('invalid response'))
                )
            }
        )

        with pytest.raises(MediaInsightsEngineLambdaHelper.MasExecutionError) as err:
            lambda_function.lambda_handler(input_parameter,{})
        assert err.value.args[0]['Status'] == 'Error'
        assert err.value.args[0]['MetaData']['GenericDataLookupError'] == "Metadata must be of type dict. Found <class 'str'> instead."

def test_empty_status():
    import rekognition.generic_data_lookup as lambda_function
    import MediaInsightsEngineLambdaHelper
    import helper

    original_function = lambda_function.DataPlane.store_asset_metadata
    lambda_function.DataPlane.store_asset_metadata = MagicMock(
        return_value = {
        }
    )

    input_parameter = helper.get_operator_parameter(
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

    with Stubber(lambda_function.s3) as stubber:
        stubber.assert_no_pending_responses()
        stubber.add_response(
            'get_object',
            expected_params = {
                'Bucket': 'testBucket',
                'Key': 'testKey'
            },
            service_response = {
                'Body': StreamingBody(
                    BytesIO(json.dumps({}).encode('utf-8')),
                    len(json.dumps({}))
                )
            }
        )
        with pytest.raises(MediaInsightsEngineLambdaHelper.MasExecutionError) as err:
            lambda_function.lambda_handler(input_parameter,{})
        assert err.value.args[0]['Status'] == 'Error'
        assert err.value.args[0]['MetaData']['GenericDataLookupError'] == 'Unable to upload metadata for asset: testAssetId'
    
    assert lambda_function.DataPlane.store_asset_metadata.call_count == 1
    assert lambda_function.DataPlane.store_asset_metadata.call_args[0][0] == 'testAssetId'
    assert lambda_function.DataPlane.store_asset_metadata.call_args[0][1] == 'testName'
    assert lambda_function.DataPlane.store_asset_metadata.call_args[0][2] == 'testWorkflowId'
    assert lambda_function.DataPlane.store_asset_metadata.call_args[0][3] == {}
    lambda_function.DataPlane.store_asset_metadata = original_function

def test_failed_case():
    import rekognition.generic_data_lookup as lambda_function
    import MediaInsightsEngineLambdaHelper
    import helper

    original_function = lambda_function.DataPlane.store_asset_metadata
    lambda_function.DataPlane.store_asset_metadata = MagicMock(
        return_value = {
            'Status': 'Fail'
        }
    )

    input_parameter = helper.get_operator_parameter(
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

    with Stubber(lambda_function.s3) as stubber:
        stubber.assert_no_pending_responses()
        stubber.add_response(
            'get_object',
            expected_params = {
                'Bucket': 'testBucket',
                'Key': 'testKey'
            },
            service_response = {
                'Body': StreamingBody(
                    BytesIO(json.dumps({}).encode('utf-8')),
                    len(json.dumps({}))
                )
            }
        )
        with pytest.raises(MediaInsightsEngineLambdaHelper.MasExecutionError) as err:
            lambda_function.lambda_handler(input_parameter,{})
        assert err.value.args[0]['Status'] == 'Error'
        assert err.value.args[0]['MetaData']['GenericDataLookupError'] == 'Unable to upload metadata for asset: testAssetId'
    
    assert lambda_function.DataPlane.store_asset_metadata.call_count == 1
    assert lambda_function.DataPlane.store_asset_metadata.call_args[0][0] == 'testAssetId'
    assert lambda_function.DataPlane.store_asset_metadata.call_args[0][1] == 'testName'
    assert lambda_function.DataPlane.store_asset_metadata.call_args[0][2] == 'testWorkflowId'
    assert lambda_function.DataPlane.store_asset_metadata.call_args[0][3] == {}
    lambda_function.DataPlane.store_asset_metadata = original_function

def test_success_case():
    import rekognition.generic_data_lookup as lambda_function
    import helper

    original_function = lambda_function.DataPlane.store_asset_metadata
    lambda_function.DataPlane.store_asset_metadata = MagicMock(
        return_value = {
            'Status': 'Success'
        }
    )

    input_parameter = helper.get_operator_parameter(
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

    with Stubber(lambda_function.s3) as stubber:
        stubber.assert_no_pending_responses()
        stubber.add_response(
            'get_object',
            expected_params = {
                'Bucket': 'testBucket',
                'Key': 'testKey'
            },
            service_response = {
                'Body': StreamingBody(
                    BytesIO(json.dumps({}).encode('utf-8')),
                    len(json.dumps({}))
                )
            }
        )

        response = lambda_function.lambda_handler(input_parameter,{})
        assert response['Status'] == 'Complete'
    
    assert lambda_function.DataPlane.store_asset_metadata.call_count == 1
    assert lambda_function.DataPlane.store_asset_metadata.call_args[0][0] == 'testAssetId'
    assert lambda_function.DataPlane.store_asset_metadata.call_args[0][1] == 'testName'
    assert lambda_function.DataPlane.store_asset_metadata.call_args[0][2] == 'testWorkflowId'
    assert lambda_function.DataPlane.store_asset_metadata.call_args[0][3] == {}
    lambda_function.DataPlane.store_asset_metadata = original_function