# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from helper import *


def test_create_workflow(test_client, sfn_client_stub, ddb_resource_stub):
    print('POST /workflow')

    stub_get_stage(
        ddb_resource_stub,
        optional_input={
            'TableName': 'testStageTable',
            'Key': {
                'Name': '_testOperationName1'
            }
        },
        optional_output={
            'Item': {
                'Name': {'S': '_testOperationName1'},
                'Definition': {'S': '{"stage":"definition","StartAt":"_testOperationName1","States":{"_testOperation1": {"End":true}}}'}
            }
        }
    )

    stub_get_stage(
        ddb_resource_stub,
        optional_input={
            'TableName': 'testStageTable',
            'Key': {
                'Name': '_testOperationName2'
            }
        },
        optional_output={
            'Item': {
                'Name': {'S': '_testOperationName2'},
                'Definition': {'S': '{"stage":"definition","StartAt":"_testOperationName2","States":{"_testOperation2": "End"}}'}
            }
        }
    )

    sfn_client_stub.add_response(
        'create_state_machine',
        expected_params={
            'name': 'testWorkflowName-test1234',
            'definition': '{"StartAt": "_testOperationName1", "States": {"_testOperation1": {"Next": "_testOperationName2"}, "_testOperation2": "End"}}',
            'roleArn': 'testExecutionRole/role',
            'loggingConfiguration': {
                'level': 'ALL',
                'includeExecutionData': False,
                'destinations': [
                    {
                        'cloudWatchLogsLogGroup': {
                            'logGroupArn': 'testExecutionSfnLogGroup'
                        }
                    }
                ]
            },
            'tags': [{
                'key': 'environment',
                'value': 'mie'
            }]
        },
        service_response={
            'stateMachineArn': 'sma',
            'creationDate': '1'
        }
    )

    ddb_resource_stub.add_response(
        'put_item',
        expected_params={
            'TableName': 'testWorkflowTable',
            'Item': {
                'Name': 'testWorkflowName',
                'StartAt': '_testOperationName1',
                'Stages': {
                    '_testOperationName1': botocore.stub.ANY,
                    '_testOperationName2': botocore.stub.ANY
                },
                'Trigger': 'api',
                'Operations': [],
                'StaleOperations': [],
                'StaleStages': [],
                'Version': 'v0',
                'Id': botocore.stub.ANY,
                'Created': botocore.stub.ANY,
                'Revisions': '1',
                'ResourceType': 'WORKFLOW',
                'ApiVersion': '3.0.0',
                'StateMachineArn': 'sma'
            },
            'ConditionExpression': 'attribute_not_exists(#workflow_name)',
            'ExpressionAttributeNames': {
                '#workflow_name': 'Name'
            }
        },
        service_response={}
    )

    response = test_client.http.post(
        '/workflow',
        body=json.dumps({
            'Name': 'testWorkflowName',
            'StartAt': '_testOperationName1',
            'Stages': {
                '_testOperationName1': {
                    'Next': '_testOperationName2',
                    'Operations': []
                },
                '_testOperationName2': {
                    'Operations': [],
                    'End': True
                }
            }
        }).encode()
    )
    assert response.status_code == 200


def test_update_workflow(test_client, ddb_resource_stub, sfn_client_stub):
    print('PUT /workflow')

    ddb_resource_stub.add_response(
        'get_item',
        expected_params={
            'TableName': 'testWorkflowTable',
            'Key': {
                'Name': 'testWorkflowName'
            }
        },
        service_response={
            'Item': {
                'Name': {'S': 'testWorkflowName'},
                'StartAt': {'S': '_testOperationName1'},
                'Version': {'S': 'v0'},
                'Created': {'S': '1'},
                'Revisions': {'S': '1'},
                'ResourceType': {'S': 'WORKFLOW'},
                'ApiVersion': {'S': '3.0.0'},
                'StateMachineArn': {'S': 'sma'},
                'Operations': {'L': []},
                'StaleOperations': {'L': []},
                'StaleStages': {'L': []},
                'Stages': {
                    'M': {
                        '_testOperationName1': {
                            'M': {
                                'Next': {'S': '_testOperationName2'}
                            }
                        },
                        '_testOperationName2': {
                            'M': {
                                'End': {'BOOL': True}
                            }
                        }
                    }
                }
            }
        }
    )

    stub_get_stage(
        ddb_resource_stub,
        optional_input={
            'TableName': 'testStageTable',
            'Key': {
                'Name': '_testOperationName1'
            }
        },
        optional_output={
            'Item': {
                'Name': {'S': '_testOperationName1'},
                'Definition': {'S': '{"stage":"definition","StartAt":"_testOperationName1","States":{"_testOperation1": {"End":true}}}'},
                'Operations': {'L': []}
            }
        }
    )

    stub_get_stage(
        ddb_resource_stub,
        optional_input={
            'TableName': 'testStageTable',
            'Key': {
                'Name': '_testOperationName2'
            }
        },
        optional_output={
            'Item': {
                'Name': {'S': '_testOperationName2'},
                'Definition': {'S': '{"stage":"definition","StartAt":"_testOperationName2","States":{"_testOperation2": "End"}}'},
                'Operations': {'L': []}
            }
        }
    )

    sfn_client_stub.add_response(
        'update_state_machine',
        expected_params={
            'stateMachineArn': botocore.stub.ANY,
            'definition': botocore.stub.ANY,
            'roleArn': 'testExecutionRole/role',
        },
        service_response={
            'updateDate': '1'
        }
    )

    ddb_resource_stub.add_response(
        'put_item',
        expected_params={
            'TableName': 'testWorkflowTable',
            'Item': {
                'Name': 'testWorkflowName',
                'StartAt': '_testOperationName1',
                'Stages': {
                    '_testOperationName1': botocore.stub.ANY,
                    '_testOperationName2': botocore.stub.ANY
                },
                'Operations': [],
                'StaleOperations': [],
                'StaleStages': [],
                'Version': 'v2',
                'Created': botocore.stub.ANY,
                'Revisions': '1',
                'ResourceType': 'WORKFLOW',
                'ApiVersion': '3.0.0',
                'StateMachineArn': 'sma'
            }
        },
        service_response={}
    )

    response = test_client.http.put(
        '/workflow',
        body=json.dumps({
            'Name': 'testWorkflowName',
        }).encode()
    )

    assert response.status_code == 200


def test_list_workflows(test_client, ddb_resource_stub):
    print('GET /workflow')

    ddb_resource_stub.add_response(
        'scan',
        expected_params={
            'TableName': 'testWorkflowTable'
        },
        service_response={
            'LastEvaluatedKey': {'S': {'S': 'lastKey'}},
            'Items': [{
                'Name': {'S': 'testWorkflowName1'}
            }]
        }
    )
    ddb_resource_stub.add_response(
        'scan',
        expected_params={
            'TableName': 'testWorkflowTable',
            'ExclusiveStartKey': {'S': 'lastKey'}
        },
        service_response={
            'Items': [{
                'Name': {'S': 'testWorkflowName2'}
            }]
        }
    )

    response = test_client.http.get('/workflow')
    assert response.status_code == 200
    assert len(response.json_body) == 2


def test_list_workflows_by_operator(test_client, ddb_resource_stub):
    print('GET /workflow/list/operation/{operator_name}')

    ddb_resource_stub.add_response(
        'scan',
        expected_params={
            'TableName': 'testWorkflowTable',
            'FilterExpression': botocore.stub.ANY,
            'ConsistentRead': True
        },
        service_response={
            'LastEvaluatedKey': {'S': {'S': 'lastKey'}},
            'Items': [{
                'Name': {'S': 'operator1'}
            }]
        }
    )

    ddb_resource_stub.add_response(
        'scan',
        expected_params={
            'TableName': 'testWorkflowTable',
            'ExclusiveStartKey': {'S': 'lastKey'}
        },
        service_response={
            'Items': [{
                'Name': {'S': 'operator2'}
            }]
        }
    )

    response = test_client.http.get(
        '/workflow/list/operation/testOperatorName'
    )
    assert response.status_code == 200
    assert len(response.json_body) == 2
    assert response.json_body[0]['Name'] == 'operator1'
    assert response.json_body[1]['Name'] == 'operator2'


def test_list_workflows_by_stage(test_client, ddb_resource_stub):
    print('GET /workflow/list/stage')

    ddb_resource_stub.add_response(
        'scan',
        expected_params={
            'TableName': 'testWorkflowTable',
            'FilterExpression': botocore.stub.ANY,
            'ConsistentRead': True
        },
        service_response={
            'LastEvaluatedKey': {'S': {'S': 'lastKey'}},
            'Items': [{
                'Name': {'S': 'stage1'}
            }]
        }
    )

    ddb_resource_stub.add_response(
        'scan',
        expected_params={
            'TableName': 'testWorkflowTable',
            'ExclusiveStartKey': {'S': 'lastKey'}
        },
        service_response={
            'Items': [{
                'Name': {'S': 'stage2'}
            }]
        }
    )

    response = test_client.http.get('/workflow/list/stage/_testOperationName')
    assert response.status_code == 200
    assert len(response.json_body) == 2
    assert response.json_body[0]['Name'] == 'stage1'
    assert response.json_body[1]['Name'] == 'stage2'


def test_get_workflow_configuration_by_name_does_not_exist(test_client, ddb_resource_stub):
    print('GET /workflow/configuration/{name}')

    configuration_name = 'testConfigurationName'

    ddb_resource_stub.add_response(
        'get_item',
        expected_params={
            'TableName': 'testWorkflowTable',
            'Key': {
                'Name': configuration_name
            }
        },
        service_response={
        }
    )

    response = test_client.http.get(
        '/workflow/configuration/{Name}'.format(Name=configuration_name)
    )
    assert response.status_code == 404
    assert "Exception: workflow '%s' not found" % configuration_name in response.json_body['Message']


def test_get_workflow_configuration_by_name(test_client, ddb_resource_stub):
    print('GET /workflow/configuration/{name}')

    configuration_name = 'testConfigurationName'

    ddb_resource_stub.add_response(
        'get_item',
        expected_params={
            'TableName': 'testWorkflowTable',
            'Key': {
                'Name': configuration_name
            }
        },
        service_response={
            'Item': {
                'Stages': {
                    'M': {
                        'stage1': {
                            'M': {
                                'Configuration': {'S': 'stage1_config'}
                            }
                        }
                    }
                }
            }
        }
    )

    response = test_client.http.get(
        '/workflow/configuration/{Name}'.format(Name=configuration_name)
    )
    assert response.status_code == 200
    assert response.json_body['stage1'] == 'stage1_config'


def test_delete_workflow_api_workflow_does_not_exist(test_client, ddb_resource_stub, sfn_client_stub):
    print('DELETE /workflow/{name}')

    ddb_resource_stub.add_response(
        'get_item',
        expected_params={
            'TableName': 'testWorkflowTable',
            'Key': {
                'Name': 'testWorkflowName'
            },
            'ConsistentRead': True
        },
        service_response={}
    )

    response = test_client.http.delete('/workflow/testWorkflowName')
    assert response.status_code == 200
    assert "Workflow 'testWorkflowName' not found" in response.json_body['Message']


def test_delete_workflow_api(test_client, ddb_resource_stub, sfn_client_stub):
    print('DELETE /workflow/{name}')

    ddb_resource_stub.add_response(
        'get_item',
        expected_params={
            'TableName': 'testWorkflowTable',
            'Key': {
                'Name': 'testWorkflowName'
            },
            'ConsistentRead': True
        },
        service_response={
            'Item': {
                'StateMachineArn': {'S': 'stateMachineArn'}
            }
        }
    )
    sfn_client_stub.add_response(
        'delete_state_machine',
        expected_params={
            'stateMachineArn': 'stateMachineArn'
        },
        service_response={}
    )
    ddb_resource_stub.add_response(
        'delete_item',
        expected_params={
            'TableName': 'testWorkflowTable',
            'Key': {
                'Name': 'testWorkflowName'
            },
        },
        service_response={}
    )

    response = test_client.http.delete('/workflow/testWorkflowName')
    assert response.status_code == 200
