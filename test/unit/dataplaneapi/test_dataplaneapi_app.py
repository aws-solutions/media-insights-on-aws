import botocore.stub
import botocore.exceptions
import json
import uuid
import boto3
import datetime
from dateutil.tz import tzutc
import io
from botocore.response import StreamingBody
import base64

s3 = boto3.client('s3')

def encode_cursor(cursor):
    cursor = json.dumps(cursor)
    encoded = base64.urlsafe_b64encode(cursor.encode('UTF-8')).decode('ascii')
    return encoded

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

def test_version(test_client):
    print('GET /version')
    response = test_client.http.get('/version')
    assert response.body == b'{"ApiVersion":"3.0.0","FrameworkVersion":"v9.9.9"}'
    print ("Pass")

def test_upload_should_fail(test_client):
    print('POST /upload')
    response = test_client.http.post('/upload',
        body=b'{"S3Key": "testBucketKey"}'
    )
    assert response.body == b'{"Code":"ChaliceViewError","Message":"ChaliceViewError: Unable to generate pre-signed S3 URL for uploading media: \'S3Bucket\'"}'
    print ('Pass')

def test_upload_success(test_client):
    print('POST /upload')
    response = test_client.http.post(
        '/upload',
        body=b'{"S3Bucket": "testBucketName", "S3Key": "testBucketKey"}'
    )
    formatted_response = json.loads(response.body)
    assert formatted_response['url'] == 'https://s3.amazonaws.com/testBucketName'
    assert formatted_response['fields'] != None
    assert formatted_response['fields']['key'] == 'testBucketKey'
    assert formatted_response['fields']['x-amz-algorithm'] != None
    assert formatted_response['fields']['x-amz-credential'] != None
    assert formatted_response['fields']['x-amz-date'] != None
    assert formatted_response['fields']['x-amz-security-token'] != None
    assert formatted_response['fields']['x-amz-signature'] != None
    assert formatted_response['fields']['policy'] != None
    print ('Pass')

def test_download_fail(test_client):
    print('POST /download')
    response = test_client.http.post(
        '/download',
        body=b'{"S3Key": "testBucketKey"}'
    )
    assert response.body == b'{"Code":"ChaliceViewError","Message":"ChaliceViewError: Unable to generate pre-signed S3 URL for downloading media: \'S3Bucket\'"}'
    print ('Pass')

def test_download_success(test_client):
    print('POST /download')
    response = test_client.http.post(
        '/download',
        body=b'{"S3Bucket": "testBucketName", "S3Key": "testBucketKey"}'
    )
    assert response.status_code == 200
    assert response.body != None
    print('Pass')

def test_media_upload_path_success(test_client):
    print('GET /mediapath/{asset_id}/{workflow_id}')
    asset_id = 'testAssetId'
    workflow_id = 'testWorkflowId'
    response = test_client.http.get(
        '/mediapath/{asset_id}/{workflow_id}'.format(asset_id = asset_id, workflow_id = workflow_id)
    )
    assert response.body == b'{"S3Bucket":"testDataplaneBucketName","S3Key":"private/assets/testAssetId/workflows/testWorkflowId/"}'
    print('Pass')

def test_create_asset_input_error(test_client, s3_client_stub):
    print('POST /create')

    response = test_client.http.post(
        '/create',
        body=b'{"Input": {"MediaType": "Video", "S3Bucket": "InputBucketName"}}')

    assert response.status_code == 400
    formatted_response = json.loads(response.body)
    assert formatted_response['Code'] == 'BadRequestError'
    assert formatted_response['Message'] == 'BadRequestError: Missing required inputs for asset creation: \'S3Key\''
    print("Pass")

def test_create_asset_s3_error(test_client, s3_client_stub):
    print('POST /create')
    
    s3_client_stub.add_client_error('put_object')

    response = test_client.http.post(
        '/create',
        body=b'{"Input": {"MediaType": "Video", "S3Bucket": "InputBucketName", "S3Key": "InputKeyName"}}')

    assert response.status_code == 500
    print("Pass")

def test_create_asset_dynamo_error(test_client, s3_client_stub, ddb_resource_stub):
    print('POST /create')

    s3_client_stub.add_response(
        'put_object',
        expected_params={'Bucket': 'testDataplaneBucketName', 'Key': botocore.stub.ANY},
        service_response={}
    )
    ddb_resource_stub.add_client_error('put_item')

    response = test_client.http.post(
        '/create',
        body=b'{"Input": {"MediaType": "Video", "S3Bucket": "InputBucketName", "S3Key": "InputKeyName"}}')

    assert response.status_code == 500
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
    response = test_client.http.post(
        '/create',
        body=b'{"Input": {"MediaType": "Video", "S3Bucket": "InputBucketName", "S3Key": "InputKeyName"}}')

    formatted_response = json.loads(response.body)
    expected_response_keys = ['AssetId', 'MediaType', 'S3Bucket', 'S3Key']

    assert all(item in formatted_response.keys() for item in expected_response_keys)

    asset_id = formatted_response['AssetId']
    assert is_valid_uuid(asset_id)

    print("Pass")

def test_put_asset_metadata_input_error1(test_client, s3_client_stub, ddb_resource_stub):
    print('POST /metadata/{asset_id}')
    test_asset_id = str(uuid.uuid4())

    response = test_client.http.post(
        '/metadata/{asset_id}?wrong_param=wrong'.format(asset_id=test_asset_id),
        body=b'{}'
    )
    assert response.status_code == 400
    print("Pass")

def test_put_asset_metadata_input_error2(test_client, s3_client_stub, ddb_resource_stub):
    print('POST /metadata/{asset_id}')
    test_asset_id = str(uuid.uuid4())

    response = test_client.http.post(
        '/metadata/{asset_id}?paginated=true'.format(asset_id=test_asset_id),
        body=b'{}'
    )
    assert response.status_code == 400
    print("Pass")

def test_put_asset_metadata_input_error3(test_client, s3_client_stub, ddb_resource_stub):
    print('POST /metadata/{asset_id}')
    test_asset_id = str(uuid.uuid4())

    response = test_client.http.post(
        '/metadata/{asset_id}?paginated=true&end=false'.format(asset_id=test_asset_id),
        body=b'{}'
    )
    assert response.status_code == 400
    print("Pass")

def test_put_asset_metadata_input_error4(test_client, s3_client_stub, ddb_resource_stub):
    print('POST /metadata/{asset_id}')
    test_asset_id = str(uuid.uuid4())

    response = test_client.http.post(
        '/metadata/{asset_id}?paginated=true&end=true'.format(asset_id=test_asset_id),
        body=b'{}'
    )
    assert response.status_code == 400
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

def test_put_asset_metadata_paginated_dynamo_error(test_client, s3_client_stub, ddb_resource_stub):
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

    ddb_resource_stub.add_client_error('get_item')
    response = test_client.http.post('/metadata/{asset_id}?paginated=true'.format(asset_id=test_asset_id),
                                     body=bytes(json.dumps(test_method_input), encoding='utf-8'))
    assert response.status_code == 500
    print('Pass')

def test_put_asset_metadata_dynamo_error(test_client, s3_client_stub, ddb_resource_stub):
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
    ddb_resource_stub.add_client_error('update_item')

    response = test_client.http.post('/metadata/{asset_id}?paginated=true&end=true'.format(asset_id=test_asset_id),
                                     body=bytes(json.dumps(test_method_input), encoding='utf-8'))
    assert response.status_code == 500
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

def test_get_asset_metadata_first_call_without_returned_cursor(test_client, ddb_resource_stub):
    print('GET /metadata/{asset_id}')
    test_asset_id = str(uuid.uuid4())
    
    test_attributes = {
        'MediaType': {'S': 'testMediaType'},
        'S3Key': {'S': 'testS3Key'},
        'S3Bucket': {'S': 'testS3Bucket'},
        'Created': {'S': 'testCreated'}
    }

    ddb_resource_stub.add_response(
        'get_item',
        expected_params={
            "Key": {
                "AssetId": test_asset_id,
            },
            "TableName": "testDataplaneTableName"
        },
        service_response={
            "Item": {
                "MediaType": test_attributes['MediaType'],
                "S3Key": test_attributes['S3Key'],
                "S3Bucket": test_attributes['S3Bucket'],
                "Created": test_attributes['Created']
            }
        }
    )
    
    response = test_client.http.get(
        '/metadata/{asset_id}'.format(asset_id = test_asset_id)
    )
    formatted_response = json.loads(response.body)
    assert formatted_response['asset_id'] == test_asset_id
    assert formatted_response['results'] != None

    for attribute in test_attributes.keys():
        assert formatted_response['results'][attribute] == test_attributes[attribute]['S']
    print('Pass')

def test_get_asset_metadata_first_call_without_returned_cursor(test_client, ddb_resource_stub):
    print('GET /metadata/{asset_id}')
    test_asset_id = str(uuid.uuid4())
    
    test_attributes = {
        'MediaType': {'S': 'testMediaType'},
        'S3Key': {'S': 'testS3Key'},
        'S3Bucket': {'S': 'testS3Bucket'},
        'Created': {'S': 'testCreated'}
    }

    ddb_resource_stub.add_client_error('get_item')
    
    response = test_client.http.get(
        '/metadata/{asset_id}'.format(asset_id = test_asset_id)
    )
    assert response.status_code == 500
    print('Pass')

def test_get_asset_metadata_first_call_with_returned_cursor(test_client, ddb_resource_stub):
    print('GET /metadata/{asset_id}')
    test_asset_id = str(uuid.uuid4())

    test_cursor = {
        'next': {
            'RandomAttribute': 'testPointer',
            'page': 0
        },
        'remaining': [{
            'RandomAttribute': 'testPointer',
            'page': 0
        }]
    }

    test_attributes = {
        'MediaType': {'S': 'testMediaType'},
        'S3Key': {'S': 'testS3Key'},
        'S3Bucket': {'S': 'testS3Bucket'},
        'Created': {'S': 'testCreated'},
        'RandomAttribute': {
            'L': [{
                'M': {
                    "pointer": {
                        'S': 'testPointer'
                    }
                }
            }]
        }
    }

    ddb_resource_stub.add_response(
        'get_item',
        expected_params={
            "Key": {
                "AssetId": test_asset_id,
            },
            "TableName": "testDataplaneTableName"
        },
        service_response={
            "Item": {
                "MediaType": test_attributes['MediaType'],
                "S3Key": test_attributes['S3Key'],
                "S3Bucket": test_attributes['S3Bucket'],
                "Created": test_attributes['Created'],
                "RandomAttribute": test_attributes['RandomAttribute']
            }
        }
    )
    
    response = test_client.http.get(
        '/metadata/{asset_id}'.format(asset_id = test_asset_id)
    )
    formatted_response = json.loads(response.body)
    assert formatted_response['asset_id'] == test_asset_id
    assert formatted_response['results'] != None
    assert formatted_response['cursor'] != None
    assert formatted_response['cursor'] == encode_cursor(test_cursor)
    for attribute in test_attributes.keys():
        if attribute == 'RandomAttribute':
            continue
        assert formatted_response['results'][attribute] == test_attributes[attribute]['S']
    print('Pass')

def test_get_asset_metadata_cursor_call(test_client, s3_client_stub):
    print('GET /metadata/{asset_id}?cursor={cursor}')
    test_asset_id = str(uuid.uuid4())
    test_cursor = {
        'next': {
            'RandomAttribute': 'testPointer',
            'page': 0
        },
        'remaining': [{
            'RandomAttribute': 'testPointer',
            'page': 0
        }]
    }

    s3_client_stub.add_response(
        'get_object',
        expected_params = {
            "Bucket": "testDataplaneBucketName",
            "Key": "testPointer"
        },  
        service_response = {
            'Body': gen_s3_streaming_object('testOperator')
        }
    )
    
    response = test_client.http.get(
        '/metadata/{asset_id}?cursor={test_cursor}'.format(asset_id = test_asset_id, test_cursor = encode_cursor(test_cursor))
    )
    formatted_response = json.loads(response.body)
    assert formatted_response['asset_id'] == test_asset_id
    assert formatted_response['operator'] == 'RandomAttribute'
    assert formatted_response['results'] == 'testOperator'
    print('Pass')

def test_get_asset_metadata_cursor_call_with_remaining(test_client, s3_client_stub):
    print('GET /metadata/{asset_id}?cursor={cursor}')
    test_asset_id = str(uuid.uuid4())
    test_cursor = {
        'next': {
            'RandomAttribute': 'testPointer',
            'page': 0
        },
        'remaining': [{
            'RandomAttribute': 'testPointer',
            'page': 0
        }, {
            'RandomAttribute': 'testPointer',
            'page': 1
        }]
    }

    s3_client_stub.add_response(
        'get_object',
        expected_params = {
            "Bucket": "testDataplaneBucketName",
            "Key": "testPointer"
        },  
        service_response = {
            'Body': gen_s3_streaming_object('testOperator')
        }
    )
    
    response = test_client.http.get(
        '/metadata/{asset_id}?cursor={test_cursor}'.format(asset_id = test_asset_id, test_cursor = encode_cursor(test_cursor))
    )
    formatted_response = json.loads(response.body)
    assert formatted_response['asset_id'] == test_asset_id
    assert formatted_response['operator'] == 'RandomAttribute'
    assert formatted_response['results'] == 'testOperator'
    assert formatted_response['cursor'] == encode_cursor({
        "next": {
            'RandomAttribute': 'testPointer',
            'page': 0
        },
        "remaining": [{
            'RandomAttribute': 'testPointer',
            'page': 0
        }]
    })
    print('Pass')

def test_get_asset_metadata_cursor_call_single_operator(test_client, s3_client_stub):
    print('GET /metadata/{asset_id}?cursor={cursor}')
    test_asset_id = str(uuid.uuid4())
    test_cursor = {
        'next': {
            'RandomAttribute': 'testPointer',
            'page': 0
        },
        'remaining': [{
            'RandomAttribute': 'testPointer',
            'page': 0
        }]
    }

    s3_client_stub.add_response(
        'get_object',
        expected_params = {
            "Bucket": "testDataplaneBucketName",
            "Key": "testPointer"
        },  
        service_response = {
            'Body': gen_s3_streaming_object(['testOperator1'])
        }
    )
    
    response = test_client.http.get(
        '/metadata/{asset_id}?cursor={test_cursor}'.format(asset_id = test_asset_id, test_cursor = encode_cursor(test_cursor))
    )
    formatted_response = json.loads(response.body)
    assert formatted_response['asset_id'] == test_asset_id
    assert formatted_response['operator'] == 'RandomAttribute'
    assert formatted_response['results'] == 'testOperator1'
    print('Pass')

def test_get_asset_metadata_cursor_call_multi_operator(test_client, s3_client_stub):
    print('GET /metadata/{asset_id}?cursor={cursor}')
    test_asset_id = str(uuid.uuid4())
    test_cursor = {
        'next': {
            'RandomAttribute': 'testPointer',
            'page': 0
        },
        'remaining': []
    }

    s3_client_stub.add_response(
        'get_object',
        expected_params = {
            "Bucket": "testDataplaneBucketName",
            "Key": "testPointer"
        },  
        service_response = {
            'Body': gen_s3_streaming_object(['testOperator1', 'testOperator2'])
        }
    )
    
    response = test_client.http.get(
        '/metadata/{asset_id}?cursor={test_cursor}'.format(asset_id = test_asset_id, test_cursor = encode_cursor(test_cursor))
    )
    formatted_response = json.loads(response.body)
    assert formatted_response['asset_id'] == test_asset_id
    assert formatted_response['operator'] == 'RandomAttribute'
    assert formatted_response['results'] == 'testOperator1'
    assert formatted_response['cursor'] == encode_cursor({
        'next': {
            'RandomAttribute': 'testPointer',
            'page': 1
        },
        'remaining': []
    })
    print('Pass')

def test_get_asset_metadata_cursor_call_with_remaining_multi_operator(test_client, s3_client_stub):
    print('GET /metadata/{asset_id}?cursor={cursor}')
    test_asset_id = str(uuid.uuid4())
    test_cursor = {
        'next': {
            'RandomAttribute': 'testPointer',
            'page': 0
        },
        'remaining': [{
            'RandomAttribute': 'testPointer',
            'page': 1
        }, {
            'RandomAttribute': 'testPointer',
            'page': 2
        }]
    }

    s3_client_stub.add_response(
        'get_object',
        expected_params = {
            "Bucket": "testDataplaneBucketName",
            "Key": "testPointer"
        },  
        service_response = {
            'Body': gen_s3_streaming_object(['testOperator1', 'testOperator2'])
        }
    )
    
    response = test_client.http.get(
        '/metadata/{asset_id}?cursor={test_cursor}'.format(asset_id = test_asset_id, test_cursor = encode_cursor(test_cursor))
    )
    formatted_response = json.loads(response.body)
    assert formatted_response['asset_id'] == test_asset_id
    assert formatted_response['operator'] == 'RandomAttribute'
    assert formatted_response['results'] == 'testOperator1'
    assert formatted_response['cursor'] == encode_cursor({
        "next": {
            'RandomAttribute': 'testPointer',
            'page': 1
        },
        "remaining": [{
            'RandomAttribute': 'testPointer',
            'page': 1
        }, {
            'RandomAttribute': 'testPointer',
            'page': 2
        }]
    })
    print('Pass')

def test_get_asset_metadata_operator_first_call_dynamo_error(test_client, s3_client_stub, ddb_resource_stub):
    print('GET /metadata/{asset_id}/{operator_name}')
    
    test_asset_id = str(uuid.uuid4())
    test_operator_name = 'testOperator'

    ddb_resource_stub.add_client_error('get_item')

    response = test_client.http.get(
        '/metadata/{asset_id}/{operator_name}'.format(asset_id = test_asset_id, operator_name = test_operator_name)
    )
    assert response.status_code == 500

def test_get_asset_metadata_operator_first_call_single_metadata(test_client, s3_client_stub, ddb_resource_stub):
    print('GET /metadata/{asset_id}/{operator_name}')
    
    test_asset_id = str(uuid.uuid4())
    test_operator_name = 'testOperator'

    ddb_resource_stub.add_response(
        'get_item',
        expected_params = {
            "Key": {
                "AssetId": test_asset_id,
            },
            "ProjectionExpression": "#attr",
            "ExpressionAttributeNames": {"#attr": test_operator_name},
            "TableName": "testDataplaneTableName"
        },
        service_response = {
            "Item": {
                "testOperator": {
                    "L": [
                        {
                            "M": {
                                "pointer": {
                                    "S": "testPointer"
                                }
                            }
                        }
                    ]
                }
            }
        }
    )

    s3_client_stub.add_response(
        'get_object',
        expected_params = {
            "Bucket": "testDataplaneBucketName",
            "Key": "testPointer"
        },  
        service_response = {
            'Body': gen_s3_streaming_object('testOperator1')
        }
    )

    response = test_client.http.get(
        '/metadata/{asset_id}/{operator_name}'.format(asset_id = test_asset_id, operator_name = test_operator_name)
    )
    formatted_response = json.loads(response.body)
    assert formatted_response['asset_id'] == test_asset_id
    assert formatted_response['operator'] == test_operator_name
    assert formatted_response['results'] == 'testOperator1'

def test_get_asset_metadata_cursor_call_with_remaining_multi_operator(test_client, s3_client_stub):
    print('GET /metadata/{asset_id}?cursor={cursor}')
    test_asset_id = str(uuid.uuid4())
    test_cursor = {
        'next': {
            'RandomAttribute': 'testPointer',
            'page': 0
        },
        'remaining': [{
            'RandomAttribute': 'testPointer',
            'page': 1
        }, {
            'RandomAttribute': 'testPointer',
            'page': 2
        }]
    }

    s3_client_stub.add_response(
        'get_object',
        expected_params = {
            "Bucket": "testDataplaneBucketName",
            "Key": "testPointer"
        },  
        service_response = {
            'Body': gen_s3_streaming_object(['testOperator1', 'testOperator2'])
        }
    )
    
    response = test_client.http.get(
        '/metadata/{asset_id}?cursor={test_cursor}'.format(asset_id = test_asset_id, test_cursor = encode_cursor(test_cursor))
    )
    formatted_response = json.loads(response.body)
    assert formatted_response['asset_id'] == test_asset_id
    assert formatted_response['operator'] == 'RandomAttribute'
    assert formatted_response['results'] == 'testOperator1'
    assert formatted_response['cursor'] == encode_cursor({
        "next": {
            'RandomAttribute': 'testPointer',
            'page': 1
        },
        "remaining": [{
            'RandomAttribute': 'testPointer',
            'page': 1
        }, {
            'RandomAttribute': 'testPointer',
            'page': 2
        }]
    })
    print('Pass')

def test_get_asset_metadata_operator_first_call_multiple_metadata(test_client, s3_client_stub, ddb_resource_stub):
    print('GET /metadata/{asset_id}/{operator_name}')
    
    test_asset_id = str(uuid.uuid4())
    test_operator_name = 'testOperator'

    ddb_resource_stub.add_response(
        'get_item',
        expected_params = {
            "Key": {
                "AssetId": test_asset_id,
            },
            "ProjectionExpression": "#attr",
            "ExpressionAttributeNames": {"#attr": test_operator_name},
            "TableName": "testDataplaneTableName"
        },
        service_response = {
            "Item": {
                "testOperator": {
                    "L": [
                        {
                            "M": {
                                "pointer": {
                                    "S": "testPointer"
                                }
                            }
                        }
                    ]
                }
            }
        }
    )

    s3_client_stub.add_response(
        'get_object',
        expected_params = {
            "Bucket": "testDataplaneBucketName",
            "Key": "testPointer"
        },  
        service_response = {
            'Body': gen_s3_streaming_object(['testOperator', 'testOperator2'])
        }
    )

    response = test_client.http.get(
        '/metadata/{asset_id}/{operator_name}'.format(asset_id = test_asset_id, operator_name = test_operator_name)
    )
    formatted_response = json.loads(response.body)
    assert formatted_response['asset_id'] == test_asset_id
    assert formatted_response['operator'] == test_operator_name
    assert formatted_response['results'] == 'testOperator'
    assert formatted_response['cursor'] == encode_cursor({
        'next': {
            'testOperator': 'testPointer',
            'page': 1
        },
        'remaining': ['testOperator']
    })
def test_get_asset_metadata_operator_cursor_call(test_client, s3_client_stub, ddb_resource_stub):
    print('GET /metadata/{asset_id}/{operator_name}')
    
    test_asset_id = str(uuid.uuid4())
    test_operator_name = 'testOperator'
    test_cursor = {
        'next': {
            'testOperator': 'testPointer',
            'page': 0
        },
        'remaining': [{
            'RandomAttribute': 'testPointer',
            'page': 1
        }, {
            'RandomAttribute': 'testPointer',
            'page': 2
        }]
    }

    s3_client_stub.add_response(
        'get_object',
        expected_params = {
            "Bucket": "testDataplaneBucketName",
            "Key": "testPointer"
        },  
        service_response = {
            'Body': gen_s3_streaming_object(['testOperator', 'testOperator2'])
        }
    )

    response = test_client.http.get(
        '/metadata/{asset_id}/{operator_name}?cursor={test_cursor}'.format(asset_id = test_asset_id, operator_name = test_operator_name, test_cursor = encode_cursor(test_cursor))
    )
    formatted_response = json.loads(response.body)
    assert formatted_response['asset_id'] == test_asset_id
    assert formatted_response['operator'] == test_operator_name
    assert formatted_response['results'] == 'testOperator'
    assert formatted_response['cursor'] == encode_cursor({
        'next': {
            'testOperator': 'testPointer',
            'page': 1
        },
        'remaining': ['testOperator']
    })

def test_lock_asset_dynamo_error(test_client, ddb_client_stub):
    print('POST /checkout/{asset_id}')
    test_asset_id = str(uuid.uuid4())
    test_user_name = 'testUserName'

    ddb_client_stub.add_client_error('update_item')

    response = test_client.http.post(
        '/checkout/{asset_id}'.format(asset_id = test_asset_id),
        body = b'{"LockedBy": "testUserName"}'
    )
    assert response.status_code == 500

def test_lock_asset(test_client, ddb_client_stub):
    print('POST /checkout/{asset_id}')
    test_asset_id = str(uuid.uuid4())
    test_user_name = 'testUserName'

    ddb_client_stub.add_response(
        'update_item',
        expected_params = {
            'TableName': 'testDataplaneTableName',
            'Key': {'AssetId': {'S': test_asset_id}},
            'UpdateExpression': 'set Locked = :locked, LockedBy = :lockedby, LockedAt = :timestamp',
            'ExpressionAttributeValues': {':locked': {'S': 'true'}, ':lockedby': {'S': test_user_name}, ':timestamp': {'N': botocore.stub.ANY}},
            'ConditionExpression': 'attribute_not_exists(LockedBy) and attribute_not_exists(LockedAt)'
        },
        service_response = {
            'ResponseMetadata': {
                'HTTPStatusCode': 200
            }
        }
    )

    response = test_client.http.post(
        '/checkout/{asset_id}'.format(asset_id = test_asset_id),
        body = b'{"LockedBy": "testUserName"}'
    )
    assert response != None
    assert response.status_code == 200

def test_unlock_asset_dynamo_error(test_client, ddb_client_stub):
    print('POST /checkin/{asset_id}')
    test_asset_id = str(uuid.uuid4())

    ddb_client_stub.add_client_error('update_item')

    response = test_client.http.post(
        '/checkin/{asset_id}'.format(asset_id = test_asset_id),
        body = b'{"LockedBy": "testUserName"}'
    )
    assert response.status_code == 500

def test_unlock_asset(test_client, ddb_client_stub):
    print('POST /checkin/{asset_id}')
    test_asset_id = str(uuid.uuid4())

    ddb_client_stub.add_response(
        'update_item',
        expected_params = {
            'TableName': 'testDataplaneTableName',
            'Key': {'AssetId': {'S': test_asset_id}},
            'UpdateExpression': 'remove Locked, LockedAt, LockedBy',
            'ConditionExpression': 'attribute_exists(Locked) and attribute_exists(LockedBy) and attribute_exists(LockedAt)'
        },
        service_response = {
            'ResponseMetadata': {
                'HTTPStatusCode': 200
            }
        }
    )

    response = test_client.http.post(
        '/checkin/{asset_id}'.format(asset_id = test_asset_id),
        body = b'{"LockedBy": "testUserName"}'
    )
    assert response != None
    assert response.status_code == 200

def test_list_all_locked_assets_dynamo_error(test_client, ddb_client_stub):
    print('GET /checkouts')

    ddb_client_stub.add_client_error('query')

    response = test_client.http.get(
        '/checkouts',
    )
    assert response.status_code == 500

def test_list_all_locked_assets(test_client, ddb_client_stub):
    print('GET /checkouts')

    ddb_client_stub.add_response(
        'query',
        expected_params = {
            'TableName': 'testDataplaneTableName',
            'IndexName': "LockIndex",
            'KeyConditionExpression': 'Locked=:locked',
            'ExpressionAttributeValues': {":locked": {"S": "true"}}
        },
        service_response = {
            'Items': [{
                'AssetId': { 'S': 'testAssetId' },
                'LockedBy': { 'S': 'testUserName' },
                'LockedAt': { 'N': '0' }
            }]
        }
    )

    response = test_client.http.get(
        '/checkouts',
    )
    assert response != None
    assert response.status_code == 200
    formatted_response = json.loads(response.body)
    assert formatted_response != None
    assert len(formatted_response['locks']) == 1
    assert formatted_response['locks'][0]['AssetId'] == 'testAssetId'
    assert formatted_response['locks'][0]['LockedBy'] == 'testUserName'
    assert formatted_response['locks'][0]['LockedAt'] == '0'

def test_list_all_assets_dynamo_error(test_client, ddb_resource_stub):
    print('GET /metadata')

    ddb_resource_stub.add_client_error('scan')

    response = test_client.http.get('/metadata')

    assert response.status_code == 500

def test_list_all_assets_no_assets(test_client, ddb_resource_stub):
    print('GET /metadata')

    ddb_resource_stub.add_response(
        'scan',
        expected_params = {
            'TableName': 'testDataplaneTableName',
            'Select': 'SPECIFIC_ATTRIBUTES',
            'AttributesToGet': ['AssetId']
        },
        service_response = {
            'Items': []
        }
    )

    response = test_client.http.get('/metadata')

    assert response.status_code == 200
    assert response.body == b'{"assets":[]}'

def test_list_all_assets(test_client, ddb_resource_stub):
    print('GET /metadata')

    ddb_resource_stub.add_response(
        'scan',
        expected_params = {
            'TableName': 'testDataplaneTableName',
            'Select': 'SPECIFIC_ATTRIBUTES',
            'AttributesToGet': ['AssetId']
        },
        service_response = {
            'Items': [{
                'AssetId': { 'S': 'testAssetId' }
            }]
        }
    )

    response = test_client.http.get('/metadata')

    assert response.status_code == 200
    assert response.body == b'{"assets":["testAssetId"]}'

def test_delete_operator_metadata_dynamo_error(test_client, ddb_resource_stub):
    print('DELETE /metadata/{asset_id}/{operator_name}')
    
    test_asset_id = 'testAssetId'
    test_operator_name = 'testOperatorName'

    ddb_resource_stub.add_client_error('update_item')

    response = test_client.http.delete(
        '/metadata/{asset_id}/{operator_name}'.format(asset_id = test_asset_id, operator_name = test_operator_name)
    )
    assert response.status_code == 500

def test_delete_operator_metadata_s3_error(test_client, ddb_resource_stub, s3_client_stub):
    print('DELETE /metadata/{asset_id}/{operator_name}')
    
    test_asset_id = 'testAssetId'
    test_operator_name = 'testOperatorName'

    ddb_resource_stub.add_response(
        'update_item',
        expected_params = {
            'TableName': 'testDataplaneTableName',
            'Key': {
                'AssetId': test_asset_id
            },
            'UpdateExpression': 'REMOVE #operator',
            'ExpressionAttributeNames': {"#operator": test_operator_name},
            'ReturnValues': 'UPDATED_OLD'
        },
        service_response = {
            'Attributes': {
                'testOperatorName': {
                    'L': [{
                        'M': {
                            'testPointer': {'S': 'testPointerValue'},
                        }
                    }]
                }
            }
        }
    )

    s3_client_stub.add_client_error('delete_objects')

    response = test_client.http.delete(
        '/metadata/{asset_id}/{operator_name}'.format(asset_id = test_asset_id, operator_name = test_operator_name)
    )
    assert response.status_code == 500

def test_delete_operator_metadata(test_client, ddb_resource_stub, s3_client_stub):
    print('DELETE /metadata/{asset_id}/{operator_name}')
    
    test_asset_id = 'testAssetId'
    test_operator_name = 'testOperatorName'

    ddb_resource_stub.add_response(
        'update_item',
        expected_params = {
            'TableName': 'testDataplaneTableName',
            'Key': {
                'AssetId': test_asset_id
            },
            'UpdateExpression': 'REMOVE #operator',
            'ExpressionAttributeNames': {"#operator": test_operator_name},
            'ReturnValues': 'UPDATED_OLD'
        },
        service_response = {
            'Attributes': {
                'testOperatorName': {
                    'L': [{
                        'M': {
                            'testPointer': {'S': 'testPointerValue'},
                        }
                    }]
                }
            }
        }
    )

    s3_client_stub.add_response(
        'delete_objects',
        expected_params = {
            'Bucket': 'testDataplaneBucketName',
            'Delete': {
                'Objects': [{
                    'Key': 'testPointerValue'
                }]
            }
        },
        service_response = {}
    )

    response = test_client.http.delete(
        '/metadata/{asset_id}/{operator_name}'.format(asset_id = test_asset_id, operator_name = test_operator_name)
    )
    assert response.status_code == 200
    assert response.body == b'{}'

def test_delete_asset_dynamo_error(test_client, ddb_resource_stub):
    print('DELETE /metadata/{asset_id}')

    test_asset_id = str(uuid.uuid4())
    
    ddb_resource_stub.add_client_error('delete_item')

    response = test_client.http.delete(
        '/metadata/{asset_id}'.format(asset_id = test_asset_id)
    )
    assert response.status_code == 500


def test_delete_asset_s3_delete_error(test_client, ddb_resource_stub, s3_client_stub, s3_resource_stub):
    print('DELETE /metadata/{asset_id}')

    test_asset_id = str(uuid.uuid4())
    
    ddb_resource_stub.add_response(
        'delete_item',
        expected_params = {
            'TableName': 'testDataplaneTableName',
            'Key': {
                'AssetId': test_asset_id
            },
            'ReturnValues': 'ALL_OLD'
        },
        service_response = {
            'Attributes': {
                'S3Key': {'S': 'testKeyValue'},
                'testOperatorName': {
                    'L': [{
                        'M': {
                            'testPointer': {'S': 'testPointerValue'},
                        }
                    }]
                }
            }
        }
    )

    s3_client_stub.add_client_error('delete_objects')

    response = test_client.http.delete(
        '/metadata/{asset_id}'.format(asset_id = test_asset_id)
    )
    assert response.status_code == 500

def test_delete_asset_s3_delete_error2(test_client, ddb_resource_stub, s3_client_stub, s3_resource_stub):
    print('DELETE /metadata/{asset_id}')

    test_asset_id = str(uuid.uuid4())
    
    ddb_resource_stub.add_response(
        'delete_item',
        expected_params = {
            'TableName': 'testDataplaneTableName',
            'Key': {
                'AssetId': test_asset_id
            },
            'ReturnValues': 'ALL_OLD'
        },
        service_response = {
            'Attributes': {
                'S3Key': {'S': 'testKeyValue'},
                'testOperatorName': {
                    'L': [{
                        'M': {
                            'testPointer': {'S': 'testPointerValue'},
                        }
                    }]
                }
            }
        }
    )

    s3_client_stub.add_response(
        'delete_objects',
        expected_params = {
            'Bucket': 'testDataplaneBucketName',
            'Delete': {
                'Objects': [{
                    'Key': 'testPointerValue'
                }, {
                    'Key': 'testKeyValue'
                }]
            }
        },
        service_response = {}
    )

    s3_resource_stub.add_client_error('delete_object')

    response = test_client.http.delete(
        '/metadata/{asset_id}'.format(asset_id = test_asset_id)
    )
    assert response.status_code == 500

def test_delete_asset(test_client, ddb_resource_stub, s3_client_stub, s3_resource_stub):
    print('DELETE /metadata/{asset_id}')

    test_asset_id = str(uuid.uuid4())
    
    ddb_resource_stub.add_response(
        'delete_item',
        expected_params = {
            'TableName': 'testDataplaneTableName',
            'Key': {
                'AssetId': test_asset_id
            },
            'ReturnValues': 'ALL_OLD'
        },
        service_response = {
            'Attributes': {
                'S3Key': {'S': 'testKeyValue'},
                'testOperatorName': {
                    'L': [{
                        'M': {
                            'testPointer': {'S': 'testPointerValue'},
                        }
                    }]
                }
            }
        }
    )

    s3_client_stub.add_response(
        'delete_objects',
        expected_params = {
            'Bucket': 'testDataplaneBucketName',
            'Delete': {
                'Objects': [{
                    'Key': 'testPointerValue'
                }, {
                    'Key': 'testKeyValue'
                }]
            }
        },
        service_response = {}
    )

    s3_resource_stub.add_response(
        'delete_object',
        expected_params = {
            'Bucket': 'testDataplaneBucketName',
            'Key': 'private/assets/' + test_asset_id +'/',
        },
        service_response = {}
    )

    response = test_client.http.delete(
        '/metadata/{asset_id}'.format(asset_id = test_asset_id)
    )
    assert response.status_code == 200
    assert response.body == 'Deleted asset: {asset_id} from the dataplane'.format(asset_id = test_asset_id).encode()
