# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import json
from botocore.stub import ANY

def test_deserialize_non_list_dict():
    # imports
    import workflowstream

    # test parameters
    data_param = 'testData'

    result = workflowstream.deserialize(data_param)

    # assertions
    assert result == data_param

def test_deserialize_dict_success():
    # imports
    import workflowstream

    #test parameters
    data_param = {
        'S': 'World'
    }
    result = workflowstream.deserialize(data_param)

    # assertions
    assert result == 'World'

def test_deserialize_dict_error_handling():
        # imports
    import workflowstream

    #test parameters
    data_param = {'Hello': 'World'}
    result = workflowstream.deserialize(data_param)

    # assertions
    assert result == {'Hello': 'World'}

def test_deserialize_list_success():
    # imports
    import workflowstream

    #test parameters
    data_param = [
        {'BOOL': True},
        {'NULL': True},
        {'N': '123'}
    ]
    result = workflowstream.deserialize(data_param)

    # assertions
    assert result[0] == True
    assert result[1] == None
    assert result[2] == 123.0

def test_lambda_handler_insert():
    import workflowstream

    event_param = {
        'Records': [{
            'dynamodb': {'S': ''},
            'eventName': 'INSERT'

        }, {
            'dynamodb': {'S': ''},
            'eventName': 'REMOVE'

        }]
    }

    response = workflowstream.lambda_handler(event_param, {})
    assert response == None

def test_lambda_handler_modify_no_change():
    import workflowstream

    event_type = 'MODIFY'
    event_param = {
        'Records': [{
            'dynamodb': {
                'OldImage': {
                    'Status': 'Created'
                },
                'NewImage': {
                    'Status': 'Created'
                }
            },
            'eventName': event_type

        }]
    }

    response = workflowstream.lambda_handler(event_param, {})
    assert response == None

def test_lambda_handler_modify(sns_client_stub):
    import workflowstream

    sns_client_stub.add_response(
        'publish',
        expected_params = {
            'TargetArn': 'testTopicArn',
            'Message': ANY,
            'MessageStructure': 'json'
        },
        service_response = {}
    )

    event_param = {
        'Records': [{
            'dynamodb': {
                'OldImage': {
                    'Status': 'Created',
                    'Id': 'testId',
                    'AssetId': 'testAssetId',
                },
                'NewImage': {
                    'Status': 'Success',
                    'Globals': 'testGlobals',
                    'Configuration': 'testConfiguration',
                    'Created': 'testCreated'
                }
            },
            'eventName': 'MODIFY'

        }]
    }

    response = workflowstream.lambda_handler(event_param, {})
    assert response == None