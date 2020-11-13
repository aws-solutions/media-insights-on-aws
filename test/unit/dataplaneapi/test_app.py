import botocore.stub
import json
import uuid


def is_valid_uuid(uuid_to_test, version=4):
    try:
        uuid_obj = uuid.UUID(uuid_to_test, version=version)
    except ValueError:
        return False

    return str(uuid_obj) == uuid_to_test


def test_index(test_client):
    response = test_client.http.get('/')
    assert response.body == b'{"hello":"world"}'


def test_create_asset(test_client, s3_client_stub, ddb_resource_stub):
    s3_client_stub.add_response(
        'put_object',
        expected_params={'Bucket': 'testDataplaneBucketName', 'Key': botocore.stub.ANY},
        service_response={}
    )
    s3_client_stub.add_response(
        'copy_object',
        expected_params={'Bucket': 'testDataplaneBucketName', 'Key': botocore.stub.ANY,
                         'CopySource': {'Bucket': 'InputBucketName', 'Key': 'InputKeyName'}},
        service_response={}
    )
    s3_client_stub.add_response(
        'delete_object',
        expected_params={'Bucket': 'InputBucketName', 'Key': 'InputKeyName'},
        service_response={}
    )
    ddb_resource_stub.add_response(
        'put_item',
        expected_params={
            'Item':
                {
                    'AssetId': botocore.stub.ANY,
                    'S3Bucket': 'testDataplaneBucketName',
                    'S3Key': botocore.stub.ANY,
                    'Created': botocore.stub.ANY
                },
            'TableName': 'testDataplaneTableName'
        },
        service_response={}
    )
    response = test_client.http.post('/create',
                                     body=b'{"Input": {"S3Bucket": "InputBucketName", "S3Key": "InputKeyName"}}')

    formatted_response = json.loads(response.body)
    expected_response_keys = ['AssetId', 'S3Bucket', 'S3Key']

    assert all(item in formatted_response.keys() for item in expected_response_keys)

    asset_id = formatted_response['AssetId']
    assert is_valid_uuid(asset_id)

    s3_key = formatted_response['S3Key']
    assert '/'.join(s3_key.split('/')[0:2]) == 'private/assets'


def test_put_asset_metadata_non_paginated(test_client, s3_client_stub, ddb_resource_stub):
    test_asset_id = str(uuid.uuid4())
    test_method_input = {"OperatorName": "testOperator",
                    "Results": {"serviceName": "testService", "someValue": {"nextValue": "testValue"}},
                    "WorkflowId": "abcd-1234-efgh-5678"}
    test_metadata_key = 'private/assets/' + test_asset_id + '/' + 'workflows' + '/' + test_method_input[
        'WorkflowId'] + '/' + test_method_input['OperatorName'] + '.json'

    test_pointer = [{"workflow": test_method_input["WorkflowId"], "pointer": test_metadata_key}]

    test_update_expression = "SET #operator_result = :result"
    test_expression_attr_name = {"#operator_result": test_method_input["OperatorName"]}
    test_expression_attr_val = {":result": test_pointer}

    ddb_resource_stub.add_response(
        'get_item',
        expected_params={"Key": {"AssetId": test_asset_id}, "TableName": "testDataplaneTableName"},
        service_response={"Item": {}}
    )
    s3_client_stub.add_response(
        'put_object',
        expected_params={"Bucket": "testDataplaneBucketName", "Key": test_metadata_key, "Body": json.dumps(test_method_input["Results"])},
        service_response={}
    )
    ddb_resource_stub.add_response(
        'update_item',
        expected_params={"Key": {"AssetId": test_asset_id}, "UpdateExpression": test_update_expression,
                         "ExpressionAttributeNames": test_expression_attr_name,
                         "ExpressionAttributeValues": test_expression_attr_val,
                         "TableName": "testDataplaneTableName"
                         },
        service_response={}
    )
    response = test_client.http.post('/metadata/{asset_id}'.format(asset_id=test_asset_id),
                                     body=bytes(json.dumps(test_method_input), encoding='utf-8'))

    formatted_response = json.loads(response.body)
    expected_response_keys = ['Status', 'Bucket', 'Key']

    assert all(item in formatted_response.keys() for item in expected_response_keys)

    assert formatted_response['Status'] == 'Success'
    assert formatted_response['Bucket'] == 'testDataplaneBucketName'
    assert formatted_response['Key'] == test_metadata_key


# def test_put_asset_metadata_paginated(test_client, s3_client_stub, ddb_resource_stub):
#     return None
#
#
# def test_put_asset_metadata_paginated_end(test_client, s3_client_stub, ddb_resource_stub):
#     return None
#
#
# def test_put_asset_metadata_asset_not_exist(test_client, s3_client_stub, ddb_resource_stub):
#     return None
