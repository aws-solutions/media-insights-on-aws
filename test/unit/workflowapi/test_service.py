from helper import *
from datetime import datetime

def test_get_vocabulary(test_client, transcribe_client_stub):
    print ('POST /service/transcribe/get_vocabulary')
    vocabulary_name = 'testVocabularyName'

    transcribe_client_stub.add_response(
        'get_vocabulary',
        expected_params = {
            'VocabularyName': vocabulary_name
        },
        service_response = {
            'LastModifiedTime': datetime(2000,1,1),
            'VocabularyName': vocabulary_name
        }
    )

    response = test_client.http.post(
        '/service/transcribe/get_vocabulary',
        body=json.dumps({
            'vocabulary_name': vocabulary_name
        }).encode()
    )
    assert response.status_code == 200
    assert response.json_body['LastModifiedTime'] == '2000-01-01T00:00:00'
    assert response.json_body['VocabularyName'] == vocabulary_name

def test_(test_client, transcribe_client_stub):
    print('GET /service/transcribe/list_vocabularies')
    
    transcribe_client_stub.add_response(
        'list_vocabularies',
        expected_params = {
            'MaxResults': 100
        },
        service_response = {
            'NextToken': 'next_token',
            'Vocabularies': [
                {
                    'VocabularyName': 'vocabulary1',
                    'LastModifiedTime': datetime(2000, 1, 1)
                }
            ]
        }
    )
    transcribe_client_stub.add_response(
        'list_vocabularies',
        expected_params = {
            'NextToken': 'next_token',
            'MaxResults': 100
        },
        service_response = {
            'Vocabularies': [
                {
                    'VocabularyName': 'vocabulary2',
                    'LastModifiedTime': datetime(2000, 1, 2)
                }
            ]
        }
    )

    response = test_client.http.get('/service/transcribe/list_vocabularies')
    assert response.status_code == 200
    assert len(response.json_body['Vocabularies']) == 1
    assert response.json_body['Vocabularies'][0]['VocabularyName'] == 'vocabulary2'
    assert response.json_body['Vocabularies'][0]['LastModifiedTime'] == '2000-01-02T00:00:00'

def test_delete_vocabulary(test_client, transcribe_client_stub):
    print('DELETE /service/transcribe/delete_vocabulary')
    
    vocabulary_name = 'testVocabularyName'

    transcribe_client_stub.add_response(
        'delete_vocabulary',
        expected_params = {
            'VocabularyName': vocabulary_name
        },
        service_response = {
            'ResponseMetadata': vocabulary_name
        }
    )

    response = test_client.http.post(
        '/service/transcribe/delete_vocabulary',
        body=json.dumps({
            'vocabulary_name': vocabulary_name
        }).encode()
    )
    assert response.status_code == 200
    assert response.json_body['ResponseMetadata'] == vocabulary_name

def test_create_vocabulary(test_client, transcribe_client_stub):
    print ('POST /service/transcribe/create_vocabulary')

    vocabulary_name = 'testVocabularyName'
    language_code = 'en-US'
    s3_uri = 'test_s3_uri'

    transcribe_client_stub.add_response(
        'create_vocabulary',
        expected_params = {
            'VocabularyName': vocabulary_name,
            'LanguageCode': 'en-US',
            'VocabularyFileUri': 'test_s3_uri'
        },
        service_response = {
            'ResponseMetadata': 'ok'
        }
    )

    response = test_client.http.post(
        '/service/transcribe/create_vocabulary',
        body = json.dumps({
            'vocabulary_name': vocabulary_name,
            'language_code': language_code,
            's3uri': s3_uri
        }).encode()
    )
    assert response.status_code == 200
    assert response.json_body['ResponseMetadata'] == 'ok'

def test_list_language_models(test_client, transcribe_client_stub):
    print('GET /service/transcribe/list_language_models')

    transcribe_client_stub.add_response(
        'list_language_models',
        expected_params = {},
        service_response = {
            'NextToken': 'next_token',
            'Models': [{
                'ModelName': 'model1',
                'CreateTime': datetime(2000,1,1),
                'LastModifiedTime': datetime(2000,1,1)
            }]
        }
    )
    transcribe_client_stub.add_response(
        'list_language_models',
        expected_params = {
            'NextToken': 'next_token',
            'MaxResults': 100
        },
        service_response = {
            'Models': [{
                'ModelName': 'model1',
                'CreateTime': datetime(2000,1,2),
                'LastModifiedTime': datetime(2000,1,2)
            }]
        }
    )

    response = test_client.http.get('/service/transcribe/list_language_models')
    assert response.status_code == 200
    assert len(response.json_body['Models']) == 1
    assert response.json_body['Models'][0]['ModelName'] == 'model1'
    assert response.json_body['Models'][0]['CreateTime'] == '2000-01-02T00:00:00'
    assert response.json_body['Models'][0]['LastModifiedTime'] == '2000-01-02T00:00:00'

def test_describe_language_model(test_client, transcribe_client_stub):
    print('POST /service/transcribe/describe_language_model')

    transcribe_client_stub.add_response(
        'describe_language_model',
        expected_params = {
            'ModelName': 'test_val'
        },
        service_response = {
            'LanguageModel': {
                'CreateTime': datetime(2000,1,1),
                'LastModifiedTime': datetime(2000,1,1)
            }
        }
    )

    response = test_client.http.post(
        '/service/transcribe/describe_language_model',
        body = json.dumps({
            'ModelName': 'test_val'
        }).encode()
    )
    assert response.status_code == 200
    assert response.json_body['LanguageModel'] != None
    assert response.json_body['LanguageModel']['CreateTime'] == '2000-01-01T00:00:00'
    assert response.json_body['LanguageModel']['LastModifiedTime'] == '2000-01-01T00:00:00'

def test_get_terminology(test_client, translate_client_stub):
    print ('POST /service/transcribe/describe_language_model')

    translate_client_stub.add_response(
        'get_terminology',
        expected_params = {
            'Name': 'testTerminologyName',
            'TerminologyDataFormat': 'CSV'
        },
        service_response = {
            'ResponseMetadata': {},
            'TerminologyProperties': {
                'CreatedAt': datetime(2000,1,1),
                'LastUpdatedAt': datetime(2000,1,1)
            }
        }
    )

    response = test_client.http.post(
        '/service/translate/get_terminology',
        body = json.dumps({
            'terminology_name': 'testTerminologyName'
        }).encode()
    )
    assert response.status_code == 200
    assert response.json_body['TerminologyProperties'] != None
    assert response.json_body['TerminologyProperties']['CreatedAt'] == '2000-01-01T00:00:00'
    assert response.json_body['TerminologyProperties']['LastUpdatedAt'] == '2000-01-01T00:00:00'

def test_list_terminologies(test_client, translate_client_stub):
    print('GET /service/translate/list_terminologies')

    translate_client_stub.add_response(
        'list_terminologies',
        expected_params = {
            'MaxResults': 100
        },
        service_response = {
            'TerminologyPropertiesList': [{
                'CreatedAt': datetime(2000,1,1),
                'LastUpdatedAt': datetime(2000,1,1)
            }],
            'NextToken': 'next_token'
        }
    )

    translate_client_stub.add_response(
        'list_terminologies',
        expected_params = {
            'MaxResults': 100,
            'NextToken': 'next_token'
        },
        service_response = {
            'TerminologyPropertiesList': [{
                'CreatedAt': datetime(2000,1,2),
                'LastUpdatedAt': datetime(2000,1,2)
            }],
        }
    )

    response = test_client.http.get('/service/translate/list_terminologies')

    assert response.status_code == 200
    assert response.json_body['TerminologyPropertiesList'][0]['CreatedAt'] == '2000-01-02T00:00:00'
    assert response.json_body['TerminologyPropertiesList'][0]['LastUpdatedAt'] == '2000-01-02T00:00:00'

def test_delete_terminology(test_client, translate_client_stub):
    print('POST /service/translate/delete_terminology')

    translate_client_stub.add_response(
        'delete_terminology',
        expected_params = {
            'Name': 'testTerminologyName'
        },
        service_response = {
            'ResponseMetadata': 'ok'
        }
    )

    response = test_client.http.post(
        '/service/translate/delete_terminology',
        body = json.dumps({
            'terminology_name': 'testTerminologyName'
        }).encode()
    )
    assert response.status_code == 200
    assert response.json_body['ResponseMetadata'] == 'ok'

def test_create_terminology(test_client, translate_client_stub):
    print('POST /service/translate/create_terminology')

    translate_client_stub.add_response(
        'import_terminology',
        expected_params = {
            'Name': 'testTerminologyName',
            'MergeStrategy': 'OVERWRITE',
            'TerminologyData': {
                'File': 'test_terminology_csv_file',
                'Format': 'CSV'
            }
        },
        service_response = {
            'TerminologyProperties': {
                'CreatedAt': datetime(2000,1,1),
                'LastUpdatedAt': datetime(2000,1,1)
            }
        }
    )

    response = test_client.http.post(
        '/service/translate/create_terminology',
        body = json.dumps({
            'terminology_name': 'testTerminologyName',
            'terminology_csv': 'test_terminology_csv_file'
        }).encode()
    )
    assert response.status_code == 200
    assert response.json_body['TerminologyProperties']['CreatedAt'] == '2000-01-01T00:00:00'
    assert response.json_body['TerminologyProperties']['LastUpdatedAt'] == '2000-01-01T00:00:00'

def test_get_parallel_data(test_client, translate_client_stub):
    print('POST /service/translate/get_parallel_data')

    translate_client_stub.add_response(
        'get_parallel_data',
        expected_params = {
            'Name': 'testName'
        },
        service_response = {
            'ParallelDataProperties': {
                'CreatedAt': datetime(2000,1,1),
                'LastUpdatedAt': datetime(2000,1,1)
            }
        }
    )

    response = test_client.http.post(
        '/service/translate/get_parallel_data',
        body=json.dumps({
            'Name': 'testName'
        }).encode()
    )
    assert response.status_code == 200
    assert response.json_body['ParallelDataProperties']['CreatedAt'] == '2000-01-01T00:00:00'
    assert response.json_body['ParallelDataProperties']['LastUpdatedAt'] == '2000-01-01T00:00:00'

def test_list_parallel_data(test_client, translate_client_stub):
    print('GET /service/translate/list_parallel_data')

    translate_client_stub.add_response(
        'list_parallel_data',
        expected_params = {
            'MaxResults': 100
        },
        service_response = {
            'NextToken': 'next_token',
            'ParallelDataPropertiesList': [{
                'CreatedAt': datetime(2000,1,1),
                'LastUpdatedAt': datetime(2000,1,1)
            }]
        }
    )

    translate_client_stub.add_response(
        'list_parallel_data',
        expected_params = {
            'MaxResults': 100,
            'NextToken': 'next_token'
        },
        service_response = {
            'ParallelDataPropertiesList': [{
                'CreatedAt': datetime(2000,1,2),
                'LastUpdatedAt': datetime(2000,1,2)
            }]
        }
    )

    response = test_client.http.get('/service/translate/list_parallel_data')
    assert response.status_code == 200
    assert response.json_body['ParallelDataPropertiesList'][0]['CreatedAt'] == '2000-01-02T00:00:00'
    assert response.json_body['ParallelDataPropertiesList'][0]['LastUpdatedAt'] == '2000-01-02T00:00:00'

def test_delete_parallel_data(test_client, translate_client_stub):
    print('POST /service/translate/delete_parallel_data')

    translate_client_stub.add_response(
        'delete_parallel_data',
        expected_params = {
            'Name': 'testName'
        },
        service_response = {
            'ResponseMetadata': 'ok'
        }
    )

    response = test_client.http.post(
        '/service/translate/delete_parallel_data',
        body = json.dumps({
            'Name': 'testName'
        }).encode()
    )
    assert response.status_code == 200
    assert response.json_body['ResponseMetadata'] == 'ok'

def test_create_parallel_data(test_client, translate_client_stub):
    print('POST /service/translate/create_parallel_data')

    translate_client_stub.add_response(
        'create_parallel_data',
        expected_params = {
            'Name': 'testName',
            'ParallelDataConfig': {
                'S3Uri': 'testS3Uri',
                'Format': 'testFormat'
            }
        },
        service_response = {
            'ResponseMetadata': 'ok'
        }
    )

    response = test_client.http.post(
        '/service/translate/create_parallel_data',
        body = json.dumps({
            'Name': 'testName',
            'ParallelDataConfig': {
                'S3Uri': 'testS3Uri',
                'Format': 'testFormat'
            }
        }).encode()
    )
    assert response.status_code == 200
    assert response.json_body['ResponseMetadata'] == 'ok'
