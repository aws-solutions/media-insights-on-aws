# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import boto3
from boto3 import resource
from botocore.client import ClientError

import uuid
import logging
import os
#from datetime import date
#from datetime import time
from datetime import datetime
import json
import time
import decimal
# from MediaInsightsEngineLambdaHelper import Status as awsmie
# from MediaInsightsEngineLambdaHelper import MediaInsightsOperationHelper
# from MediaInsightsEngineLambdaHelper import MasExecutionError

# Setup logging
# Logging Configuration
#extra = {'requestid': app.current_request.context}
# fmt = '[%(levelname)s] [%(funcName)s] - %(message)s'
# logger = logging.getLogger('LUCIFER')
# logging.basicConfig(format=fmt)
# root = logging.getLogger()
# if root.handlers:
#     for handler in root.handlers:
#         root.removeHandler(handler)
# logging.basicConfig(format=fmt)
logger = logging.getLogger('boto3')
logger.setLevel(logging.INFO)

class awsmie:
    WORKFLOW_STATUS_QUEUED = "Queued"
    WORKFLOW_STATUS_STARTED = "Started"
    WORKFLOW_STATUS_ERROR = "Error"
    WORKFLOW_STATUS_COMPLETE = "Complete"

    STAGE_STATUS_NOT_STARTED = "Not Started"
    STAGE_STATUS_STARTED = "Started"
    STAGE_STATUS_EXECUTING = "Executing"
    STAGE_STATUS_ERROR = "Error"
    STAGE_STATUS_COMPLETE = "Complete"

    OPERATION_STATUS_NOT_STARTED = "Not Started"
    OPERATION_STATUS_STARTED = "Started"
    OPERATION_STATUS_EXECUTING = "Executing"
    OPERATION_STATUS_ERROR = "Error"
    OPERATION_STATUS_COMPLETE = "Complete"
    OPERATION_STATUS_SKIPPED = "Skipped"


class MediaInsightsOperationHelper:
    """Helper class to work with input and output passed between MIE operators in a workflow."""
    def __init__(self, event):
        """
        :param event: The event passed in to the operator

        """
        print("Operation Helper init event = {}".format(event))
        self.name = event["Name"]
        self.asset_id = event["AssetId"]
        self.workflow_execution_id = event["WorkflowExecutionId"]
        self.input = event["Input"]
        self.configuration = event["Configuration"]
        self.status = event["Status"]
        if "MetaData" in event:
            self.metadata = event["MetaData"]
        else:
            self.metadata = {}
        if "Media" in event:
            self.media = event["Media"]
        else:
            self.media = {}
        self.base_s3_key = 'private/media/'

    def workflow_info(self):
        return {"AssetId": self.asset_id, "WorkflowExecutionId": self.workflow_execution_id}

    def return_output_object(self):
        """Method to return the output object that was created

        :return: Dict of the output object
        """
        return {"Name": self.name, "AssetId": self.asset_id, "WorkflowExecutionId": self.workflow_execution_id,  "Input": self.input, "Configuration": self.configuration, "Status": self.status, "MetaData": self.metadata, "Media": self.media}

    def update_workflow_status(self, status):
        """ Method to update the status of the output object
        :param status: A valid status
        :return: Nothing
        """
        self.status = status

    def add_workflow_metadata(self, **kwargs):
        """ Method to update the metadata key of the output object

        :param kwargs: Any key value pair you want added to the metadata of the output object
        :return: Nothing
        """
        for key, value in kwargs.items():
            # TODO: Add validation here to check if item exists
            self.metadata.update({key: value})

    def add_workflow_metadata_json(self, json_metadata):
        """ Method to update the metadata key of the output object

        :param json_metadata: json dictionary of key-value pairs to add to workflow metadata
        :return: Nothing
        """
        for key, value in json_metadata.items():
            # TODO: Add validation here to check if item exists
            print(key)
            print(value)
            self.metadata.update({key: value})

    def add_media_object(self, media_type, s3_bucket, s3_key):
        """ Method to add a media object to the output object

        :param media_type: The type of media
        :param s3_bucket: S3 bucket of the media
        :param s3_key: S3 key of the media
        :return: Nothing
        """

        self.media[media_type] = {"S3Bucket": s3_bucket, "S3Key": s3_key}


class OutputHelper:
    """Helper class to generate a valid output object"""
    def __init__(self, name):
        """
        :param name: The name of the operator generating the output object

        """
        self.name = name
        self.status = ""
        self.metadata = {}
        self.media = {}
        self.base_s3_key = 'private/media/'

    def return_output_object(self):
        """Method to return the output object that was created

        :return: Dict of the output object
        """
        return {"Name": self.name, "Status": self.status, "MetaData": self.metadata, "Media": self.media}

    def update_workflow_status(self, status):
        """ Method to update the status of the output object
        :param status: A valid status
        :return: Nothing
        """
        self.status = status

    def add_workflow_metadata(self, **kwargs):
        """ Method to update the metadata key of the output object

        :param kwargs: Any key value pair you want added to the metadata of the output object
        :return: Nothing
        """
        for key, value in kwargs.items():
            # TODO: Add validation here to check if item exists
            self.metadata.update({key: value})

    def add_media_object(self, media_type, s3_bucket, s3_key):
        """ Method to add a media object to the output object

        :param media_type: The type of media
        :param s3_bucket: S3 bucket of the media
        :param s3_key: S3 key of the media
        :return: Nothing
        """

        self.media[media_type] = {"S3Bucket": s3_bucket, "S3Key": s3_key}


class MasExecutionError(Exception):
    pass


class DataPlane:
    """Helper Class for interacting with the dataplane"""

    def __init__(self):
        self.dataplane_function_name = os.environ["DataplaneEndpoint"]
        self.lambda_client = boto3.client('lambda')
        self.lambda_invoke_object = {
            # some api uri
            "resource": "",
            # some api uri, not sure why this is needed twice
            "path": "",
            # HTTP Method
            "httpMethod": "",
            # Headers, just here so chalice formatting doesn't fail
            "headers": {
                'Content-Type': 'application/json'
            },
            # Not sure the difference between this header object and the above
            "multiValueHeaders": {},
            # Mock query string params
            "queryStringParameters": {},
            # Not sure the difference here either
            "multiValueQueryStringParameters": {},
            # Not sure what these are
            "pathParameters": {},
            # API Stage variables, again just here for chalice formatting
            "stageVariables": {},
            # request context, we generate most of this now
            "requestContext": {
                'resourcePath': '',
                'requestTime': None,
                'httpMethod': '',
                'requestId': None,
            },
            "body": {},
            "isBase64Encoded": False
        }

    def call_dataplane(self, path, resource, method, body=None, path_params=None, query_params=None):
        encoded_body = json.dumps(body)

        self.lambda_invoke_object["resource"] = resource
        self.lambda_invoke_object["path"] = path
        self.lambda_invoke_object["requestContext"]["resourcePath"] = resource
        self.lambda_invoke_object["httpMethod"] = method
        self.lambda_invoke_object["pathParameters"] = path_params
        self.lambda_invoke_object["body"] = encoded_body
        self.lambda_invoke_object["queryStringParameters"] = query_params
        if query_params is not None:
            self.lambda_invoke_object["multiValueQueryStringParameters"] = {}
            for k, v in query_params.items():
                self.lambda_invoke_object["multiValueQueryStringParameters"][k] = [v]
        else:
            self.lambda_invoke_object["multiValueQueryStringParameters"] = query_params
        self.lambda_invoke_object["requestContext"]["httpMethod"] = method
        self.lambda_invoke_object["requestContext"]["requestId"] = 'lambda_' + str(uuid.uuid4()).split('-')[-1]
        self.lambda_invoke_object["requestContext"]["requestTime"] = time.time()

        request_object = json.dumps(self.lambda_invoke_object)

        invoke_request = self.lambda_client.invoke(
            FunctionName=self.dataplane_function_name,
            InvocationType='RequestResponse',
            LogType='None',
            Payload=bytes(request_object, encoding='utf-8')
        )

        response = invoke_request["Payload"].read().decode('utf-8')

        # TODO: Do we want to do any validation on the status code or let clients parse the response as needed?
        dataplane_response = json.loads(response)
        return json.loads(dataplane_response["body"])

    def create_asset(self, s3bucket, s3key):
        """
        Method to create an asset in the dataplane

        :param s3bucket: S3 Bucket of the asset
        :param s3key: S3 Key of the asset

        :return: Dataplane response
        """
        path = "/create"
        resource = "/create"
        method = "POST"
        body = {"Input": {"S3Bucket": s3bucket, "S3Key": s3key}}
        dataplane_response = self.call_dataplane(path, resource, method, body)
        return dataplane_response

    def store_asset_metadata(self, asset_id, operator_name, workflow_id, results, paginate=False, end=False):
        """
        Method to store asset metadata in the dataplane

        :param operator_name: The name of the operator that created this metadata
        :param results: The metadata itself, or what the result of the operator was
        :param asset_id: The id of the asset
        :param workflow_id: Worfklow ID that generated this metadata

        Pagination params:
        :param paginate: Boolean to tell dataplane that the results will come in as pages
        :param end: Boolean to declare the last page in a set of paginated results

        :return: Dataplane response

        """

        path = "/metadata/{asset_id}".format(asset_id=asset_id)
        resource = "/metadata/{asset_id}"
        path_params = {"asset_id": asset_id}
        method = "POST"
        body = {"OperatorName": operator_name, "Results": results, "WorkflowId": workflow_id}

        query_params = {}

        if paginate or end:
            if paginate is True:
                query_params["paginated"] = "true"
            if end is True:
                query_params["end"] = "true"
        else:
            query_params = None

        dataplane_response = self.call_dataplane(path, resource, method, body, path_params, query_params)
        return dataplane_response

    def retrieve_asset_metadata(self, asset_id, operator_name=None, cursor=None):
        """
        Method to retrieve metadata from the dataplane

        :param asset_id: The id of the asset
        :param operator_name: Optional parameter for filtering response to include only data
        generated by a specific operator
        :param cursor: Optional parameter for retrieving additional pages of asset metadata

        :return: Dataplane response
        """
        if operator_name:
            path = "/metadata/{asset_id}/operator".format(asset_id=asset_id, operator=operator_name)
        else:
            path = "/metadata/{asset_id}".format(asset_id=asset_id)

        resource = "/metadata/{asset_id}"
        path_params = {"asset_id": asset_id}
        method = "GET"

        query_params = {}

        if cursor:
            query_params["cursor"] = cursor
        else:
            query_params = None

        dataplane_response = self.call_dataplane(path, resource, method, None, path_params, query_params)

        return dataplane_response

    def generate_media_storage_path(self, asset_id, workflow_id):
        path = "/mediapath/{asset_id}/{workflow_id}".format(asset_id=asset_id, workflow_id=workflow_id)
        resource = "/mediapath/{asset_id}/{workflow_id}"
        path_params = {"asset_id": asset_id, "workflow_id": workflow_id}
        method = "GET"

        dataplane_response = self.call_dataplane(path, resource, method, None, path_params)

        return dataplane_response

WORKFLOW_TABLE_NAME = os.environ["WORKFLOW_TABLE_NAME"]
STAGE_TABLE_NAME = os.environ["STAGE_TABLE_NAME"]
OPERATION_TABLE_NAME = os.environ["OPERATION_TABLE_NAME"]
WORKFLOW_EXECUTION_TABLE_NAME = os.environ["WORKFLOW_EXECUTION_TABLE_NAME"]
STAGE_EXECUTION_QUEUE_URL = os.environ["STAGE_EXECUTION_QUEUE_URL"]

if "WORKFLOW_SCHEDULER_LAMBDA_ARN" in os.environ:
    WORKFLOW_SCHEDULER_LAMBDA_ARN = os.environ["WORKFLOW_SCHEDULER_LAMBDA_ARN"]
else:
    WORKFLOW_SCHEDULER_LAMBDA_ARN = ""

if "SYSTEM_TABLE_NAME" in os.environ:
    SYSTEM_TABLE_NAME = os.environ["SYSTEM_TABLE_NAME"]
else:
    ""

if "DEFAULT_MAX_CONCURRENT_WORKFLOWS" in os.environ:
    DEFAULT_MAX_CONCURRENT_WORKFLOWS = int(os.environ["DEFAULT_MAX_CONCURRENT_WORKFLOWS"])
else:
    DEFAULT_MAX_CONCURRENT_WORKFLOWS = 10

# DynamoDB
DYNAMO_CLIENT = boto3.client("dynamodb")
DYNAMO_RESOURCE = boto3.resource("dynamodb")

# Step Functions
SFN_CLIENT = boto3.client('stepfunctions')

# Simple Queue Service
SQS_RESOURCE = boto3.resource('sqs')
SQS_CLIENT = boto3.client('sqs')

# Lambda
LAMBDA_CLIENT = boto3.client("lambda")


def list_workflow_executions_by_status(Status):
    table = DYNAMO_RESOURCE.Table(WORKFLOW_EXECUTION_TABLE_NAME)
    projection_expression = "Id, AssetId, CurrentStage, StateMachineExecutionArn, #workflow_status, Workflow.#workflow_name"

    response = table.query(
        IndexName='WorkflowExecutionStatus',
        ExpressionAttributeNames={
            '#workflow_status': "Status",
            '#workflow_name': "Name"
        },
        ExpressionAttributeValues={
            ':workflow_status': Status
        },
        KeyConditionExpression='#workflow_status = :workflow_status',
        ProjectionExpression = projection_expression
        )

    workflow_executions = response['Items']
    while 'LastEvaluatedKey' in response:
        response = table.query(ExclusiveStartKey=response['LastEvaluatedKey'])
        workflow_executions.extend(response['Items'])

    return workflow_executions

def workflow_scheduler_lambda(event, context):

    execution_table = DYNAMO_RESOURCE.Table(WORKFLOW_EXECUTION_TABLE_NAME)
    arn = ""
    workflow_execution = {}
    MaxConcurrentWorkflows = DEFAULT_MAX_CONCURRENT_WORKFLOWS
    empty = False

    try:
        print(json.dumps(event))

        # Get the MaxConcurrent configruation parameter, if it is not set, use the default
        system_table = DYNAMO_RESOURCE.Table(SYSTEM_TABLE_NAME)

        # Check if any configuration has been added yet
        response = system_table.get_item(
            Key={
                'Name': 'MaxConcurrentWorkflows'
            },
            ConsistentRead=True)

        if "Item" in response:
            MaxConcurrentWorkflows = response["Item"]["Value"]
            logger.info("Got MaxConcurrentWorkflows = {}".format(response["Item"]["Value"]))

        # Check if there are slots to run a workflow
        # FIXME - we really need consistent read here.  Index query is not consistent read
        started_workflows = list_workflow_executions_by_status(awsmie.WORKFLOW_STATUS_STARTED)
        num_started_workflows = len(started_workflows)

        if num_started_workflows >= MaxConcurrentWorkflows:
            logger.info("MaxConcurrentWorkflows has been reached {}/{} - nothing to do".format(num_started_workflows, MaxConcurrentWorkflows))

        else:
            # We can only read 10 messages at a time from the queue.  Loop reading from the queue until
            # it is empty or we are out of slots
            while (num_started_workflows < MaxConcurrentWorkflows and not empty):

                capacity = min(int(MaxConcurrentWorkflows - num_started_workflows), 10)

                logger.info("MaxConcurrentWorkflows has not been reached {}/{} - check if a workflow is available to run".format(num_started_workflows, MaxConcurrentWorkflows))

                # Check if there are workflows waiting to run on the STAGE_EXECUTION_QUEUE_URL
                messages = SQS_CLIENT.receive_message(
                    QueueUrl=STAGE_EXECUTION_QUEUE_URL,
                    MaxNumberOfMessages=capacity
                )
                if 'Messages' in messages: # when the queue is exhausted, the response dict contains no 'Messages' key
                    for message in messages['Messages']: # 'Messages' is a list
                        # process the messages
                        logger.info(message['Body'])
                        # next, we delete the message from the queue so no one else will process it again,
                        # once it is in our hands it is going run or fail, no reprocessing
                        # FIXME - we may want to delay deleting the message until complete_stage is called on the
                        # final stage so we can detect hung workflows and time them out.  For now, do the simple thing.
                        SQS_CLIENT.delete_message(QueueUrl=STAGE_EXECUTION_QUEUE_URL,ReceiptHandle=message['ReceiptHandle'])

                        workflow_execution = json.loads(message['Body'])
                        workflow_execution['Status'] = awsmie.WORKFLOW_STATUS_STARTED

                        # Update the workflow status now to indicate we have taken it off the queue
                        update_workflow_execution_status(workflow_execution["Id"], awsmie.WORKFLOW_STATUS_STARTED, "")

                        # Kick off the state machine for the workflow
                        response = SFN_CLIENT.start_execution(
                            stateMachineArn=workflow_execution["Workflow"]["StateMachineArn"],
                            name=workflow_execution["Workflow"]["Name"]+workflow_execution["Id"],
                            input=json.dumps(workflow_execution["Workflow"]["Stages"][workflow_execution["CurrentStage"]])
                        )

                        workflow_execution["StateMachineExecutionArn"] = response["executionArn"]

                        # Update the workflow with the state machine id
                        response = execution_table.update_item(
                            Key={
                                'Id': workflow_execution["Id"]
                            },
                            UpdateExpression='SET StateMachineExecutionArn = :arn',
                            ExpressionAttributeValues={
                                ':arn': response["executionArn"]
                            }
                        )

                else:
                    logger.info('Queue is empty')
                    empty = True

                started_workflows = list_workflow_executions_by_status(awsmie.WORKFLOW_STATUS_STARTED)
                num_started_workflows = len(started_workflows)


    except Exception as e:

        logger.info("Exception in scheduler {}".format(e))
        if "Id" in workflow_execution:

            update_workflow_execution_status(workflow_execution["Id"], awsmie.WORKFLOW_STATUS_ERROR, "Exception in workflow_scheduler_lambda {}".format(e))
        raise

    return arn

def filter_operation_lambda(event, context):
    '''
    event is
    - Operation input
    - Operation configuration

    returns:
    Operation output
    - Operation status "Skipped" if operation should be skipped
    '''
    logger.info(json.dumps(event))

    operation_object = MediaInsightsOperationHelper(event)

    if operation_object.configuration["MediaType"] != "MetadataOnly" and operation_object.configuration["MediaType"] not in operation_object.input["Media"]:

        operation_object.update_workflow_status(awsmie.OPERATION_STATUS_SKIPPED)

    elif operation_object.configuration["Enabled"] == False:

        operation_object.update_workflow_status(awsmie.OPERATION_STATUS_SKIPPED)

    else:

        operation_object.update_workflow_status(awsmie.OPERATION_STATUS_STARTED)

    return operation_object.return_output_object()

def complete_stage_execution_lambda(event, context):
    '''
    event is a stage execution object
    '''
    logger.info(json.dumps(event))
    return complete_stage_execution("lambda", event["Name"], event["Status"], event["Outputs"], event["WorkflowExecutionId"])


def complete_stage_execution(trigger, stage_name, status, outputs, workflow_execution_id):

    try:

        execution_table = DYNAMO_RESOURCE.Table(WORKFLOW_EXECUTION_TABLE_NAME)
        # lookup the workflow
        response = execution_table.get_item(
            Key={
                'Id': workflow_execution_id
            },
            ConsistentRead=True)

        if "Item" in response:
            workflow_execution = response["Item"]
        else:
            workflow_execution = None
            # raise ChaliceViewError(
            raise ValueError(
                "Exception: workflow execution id '%s' not found" % workflow_execution_id)

        logger.info("workflow_execution: {}".format(
            json.dumps(workflow_execution)))


        # Roll-up the results of the stage execution.  If anything fails here, we will fail the
        # stage, but still attempt to update the workflow execution the stage belongs to
        try:
            # Roll up operation status
            # # if any operation did not complete successfully, the stage has failed
            opstatus = awsmie.STAGE_STATUS_COMPLETE
            errorMessage = "none"
            for operation in outputs:
                if operation["Status"] not in [awsmie.OPERATION_STATUS_COMPLETE, awsmie.OPERATION_STATUS_SKIPPED]:
                    opstatus = awsmie.STAGE_STATUS_ERROR
                    if "Message" in operation:
                        errorMessage = "Stage failed because operation {} execution failed. Message: {}".format(
                            operation["Name"], operation["Message"])
                    else:
                        errorMessage = "Stage failed because operation {} execution failed.".format(
                            operation["Name"])

            # don't overwrite an error
            if status != awsmie.STAGE_STATUS_ERROR:
                status = opstatus

            logger.info("Stage status: {}".format(status))

            workflow_execution["Workflow"]["Stages"][stage_name
                                                     ]["Outputs"] = outputs

            if "MetaData" not in workflow_execution["Globals"]:
                workflow_execution["Globals"]["MetaData"] = {}

            # Roll up operation media and metadata outputs from this stage and add them to
            # the global workflow metadata:
            #
            #     1. mediaType and metatdata output keys must be unique withina stage - if
            #        non-unique keys are found across operations within a stage, then the
            #        stage execution will fail.
            #     2. if a stage has a duplicates a mediaType or metadata output key from the globals,
            #        then the global value is replaced by the stage output value

            # Roll up media
            stageOutputMediaTypeKeys = []
            for operation in outputs:
                if "Media" in operation:
                    for mediaType in operation["Media"].keys():
                        # replace media with trasformed or created media from this stage
                        print(mediaType)
                        if mediaType in stageOutputMediaTypeKeys:

                            raise ValueError(
                                "Duplicate mediaType '%s' found in operation ouput media.  mediaType keys must be unique within a stage." % mediaType)
                        else:
                            workflow_execution["Globals"]["Media"][mediaType] = operation["Media"][mediaType]
                            stageOutputMediaTypeKeys.append(mediaType)

                # Roll up metadata
                stageOutputMetadataKeys = []
                if "MetaData" in operation:
                    for key in operation["MetaData"].keys():
                        print(key)
                        if key in stageOutputMetadataKeys:
                            raise ValueError(
                                "Duplicate key '%s' found in operation ouput metadata.  Metadata keys must be unique within a stage." % key)
                        else:
                            workflow_execution["Globals"]["MetaData"][key] = operation["MetaData"][key]
                            stageOutputMetadataKeys.append(key)

            workflow_execution["Workflow"]["Stages"][stage_name
                                                     ]["Status"] = status

        # The status roll up failed.  Handle the error and fall through to update the workflow status
        except Exception as e:

            logger.info("Exception while rolling up stage status {}".format(e))
            update_workflow_execution_status(workflow_execution["Id"], awsmie.WORKFLOW_STATUS_ERROR, "Exception while rolling up stage status {}".format(e))
            status = awsmie.STAGE_STATUS_ERROR

            raise ValueError("Error rolling up stage status: %s" % e)

        logger.info("Updating the workflow status in dynamodb: current stage {}, globals {}".format(workflow_execution["Workflow"]["Stages"][stage_name],workflow_execution["Globals"]))
        # Save the new stage and workflow status
        response = execution_table.update_item(
            Key={
                'Id': workflow_execution_id
            },
            UpdateExpression='SET Workflow.Stages.#stage = :stage, Globals = :globals',
            ExpressionAttributeNames={
                '#stage': stage_name
            },
            ExpressionAttributeValues={
                # ':stage': json.dumps(stage)
                ':stage': workflow_execution["Workflow"]["Stages"][stage_name],
                ':globals': workflow_execution["Globals"]
                # ':step_function_arn': step_function_execution_arn
            }
        )

        # Start the next stage for execution
        # FIXME - try always completing stage
        # status == awsmie.STAGE_STATUS_COMPLETE:
        workflow_execution = start_next_stage_execution(
            "Workflow", stage_name, workflow_execution)

        if status == awsmie.STAGE_STATUS_ERROR:
            raise Exception("Stage {} encountered and error during execution, aborting the workflow".format(stage_name))

    except Exception as e:
        logger.info("Exception {}".format(e))

        # Need a try/catch here? Try to save the status
        execution_table.put_item(Item=workflow_execution)
        update_workflow_execution_status(workflow_execution["Id"], awsmie.WORKFLOW_STATUS_ERROR, "Exception while rolling up stage status {}".format(e))

        logger.info("Exception {}".format(e))

        raise ValueError(
            "Exception: '%s'" % e)

    # If it is not the end of the workflow, pass the next stage out to be consumed by the next stage.
    if workflow_execution["CurrentStage"] == "End":
        return {}
    else:
        return workflow_execution["Workflow"]["Stages"][workflow_execution["CurrentStage"]]


def start_next_stage_execution(trigger, stage_name, workflow_execution):

    try:
        print("START NEXT STAGE: stage_name {}".format(stage_name))

        execution_table = DYNAMO_RESOURCE.Table(WORKFLOW_EXECUTION_TABLE_NAME)

        current_stage = stage_name

        message = "stage completed with status {}".format(workflow_execution["Workflow"]["Stages"][current_stage]["Status"])

        if "End" in workflow_execution["Workflow"]["Stages"][current_stage]:


            if workflow_execution["Workflow"]["Stages"][current_stage]["End"] == True:
                workflow_execution["CurrentStage"] = "End"
                workflow_execution["Status"] = workflow_execution["Workflow"]["Stages"][current_stage]["Status"]


            # Save the new stage
            response = execution_table.update_item(
                Key={
                    'Id': workflow_execution["Id"]
                },
                UpdateExpression='SET CurrentStage = :current_stage',
                ExpressionAttributeValues={
                    ':current_stage': "End"
                }
            )

            update_workflow_execution_status(workflow_execution["Id"], workflow_execution["Status"], message)

        elif workflow_execution["Workflow"]["Stages"][current_stage]["Status"] == "Error":
            workflow_execution["Status"] = workflow_execution["Workflow"]["Stages"][current_stage]["Status"]

            # Save the new stage and workflow status
            response = execution_table.update_item(
                Key={
                    'Id': workflow_execution["Id"]
                },
                UpdateExpression='SET CurrentStage = :current_stage',
                ExpressionAttributeValues={
                    ':current_stage': "End"
                }
            )

            update_workflow_execution_status(workflow_execution["Id"], workflow_execution["Status"], message)

        elif "Next" in workflow_execution["Workflow"]["Stages"][current_stage]:
            current_stage = workflow_execution["CurrentStage"] = workflow_execution[
                "Workflow"]["Stages"][current_stage]["Next"]

            workflow_execution["Workflow"]["Stages"][current_stage]["Input"] = workflow_execution["Globals"]
            # workflow_execution["Workflow"]["Stages"][current_stage]["metrics"]["queue_time"] = int(
            #    time.time())
            workflow_execution["Workflow"]["Stages"][current_stage]["Status"] = awsmie.STAGE_STATUS_STARTED

            try:
                logger.info(
                    "Updating workflow with new current stage")
                logger.info(json.dumps(workflow_execution))

                workitem = {
                    "WorkflowExecutionId": workflow_execution["Id"],
                    "stage": workflow_execution["Workflow"]["Stages"][current_stage]
                }

                # IMPORTANT: update the workflow_execution before queueing the work item...the
                # queued workitem must match the current stage when we start stage execution.
                # execution_table.put_item(Item=workflow_execution)
                response = execution_table.update_item(
                    Key={
                        'Id': workflow_execution["Id"]
                    },
                    UpdateExpression='SET Workflow.Stages.#stage = :stage, CurrentStage = :current_stage',
                    ExpressionAttributeNames={
                        '#stage': current_stage,
                    },
                    ExpressionAttributeValues={
                        ':stage': workflow_execution["Workflow"]["Stages"][current_stage],
                        ':current_stage': current_stage


                    }
                )

                update_workflow_execution_status(workflow_execution["Id"], workflow_execution["Status"], message)
                print(json.dumps(workitem))

            except Exception as e:
                message = "Exception queuing work item: {} ".format(e)

                workflow_execution["Status"] = awsmie.WORKFLOW_STATUS_ERROR

                logger.info(message)

                update_workflow_execution_status(workflow_execution["Id"], workflow_execution["Status"], message)

                # raise ChaliceViewError(
                raise ValueError(message)

    except Exception as e:
        workflow_execution["Status"] = awsmie.WORKFLOW_STATUS_ERROR
        message = "Exception {}".format(e)
        logger.info(message)
        update_workflow_execution_status(workflow_execution["Id"], workflow_execution["Status"], message)
        # raise ChaliceViewError(
        raise ValueError(
            "Exception: '%s'" % e)


    logger.info("workflow_execution: {}".format(
        json.dumps(workflow_execution)))
    return workflow_execution


def update_workflow_execution_status(id, status, message):
    """
    Get the workflow execution by id from dyanamo and assign to this object
    :param id: The id of the workflow execution
    :param status: The new status of the workflow execution

    """
    print("Update workflow execution {} set status = {}".format(id, status))
    execution_table = DYNAMO_RESOURCE.Table(WORKFLOW_EXECUTION_TABLE_NAME)

    if status == awsmie.WORKFLOW_STATUS_ERROR:
        response = execution_table.update_item(
            Key={
                'Id': id
            },
            UpdateExpression='SET #workflow_status = :workflow_status, Message = :message',
            ExpressionAttributeNames={
                '#workflow_status': "Status"
            },
            ExpressionAttributeValues={
                ':workflow_status': status,
                ':message': message

            }
        )
    else:
        response = execution_table.update_item(
            Key={
                'Id': id
            },
            UpdateExpression='SET #workflow_status = :workflow_status',
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


