# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from helper import *
from unittest.mock import MagicMock

mocked_app_functions = {
    'send_response': 'ok',
    'create_operation': {'StageName': 'test_stage'},
    'create_stage': 'ok',
    'create_workflow': {'StateMachineArn': 'stateMachineArn'}
}

def mock_app_functions():
    import app
    response = {}
    for function_name, mock_result in mocked_app_functions.items():
        response['original_' + function_name] = getattr(app, function_name)
        response[function_name] = MagicMock(return_value = mock_result)
        setattr(app, function_name, response[function_name])
    return response

def restore_mock(mock):
    import app
    for function_name in mocked_app_functions:
        setattr(app, function_name, mock['original_' + function_name])

def test_workflow_custom_resource_invalid_resource(test_client):
    mock = mock_app_functions()
    test_client.lambda_.invoke(
        'WorkflowCustomResource',
        {
            'ResourceProperties': {
                'ResourceType': 'invalid_resource'
            }
        }
    )
    assert mock['send_response'].call_count == 1
    assert mock['send_response'].call_args[0][2] == 'FAILED'
    assert mock['send_response'].call_args[0][3] == {"Message": "Unexpected resource type received from CloudFormation"}
    restore_mock(mock)

def test_workflow_custom_resource_operation_resource(test_client):
    mock = mock_app_functions()
    test_client.lambda_.invoke(
        'WorkflowCustomResource',
        {
            'RequestType': 'Create',
            'ResourceProperties': {
                'Name': 'testOperationName',
                'ResourceType': 'Operation',
                'Configuration': {
                    'Enabled': 'true'
                }
            }
        }
    )
    assert mock['create_operation'].call_count == 1
    assert mock['create_operation'].call_args[0][0] == {
        'Name': 'testOperationName',
        'ResourceType': 'Operation',
        'Configuration': {
            'Enabled': True
        }
    }
    assert mock['send_response'].call_count == 1
    assert mock['send_response'].call_args[0][2] == 'SUCCESS'
    assert mock['send_response'].call_args[0][3]['Message'] == 'Resource creation successful!'
    assert mock['send_response'].call_args[0][3]['Name'] == 'testOperationName'
    assert mock['send_response'].call_args[0][3]['StageName'] == 'test_stage'
    restore_mock(mock)

def test_workflow_custom_resource_stage_resource(test_client):
    mock = mock_app_functions()
    test_client.lambda_.invoke(
        'WorkflowCustomResource',
        {
            'RequestType': 'Create',
            'ResourceProperties': {
                'Name': 'testStageName',
                'ResourceType': 'Stage'
            }
        }
    )
    assert mock['create_stage'].call_count == 1
    assert mock['create_stage'].call_args[0][0] == {
        'Name': 'testStageName',
        'ResourceType': 'Stage'
    }
    assert mock['send_response'].call_count == 1
    assert mock['send_response'].call_args[0][2] == 'SUCCESS'
    assert mock['send_response'].call_args[0][3]['Message'] == 'Resource creation successful!'
    assert mock['send_response'].call_args[0][3]['Name'] == 'testStageName'
    restore_mock(mock)

def test_workflow_custom_resource_workflow_resource(test_client):
    mock = mock_app_functions()
    test_client.lambda_.invoke(
        'WorkflowCustomResource',
        {
            'RequestType': 'Create',
            'ResourceProperties': {
                'Name': 'testWorkflowName',
                'ResourceType': 'Workflow',
                'Stages': json.dumps({'Name': 'stage'})
            }
        }
    )
    assert mock['create_workflow'].call_count == 1
    assert mock['create_workflow'].call_args[0][0] == 'custom-resource'
    assert mock['create_workflow'].call_args[0][1] == {
        'Name': 'testWorkflowName',
        'ResourceType': 'Workflow',
        'Stages': {'Name':'stage'}
    }

    assert mock['send_response'].call_count == 1
    assert mock['send_response'].call_args[0][2] == 'SUCCESS'
    assert mock['send_response'].call_args[0][3]['Message'] == 'Resource creation successful!'
    assert mock['send_response'].call_args[0][3]['Name'] == 'testWorkflowName'
    assert mock['send_response'].call_args[0][3]['StateMachineArn'] == 'stateMachineArn'
    restore_mock(mock)
