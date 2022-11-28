from helper import *

workflow_operation_endpoint = '/workflow/operation'

def test_create_operation_api_input_error1(test_client):
    print('POST {endpoint}'.format(endpoint = workflow_operation_endpoint))
    
    response = test_client.http.post(
        workflow_operation_endpoint,
        body=json.dumps({
            "Name": "testOperationName",
            "Type":"Async",
            "Configuration": {
                "MediaType": "Video",
                "Enabled": True
            },
            "StartLambdaArn": "startArn"
        }).encode()
    )
    
    assert response.status_code == 500
    assert response.json_body['Message'] == "Exception 'Key 'MonitorLambdaArn' is required in 'Operation monitoring lambda function ARN' input'"

def test_create_operation_api_input_error2(test_client):
    print('POST {endpoint}'.format(endpoint = workflow_operation_endpoint))
    
    response = test_client.http.post(
        workflow_operation_endpoint,
        body=json.dumps({
            "Name": "testOperationName",
            "Configuration": {
                "MediaType": "Video",
                "Enabled": True
            },
            "StartLambdaArn": "startArn"
        }).encode()
    )
    
    assert response.json_body['Code'] == 'BadRequestError'
    assert response.status_code == 400

def test_create_operation_api_operation_exists_error(test_client, ddb_resource_stub):
    print('POST {endpoint}'.format(endpoint = workflow_operation_endpoint))
    
    stub_get_operation(ddb_resource_stub)

    response = test_client.http.post(
        workflow_operation_endpoint,
        body=json.dumps({
            "Name": "testOperationName",
            "Type":"Async",
            "Configuration": {
                "MediaType": "Video",
                "Enabled": True
            },
            "StartLambdaArn": "startArn",
            "MonitorLambdaArn": "monitorArn"
        }).encode()
    )
    
    assert response.status_code == 409
    assert response.json_body['Message'] == "A operation with the name 'testOperationName' already exists"

def test_create_operation_api_operation_dynamo_put_error(test_client, ddb_resource_stub):
    print('POST {endpoint}'.format(endpoint = workflow_operation_endpoint))
    
    stub_get_operation(ddb_resource_stub, optional_output = {})

    ddb_resource_stub.add_client_error('put_item')

    response = test_client.http.post(
        workflow_operation_endpoint,
        body=json.dumps({
            "Name": "testOperationName",
            "Type":"Async",
            "Configuration": {
                "MediaType": "Video",
                "Enabled": True
            },
            "StartLambdaArn": "startArn",
            "MonitorLambdaArn": "monitorArn"
        }).encode()
    )
    
    assert response.json_body['Message'] == "Exception 'An error occurred () when calling the PutItem operation: '"
    assert response.status_code == 500

def test_create_operation_api_operation_dynamo_put_error2(test_client, ddb_resource_stub):
    print('POST {endpoint}'.format(endpoint = workflow_operation_endpoint))
    
    stub_get_operation(ddb_resource_stub, optional_output={})
    stub_put_operation(ddb_resource_stub)
    stub_create_stage(ddb_resource_stub)

    ddb_resource_stub.add_client_error('put_item')
    ddb_resource_stub.add_response(
        'delete_item',
        expected_params = {
            'TableName': 'testOperationTable',
            'Key': {
                'Name': 'testOperationName'
            }
        },
        service_response = {}
    )

    response = test_client.http.post(
        workflow_operation_endpoint,
        body=json.dumps({
            "Name": "testOperationName",
            "Type":"Async",
            "Configuration": {
                "MediaType": "Video",
                "Enabled": True
            },
            "StartLambdaArn": "startArn",
            "MonitorLambdaArn": "monitorArn"
        }).encode()
    )
    
    assert response.status_code == 500

def test_create_operation_api_operation_iam_error(test_client, ddb_resource_stub, iam_client_stub):
    print('POST {endpoint}'.format(endpoint = workflow_operation_endpoint))
    
    stub_get_operation(ddb_resource_stub, optional_output={})
    stub_put_operation(ddb_resource_stub)
    stub_create_stage(ddb_resource_stub)
    operation_input = get_sample_operation_input()
    operation_input['Item']['StageName'] = '_' + test_operation_name
    stub_put_operation(ddb_resource_stub, optional_input=operation_input)

    iam_client_stub.add_client_error(
        'put_role_policy'
    )

    response = test_client.http.post(
        workflow_operation_endpoint,
        body=b'''{
            "Name": "testOperationName",
            "Type":"Async",
            "Configuration": {
                "MediaType": "Video",
                "Enabled": true
            },
            "StartLambdaArn": "startArn",
            "MonitorLambdaArn": "monitorArn"
        }'''
    )
    
    assert response.status_code == 500
    assert response.json_body['Message'] == "Exception 'An error occurred () when calling the PutRolePolicy operation: '"

def test_create_operation_api_operation(test_client, ddb_resource_stub, iam_client_stub):
    print('POST {endpoint}'.format(endpoint = workflow_operation_endpoint))
    
    stub_get_operation(ddb_resource_stub, optional_output={})
    stub_put_operation(ddb_resource_stub)
    stub_create_stage(ddb_resource_stub)
    operation_input = get_sample_operation_input()
    operation_input['Item']['StageName'] = '_' + test_operation_name
    stub_put_operation(ddb_resource_stub, optional_input=operation_input)
    stub_put_role_policy(iam_client_stub)

    response = test_client.http.post(
        workflow_operation_endpoint,
        body=b'''{
            "Name": "testOperationName",
            "Type":"Async",
            "Configuration": {
                "MediaType": "Video",
                "Enabled": true
            },
            "StartLambdaArn": "startArn",
            "MonitorLambdaArn": "monitorArn"
        }'''
    )
    
    assert response.status_code == 200

def test_update_operation(test_client):
    print('PUT /workflow/operation')
    
    response = test_client.http.put(workflow_operation_endpoint)

    assert response.status_code == 200
    assert response.body == b'{"Message":"Update on stages is not implemented"}'

def test_list_operations(test_client, ddb_resource_stub):
    print('GET /workflow/operation')

    ddb_resource_stub.add_response(
        'scan',
        expected_params = {
            'TableName': 'testOperationTable',
        },
        service_response = {
            'Items': [],
            'LastEvaluatedKey': {}
        }
    )

    ddb_resource_stub.add_response(
        'scan',
        expected_params = {
            'TableName': 'testOperationTable',
            'ExclusiveStartKey': {}
        },
        service_response = {
            'Items': []
        }
    )

    response = test_client.http.get(workflow_operation_endpoint)
    assert response.status_code == 200
    assert len(response.json_body) == 0

def test_get_operation_by_name_no_operation(test_client, ddb_resource_stub):
    print('GET /workflow/operation/{Name}')

    stub_get_operation(ddb_resource_stub, optional_input = {
        'TableName': 'testOperationTable',
        'Key': {
            'Name': test_operation_name
        }
    }, optional_output={})

    response = test_client.http.get('/workflow/operation/{Name}'.format(Name = test_operation_name))
    assert response.status_code == 404

def test_get_operation_by_name(test_client, ddb_resource_stub):
    print('GET /workflow/operation/{Name}')

    stub_get_operation(
        ddb_resource_stub,
        optional_input={
            'TableName': 'testOperationTable',
            'Key': {
                'Name': test_operation_name
            }
        },
        optional_output={
            'Item': {
                'operation': {'S': 'sample'}
            }
        }
    )
    response = test_client.http.get('/workflow/operation/{Name}'.format(Name = test_operation_name))
    assert response.status_code == 200
    assert response.body == b'{"operation":"sample"}'

def test_delete_operation_api_no_operation_available(test_client, ddb_resource_stub):
    print('DELETE /workflow/operation/{Name}')

    stub_get_operation(ddb_resource_stub, optional_output={})
    
    response = test_client.http.delete('/workflow/operation/{Name}'.format(Name = test_operation_name))
    assert response.status_code == 200
    assert response.json_body['Message'] == "Warning: operation '{}' not found".format(test_operation_name)

def test_delete_operation_api_workflow_running(test_client, ddb_resource_stub):
    print('DELETE /workflow/operation/{Name}')

    stub_get_operation(ddb_resource_stub)

    ddb_resource_stub.add_response(
        'scan',
        expected_params = {
            'TableName': 'testWorkflowTable',
            'FilterExpression': botocore.stub.ANY,
            'ConsistentRead': True
        },
        service_response = {
            'Items': [{}]
        }
    )
    
    response = test_client.http.delete('/workflow/operation/{Name}'.format(Name = test_operation_name))
    assert response.status_code == 400
    assert response.json_body['Message'] == """Dependent workflows were found for operation {}.
                    Either delete the dependent workflows or set the query parameter
                    force=true to delete the stage anyhow.  Undeleted dependent workflows
                    will be kept but will contain the deleted definition of the stage.  To
                    find the workflow that depend on a stage use the following endpoint:
                    GET /workflow/list/operation/""".format(test_operation_name)

def test_delete_operation_api(test_client, ddb_resource_stub, iam_client_stub):
    print('DELETE /workflow/operation/{Name}')

    stub_get_operation(ddb_resource_stub)

    ddb_resource_stub.add_response(
        'scan',
        expected_params = {
            'TableName': 'testWorkflowTable',
            'FilterExpression': botocore.stub.ANY,
            'ConsistentRead': True
        },
        service_response = {
            'Items': []
        }
    )
    stub_get_stage(ddb_resource_stub)
    
    ddb_resource_stub.add_response(
        'scan',
        expected_params = {
            'TableName': 'testWorkflowTable',
            'FilterExpression': botocore.stub.ANY,
            'ConsistentRead': True
        },
        service_response = {
            'Items': []
        }
    )

    stub_delete_stage(ddb_resource_stub)

    ddb_resource_stub.add_response(
        'scan',
        expected_params = {
            'TableName': 'testWorkflowTable',
            'FilterExpression': botocore.stub.ANY,
            'ConsistentRead': True
        },
        service_response = {
            'Items': []
        }
    )
    stub_delete_operation(ddb_resource_stub)

    iam_client_stub.add_response(
        'list_role_policies',
        expected_params = {
            'RoleName': 'role',
        },
        service_response = {
            'PolicyNames': [
                test_operation_name
            ]
        }
    )

    iam_client_stub.add_response(
        'delete_role_policy',
        expected_params = {
            'RoleName': 'role',
            'PolicyName': test_operation_name
        },
        service_response = {}
    )

    ddb_resource_stub.add_response(
        'scan',
        expected_params = {
            'TableName': 'testWorkflowTable',
            'FilterExpression': botocore.stub.ANY,
            'ConsistentRead': True
        },
        service_response = {
            'Items': [{
                'Name': {'S':'workflow1'}
            }]
        }
    )
    ddb_resource_stub.add_response(
        'update_item',
        expected_params = {
            'TableName': 'testWorkflowTable',
            'Key': {
                'Name': 'workflow1'
            },
            'UpdateExpression': 'SET StaleOperations = list_append(StaleOperations, :i)',
            'ExpressionAttributeValues': {
                ':i': [test_operation_name]
            },
            'ReturnValues': 'UPDATED_NEW'
        },
        service_response = {}
    )
    
    response = test_client.http.delete('/workflow/operation/{Name}'.format(Name = test_operation_name))
    assert response.status_code == 200
