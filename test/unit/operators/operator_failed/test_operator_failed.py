# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import pytest

def get_input_parameter():
    return {
        'Outputs': {
            'Error': Exception('test_error')
        },
        'Name': 'testName',
        'AssetId': 'testAssetId',
        'WorkflowExecutionId': 'testWorkflowExecutionId',
        'Input': 'testInput',
        'Configuration': 'testConfiguration'
    }

def test_invalid_input():
    import operator_failed.operator_failed as lambda_function

    response = lambda_function.lambda_handler({'test':'input'}, {})
    assert response == {'test':'input'}

def test_parameter_validation():
    import operator_failed.operator_failed as lambda_function
    keys_to_test = [
        'Name', 'AssetId', 'WorkflowExecutionId', 'Input', 'Configuration'
    ]
    for key in keys_to_test:
        input_parameter = get_input_parameter()
        del input_parameter[key]
        with pytest.raises(Exception):
            lambda_function.lambda_handler(input_parameter, {})

def test_with_valid_parameters():
    import operator_failed.operator_failed as lambda_function
    input_parameter = get_input_parameter()
    response = lambda_function.lambda_handler(input_parameter, {})
    assert response['Status'] == 'Error'
    assert response['MetaData']['testNameError'].args[0] == 'test_error'
