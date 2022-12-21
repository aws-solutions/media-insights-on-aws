import pytest

def test_input_parameter():
    import mediaconvert.get_media_convert as lambda_function
    import MediaInsightsEngineLambdaHelper
    import helper
    
    # Empty Mediaconvert Job Id
    operator_parameter = helper.get_operator_parameter(
        metadata={
            'MediaconvertJobId': 'testJobId',
            'MediaconvertInputFile': 'testInputFile'
        }
    )
    del operator_parameter['MetaData']['MediaconvertJobId']
    with pytest.raises(MediaInsightsEngineLambdaHelper.MasExecutionError) as err:
        lambda_function.lambda_handler(operator_parameter, {})
    assert err.value.args[0]['MetaData']['MediaconvertError'] == "Missing a required metadata key 'MediaconvertJobId'"

    # Empty Mediaconvert Input File
    operator_parameter = helper.get_operator_parameter(
        metadata={
            'MediaconvertJobId': 'testJobId',
            'MediaconvertInputFile': 'testInputFile'
        }
    )
    del operator_parameter['MetaData']['MediaconvertInputFile']
    with pytest.raises(MediaInsightsEngineLambdaHelper.MasExecutionError) as err:
        lambda_function.lambda_handler(operator_parameter, {})
    assert err.value.args[0]['MetaData']['MediaconvertError'] == "Missing a required metadata key 'MediaconvertInputFile'"

def test_job_unknown_status(mediaconvert_get_stub):
    import mediaconvert.get_media_convert as lambda_function
    import MediaInsightsEngineLambdaHelper
    import helper

    mediaconvert_get_stub.add_response(
        'get_job',
        expected_params = {
            'Id': 'testJobId'
        },
        service_response = {
            'Job': {
                'Status': 'UNKNOWN',
                'Role': 'testMediaconvertRole',
                'Settings': {}
            }
        }
    )

    operator_parameter = helper.get_operator_parameter(
        metadata={
            'MediaconvertJobId': 'testJobId',
            'MediaconvertInputFile': 'testInputFile'
        }
    )
    with pytest.raises(MediaInsightsEngineLambdaHelper.MasExecutionError) as err:
        lambda_function.lambda_handler(operator_parameter, {})
    assert err.value.args[0]['Status'] == 'Error'
    assert err.value.args[0]['MetaData']['MediaconvertError'] == "Unhandled exception, unable to get status from mediaconvert: {'Job': {'Status': 'UNKNOWN', 'Role': 'testMediaconvertRole', 'Settings': {}}}"
    assert err.value.args[0]['MetaData']['MediaconvertJobId'] == 'testJobId'

def test_job_in_progress(mediaconvert_get_stub):
    import mediaconvert.get_media_convert as lambda_function
    import helper

    mediaconvert_get_stub.add_response(
        'get_job',
        expected_params = {
            'Id': 'testJobId'
        },
        service_response = {
            'Job': {
                'Status': 'IN_PROGRESS',
                'Role': 'testMediaconvertRole',
                'Settings': {}
            }
        }
    )

    operator_parameter = helper.get_operator_parameter(
        metadata={
            'MediaconvertJobId': 'testJobId',
            'MediaconvertInputFile': 'testInputFile'
        }
    )
    response = lambda_function.lambda_handler(operator_parameter, {})
    assert response['Status'] == 'Executing'
    assert response['MetaData']['MediaconvertJobId'] == 'testJobId'
    assert response['MetaData']['MediaconvertInputFile'] == 'testInputFile'
    assert response['MetaData']['AssetId'] == 'testAssetId'
    assert response['MetaData']['WorkflowExecutionId'] == 'testWorkflowId'

def test_job_completed(mediaconvert_get_stub):
    import mediaconvert.get_media_convert as lambda_function
    import helper

    mediaconvert_get_stub.add_response(
        'get_job',
        expected_params = {
            'Id': 'testJobId'
        },
        service_response = {
            'Job': {
                'Status': 'COMPLETE',
                'Role': 'testMediaconvertRole',
                'Settings': {
                    'OutputGroups': [{
                        'OutputGroupSettings': {
                            'FileGroupSettings': {
                                'Destination': 's3://bucket_name/folder/file'
                            }
                        },
                        'Outputs': [{
                            'Extension': 'testExtension',
                            'NameModifier': 'testModifier'
                        }]
                    }]
                }
            }
        }
    )

    operator_parameter = helper.get_operator_parameter(
        metadata={
            'MediaconvertJobId': 'testJobId',
            'MediaconvertInputFile': 'testInputFile'
        }
    )
    response = lambda_function.lambda_handler(operator_parameter, {})
    assert response['Status'] == 'Complete'
    assert response['MetaData']['MediaconvertJobId'] == 'testJobId'
    assert response['MetaData']['MediaconvertInputFile'] == 'testInputFile'
    assert response['Media']['Audio'] == { 'S3Bucket': 'bucket_name', 'S3Key': 'folder/testInputFiletestModifier.testExtension' }
    