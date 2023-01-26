import pytest
from unittest.mock import MagicMock

test_operator_parameter = {
    'Name': 'testName',
    'AssetId': 'testAssetId',
    'WorkflowExecutionId': 'testWorkflowId',
    'Configuration': {
        'Enabled': True,
        'MediaType': 'testMedia'
    },
    'Status': 'testStatus',
    'MetaData': {'test': 'metadataValue'},
    'Media': 'testMedia',
    'Input': {
        'Media': {
            'testMedia': 'testMediaValue'
        }
    }
}


def stub_max_concurrent_workflows(value, dynamoStub):
    dynamoStub.add_response(
        'get_item',
        expected_params={
            'TableName': 'testSystemTable',
            'Key': {
                'Name': 'MaxConcurrentWorkflows'
            },
            'ConsistentRead': True
        },
        service_response={
            'Item': {
                'Value': {'N': str(value)}
            }
        }
    )


def stub_list_workflows(count, dynamoStub):
    dynamoStub.add_response(
        'query',
        expected_params={
            'TableName': 'testExecutionTable',
            'IndexName': 'WorkflowExecutionStatus',
            'ExpressionAttributeNames': {
                '#workflow_status': 'Status',
                '#workflow_name': 'Name'
            },
            'ExpressionAttributeValues': {
                ':workflow_status': 'Started'
            },
            'KeyConditionExpression': '#workflow_status = :workflow_status',
            'ProjectionExpression': 'Id, AssetId, CurrentStage, StateMachineExecutionArn, #workflow_status, Workflow.#workflow_name'
        },
        service_response={
            'Items': [
                {
                    'Id': {'S': 'testWorkflowId'},
                    'StateMachineExecutionArn': {'S': 'testArn'}
                } for i in range(count)
            ]
        }
    )


def stub_update_workflow_status(status, dynamoStub):
    dynamoStub.add_response(
        'update_item',
        expected_params={
            'TableName': 'testExecutionTable',
            'Key': {
                'Id': 'testWorkflowId',
            },
            'UpdateExpression': 'SET #workflow_status = :workflow_status',
            'ExpressionAttributeNames': {
                '#workflow_status': "Status"
            },
            'ExpressionAttributeValues': {
                ':workflow_status': status
            }
        },
        service_response={}
    )


def test_dummy():
    # dummy test to satisfy code covererage for constant file
    import awsmas
    assert 1==1


def test_list_workflow_executions_when_empty(dynamo_client_stub):
    import app

    dynamo_client_stub.add_response(
        'query',
        expected_params={
            'TableName': 'testExecutionTable',
            'IndexName': 'WorkflowExecutionStatus',
            'ExpressionAttributeNames': {
                '#workflow_status': 'Status',
                '#workflow_name': 'Name'
            },
            'ExpressionAttributeValues': {
                ':workflow_status': 'testStatus'
            },
            'KeyConditionExpression': '#workflow_status = :workflow_status',
            'ProjectionExpression': 'Id, AssetId, CurrentStage, StateMachineExecutionArn, #workflow_status, Workflow.#workflow_name'
        },
        service_response={
            'Items': []
        }
    )

    results = app.list_workflow_executions_by_status('testStatus')
    assert len(results) == 0


def test_list_workflow_executions(dynamo_client_stub):
    import app

    dynamo_client_stub.add_response(
        'query',
        expected_params={
            'TableName': 'testExecutionTable',
            'IndexName': 'WorkflowExecutionStatus',
            'ExpressionAttributeNames': {
                '#workflow_status': 'Status',
                '#workflow_name': 'Name'
            },
            'ExpressionAttributeValues': {
                ':workflow_status': 'testStatus'
            },
            'KeyConditionExpression': '#workflow_status = :workflow_status',
            'ProjectionExpression': 'Id, AssetId, CurrentStage, StateMachineExecutionArn, #workflow_status, Workflow.#workflow_name'
        },
        service_response={
            'LastEvaluatedKey': {'key': {'S': 'lastKey'}},
            'Items': [{
                'TestExecution': {'S': 'testExecutionValue1'}
            }]
        }
    )

    dynamo_client_stub.add_response(
        'query',
        expected_params={
            'TableName': 'testExecutionTable',
            'IndexName': 'WorkflowExecutionStatus',
            'ExpressionAttributeNames': {
                '#workflow_status': 'Status',
                '#workflow_name': 'Name'
            },
            'ExpressionAttributeValues': {
                ':workflow_status': 'testStatus'
            },
            'KeyConditionExpression': '#workflow_status = :workflow_status',
            'ProjectionExpression': 'Id, AssetId, CurrentStage, StateMachineExecutionArn, #workflow_status, Workflow.#workflow_name',
            'ExclusiveStartKey': {'key': 'lastKey'}
        },
        service_response={
            'Items': [{
                'TestExecution': {'S': 'testExecutionValue2'}
            }]
        }
    )

    results = app.list_workflow_executions_by_status('testStatus')
    assert len(results) == 2
    assert results[0]['TestExecution'] == 'testExecutionValue1'
    assert results[1]['TestExecution'] == 'testExecutionValue2'


def test_workflow_scheduler_lambda_max_concurrency_reached(dynamo_client_stub):
    import app

    stub_max_concurrent_workflows(1, dynamo_client_stub)
    stub_list_workflows(1, dynamo_client_stub)

    result = app.workflow_scheduler_lambda({}, {})
    assert result == ''


def test_workflow_scheduler_lambda_empty_queue(dynamo_client_stub, sqs_client_stub, sfn_client_stub):
    import app

    # stubs
    stub_max_concurrent_workflows(2, dynamo_client_stub)
    stub_list_workflows(1, dynamo_client_stub)
    sqs_client_stub.add_response(
        'receive_message',
        expected_params={
            'QueueUrl': 'testExecutionQueueUrl',
            'MaxNumberOfMessages': 1
        },
        service_response={
            'Messages': [{
                'Body': '''{
                    "Status": "testStatus",
                    "Id": "testWorkflowId",
                    "CurrentStage": "testCurrentStage",
                    "Workflow": {
                        "StateMachineArn": "testStateMachineArn",
                        "Name": "testWorkflowName",
                        "Stages": {
                            "testCurrentStage": {}
                        }
                    }
                }''',
                'ReceiptHandle': 'testReceiptHandle'
            }]
        }
    )
    sqs_client_stub.add_response(
        'delete_message',
        expected_params={
            'QueueUrl': 'testExecutionQueueUrl',
            'ReceiptHandle': 'testReceiptHandle'
        },
        service_response={}
    )

    stub_update_workflow_status('Started', dynamo_client_stub)

    sfn_client_stub.add_response(
        'start_execution',
        expected_params={
            'stateMachineArn': 'testStateMachineArn',
            'name': 'testWorkflowName' + 'testWorkflowId',
            'input': '{}',
        },
        service_response={
            'executionArn': 'testExecutionArn',
            'startDate': 1
        }
    )

    dynamo_client_stub.add_response(
        'update_item',
        expected_params={
            'TableName': 'testExecutionTable',
            'Key': {
                'Id': 'testWorkflowId'
            },
            'UpdateExpression': 'SET StateMachineExecutionArn = :arn',
            'ExpressionAttributeValues': {
                ':arn': 'testExecutionArn'
            }
        },
        service_response={

        }
    )
    stub_list_workflows(2, dynamo_client_stub)

    result = app.workflow_scheduler_lambda({}, {})
    assert result == ''


def test_filter_operation_lambda():
    import app

    event_param = test_operator_parameter
    response = app.filter_operation_lambda(event_param, {})
    event_param['Status'] = 'Started'
    assert response == event_param


def test_start_wait_operation_lambda(dynamo_client_stub):
    import app

    stub_update_workflow_status('Waiting', dynamo_client_stub)

    event_param = test_operator_parameter
    response = app.start_wait_operation_lambda(event_param, {})
    assert response == event_param


def test_check_wait_operation_lambda_operator_does_not_exit(dynamo_client_stub):
    import app
    from MediaInsightsEngineLambdaHelper import MasExecutionError
    dynamo_client_stub.add_response(
        'get_item',
        expected_params={
            'TableName': 'testExecutionTable',
            'Key': {
                'Id': 'testWorkflowId'
            },
            'ConsistentRead': True
        },
        service_response={}
    )

    event_param = test_operator_parameter
    with pytest.raises(MasExecutionError):
        app.check_wait_operation_lambda(event_param, ())


def test_check_wait_operation_lambda_operator_unexpected_status(dynamo_client_stub):
    import app
    from MediaInsightsEngineLambdaHelper import MasExecutionError
    dynamo_client_stub.add_response(
        'get_item',
        expected_params={
            'TableName': 'testExecutionTable',
            'Key': {
                'Id': 'testWorkflowId'
            },
            'ConsistentRead': True
        },
        service_response={
            'Item': {
                'Status': {'S': 'unexpected_status'}
            }
        }
    )

    event_param = test_operator_parameter
    with pytest.raises(MasExecutionError):
        app.check_wait_operation_lambda(event_param, ())


def test_check_wait_operation_lambda_operator_started_status(dynamo_client_stub):
    import app

    dynamo_client_stub.add_response(
        'get_item',
        expected_params={
            'TableName': 'testExecutionTable',
            'Key': {
                'Id': 'testWorkflowId'
            },
            'ConsistentRead': True
        },
        service_response={
            'Item': {
                'Status': {'S': 'Started'}
            }
        }
    )

    event_param = test_operator_parameter
    response = app.check_wait_operation_lambda(event_param, ())
    assert response['Status'] == 'Complete'


def test_check_wait_operation_lambda_operator_waiting_status(dynamo_client_stub):
    import app

    dynamo_client_stub.add_response(
        'get_item',
        expected_params={
            'TableName': 'testExecutionTable',
            'Key': {
                'Id': 'testWorkflowId'
            },
            'ConsistentRead': True
        },
        service_response={
            'Item': {
                'Status': {'S': 'Waiting'}
            }
        }
    )

    event_param = test_operator_parameter
    response = app.check_wait_operation_lambda(event_param, ())
    assert response['Status'] == 'Executing'


def test_complete_stage_execution_lambda_error_output(dynamo_client_stub):
    import app

    stub = app.start_next_stage_execution
    app.start_next_stage_execution = MagicMock(return_value={'Id': 'testWorkflowId'})
    stub2 = app.update_workflow_execution_status
    app.update_workflow_execution_status = MagicMock()

    dynamo_client_stub.add_response(
        'get_item',
        expected_params={
            'TableName': 'testExecutionTable',
            'Key': {
                'Id': 'testWorkflowId'
            },
            'ConsistentRead': True
        },
        service_response={
            'Item': {
                'Workflow': {
                    'M': {
                        'Stages': {
                            'M': {
                                'testName': {
                                    'M': {
                                        'Outputs': {
                                            'M': {}
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                'Globals': {
                    'M': {
                        'Media': {
                            'M': {}
                        }
                    }
                },
                'CurrentStage': {'S': 'End'}
            }
        }
    )

    dynamo_client_stub.add_response(
        'update_item',
        expected_params={
            'TableName': 'testExecutionTable',
            'Key': {
                'Id': 'testWorkflowId'
            },
            'UpdateExpression': 'SET Workflow.Stages.#stage = :stage, Globals = :globals',
            'ExpressionAttributeNames': {
                '#stage': 'testName'
            },
            'ExpressionAttributeValues': {
                # ':stage': json.dumps(stage)
                ':stage': {
                    'Outputs': [{
                        'Name': 'testName',
                        'Status': 'Error'
                    }, {
                        'Name': 'testName',
                        'Status': 'Error',
                        'Message': 'message'
                    }],
                    'Status': 'Error'
                },
                ':globals': {
                    'Media': {},
                    'MetaData': {}
                }
                # ':step_function_arn': step_function_execution_arn
            }
        },
        service_response={}
    )
    dynamo_client_stub.add_response(
        'put_item',
        expected_params={
            'TableName': 'testExecutionTable',
            'Item': {'Id': 'testWorkflowId'}
        },
        service_response={}
    )

    event_param = test_operator_parameter
    event_param['Outputs'] = [{
        'Name': 'testName',
        'Status': 'Error'
    }, {
        'Name': 'testName',
        'Status': 'Error',
        'Message': 'message'
    }]

    with pytest.raises(ValueError):
        app.complete_stage_execution_lambda(event_param, {})

    assert app.start_next_stage_execution.call_count == 1
    assert app.start_next_stage_execution.call_args[0][0] == 'testName'
    assert app.update_workflow_execution_status.call_count == 1
    assert app.update_workflow_execution_status.call_args[0][0] == 'testWorkflowId'
    assert app.update_workflow_execution_status.call_args[0][1] == 'Error'

    app.start_next_stage_execution = stub
    app.update_workflow_execution_status = stub2


def test_complete_stage_execution_lambda(dynamo_client_stub):
    import app

    stub = app.start_next_stage_execution
    app.start_next_stage_execution = MagicMock(return_value={
        'CurrentStage': 'End'
    })

    dynamo_client_stub.add_response(
        'get_item',
        expected_params={
            'TableName': 'testExecutionTable',
            'Key': {
                'Id': 'testWorkflowId'
            },
            'ConsistentRead': True
        },
        service_response={
            'Item': {
                'Workflow': {
                    'M': {
                        'Stages': {
                            'M': {
                                'testName': {
                                    'M': {
                                        'Outputs': {
                                            'M': {}
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                'Globals': {
                    'M': {
                        'Media': {
                            'M': {}
                        }
                    }
                },
                'CurrentStage': {'S': 'End'}
            }
        }
    )

    dynamo_client_stub.add_response(
        'update_item',
        expected_params={
            'TableName': 'testExecutionTable',
            'Key': {
                'Id': 'testWorkflowId'
            },
            'UpdateExpression': 'SET Workflow.Stages.#stage = :stage, Globals = :globals',
            'ExpressionAttributeNames': {
                '#stage': 'testName'
            },
            'ExpressionAttributeValues': {
                # ':stage': json.dumps(stage)
                ':stage': {
                    'Outputs': [{
                        'Name': 'testName',
                        'Status': 'Complete',
                        'Media': {
                            'media1': 'value1',
                            'media2': 'value2'
                        }
                    }, {
                        'Name': 'testName',
                        'Status': 'Complete',
                        'MetaData': {
                            'metadata1': 'value1',
                            'metadata2': 'value2'
                        }
                    }],
                    'Status': 'Complete'
                },
                ':globals': {
                    'Media': {'media1': 'value1', 'media2': 'value2'},
                    'MetaData': {'metadata1': 'value1', 'metadata2': 'value2'}
                }
                # ':step_function_arn': step_function_execution_arn
            }
        },
        service_response={}
    )

    event_param = test_operator_parameter
    event_param['Outputs'] = [{
        'Name': 'testName',
        'Status': 'Complete',
        'Media': {
            'media1': 'value1',
            'media2': 'value2'
        }
    }, {
        'Name': 'testName',
        'Status': 'Complete',
        'MetaData': {
            'metadata1': 'value1',
            'metadata2': 'value2'
        }
    }]

    response = app.complete_stage_execution_lambda(event_param, {})
    assert response == {}
    assert app.start_next_stage_execution.call_count == 1
    assert app.start_next_stage_execution.call_args[0][0] == 'testName'
    app.start_next_stage_execution = stub


def test_update_workflow_error_case(dynamo_client_stub, lambda_client_stub):
    import app

    dynamo_client_stub.add_response(
        'update_item',
        expected_params={
            'TableName': 'testExecutionTable',
            'Key': {
                'Id': 'testWorkflowId',
            },
            'UpdateExpression': 'SET #workflow_status = :workflow_status, Message = :message',
            'ExpressionAttributeNames': {
                '#workflow_status': "Status"
            },
            'ExpressionAttributeValues': {
                ':workflow_status': 'Error',
                ':message': 'testMessage'
            }
        },
        service_response={}
    )

    lambda_client_stub.add_response(
        'invoke',
        expected_params={
            'FunctionName': 'testSchedulerLambdaArn',
            'InvocationType': 'Event'
        },
        service_response={}
    )

    response = app.update_workflow_execution_status('testWorkflowId', 'Error', 'testMessage')
    assert response is None


def test_update_workflow_success_case(dynamo_client_stub):
    import app

    stub_update_workflow_status('Success', dynamo_client_stub)

    response = app.update_workflow_execution_status('testWorkflowId', 'Success', '')
    assert response is None


def test_start_next_execution_end_stage(dynamo_client_stub):
    import app

    # mocks and stubs
    saved_stub = app.update_workflow_execution_status
    app.update_workflow_execution_status = MagicMock()

    dynamo_client_stub.add_response(
        'update_item',
        expected_params={
            'TableName': 'testExecutionTable',
            'Key': {
                'Id': 'testWorkflowId'
            },
            'UpdateExpression': 'SET CurrentStage = :current_stage',
            'ExpressionAttributeValues': {
                ':current_stage': "End"
            }
        },
        service_response={}
    )

    stage_name_param = 'testName'
    workflow_execution_param = {
        'Id': 'testWorkflowId',
        'Workflow': {
            'Stages': {
                'testName': {
                    'Status': 'Success',
                    'Outputs': {
                    },
                    'End': True
                }
            }
        },
        'Globals': {
        },
        'CurrentStage': 'End'
    }

    response = app.start_next_stage_execution(stage_name_param, workflow_execution_param)
    assert response == workflow_execution_param
    assert app.update_workflow_execution_status.call_count == 1
    assert app.update_workflow_execution_status.call_args[0][0] == 'testWorkflowId'
    assert app.update_workflow_execution_status.call_args[0][1] == 'Success'
    assert app.update_workflow_execution_status.call_args[0][2] == 'stage completed with status Success'

    app.update_workflow_execution_status = saved_stub


def test_start_next_execution_error(dynamo_client_stub):
    import app

    # mocks and stubs
    saved_stub = app.update_workflow_execution_status
    app.update_workflow_execution_status = MagicMock()

    dynamo_client_stub.add_response(
        'update_item',
        expected_params={
            'TableName': 'testExecutionTable',
            'Key': {
                'Id': 'testWorkflowId'
            },
            'UpdateExpression': 'SET CurrentStage = :current_stage',
            'ExpressionAttributeValues': {
                ':current_stage': "End"
            }
        },
        service_response={}
    )

    stage_name_param = 'testName'
    workflow_execution_param = {
        'Id': 'testWorkflowId',
        'Workflow': {
            'Stages': {
                'testName': {
                    'Status': 'Error',
                    'Outputs': {
                    },
                }
            }
        },
        'Status': 'Error',
        'Globals': {
        },
        'CurrentStage': 'testName'
    }

    response = app.start_next_stage_execution(stage_name_param, workflow_execution_param)
    assert response == workflow_execution_param
    assert app.update_workflow_execution_status.call_count == 1
    assert app.update_workflow_execution_status.call_args[0][0] == 'testWorkflowId'
    assert app.update_workflow_execution_status.call_args[0][1] == 'Error'
    assert app.update_workflow_execution_status.call_args[0][2] == 'stage completed with status Error'

    app.update_workflow_execution_status = saved_stub


def test_start_next_execution(dynamo_client_stub):
    import app

    # mocks and stubs
    saved_stub = app.update_workflow_execution_status
    app.update_workflow_execution_status = MagicMock()

    dynamo_client_stub.add_response(
        'update_item',
        expected_params={
            'TableName': 'testExecutionTable',
            'Key': {
                'Id': 'testWorkflowId'
            },
            'UpdateExpression': 'SET Workflow.Stages.#stage = :stage, CurrentStage = :current_stage',
            'ExpressionAttributeNames': {
                '#stage': "stage2"
            },
            'ExpressionAttributeValues': {
                ':stage': {'End': True, 'Input': {}, 'Status': 'Started'},
                ':current_stage': 'stage2'
            }
        },
        service_response={}
    )

    stage_name_param = 'testName'
    workflow_execution_param = {
        'Id': 'testWorkflowId',
        'Workflow': {
            'Stages': {
                'testName': {
                    'Status': 'Success',
                    'Outputs': {
                    },
                    'Next': 'stage2'
                },
                'stage2': {
                    'End': True
                }
            }
        },
        'Status': 'Success',
        'Globals': {
        },
        'CurrentStage': 'testName'
    }

    response = app.start_next_stage_execution(stage_name_param, workflow_execution_param)
    assert response == workflow_execution_param
    assert app.update_workflow_execution_status.call_count == 1
    assert app.update_workflow_execution_status.call_args[0][0] == 'testWorkflowId'
    assert app.update_workflow_execution_status.call_args[0][1] == 'Success'
    assert app.update_workflow_execution_status.call_args[0][2] == 'stage completed with status Success'

    app.update_workflow_execution_status = saved_stub


def test_parse_execution_error():
    import app

    executions_param = [{
        'Failed': {'cause': 'failed cause'},
    }, {
        'Aborted': {'cause': 'aborted cause'},
    }, {
        'TimedOut': {'cause': 'timedout cause'},
    }, {
        'ShouldNotBeParsed': {'cause': 'some cause'}
    }]
    message = app.parse_execution_error(
        'testArn',
        executions_param,
        'status'
    )
    assert message == 'Caught Step Function Execution Status Change event for execution: testArn, status:status' \
        + ', cause: failed cause' \
        + ', cause: aborted cause' \
        + ', cause: timedout cause'


def test_workflow_error_handler_param_validation():
    import app

    event_param = {}
    with pytest.raises(Exception):
        app.workflow_error_handler_lambda(event_param, {})
    event_param['detail'] = {}
    with pytest.raises(Exception):
        app.workflow_error_handler_lambda(event_param, {})
    event_param['detail']['name'] = 'name'
    with pytest.raises(Exception):
        app.workflow_error_handler_lambda(event_param, {})
    event_param['detail']['status'] = 'status'
    with pytest.raises(Exception):
        app.workflow_error_handler_lambda(event_param, {})
    event_param['detail']['executionArn'] = 'executionArn'
    with pytest.raises(Exception):
        app.workflow_error_handler_lambda(event_param, {})
    event_param['detail']['stateMachineArn'] = 'shortuuid'
    response = app.workflow_error_handler_lambda(event_param, {})
    assert response == {}


def test_workflow_error_handler(dynamo_client_stub):
    import app

    saved_stub = app.get_execution_errors
    saved_stub2 = app.update_workflow_execution_status
    app.get_execution_errors = MagicMock(return_value=[
        {'Failed': {'cause': 'failed cause'}},
        {'Aborted': {'cause': 'aborted cause'}},
        {'TimedOut': {'cause': 'timedout cause'}},
        {'ShouldNotBeParsed': {'cause': 'some cause'}}
    ])
    app.update_workflow_execution_status = MagicMock()
    stub_list_workflows(1, dynamo_client_stub)

    event_param = {
        'detail': {
            'name': 'testName',
            'status': 'testStatus',
            'executionArn': 'testArn',
            'stateMachineArn': 'testshortuuid'
        }
    }
    response = app.workflow_error_handler_lambda(event_param, {})
    assert response == {
        'stateMachineExecution': 'testArn',
        'errorMessage': 'Caught Step Function Execution Status Change event for execution: testArn, status:testStatus, cause: failed cause, cause: aborted cause, cause: timedout cause'
    }
    assert app.get_execution_errors.call_count == 1
    assert app.get_execution_errors.call_args[0][0] == 'testArn'
    assert app.update_workflow_execution_status.call_count == 1
    assert app.update_workflow_execution_status.call_args[0][0] == 'testWorkflowId'
    assert app.update_workflow_execution_status.call_args[0][1] == 'Error'
    assert app.update_workflow_execution_status.call_args[0][2] == 'Caught Step Function Execution Status Change event for execution: testArn, status:testStatus, cause: failed cause, cause: aborted cause, cause: timedout cause'

    app.get_execution_errors = saved_stub
    app.update_workflow_execution_status = saved_stub2
