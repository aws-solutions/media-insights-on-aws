import botocore.stub
import botocore.exceptions
import json
import uuid
import boto3
import datetime
from dateutil.tz import tzutc
import io
from botocore.response import StreamingBody


s3 = boto3.client('s3')


def is_valid_uuid(uuid_to_test, version=4):
    try:
        uuid_obj = uuid.UUID(uuid_to_test, version=version)
    except ValueError:
        return False

    return str(uuid_obj) == uuid_to_test


def gen_s3_streaming_object(content):
    content = json.dumps(content)
    encoded_content = content.encode()
    return StreamingBody(io.BytesIO(encoded_content),
                         len(encoded_content))


def test_index(test_client):
    print('GET /')
    response = test_client.http.get('/')
    assert response.body == b'{"hello":"world"}'
    print("Pass")


def test_create_asset(test_client, s3_client_stub, ddb_resource_stub):
    print('POST /create')
    s3_client_stub.add_response(
        'put_object',
        expected_params={'Bucket': 'testDataplaneBucketName', 'Key': botocore.stub.ANY},
        service_response={}
    )
    ddb_resource_stub.add_response(
        'put_item',
        expected_params={
            'Item':
                {
                    'AssetId': botocore.stub.ANY,
                    'MediaType': 'Video',
                    'S3Bucket': 'InputBucketName',
                    'S3Key': 'InputKeyName',
                    'Created': botocore.stub.ANY
                },
            'TableName': 'testDataplaneTableName'
        },
        service_response={}
    )
    response = test_client.http.post('/create',
                                     body=b'{"Input": {"MediaType": "Video", "S3Bucket": "InputBucketName", "S3Key": "InputKeyName"}}')

    formatted_response = json.loads(response.body)
    expected_response_keys = ['AssetId', 'MediaType', 'S3Bucket', 'S3Key']

    assert all(item in formatted_response.keys() for item in expected_response_keys)

    asset_id = formatted_response['AssetId']
    assert is_valid_uuid(asset_id)

    print("Pass")


def test_put_asset_metadata_non_paginated(test_client, s3_client_stub, ddb_resource_stub):
    print('POST /metadata/{asset_id}')
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

    assert response.status_code == 200
    formatted_response = json.loads(response.body)
    expected_response_keys = ['Status', 'Bucket', 'Key']

    assert all(item in formatted_response.keys() for item in expected_response_keys)

    assert formatted_response['Status'] == 'Success'
    assert formatted_response['Bucket'] == 'testDataplaneBucketName'
    assert formatted_response['Key'] == test_metadata_key
    print("Pass")


def test_put_asset_metadata_paginated(test_client, s3_client_stub, ddb_resource_stub):
    print('POST /metadata/{asset_id}?paginated=true')
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
    s3_client_stub.add_client_error(
        'get_object',
        expected_params={"Bucket": "testDataplaneBucketName", "Key": test_metadata_key},
        service_error_code='404'
    )
    s3_client_stub.add_response(
        'put_object',
        expected_params={"Bucket": "testDataplaneBucketName", "Key": test_metadata_key, "Body": botocore.stub.ANY},
        service_response={}
    )
    response = test_client.http.post('/metadata/{asset_id}?paginated=true'.format(asset_id=test_asset_id),
                                     body=bytes(json.dumps(test_method_input), encoding='utf-8'))
    assert response.status_code == 200
    formatted_response = json.loads(response.body)
    print(formatted_response)
    print('Pass')


def test_put_asset_metadata_paginated_end(test_client, s3_client_stub, ddb_resource_stub):
    print('POST /metadata/{asset_id}?paginated=true&end=true')
    test_s3_get_object_response = {'ResponseMetadata': {'RequestId': 'C6B8150894ABC0CE',
                                                        'HostId': 'AF2tM9QcyL4DJlvHpccJBKOgOQbydnQLjfplgHGT8Fo+BNWrzjCeRcNyBkzKoTru1pG5nFWfPfM=',
                                                        'HTTPStatusCode': 200, 'HTTPHeaders': {
            'x-amz-id-2': 'AF2tM9QcyL4DJlvHpccJBKOgOQbydnQLjfplgHGT8Fo+BNWrzjCeRcNyBkzKoTru1pG5nFWfPfM=',
            'x-amz-request-id': 'C6B8150894ABC0CE', 'date': 'Mon, 23 Nov 2020 20:45:06 GMT',
            'last-modified': 'Fri, 13 Nov 2020 01:09:08 GMT', 'etag': '"6e6e13b8c0dcd187864fb3d4a7fce913"',
            'accept-ranges': 'bytes', 'content-type': 'binary/octet-stream', 'content-length': '10279',
            'server': 'AmazonS3'}, 'RetryAttempts': 0}, 'AcceptRanges': 'bytes',
                                   'LastModified': datetime.datetime(2020, 11, 13, 1, 9, 8, tzinfo=tzutc()),
                                   'ContentLength': 10279, 'ETag': '"6e6e13b8c0dcd187864fb3d4a7fce913"',
                                   'ContentType': 'binary/octet-stream', 'Metadata': {}, 'Body': gen_s3_streaming_object([{"serviceName": "testService", "someValue": {"nextValue": "testValue"}}])}

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
        'get_object',
        expected_params={"Bucket": "testDataplaneBucketName", "Key": test_metadata_key},
        service_response=test_s3_get_object_response
    )
    s3_client_stub.add_response(
        'put_object',
        expected_params={"Bucket": "testDataplaneBucketName", "Key": test_metadata_key, "Body": botocore.stub.ANY},
        service_response={}
    )
    ddb_resource_stub.add_response(
        'update_item',
        expected_params={"Key": {"AssetId": test_asset_id}, "UpdateExpression": test_update_expression,
                         "ExpressionAttributeNames": test_expression_attr_name,
                         "ExpressionAttributeValues": test_expression_attr_val,
                         "TableName": "testDataplaneTableName"
                         },
        service_response={})

    response = test_client.http.post('/metadata/{asset_id}?paginated=true&end=true'.format(asset_id=test_asset_id),
                                     body=bytes(json.dumps(test_method_input), encoding='utf-8'))
    assert response.status_code == 200
    formatted_response = json.loads(response.body)
    print(formatted_response)
    print('Pass')
