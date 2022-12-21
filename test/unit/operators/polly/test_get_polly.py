import pytest

def test_input_parameter():
    import polly.get_polly as lambda_function
    import MediaInsightsEngineLambdaHelper
    import helper
    
    operator_parameter = helper.get_operator_parameter()
    
    with pytest.raises(MediaInsightsEngineLambdaHelper.MasExecutionError) as err:
        lambda_function.lambda_handler(operator_parameter, {})
    assert err.value.args[0]['Status'] == 'Error'
    assert err.value.args[0]['MetaData']['PollyError'] == "Missing a required metadata key 'PollyJobId'"

def test_polly_get_speech_task_error(polly_get_stub):
    import polly.get_polly as lambda_function
    import MediaInsightsEngineLambdaHelper
    import helper
    
    operator_parameter = helper.get_operator_parameter(
        metadata = {
            'PollyJobId': 'testPollyJobId'
        }
    )
    
    polly_get_stub.add_client_error('get_speech_synthesis_task')

    with pytest.raises(MediaInsightsEngineLambdaHelper.MasExecutionError) as err:
        lambda_function.lambda_handler(operator_parameter, {})
    assert err.value.args[0]['Status'] == 'Error'
    assert err.value.args[0]['MetaData']['PollyError'] == "Unable to get response from polly: An error occurred () when calling the GetSpeechSynthesisTask operation: "

def test_polly_job_not_completed(polly_get_stub):
    import polly.get_polly as lambda_function
    import MediaInsightsEngineLambdaHelper
    import helper
    
    operator_parameter = helper.get_operator_parameter(
        metadata = {
            'PollyJobId': 'testPollyJobId'
        }
    )

    statuses_to_check = [
        'inProgress',
        'scheduled'
    ]
    for status in statuses_to_check:
        polly_get_stub.add_response(
            'get_speech_synthesis_task',
            expected_params = {
                'TaskId': 'testPollyJobId'
            },
            service_response = {
                'SynthesisTask': {
                    'TaskStatus': status,
                    'TaskId': 'testPollyJobId'
                }
            }
        )

        response = lambda_function.lambda_handler(operator_parameter, {})
        assert response['Status'] == 'Executing'
        assert response['MetaData']['PollyJobId'] == 'testPollyJobId'
        assert response['MetaData']['AssetId'] == 'testAssetId'
        assert response['MetaData']['WorkflowExecutionId'] == 'testWorkflowId'

def test_polly_job_failed_and_no_status(polly_get_stub):
    import polly.get_polly as lambda_function
    import MediaInsightsEngineLambdaHelper
    import helper
    
    operator_parameter = helper.get_operator_parameter(
        metadata = {
            'PollyJobId': 'testPollyJobId'
        }
    )
    statuses_to_check = [
        'failed',
        'unknown_status'
    ]
    for status in statuses_to_check:
        polly_get_stub.add_response(
            'get_speech_synthesis_task',
            expected_params = {
                'TaskId': 'testPollyJobId'
            },
            service_response = {
                'SynthesisTask': {
                    'TaskStatus': status,
                    'TaskId': 'testPollyJobId',
                    'TaskStatusReason': 'task has failed test'
                }
            }
        )
        with pytest.raises(MediaInsightsEngineLambdaHelper.MasExecutionError) as err:
            lambda_function.lambda_handler(operator_parameter, {})
        assert err.value.args[0]['Status'] == 'Error'
        assert err.value.args[0]['MetaData']['PollyError'] == 'Polly returned as failed: task has failed test'

def test_polly_job_completed(polly_get_stub):
    import polly.get_polly as lambda_function
    import MediaInsightsEngineLambdaHelper
    import helper
    
    operator_parameter = helper.get_operator_parameter(
        metadata = {
            'PollyJobId': 'testPollyJobId'
        }
    )
    polly_get_stub.add_response(
        'get_speech_synthesis_task',
        expected_params = {
            'TaskId': 'testPollyJobId'
        },
        service_response = {
            'SynthesisTask': {
                'TaskStatus': 'completed',
                'TaskId': 'testPollyJobId',
                'OutputUri': 's3://aws/bucket_name/folder_name/file_name'
            }
        }
    )
    response = lambda_function.lambda_handler(operator_parameter, {})
    assert response['Status'] == 'Complete'
    assert response['Media']['Audio'] == {"S3Bucket": 'bucket_name', "S3Key": 'folder_name/file_name'}
    assert response['MetaData']['PollyJobId'] == 'testPollyJobId'
