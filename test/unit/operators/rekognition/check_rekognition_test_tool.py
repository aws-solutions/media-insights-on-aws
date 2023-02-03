import pytest
from botocore.stub import Stubber
from unittest.mock import MagicMock


class CheckRekognitionTestTool:
    def __init__(
        self,
        subject_under_test,
        lambda_handler,
        MasExecutionError,
        parameter_helper,
        rekognition_function_name,
        error_key
    ) -> None:
        self.subject_under_test = subject_under_test
        self.lambda_handler = lambda_handler
        self.MasExecutionError = MasExecutionError
        self.parameter_helper = parameter_helper
        self.rekognition_function_name = rekognition_function_name
        self.error_key = error_key
        self.original_dataplane_function = None

    def start_mock(self, mock_response={}):
        self.original_dataplane_function = self.subject_under_test.DataPlane.store_asset_metadata
        self.subject_under_test.DataPlane.store_asset_metadata = MagicMock(return_value=mock_response)

    def reset_subject_under_test(self):
        self.subject_under_test.output_object = self.subject_under_test.OutputHelper(self.subject_under_test.operator_name)
        self.subject_under_test.DataPlane.store_asset_metadata = self.original_dataplane_function

    def run_tests(self):
        with Stubber(self.subject_under_test.rek) as stubber:
            stubber.assert_no_pending_responses()
            self.test_empty_event_status()
            self.test_complete_status()
            self.test_empty_job_id()
            self.test_job_status_in_progress(stubber)
            self.test_job_status_failed(stubber)
            self.test_job_status_succeeded_non_paginated(stubber)
            self.test_job_status_invalid_non_paginated(stubber)
            self.test_job_status_succeeded_paginated(stubber)

    def test_empty_event_status(self):
        with pytest.raises(self.MasExecutionError) as err:
            self.lambda_handler({}, {})
        assert err.value.args[0]['Status'] == 'Error'
        assert err.value.args[0]['MetaData'][self.error_key] == "Missing key 'Status'"
        self.reset_subject_under_test()

    def test_complete_status(self):
        input_parameter = self.parameter_helper.get_operator_parameter(
            metadata={
                'AssetId': 'testAssetId'
            }
        )
        input_parameter['Status'] = 'Complete'
        response = self.lambda_handler(input_parameter, {})
        assert response['Status'] == 'Complete'
        self.reset_subject_under_test()

    def test_empty_job_id(self):
        input_parameter = self.parameter_helper.get_operator_parameter(
            metadata={
                'AssetId': 'testAssetId'
            }
        )
        with pytest.raises(self.MasExecutionError) as err:
            self.lambda_handler(input_parameter, {})
        assert err.value.args[0]['Status'] == 'Error'
        assert err.value.args[0]['MetaData'][self.error_key] == "Missing a required metadata key 'JobId'"
        self.reset_subject_under_test()

    def test_job_status_in_progress(self, stub):
        self.start_mock()

        stub.add_response(
            self.rekognition_function_name,
            expected_params={
                'JobId': 'testJobId',
                'NextToken': ''
            },
            service_response={
                'JobStatus': 'IN_PROGRESS'
            }
        )
        input_parameter = self.parameter_helper.get_operator_parameter(
            metadata={
                'AssetId': 'testAssetId',
                'JobId': 'testJobId',
                'WorkflowExecutionId': 'testWorkflowId'
            }
        )
        response = self.lambda_handler(input_parameter, {})
        assert response['Status'] == 'Executing'
        assert response['MetaData']['JobId'] == 'testJobId'
        assert response['MetaData']['AssetId'] == 'testAssetId'
        assert response['MetaData']['WorkflowExecutionId'] == 'testWorkflowId'
        self.reset_subject_under_test()

    def test_job_status_failed(self, stub):
        self.start_mock()

        stub.add_response(
            self.rekognition_function_name,
            expected_params={
                'JobId': 'testJobId',
                'NextToken': ''
            },
            service_response={
                'JobStatus': 'FAILED',
                'StatusMessage': 'test_job_failed_message'
            }
        )
        input_parameter = self.parameter_helper.get_operator_parameter(
            metadata={
                'AssetId': 'testAssetId',
                'JobId': 'testJobId',
                'WorkflowExecutionId': 'testWorkflowId'
            }
        )
        with pytest.raises(self.MasExecutionError) as err:
            self.lambda_handler(input_parameter, {})
        assert err.value.args[0]['Status'] == 'Error'
        assert err.value.args[0]['MetaData']['JobId'] == 'testJobId'
        assert err.value.args[0]['MetaData'][self.error_key] == 'test_job_failed_message'
        self.reset_subject_under_test()

    def test_job_status_succeeded_non_paginated(self, stub):
        self.start_mock({
            'Status': 'Success'
        })

        stub.add_response(
            self.rekognition_function_name,
            expected_params={
                'JobId': 'testJobId',
                'NextToken': ''
            },
            service_response={
                'JobStatus': 'SUCCEEDED'
            }
        )
        input_parameter = self.parameter_helper.get_operator_parameter(
            metadata={
                'AssetId': 'testAssetId',
                'JobId': 'testJobId',
                'WorkflowExecutionId': 'testWorkflowId'
            }
        )
        response = self.lambda_handler(input_parameter, {})
        assert response['Status'] == 'Complete'
        assert response['MetaData']['JobId'] == 'testJobId'
        assert self.subject_under_test.DataPlane.store_asset_metadata.call_count == 1
        assert self.subject_under_test.DataPlane.store_asset_metadata.call_args[1]['asset_id'] == 'testAssetId'
        assert self.subject_under_test.DataPlane.store_asset_metadata.call_args[1]['operator_name'] == 'testOperatorName'
        assert self.subject_under_test.DataPlane.store_asset_metadata.call_args[1]['workflow_id'] == 'testWorkflowId'
        assert self.subject_under_test.DataPlane.store_asset_metadata.call_args[1]['results'] == {'JobStatus': 'SUCCEEDED'}
        self.reset_subject_under_test()

    def test_job_status_invalid_non_paginated(self, stub):
        self.start_mock({
            'test': 'error'
        })

        stub.add_response(
            self.rekognition_function_name,
            expected_params={
                'JobId': 'testJobId',
                'NextToken': ''
            },
            service_response={
                'JobStatus': 'SUCCEEDED'
            }
        )
        input_parameter = self.parameter_helper.get_operator_parameter(
            metadata={
                'AssetId': 'testAssetId',
                'JobId': 'testJobId',
                'WorkflowExecutionId': 'testWorkflowId'
            }
        )
        with pytest.raises(self.MasExecutionError) as err:
            self.lambda_handler(input_parameter, {})
        assert err.value.args[0]['Status'] == 'Error'
        assert err.value.args[0]['MetaData'][self.error_key] == "Unable to upload metadata for testAssetId: {'test': 'error'}"
        assert err.value.args[0]['MetaData']['JobId'] == 'testJobId'
        assert self.subject_under_test.DataPlane.store_asset_metadata.call_count == 1
        assert self.subject_under_test.DataPlane.store_asset_metadata.call_args[1]['asset_id'] == 'testAssetId'
        assert self.subject_under_test.DataPlane.store_asset_metadata.call_args[1]['operator_name'] == 'testOperatorName'
        assert self.subject_under_test.DataPlane.store_asset_metadata.call_args[1]['workflow_id'] == 'testWorkflowId'
        assert self.subject_under_test.DataPlane.store_asset_metadata.call_args[1]['results'] == {'JobStatus': 'SUCCEEDED'}
        self.reset_subject_under_test()

    def test_job_status_succeeded_paginated(self, stub):
        self.start_mock({
            'Status': 'Success'
        })

        stub.add_response(
            self.rekognition_function_name,
            expected_params={
                'JobId': 'testJobId',
                'NextToken': 'next_token'
            },
            service_response={
                'JobStatus': 'SUCCEEDED',
                'NextToken': 'next_token2'
            }
        )
        stub.add_response(
            self.rekognition_function_name,
            expected_params={
                'JobId': 'testJobId',
                'NextToken': 'next_token2'
            },
            service_response={
                'JobStatus': 'SUCCEEDED',
            }
        )
        input_parameter = self.parameter_helper.get_operator_parameter(
            metadata={
                'AssetId': 'testAssetId',
                'JobId': 'testJobId',
                'WorkflowExecutionId': 'testWorkflowId',
                'PageToken': 'next_token'
            }
        )
        response = self.lambda_handler(input_parameter, {})
        assert response['Status'] == 'Complete'
        assert response['MetaData']['JobId'] == 'testJobId'
        assert self.subject_under_test.DataPlane.store_asset_metadata.call_count == 2
        assert self.subject_under_test.DataPlane.store_asset_metadata.call_args_list[0][1]['asset_id'] == 'testAssetId'
        assert self.subject_under_test.DataPlane.store_asset_metadata.call_args_list[0][1]['operator_name'] == 'testOperatorName'
        assert self.subject_under_test.DataPlane.store_asset_metadata.call_args_list[0][1]['workflow_id'] == 'testWorkflowId'
        assert self.subject_under_test.DataPlane.store_asset_metadata.call_args_list[0][1]['results'] == {'JobStatus': 'SUCCEEDED', 'NextToken': 'next_token2'}
        assert self.subject_under_test.DataPlane.store_asset_metadata.call_args_list[0][1]['paginate'] is True
        assert self.subject_under_test.DataPlane.store_asset_metadata.call_args_list[0][1]['end'] is False
        assert self.subject_under_test.DataPlane.store_asset_metadata.call_args_list[1][1]['asset_id'] == 'testAssetId'
        assert self.subject_under_test.DataPlane.store_asset_metadata.call_args_list[1][1]['operator_name'] == 'testOperatorName'
        assert self.subject_under_test.DataPlane.store_asset_metadata.call_args_list[1][1]['workflow_id'] == 'testWorkflowId'
        assert self.subject_under_test.DataPlane.store_asset_metadata.call_args_list[1][1]['results'] == {'JobStatus': 'SUCCEEDED'}
        assert self.subject_under_test.DataPlane.store_asset_metadata.call_args_list[1][1]['paginate'] is True
        assert self.subject_under_test.DataPlane.store_asset_metadata.call_args_list[1][1]['end'] is True
        self.reset_subject_under_test()
