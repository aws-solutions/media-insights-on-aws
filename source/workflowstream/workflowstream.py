# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import os
import time
import logging
import boto3
# need to use simplejson as the std lib json package cannot handle float values
import simplejson as json
from botocore.client import ClientError
from botocore.config import Config
from boto3.dynamodb.types import TypeDeserializer

formatter = logging.Formatter('{%(pathname)s:%(lineno)d} %(levelname)s - %(message)s')
handler = logging.StreamHandler()
handler.setFormatter(formatter)

logger = logging.getLogger('boto3')
logger.setLevel(logging.INFO)
logger.addHandler(handler)

serializer = TypeDeserializer()

mie_config = json.loads(os.environ['botoConfig'])
config = Config(**mie_config)

topic_arn = os.environ['TOPIC_ARN']
sns = boto3.client('sns', config=config)

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

def lambda_handler(event, context):

    for record in event["Records"]:

        deserialized_record = deserialize(record["dynamodb"])
        logger.info(f"Received event: {deserialized_record}")

        event_type = record["eventName"]

        if event_type == "MODIFY":
            logger.info("event_type == MODIFY: Checking workflow status")
            timestamp = time.time()
            old = deserialized_record["OldImage"]
            new = deserialized_record["NewImage"]

            if new["Status"] != old["Status"]:
                logger.info("Workflow status was changed: Creating message for SNS publishing")
                message = {}
                message["EventTimestamp"] = timestamp
                message["WorkflowExecutionId"] = old["Id"]
                message["AssetId"] = old["AssetId"]
                message["Status"] = new["Status"]
                message["Globals"] = new["Globals"]
                message["Configuration"] = new["Configuration"]
                message["Created"] = new["Created"]
                #message["StateMachineExecutionArn"] = new["StateMachineExecutionArn"]
                logger.info(f"Publishing the following message: {message}")
                try:
                    response = sns.publish(
                        TargetArn=topic_arn,
                        Message=json.dumps({'default': json.dumps(message)}),
                        MessageStructure='json'
                    )
                except ClientError as e:
                    error = e.response['Error']['Message']
                    logger.error(f"Exception occurred while publishing message to SNS: {error}")
                else:
                    logger.info(f"Successfully published message to SNS: {response}")
            else:
                logger.info("Workflow status was not changed: Nothing to do")
        if event_type == "INSERT":
            logger.info("event_type == INSERT: Nothing to do")
        if event_type == "REMOVE":
            logger.info("event_type == REMOVE: Nothing to do")
