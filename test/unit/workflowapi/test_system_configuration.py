system_configuration_endpoint = '/system/configuration'

def test_create_system_configuration_api_input_error(test_client):
    print('POST /system/configuration')

    response = test_client.http.post(
        system_configuration_endpoint,
        body=b'{"Name":"MaxConcurrentWorkflows","Value":0}'
    )
    assert response.status_code == 500
    assert response.json_body['Message'] == "ChaliceViewError: Exception 'BadRequestError: MaxConcurrentWorkflows must be a value > 1'"

def test_create_system_configuration_api(test_client, ddb_resource_stub):
    print('POST /system/configuration')

    ddb_resource_stub.add_response(
        'put_item',
        expected_params = {
            'TableName': 'testSystemTable',
            'Item': {
                'Name': 'MaxConcurrentWorkflows',
                'Value': 2
            }
        },
        service_response = {}
    )

    response = test_client.http.post(
        system_configuration_endpoint,
        body=b'{"Name":"MaxConcurrentWorkflows","Value":2}'
    )
    assert response.status_code == 200

def test_get_system_configuration_api_dynamo_error(test_client, ddb_resource_stub):
    print ('GET /system/configuration')
    
    ddb_resource_stub.add_client_error('scan')

    response = test_client.http.get(system_configuration_endpoint)
    assert response.status_code == 500

def test_get_system_configuration_api(test_client, ddb_resource_stub):
    print ('GET /system/configuration')
    
    ddb_resource_stub.add_response(
        'scan',
        expected_params = {
            'TableName': 'testSystemTable',
            'ConsistentRead': True
        },
        service_response = {
            'Items': [{
                'MaxConcurrentWorkflows': { 'N': '2'}
            }]
        }
    )

    response = test_client.http.get(system_configuration_endpoint)
    assert response.body == b'[{"MaxConcurrentWorkflows":2.0}]'