# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

def test_deserialize_non_list_dict():
    # imports
    import stream

    # test parameters
    data_param = 'testData'

    result = stream.deserialize(data_param)

    # assertions
    assert result == data_param

def test_deserialize_dict_success():
    # imports
    import stream

    #test parameters
    data_param = {
        'S': 'World'
    }
    result = stream.deserialize(data_param)

    # assertions
    assert result == 'World'

def test_deserialize_dict_error_handling():
        # imports
    import stream

    #test parameters
    data_param = {'Hello': 'World'}
    result = stream.deserialize(data_param)

    # assertions
    assert result == {'Hello': 'World'}

def test_deserialize_list_success():
    # imports
    import stream

    #test parameters
    data_param = [
        {'BOOL': True},
        {'NULL': True},
        {'N': '123'}
    ]
    result = stream.deserialize(data_param)

    # assertions
    assert result[0] == True
    assert result[1] == None
    assert result[2] == 123.0

def test_put_ks_record(kinesis_client_stub):
    import stream
    kinesis_client_stub.add_response(
        'put_record',
        expected_params = {
            'StreamName': 'testStreamName',
            'Data': '{"test": "Data"}',
            'PartitionKey': 'testPartitionKey'
        },
        service_response = {
            'ShardId': 'testShardId',
            'SequenceNumber': '0.0'
        }
    )
    stream.put_ks_record(
        'testPartitionKey',
        {
            'test': 'Data'
        }
    )

def test_lambda_handler_insert_record(kinesis_client_stub):
    import stream
    kinesis_client_stub.add_response(
        'put_record',
        expected_params = {
            'StreamName': 'testStreamName',
            'Data': '{"TestKey": "testValue", "Action": "INSERT"}',
            'PartitionKey': 'testAssetId'
        },
        service_response = {
            'ShardId': 'testShardId',
            'SequenceNumber': '0.0'
        }
    )

    event_param = {
        'Records': [{
            'eventName': 'INSERT',
            'dynamodb': {
                'M': {
                    'Keys': {
                        'M': {
                            'AssetId': {'S':'testAssetId'}
                        }
                    },
                    'NewImage': {
                        'M': {
                            'AssetId': {'S': 'testAssetId'},
                            'TestKey': {'S': 'testValue'}
                        }
                    }
                }
            }
        }]
    }

    stream.lambda_handler(event_param, {})

def test_lambda_handler_delete_record(kinesis_client_stub):
    import stream
    kinesis_client_stub.add_response(
        'put_record',
        expected_params = {
            'StreamName': 'testStreamName',
            'Data': '{"Action": "REMOVE"}',
            'PartitionKey': 'testAssetId'
        },
        service_response = {
            'ShardId': 'testShardId',
            'SequenceNumber': '0.0'
        }
    )

    event_param = {
        'Records': [{
            'eventName': 'REMOVE',
            'dynamodb': {
                'M': {
                    'Keys': {
                        'M': {
                            'AssetId': {'S': 'testAssetId'}
                        }
                    },
                    'NewImage': {
                        'M': {
                            'AssetId': {'S': 'testAssetId'},
                            'TestKey': {'S': 'testValue'}
                        }
                    }
                }
            }
        }]
    }

    stream.lambda_handler(event_param, {})

def test_lambda_handler_modify_record_no_modifications():
    import stream

    event_param = {
        'Records': [{
            'eventName': 'MODIFY',
            'dynamodb': {
                'M': {
                    'Keys': {
                        'M': {
                            'AssetId': {'S': 'testAssetId'}
                        }
                    },
                    'NewImage': {
                        'M': {
                            'AssetId': {'S': 'testAssetId'},
                            'TestOperator': {
                                'L': [{
                                    'M': {
                                        'pointer': {'S':'Pointer1'}
                                    }
                                }]
                            }
                        }
                    },
                    'OldImage': {
                        'M': {
                            'AssetId': {'S': 'testAssetId'},
                            'TestOperator': {
                                'L': [{
                                    'M': {
                                        'pointer': {'S':'Pointer1'}
                                    }
                                }]
                            }
                        }
                    }
                }
            }
        }]
    }

    response = stream.lambda_handler(event_param, {})
    assert response == None

def test_lambda_handler_modify_record_existing_attribute_modified(kinesis_client_stub):
    import stream

    kinesis_client_stub.add_response(
        'put_record',
        expected_params = {
            'StreamName': 'testStreamName',
            'Data': '{"Action": "MODIFY", "Pointer": "Pointer1", "Operator": "TestOperator", "Workflow": "workflow1"}',
            'PartitionKey': 'testAssetId'
        },
        service_response = {
            'ShardId': 'testShardId',
            'SequenceNumber': '0.0'
        }
    )

    event_param = {
        'Records': [{
            'eventName': 'MODIFY',
            'dynamodb': {
                'M': {
                    'Keys': {
                        'M': {
                            'AssetId': {'S': 'testAssetId'}
                        }
                    },
                    'NewImage': {
                        'M': {
                            'AssetId': {'S': 'testAssetId'},
                            'TestOperator': {
                                'L': [{
                                    'M': {
                                        'workflow': {'S':'workflow1'},
                                        'pointer': {'S':'Pointer1'}
                                    }
                                }]
                            }
                        }
                    },
                    'OldImage': {
                        'M': {
                            'AssetId': {'S': 'testAssetId'},
                            'TestOperator': {
                                'L': [{
                                    'M': {
                                        'pointer': {'S':'Pointer2'}
                                    }
                                }]
                            }
                        }
                    }
                }
            }
        }]
    }

    response = stream.lambda_handler(event_param, {})
    assert response == None

def test_lambda_handler_modify_record_attribute_added(kinesis_client_stub):
    import stream

    kinesis_client_stub.add_response(
        'put_record',
        expected_params = {
            'StreamName': 'testStreamName',
            'Data': '{"Action": "MODIFY", "Pointer": "Pointer2", "Operator": "TestKey2", "Workflow": "workflow2"}',
            'PartitionKey': 'testAssetId'
        },
        service_response = {
            'ShardId': 'testShardId',
            'SequenceNumber': '0.0'
        }
    )

    event_param = {
        'Records': [{
            'eventName': 'MODIFY',
            'dynamodb': {
                'M': {
                    'Keys': {
                        'M': {
                            'AssetId': {'S': 'testAssetId'}
                        }
                    },
                    'NewImage': {
                        'M': {
                            'AssetId': {'S': 'testAssetId'},
                            'TestKey1': {
                                'L': [{
                                    'M': {
                                        'workflow': {'S':'workflow1'},
                                        'pointer': {'S':'Pointer1'}
                                    }
                                }]
                            },
                            'TestKey2': {
                                'L': [{
                                    'M': {
                                        'workflow': {'S':'workflow2'},
                                        'pointer': {'S':'Pointer2'}
                                    }
                                }]
                            }
                        }
                    },
                    'OldImage': {
                        'M': {
                            'AssetId': {'S': 'testAssetId'},
                            'TestKey1': {
                                'L': [{
                                    'M': {
                                        'workflow': {'S':'workflow1'},
                                        'pointer': {'S':'Pointer1'}
                                    }
                                }]
                            }
                        }
                    }
                }
            }
        }]
    }

    response = stream.lambda_handler(event_param, {})
    assert response == None

def test_lambda_handler_modify_record_attribute_removed(kinesis_client_stub):
    import stream

    kinesis_client_stub.add_response(
        'put_record',
        expected_params = {
            'StreamName': 'testStreamName',
            'Data': '{"Action": "REMOVE", "Operator": "TestKey2"}',
            'PartitionKey': 'testAssetId'
        },
        service_response = {
            'ShardId': 'testShardId',
            'SequenceNumber': '0.0'
        }
    )

    event_param = {
        'Records': [{
            'eventName': 'MODIFY',
            'dynamodb': {
                'M': {
                    'Keys': {
                        'M': {
                            'AssetId': {'S': 'testAssetId'}
                        }
                    },
                    'NewImage': {
                        'M': {
                            'AssetId': {'S': 'testAssetId'},
                            'TestKey1': {
                                'L': [{
                                    'M': {
                                        'workflow': {'S':'workflow1'},
                                        'pointer': {'S':'Pointer1'}
                                    }
                                }]
                            }
                        }
                    },
                    'OldImage': {
                        'M': {
                            'AssetId': {'S': 'testAssetId'},
                            'TestKey1': {
                                'L': [{
                                    'M': {
                                        'workflow': {'S':'workflow1'},
                                        'pointer': {'S':'Pointer1'}
                                    }
                                }]
                            },
                            'TestKey2': {
                                'L': [{
                                    'M': {
                                        'workflow': {'S':'workflow2'},
                                        'pointer': {'S':'Pointer2'}
                                    }
                                }]
                            }
                        }
                    }
                }
            }
        }]
    }

    response = stream.lambda_handler(event_param, {})
    assert response == None
