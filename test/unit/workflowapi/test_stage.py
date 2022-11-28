from helper import *

def test_create_stage(test_client, ddb_resource_stub):
    print('POST /workflow/stage')

    stub_create_stage(ddb_resource_stub)

    response = test_client.http.post(
        '/workflow/stage',
        body=json.dumps({
            'Name': '_' + test_operation_name,
            'Operations': [
                test_operation_name
            ]
        }).encode()
    )
    assert response.status_code == 200

def test_update_stage(test_client):
    print('PUT /workflow/stage')
    response = test_client.http.put('/workflow/stage')
    assert response.status_code == 200
    assert response.json_body['Message'] == 'NOT IMPLEMENTED'

def test_list_stages(test_client, ddb_resource_stub):
    print('GET /workflow/stage')

    ddb_resource_stub.add_response(
        'scan',
        expected_params = {
            'TableName': 'testStageTable'
        },
        service_response = {
            'LastEvaluatedKey': { 'S': { 'S': 'lastKey' } },
            'Items': [{
                'Name': { 'S': 'stage1' }
            }]
        }
    )
    ddb_resource_stub.add_response(
        'scan',
        expected_params = {
            'TableName': 'testStageTable',
            'ExclusiveStartKey': { 'S': 'lastKey' }
        },
        service_response = {
            'Items': [{
                'Name': {'S': 'stage2' }
            }]
        }
    )

    response = test_client.http.get('/workflow/stage')
    assert response.status_code == 200
    assert len(response.json_body) == 2
    assert response.json_body[0]['Name'] == 'stage1'
    assert response.json_body[1]['Name'] == 'stage2'

def test_get_stage_by_name_when_stage_dne(test_client, ddb_resource_stub):
    print('GET /workflow/stage/{Name}')

    stub_get_stage(
        ddb_resource_stub,
        optional_input = {
            'TableName': 'testStageTable',
            'Key': {
                'Name': '_' + test_operation_name
            }
        },
        optional_output={}
    )

    response = test_client.http.get(
        '/workflow/stage/_testOperationName'
    )
    assert response.status_code == 404
    assert response.json_body['Message'] == "Exception: stage '_testOperationName' not found"

def test_get_stage_by_name_when_stage_does_not_exist(test_client, ddb_resource_stub):
    print('GET /workflow/stage/{Name}')

    stub_get_stage(
        ddb_resource_stub,
        optional_input = {
            'TableName': 'testStageTable',
            'Key': {
                'Name': '_' + test_operation_name
            }
        },
        optional_output={
            'Item': {
                'Name': { 'S': '_testOperationName' }
            }
        }
    )

    response = test_client.http.get(
        '/workflow/stage/_testOperationName'
    )
    assert response.status_code == 200
    assert response.json_body['Name'] == '_testOperationName'

def test_delete_stage(test_client, ddb_resource_stub):
    print('DELETE /workflow/stage/{Name}')
    
    stub_get_stage(ddb_resource_stub)
    ddb_resource_stub.add_response(
        'scan',
        expected_params = {
            'TableName': 'testWorkflowTable',
            'FilterExpression': botocore.stub.ANY,
            'ConsistentRead': True
        },
        service_response = { 'Items': [] }
    )
    stub_delete_stage(ddb_resource_stub)
    ddb_resource_stub.add_response(
        'scan',
        expected_params = {
            'TableName': 'testWorkflowTable',
            'FilterExpression': botocore.stub.ANY,
            'ConsistentRead': True
        },
        service_response = { 'Items': [{
            'Name': {'S':'workflow1'}
        }] }
    )
    ddb_resource_stub.add_response(
        'update_item',
        expected_params = {
            'TableName': 'testWorkflowTable',
            'Key': {
                'Name': 'workflow1'
            },
            'UpdateExpression': 'SET StaleStages = list_append(StaleStages, :i)',
            'ExpressionAttributeValues': {
                ':i': ['_testOperationName']
            },
            'ReturnValues': 'UPDATED_NEW'
        },
        service_response = {}
    )

    response = test_client.http.delete('/workflow/stage/_testOperationName')

    assert response.status_code == 200
    assert response.json_body['Name'] == '_testOperationName'