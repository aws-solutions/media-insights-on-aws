# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import os
import boto3
from chalice import Chalice
from chalice import NotFoundError, BadRequestError, ChaliceViewError, Response, ConflictError
from MediaInsightsEngineLambdaHelper import Status as awsmie

WORKFLOW_TABLE_NAME = os.environ["WORKFLOW_TABLE_NAME"]
STAGE_TABLE_NAME = os.environ["STAGE_TABLE_NAME"]
OPERATION_TABLE_NAME = os.environ["OPERATION_TABLE_NAME"]
WORKFLOW_EXECUTION_TABLE_NAME = os.environ["WORKFLOW_EXECUTION_TABLE_NAME"]
STAGE_EXECUTION_QUEUE_URL = os.environ["STAGE_EXECUTION_QUEUE_URL"]
STAGE_EXECUTION_ROLE = os.environ["STAGE_EXECUTION_ROLE"]
# FIXME testing NoQ execution
COMPLETE_STAGE_LAMBDA_ARN = os.environ["COMPLETE_STAGE_LAMBDA_ARN"] 
FILTER_OPERATION_LAMBDA_ARN = os.environ["FILTER_OPERATION_LAMBDA_ARN"]

# Not all lambdas here have this as input.  Only complete_stage. 
if "WORKFLOW_SCHEDULER_LAMBDA_ARN" in os.environ:
    WORKFLOW_SCHEDULER_LAMBDA_ARN = os.environ["WORKFLOW_SCHEDULER_LAMBDA_ARN"]
else:
    WORKFLOW_SCHEDULER_LAMBDA_ARN = ""

# DynamoDB
DYNAMO_CLIENT = boto3.client("dynamodb")
DYNAMO_RESOURCE = boto3.resource("dynamodb")

# Step Functions
SFN_CLIENT = boto3.client('stepfunctions')

# Simple Queue Service
SQS_RESOURCE = boto3.resource('sqs')
SQS_CLIENT = boto3.client('sqs')

# IAM resource
IAM_CLIENT = boto3.client('iam')
IAM_RESOURCE = boto3.resource('iam')

# Lambda
LAMBDA_CLIENT = boto3.client("lambda")

class MediaInsightsEngineWorkflowExecutionHelper:
    """Helper class to work with Media Insights Engine workflow execution objects"""
    def __init__(self, id):
        """
        Get the workflow execution by id from dyanamo and assign to this object
        :param id: The id of the workflow execution

        """
        print("Workflow execution init workflow_execution = {}".format(id))

        table = DYNAMO_RESOURCE.Table(WORKFLOW_EXECUTION_TABLE_NAME)
        workflow_execution = None
        response = table.get_item(
            Key={
                'Id': id
            },
            ConsistentRead=True)

        if "Item" in response:
            workflow_execution = response["Item"]
        else:
            raise NotFoundError(
                "Exception: workflow execution '%s' not found" % id)

        self.id = workflow_execution["Id"]
        self.asset_id = workflow_execution["AssetId"]
        self.configuration = workflow_execution["Configuration"]
        self.current_stage = workflow_execution["CurrentStage"]
        self.status = workflow_execution["Status"] 
        self.trigger = workflow_execution["Trigger"] 
        self.workflow = workflow_execution["workflow"] 

    def update_status(self, status):
        """
        Get the workflow execution by id from dyanamo and assign to this object
        :param status: The new status of the workflow execution

        """
        print("Update workflow execution {} set status = {}".format(self.id, status))
        execution_table = DYNAMO_RESOURCE.Table(WORKFLOW_EXECUTION_TABLE_NAME)
        
        self.status = status
        response = execution_table.update_item(
            Key={
                'Id': self.id
            },
            UpdateExpression='SET #workflow_status = :status',
            ExpressionAttributeNames={
                '#workflow_status': "Status"
            },
            ExpressionAttributeValues={
                ':workflow_status': status

            }
        )

        if status in [awsmie.WORKFLOW_STATUS_QUEUED, awsmie.WORKFLOW_STATUS_COMPLETE, awsmie.WORKFLOW_STATUS_ERROR]:
            # Trigger the workflow_scheduler
            response = LAMBDA_CLIENT.invoke(
                FunctionName=WORKFLOW_SCHEDULER_LAMBDA_ARN,
                InvocationType='Event'
            )

        

           