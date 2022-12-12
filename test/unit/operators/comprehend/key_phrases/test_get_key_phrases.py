import io, pytest
import tarfile as tar
from botocore.response import StreamingBody
from unittest.mock import MagicMock

def stub_comprehend_client(stub):
    stub.add_response(
        'list_key_phrases_detection_jobs',
        expected_params = {
            'Filter': {
                'JobName': 'comprehend_phrases_job_id'
            }
        },
        service_response = {
            'KeyPhrasesDetectionJobPropertiesList': [{
                'JobStatus': 'COMPLETED',
                'OutputDataConfig': {
                    'S3Uri': 's3://bucket_name/comprehend/key_name'
                },
                'LanguageCode': 'en-US'
            }]
        }
    )

def stub_s3_response(stub, bucket_name, key_name, response_body):
    stub.add_response(
        'get_object',
        expected_params = {
            'Bucket': bucket_name,
            'Key': key_name
        },
        service_response = {
            'Body': StreamingBody(
                io.BytesIO(response_body.encode()),
                len(response_body)
            )
        }
    )

def test_parameter_validation():
    import comprehend.key_phrases.get_key_phrases as lambda_function
    import MediaInsightsEngineLambdaHelper
    import helper

    operator_parameter = helper.get_operator_parameter()
    
    with pytest.raises(MediaInsightsEngineLambdaHelper.MasExecutionError) as err:
        lambda_function.lambda_handler(operator_parameter, {})
    
    operator_parameter['Status'] = 'Error'
    assert operator_parameter == err.value.args[0]

def test_comprehend_error_handling(comprehend_get_key_phrases):
    import comprehend.key_phrases.get_key_phrases as lambda_function
    import MediaInsightsEngineLambdaHelper
    import helper

    operator_parameter = helper.get_operator_parameter({
        'comprehend_phrases_job_id': 'comprehend_phrases_job_id'
    })

    comprehend_get_key_phrases.add_client_error(
        'list_key_phrases_detection_jobs',
        expected_params = {
            'Filter': {
                'JobName': 'comprehend_phrases_job_id'
            }
        },
        service_message = 'stubbed_error_message'
    )

    with pytest.raises(MediaInsightsEngineLambdaHelper.MasExecutionError) as err:
        lambda_function.lambda_handler(operator_parameter, {})
    
    operator_parameter['Status'] = 'Error'
    assert operator_parameter == err.value.args[0]
    assert 'stubbed_error_message' in err.value.args[0]['MetaData']['comprehend_error']

def test_comprehend_job_in_progress(comprehend_get_key_phrases):
    import comprehend.key_phrases.get_key_phrases as lambda_function
    import MediaInsightsEngineLambdaHelper
    import helper

    # IN_PROGRESS
    operator_parameter = helper.get_operator_parameter({
        'comprehend_phrases_job_id': 'comprehend_phrases_job_id'
    })

    comprehend_get_key_phrases.add_response(
        'list_key_phrases_detection_jobs',
        expected_params = {
            'Filter': {
                'JobName': 'comprehend_phrases_job_id'
            }
        },
        service_response = {
            'KeyPhrasesDetectionJobPropertiesList': [{
                'JobStatus': 'IN_PROGRESS'
            }]
        }
    )

    response = lambda_function.lambda_handler(operator_parameter, {})
    assert response['Status'] == 'Executing'

    # SUBMITTED
    comprehend_get_key_phrases.add_response(
        'list_key_phrases_detection_jobs',
        expected_params = {
            'Filter': {
                'JobName': 'comprehend_phrases_job_id'
            }
        },
        service_response = {
            'KeyPhrasesDetectionJobPropertiesList': [{
                'JobStatus': 'SUBMITTED'
            }]
        }
    )

    response = lambda_function.lambda_handler(operator_parameter, {})
    assert response['Status'] == 'Executing'

    # UNKNOWN STATUS
    comprehend_get_key_phrases.add_response(
        'list_key_phrases_detection_jobs',
        expected_params = {
            'Filter': {
                'JobName': 'comprehend_phrases_job_id'
            }
        },
        service_response = {
            'KeyPhrasesDetectionJobPropertiesList': [{
                'JobStatus': 'UNKNOWN',
                'Message': 'test_message'
            }]
        }
    )
    with pytest.raises(MediaInsightsEngineLambdaHelper.MasExecutionError) as err:
        response = lambda_function.lambda_handler(operator_parameter, {})
    assert err.value.args[0]['Status'] == 'Error'
    assert 'comprehend returned as failed: ' in err.value.args[0]['MetaData']['comprehend_error']

def test_comprehend_job_error(comprehend_get_key_phrases, s3_get_key_phrases):
    import comprehend.key_phrases.get_key_phrases as lambda_function
    import MediaInsightsEngineLambdaHelper
    import helper

    operator_parameter = helper.get_operator_parameter({
        'comprehend_phrases_job_id': 'comprehend_phrases_job_id'
    })

    stub_comprehend_client(comprehend_get_key_phrases)
    stub_s3_response(
        s3_get_key_phrases,
        'bucket_name',
        'comprehend/key_name',
        'hello world'
    )
    original_open = tar.open
    tar.open = MagicMock()

    original_dataplane = lambda_function.DataPlane.store_asset_metadata
    lambda_function.DataPlane.store_asset_metadata = MagicMock(
        return_value = {
        }
    )
    with pytest.raises(MediaInsightsEngineLambdaHelper.MasExecutionError) as err:
        response = lambda_function.lambda_handler(operator_parameter, {})
        assert response['Status'] == 'Error'
        assert 'Unable to store entity data' in response['MetaData']['comprehend_error']
    assert tar.open.call_count == 1
    assert lambda_function.DataPlane.store_asset_metadata.call_count == 1
    assert lambda_function.DataPlane.store_asset_metadata.call_args[0][0] == 'testAssetId'
    assert lambda_function.DataPlane.store_asset_metadata.call_args[0][1] == 'key_phrases'
    assert lambda_function.DataPlane.store_asset_metadata.call_args[0][2] == 'testWorkflowId'
    assert lambda_function.DataPlane.store_asset_metadata.call_args[0][3] == {'LanguageCode': 'en-US', 'Results': []}

    
    tar.open = original_open
    lambda_function.DataPlane.store_asset_metadata = original_dataplane

def test_comprehend_job_completed(comprehend_get_key_phrases, s3_get_key_phrases):
    import comprehend.key_phrases.get_key_phrases as lambda_function
    import helper

    operator_parameter = helper.get_operator_parameter({
        'comprehend_phrases_job_id': 'comprehend_phrases_job_id'
    })

    stub_comprehend_client(comprehend_get_key_phrases)
    stub_s3_response(
        s3_get_key_phrases,
        'bucket_name',
        'comprehend/key_name',
        'hello world'
    )
    original_open = tar.open
    tar.open = MagicMock()

    original_dataplane = lambda_function.DataPlane.store_asset_metadata
    lambda_function.DataPlane.store_asset_metadata = MagicMock(
        return_value = {
            'Status': 'Success'
        }
    )

    response = lambda_function.lambda_handler(operator_parameter, {})
    assert response['Status'] == 'Complete'
    assert response['MetaData']['output_uri'] == 's3://bucket_name/comprehend/key_name'
    assert tar.open.call_count == 1
    assert lambda_function.DataPlane.store_asset_metadata.call_count == 1
    assert lambda_function.DataPlane.store_asset_metadata.call_args[0][0] == 'testAssetId'
    assert lambda_function.DataPlane.store_asset_metadata.call_args[0][1] == 'key_phrases'
    assert lambda_function.DataPlane.store_asset_metadata.call_args[0][2] == 'testWorkflowId'
    assert lambda_function.DataPlane.store_asset_metadata.call_args[0][3] == {'LanguageCode': 'en-US', 'Results': []}

    
    tar.open = original_open
    lambda_function.DataPlane.store_asset_metadata = original_dataplane