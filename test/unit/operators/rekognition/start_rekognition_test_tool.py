# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import pytest
from botocore.stub import Stubber
from unittest.mock import MagicMock


class StartRekognitionTestTool:
    def __init__(
        self,
        subject_under_test,
        lambda_handler,
        MasExecutionError,
        parameter_helper,
        error_key,
        image_rekognition_function_name,
        video_rekognition_function_name,
        image_stub_function=None,
        video_stub_function=None
    ):

        self.subject_under_test = subject_under_test
        self.lambda_handler = lambda_handler
        self.MasExecutionError = MasExecutionError
        self.parameter_helper = parameter_helper
        self.image_rekognition_function_name = image_rekognition_function_name
        self.video_rekognition_function_name = video_rekognition_function_name
        self.image_stub_function = image_stub_function
        self.video_stub_function = video_stub_function
        self.error_key = error_key
        self.original_dataplane_function = None

    def start_mock(self, mock_response={}):
        self.original_dataplane_function = self.subject_under_test.DataPlane.store_asset_metadata
        self.subject_under_test.DataPlane.store_asset_metadata = MagicMock(return_value=mock_response)

    def reset_subject_under_test(self):
        self.subject_under_test.output_object = self.subject_under_test.OutputHelper(self.subject_under_test.operator_name)
        self.subject_under_test.DataPlane.store_asset_metadata = self.original_dataplane_function

    def default_image_stub_function(self, stub):
        image_input = {
            'Image': {
                'S3Object': {
                    'Bucket': 'test_bucket',
                    'Name': 'test_key.png'
                }
            }
        }
        image_output = {}
        stub.add_response(
            self.image_rekognition_function_name,
            expected_params=image_input,
            service_response=image_output
        )

    def default_video_stub_function(self, stub):
        video_input = {
            'Video': {
                'S3Object': {
                    'Bucket': 'test_bucket',
                    'Name': 'test_key.mp4'
                }
            },
            'NotificationChannel': {
                'SNSTopicArn': 'testRekognitionSNSTopicArn',
                'RoleArn': 'testRekognitionRoleArn'
            }
        }

        video_output = {'JobId': 'testJobId'}

        stub.add_response(
            self.video_rekognition_function_name,
            expected_params=video_input,
            service_response=video_output
        )

    def run_tests(self):
        with Stubber(self.subject_under_test.rek) as stubber:
            stubber.assert_no_pending_responses()
            self.test_parameter_validation()
            self.test_process_video(stubber)
            self.test_process_image_empty_status(stubber)
            self.test_process_image_invalid_status(stubber)
            self.test_process_image_failed_status(stubber)
            self.test_process_image_success_status(stubber)

    def test_parameter_validation(self):
        with pytest.raises(self.MasExecutionError) as err:
            self.lambda_handler({}, {})
        assert err.value.args[0]['Status'] == 'Error'
        assert err.value.args[0]['MetaData'][self.error_key] == 'No valid inputs'
        self.reset_subject_under_test()

    def test_process_video(self, stub):
        input_paramter = self.parameter_helper.get_operator_parameter(
            input={
                'Media': {
                    'Video': {
                        'S3Bucket': 'test_bucket',
                        'S3Key': 'test_key.mp4'
                    }
                }
            }
        )
        if self.video_stub_function is not None:
            self.video_stub_function(stub)
        else:
            self.default_video_stub_function(stub)

        response = self.lambda_handler(input_paramter, {})
        assert response['Status'] == 'Executing'
        assert response['MetaData']['JobId'] == 'testJobId'
        assert response['MetaData']['AssetId'] == 'testAssetId'
        assert response['MetaData']['WorkflowExecutionId'] == 'testWorkflowId'
        self.reset_subject_under_test()

    def test_process_image_empty_status(self, stub):
        self.start_mock({
        })
        input_paramter = self.parameter_helper.get_operator_parameter(
            input={
                'Media': {
                    'Image': {
                        'S3Bucket': 'test_bucket',
                        'S3Key': 'test_key.png'
                    }
                }
            }
        )

        if self.image_stub_function is not None:
            self.image_stub_function(stub)
        else:
            self.default_image_stub_function(stub)

        with pytest.raises(self.MasExecutionError) as err:
            self.lambda_handler(input_paramter, {})
        assert err.value.args[0]['Status'] == 'Error'
        assert err.value.args[0]['MetaData'][self.error_key] == 'Unable to upload metadata for asset: testAssetId'
        assert self.subject_under_test.DataPlane.store_asset_metadata.call_count == 1
        assert self.subject_under_test.DataPlane.store_asset_metadata.call_args[0][0] == 'testAssetId'
        assert self.subject_under_test.DataPlane.store_asset_metadata.call_args[0][1] == 'testOperatorName'
        assert self.subject_under_test.DataPlane.store_asset_metadata.call_args[0][2] == 'testWorkflowId'
        assert self.subject_under_test.DataPlane.store_asset_metadata.call_args[0][3] == {}
        self.reset_subject_under_test()

    def test_process_image_failed_status(self, stub):
        self.start_mock({
            'Status': 'Failed'
        })
        input_paramter = self.parameter_helper.get_operator_parameter(
            input={
                'Media': {
                    'Image': {
                        'S3Bucket': 'test_bucket',
                        'S3Key': 'test_key.png'
                    }
                }
            }
        )

        if self.image_stub_function is not None:
            self.image_stub_function(stub)
        else:
            self.default_image_stub_function(stub)

        with pytest.raises(self.MasExecutionError) as err:
            self.lambda_handler(input_paramter, {})
        assert err.value.args[0]['Status'] == 'Error'
        assert err.value.args[0]['MetaData'][self.error_key] == 'Unable to upload metadata for asset: testAssetId'
        assert self.subject_under_test.DataPlane.store_asset_metadata.call_count == 1
        assert self.subject_under_test.DataPlane.store_asset_metadata.call_args[0][0] == 'testAssetId'
        assert self.subject_under_test.DataPlane.store_asset_metadata.call_args[0][1] == 'testOperatorName'
        assert self.subject_under_test.DataPlane.store_asset_metadata.call_args[0][2] == 'testWorkflowId'
        assert self.subject_under_test.DataPlane.store_asset_metadata.call_args[0][3] == {}
        self.reset_subject_under_test()

    def test_process_image_invalid_status(self, stub):
        self.start_mock({
            'Status': 'Invalid'
        })
        input_paramter = self.parameter_helper.get_operator_parameter(
            input={
                'Media': {
                    'Image': {
                        'S3Bucket': 'test_bucket',
                        'S3Key': 'test_key.png'
                    }
                }
            }
        )

        if self.image_stub_function is not None:
            self.image_stub_function(stub)
        else:
            self.default_image_stub_function(stub)

        with pytest.raises(self.MasExecutionError) as err:
            self.lambda_handler(input_paramter, {})
        assert err.value.args[0]['Status'] == 'Error'
        assert err.value.args[0]['MetaData'][self.error_key] == 'Unable to upload metadata for asset: testAssetId'
        assert self.subject_under_test.DataPlane.store_asset_metadata.call_count == 1
        assert self.subject_under_test.DataPlane.store_asset_metadata.call_args[0][0] == 'testAssetId'
        assert self.subject_under_test.DataPlane.store_asset_metadata.call_args[0][1] == 'testOperatorName'
        assert self.subject_under_test.DataPlane.store_asset_metadata.call_args[0][2] == 'testWorkflowId'
        assert self.subject_under_test.DataPlane.store_asset_metadata.call_args[0][3] == {}
        self.reset_subject_under_test()

    def test_process_image_success_status(self, stub):
        self.start_mock({
            'Status': 'Success'
        })
        input_paramter = self.parameter_helper.get_operator_parameter(
            input={
                'Media': {
                    'Image': {
                        'S3Bucket': 'test_bucket',
                        'S3Key': 'test_key.png'
                    }
                }
            }
        )

        if self.image_stub_function is not None:
            self.image_stub_function(stub)
        else:
            self.default_image_stub_function(stub)

        response = self.lambda_handler(input_paramter, {})
        assert response['Status'] == 'Complete'
        assert self.subject_under_test.DataPlane.store_asset_metadata.call_count == 1
        assert self.subject_under_test.DataPlane.store_asset_metadata.call_args[0][0] == 'testAssetId'
        assert self.subject_under_test.DataPlane.store_asset_metadata.call_args[0][1] == 'testOperatorName'
        assert self.subject_under_test.DataPlane.store_asset_metadata.call_args[0][2] == 'testWorkflowId'
        assert self.subject_under_test.DataPlane.store_asset_metadata.call_args[0][3] == {}
        self.reset_subject_under_test()
