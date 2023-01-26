from helper import *


def test_create_workflow_execution_api_fail(test_client, ddb_resource_stub, sqs_client_stub, lambda_client_stub):
    print('POST /workflow/execution')
    ddb_resource_stub.add_response(
        'get_item',
        expected_params={"Key": {"Name": "testWorkflow"}, "ConsistentRead": True, "TableName": "testWorkflowTable"},
        service_response={"Item": get_sample_workflow_output()}
    )
    ddb_resource_stub.add_response(
        'put_item',
        expected_params={"Item": sample_workflow_execution, "TableName": "testExecutionTable"},
        service_response={}
    )
    sqs_client_stub.add_client_error('send_message')

    ddb_resource_stub.add_response(
        'update_item',
        expected_params={
            'TableName': 'testExecutionTable',
            'Key': {
                'Id': botocore.stub.ANY
            },
            'UpdateExpression': 'SET #workflow_status = :workflow_status, Message = :message',
            'ExpressionAttributeNames': {
                '#workflow_status': "Status"
            },
            'ExpressionAttributeValues': {
                ':workflow_status': awsmie.WORKFLOW_STATUS_ERROR,
                ':message': 'Exception An error occurred () when calling the SendMessage operation: '

            }
        },
        service_response={}
    )
    lambda_client_stub.add_response(
        'invoke',
        expected_params={"FunctionName": "testSchedulerArn", "InvocationType": "Event"},
        service_response={}
    )

    response = test_client.http.post('/workflow/execution', body=b'{"Name": "testWorkflow","Input": {"Media": {'
                                                                 b'"Video": {"S3Bucket": "testBucket",'
                                                                 b'"S3Key": "testFile.mp4"}}}}')

    assert response.status_code == 500


def test_create_workflow_execution_api_success(test_client, ddb_resource_stub, sqs_client_stub, lambda_client_stub):
    print('POST /workflow/execution')
    ddb_resource_stub.add_response(
        'get_item',
        expected_params={"Key": {"Name": "testWorkflow"}, "ConsistentRead": True, "TableName": "testWorkflowTable"},
        service_response={"Item": get_sample_workflow_output()}
    )
    ddb_resource_stub.add_response(
        'put_item',
        expected_params={"Item": sample_workflow_execution, "TableName": "testExecutionTable"},
        service_response={}
    )
    sqs_client_stub.add_response(
        'send_message',
        expected_params={"QueueUrl": "testQueueUrl", "MessageBody": botocore.stub.ANY},
        service_response={"MessageId": "abcd-1234"}
    )
    lambda_client_stub.add_response(
        'invoke',
        expected_params={"FunctionName": "testSchedulerArn", "InvocationType": "Event"},
        service_response={}
    )
    response = test_client.http.post('/workflow/execution', body=b'{"Name": "testWorkflow","Input": {"Media": {'
                                                                 b'"Video": {"S3Bucket": "testBucket",'
                                                                 b'"S3Key": "testFile.mp4"}}}}')

    assert response.status_code == 200
    formatted_response = json.loads(response.body)
    assert formatted_response['Status'] == 'Queued'


def test_list_workflow_executions_by_assetid(test_client, ddb_resource_stub):
    print('GET /workflow/execution/{asset_id}')
    test_asset_id = "c1752400-ba2f-4682-a8dd-6eba0932d148"
    ddb_resource_stub.add_response(
        'query',
        expected_params={"IndexName": "WorkflowExecutionAssetId",
                         "ExpressionAttributeNames": {'#workflow_status': "Status",
                                                      '#workflow_name': "Name"},
                         "ExpressionAttributeValues": {':assetid': test_asset_id},
                         "KeyConditionExpression": 'AssetId = :assetid',
                         "ProjectionExpression": botocore.stub.ANY, "TableName": "testExecutionTable"},
        service_response={
            "Items": sample_workflow_status_by_asset_id,
            "Count": 1,
            "ScannedCount": 1,
            "ResponseMetadata": {
                "M": {
                    "RequestId": {
                        "S": ""
                    },
                    "HTTPStatusCode": {
                        "N": 200
                    },
                    "HTTPHeaders": {
                        "M": {
                            "server": {
                                "S": "Server"
                            },
                            "date": {
                                "S": "Fri, 20 Nov 2020 19:21:33 GMT"
                            },
                            "content-type": {
                                "S": "application/x-amz-json-1.0"
                            },
                            "content-length": {
                                "S": "424"
                            },
                            "connection": {
                                "S": "keep-alive"
                            },
                            "x-amzn-requestid": {
                                "S": ""
                            },
                            "x-amz-crc32": {
                                "S": ""
                            }
                        }
                    },
                    "RetryAttempts": {
                        "N": 0
                    }
                }
            }
        }
    )

    response = test_client.http.get('/workflow/execution/asset/{AssetId}'.format(AssetId=test_asset_id))
    formatted_response = json.loads(response.body)
    assert response.status_code == 200
    assert "Status" in formatted_response[0]
    assert formatted_response[0]["AssetId"] == test_asset_id
    print("Pass")


def test_get_workflow_execution_by_id(test_client, ddb_resource_stub):
    print('GET /workflow/execution/{id}')
    test_workflow_id = "0c6c202a-dd21-4791-b7b1-28c0ab60575d"
    ddb_resource_stub.add_response(
        'get_item',
        expected_params={"Key": {"Id": test_workflow_id}, "ConsistentRead": True, "TableName": "testExecutionTable"},
        service_response={"Item": sample_workflow_status_by_id}
    )
    response = test_client.http.get('/workflow/execution/{id}'.format(id=test_workflow_id))
    formatted_response = json.loads(response.body)
    assert response.status_code == 200
    assert formatted_response['Id'] == test_workflow_id
    print("Pass")


def test_update_workflow_execution(test_client, ddb_resource_stub):
    print('PUT /workflow/execution/{id}')

    workflow_execution_id = 'testWorkflowExecutionId'

    response = test_client.http.put(
        '/workflow/execution/{Id}'.format(Id=workflow_execution_id),
        body=json.dumps({'stage': True}).encode()
    )

    assert response.status_code == 200
    assert response.json_body == {}


def test_update_workflow_execution(test_client, ddb_resource_stub, sqs_client_stub, lambda_client_stub):
    print('PUT /workflow/execution/{id}')

    workflow_execution_id = 'testWorkflowExecutionId'

    ddb_resource_stub.add_response(
        'update_item',
        expected_params={
            'TableName': 'testExecutionTable',
            'Key': {
                'Id': workflow_execution_id
            },
            'UpdateExpression': 'SET #workflow_status = :workflow_status',
            'ExpressionAttributeNames': {
                '#workflow_status': "Status"
            },
            'ConditionExpression': "#workflow_status = :workflow_waiting_status AND CurrentStage = :waiting_stage_name",
            'ExpressionAttributeValues': {
                ':workflow_waiting_status': awsmie.WORKFLOW_STATUS_WAITING,
                ':workflow_status': awsmie.WORKFLOW_STATUS_RESUMED,
                ':waiting_stage_name': 'testWaitStage'
            }
        },
        service_response={}
    )

    sqs_client_stub.add_response(
        'send_message',
        expected_params={
            'QueueUrl': 'testQueueUrl',
            'MessageBody': json.dumps({
                'Id': workflow_execution_id,
                'Status': awsmie.WORKFLOW_STATUS_RESUMED
            })
        },
        service_response={
            'MessageId': 'id'
        }
    )

    lambda_client_stub.add_response(
        'invoke',
        expected_params={
            'FunctionName': 'testSchedulerArn',
            'InvocationType': 'Event'
        },
        service_response={
            'StatusCode': 0
        }
    )

    response = test_client.http.put(
        '/workflow/execution/{Id}'.format(Id=workflow_execution_id),
        body=json.dumps({'WaitingStageName': 'testWaitStage'}).encode()
    )

    assert response.status_code == 200
    assert response.json_body == {
        'Id': workflow_execution_id,
        'Status': 'Resumed'
    }


def test_list_workflow_executions(test_client, ddb_resource_stub):
    print('GET /workflow/execution')

    ddb_resource_stub.add_response(
        'scan',
        expected_params={
            'TableName': 'testExecutionTable'
        },
        service_response={
            'LastEvaluatedKey': {'S': {'S': 'lastKey'}},
            'Items': [{
                'Name': {'S': 'workflow_execution1'}
            }]
        }
    )
    ddb_resource_stub.add_response(
        'scan',
        expected_params={
            'TableName': 'testExecutionTable',
            'ExclusiveStartKey': {'S': 'lastKey'}
        },
        service_response={
            'Items': [{
                'Name': {'S': 'workflow_execution2'}
            }]
        }
    )

    response = test_client.http.get('/workflow/execution')
    assert response.status_code == 200
    assert len(response.json_body) == 2
    assert response.json_body[0]['Name'] == 'workflow_execution1'
    assert response.json_body[1]['Name'] == 'workflow_execution2'


def test_list_workflow_executions_by_status(test_client, ddb_resource_stub):
    print('GET /workflow/execution/status/{status}')
    test_status = 'testStatus'

    ddb_resource_stub.add_response(
        'query',
        expected_params={
            'TableName': 'testExecutionTable',
            'IndexName': 'WorkflowExecutionStatus',
            'ExpressionAttributeNames': {
                '#workflow_status': "Status",
                '#workflow_name': "Name"
            },
            'ExpressionAttributeValues': {
                ':workflow_status': test_status
            },
            'KeyConditionExpression': '#workflow_status = :workflow_status',
            'ProjectionExpression': 'Id, AssetId, CurrentStage, StateMachineExecutionArn, #workflow_status, Workflow.#workflow_name'
        },
        service_response={
            'LastEvaluatedKey': {'S': {'S': 'lastKey'}},
            'Items': [{
                'Name': {'S': 'execution1'}
            }]
        }
    )

    ddb_resource_stub.add_response(
        'query',
        expected_params={
            'TableName': 'testExecutionTable',
            'IndexName': 'WorkflowExecutionStatus',
            'ExpressionAttributeNames': {
                '#workflow_status': "Status",
                '#workflow_name': "Name"
            },
            'ExpressionAttributeValues': {
                ':workflow_status': test_status
            },
            'KeyConditionExpression': '#workflow_status = :workflow_status',
            'ProjectionExpression': 'Id, AssetId, CurrentStage, StateMachineExecutionArn, #workflow_status, Workflow.#workflow_name',
            'ExclusiveStartKey': {'S': 'lastKey'}
        },
        service_response={
            'Items': [{
                'Name': {'S': 'execution2'}
            }]
        }
    )

    response = test_client.http.get(
        '/workflow/execution/status/{Status}'.format(Status=test_status)
    )
    assert response.status_code == 200
    assert len(response.json_body) == 2
    assert response.json_body[0]['Name'] == 'execution1'
    assert response.json_body[1]['Name'] == 'execution2'


def test_list_workflow_executions_by_asset_id(test_client, ddb_resource_stub):
    print('GET /workflow/execution/asset/{asset_id}')
    test_asset_id = 'testAssetId'

    ddb_resource_stub.add_response(
        'query',
        expected_params={
            'TableName': 'testExecutionTable',
            'IndexName': 'WorkflowExecutionAssetId',
            'ExpressionAttributeNames': {
                '#workflow_status': "Status",
                '#workflow_name': "Name"
            },
            'ExpressionAttributeValues': {
                ':assetid': test_asset_id
            },
            'KeyConditionExpression': 'AssetId = :assetid',
            'ProjectionExpression': 'Id, AssetId, CurrentStage, Created, StateMachineExecutionArn, #workflow_status, Workflow.#workflow_name'
        },
        service_response={
            'LastEvaluatedKey': {'S': {'S': 'lastKey'}},
            'Items': [{
                'Name': {'S': 'workflowExecutionAsset1'},
                'Created': {'N': '1'}
            }]
        }
    )

    ddb_resource_stub.add_response(
        'query',
        expected_params={
            'TableName': 'testExecutionTable',
            'IndexName': 'WorkflowExecutionAssetId',
            'ExpressionAttributeNames': {
                '#workflow_status': "Status",
                '#workflow_name': "Name"
            },
            'ExpressionAttributeValues': {
                ':assetid': test_asset_id
            },
            'KeyConditionExpression': 'AssetId = :assetid',
            'ProjectionExpression': 'Id, AssetId, CurrentStage, Created, StateMachineExecutionArn, #workflow_status, Workflow.#workflow_name',
            'ExclusiveStartKey': {'S': 'lastKey'}
        },
        service_response={
            'Items': [{
                'Name': {'S': 'workflowExecutionAsset2'},
                'Created': {'N': '2'}
            }]
        }
    )

    response = test_client.http.get('/workflow/execution/asset/{test_asset_id}'.format(test_asset_id=test_asset_id))
    assert response.status_code == 200
    assert len(response.json_body) == 2
    assert response.json_body[0]['Name'] == 'workflowExecutionAsset2'
    assert response.json_body[1]['Name'] == 'workflowExecutionAsset1'


def test_get_workflow_execution_by_id2(test_client, ddb_resource_stub):
    print('GET /workflow/execution/{id}')
    test_workflow_execution_id = 'testWorkflowExecutionId'

    ddb_resource_stub.add_response(
        'get_item',
        expected_params={
            'TableName': 'testExecutionTable',
            'Key': {
                'Id': test_workflow_execution_id
            },
            'ConsistentRead': True
        },
        service_response={
            'Item': {
                'Name': {'S': 'execution1'}
            }
        }
    )
    response = test_client.http.get('/workflow/execution/{Id}'.format(Id=test_workflow_execution_id))
    assert response.status_code == 200
    assert response.json_body['Name'] == 'execution1'


def test_delete_workflow_execution_execution_does_not_exist(test_client, ddb_resource_stub):
    print('DELETE /workflow/execution/{id}')

    test_execution_id = 'workflowExecutionId'

    ddb_resource_stub.add_response(
        'get_item',
        expected_params={
            'TableName': 'testExecutionTable',
            'Key': {
                'Id': test_execution_id
            },
            'ConsistentRead': True
        },
        service_response={}
    )

    response = test_client.http.delete('/workflow/execution/{Id}'.format(Id=test_execution_id))
    assert response.status_code == 500
    assert "workflow execution '%s' not found'" % test_execution_id in response.json_body['Message']


def test_delete_workflow_execution(test_client, ddb_resource_stub):
    print('DELETE /workflow/execution/{id}')

    test_execution_id = 'workflowExecutionId'

    ddb_resource_stub.add_response(
        'get_item',
        expected_params={
            'TableName': 'testExecutionTable',
            'Key': {
                'Id': test_execution_id
            },
            'ConsistentRead': True
        },
        service_response={
            'Item': {
                'Name': {'S': test_execution_id}
            }
        }
    )
    ddb_resource_stub.add_response(
        'delete_item',
        expected_params={
            'TableName': 'testExecutionTable',
            'Key': {
                'Id': test_execution_id
            }
        },
        service_response={}
    )

    response = test_client.http.delete('/workflow/execution/{Id}'.format(Id=test_execution_id))
    assert response.status_code == 200
    assert response.json_body['Name'] == test_execution_id
