# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import os
import boto3
# need to use simplejson as the std lib json package cannot handle float values
import simplejson as json
from boto3.dynamodb.types import TypeDeserializer

serializer = TypeDeserializer()

topic_arn = os.environ['TOPIC_ARN']
sns = boto3.client('sns')

def deserialize(data):
    if isinstance(data, list):
        return [deserialize(v) for v in data]

    if isinstance(data, dict):
        try:
            return serializer.deserialize(data)
        except TypeError:
            return {k: deserialize(v) for k, v in data.items()}
    else:
        return data
        
print('Loading function')


def lambda_handler(event, context):
        
    for i,record in enumerate(event["Records"]):
        print(i)
        
        deserialized_record = deserialize(record["dynamodb"])
        print(deserialized_record)
        
        event_type = record["eventName"]
        if event_type == "MODIFY":
            old = deserialized_record["OldImage"]
            new = deserialized_record["NewImage"]
            
            if new["Status"] != old["Status"]:
                message = {}
                message["Id"] = old["Id"]
                message["AssetId"] = old["AssetId"]
                message["Status"] = new["Status"]
                message["Globals"] = new["Globals"]
                message["Configuration"] = new["Configuration"]
                message["Created"] = new["Created"]
                #message["StateMachineExecutionArn"] = new["StateMachineExecutionArn"]
                print("Send an SNS - this is big news!")
                print(message)
                response = sns.publish(
                    TargetArn=topic_arn,
                    Message=json.dumps({'default': json.dumps(message)}),
                    MessageStructure='json'
                )
            print("Nothing to put into stream")
        if event_type == "INSERT":
            
            print("event_type == INSERT: Nothing to do")
        if event_type == "REMOVE":
            
            print("event_type == REMOVE: Nothing to do")