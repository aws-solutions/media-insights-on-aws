# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import boto3
from boto3 import resource
from botocore.client import ClientError
from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.core import patch_all
from botocore import config
import uuid
import logging
import os
#from datetime import date
#from datetime import time
from datetime import datetime
import json
import time
import decimal
from MediaInsightsEngineLambdaHelper import Status as awsmie
from MediaInsightsEngineLambdaHelper import MediaInsightsOperationHelper
from MediaInsightsEngineLambdaHelper import MasExecutionError

patch_all()

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

if "ShortUUID" in os.environ:
    ShortUUID = os.environ["ShortUUID"]

if "DEFAULT_MAX_CONCURRENT_WORKFLOWS" in os.environ:
    DEFAULT_MAX_CONCURRENT_WORKFLOWS = int(os.environ["DEFAULT_MAX_CONCURRENT_WORKFLOWS"])
else:
    DEFAULT_MAX_CONCURRENT_WORKFLOWS = 10

mie_config = json.loads(os.environ['botoConfig'])
config = config.Config(**mie_config)

# DynamoDB
DYNAMO_CLIENT = boto3.client("dynamodb", config=config)
DYNAMO_RESOURCE = boto3.resource("dynamodb", config=config)

# Step Functions
SFN_CLIENT = boto3.client('stepfunctions', config=config)

# Simple Queue Service
SQS_RESOURCE = boto3.resource('sqs', config=config)
SQS_CLIENT = boto3.client('sqs', config=config)

# Lambda
LAMBDA_CLIENT = boto3.client("lambda", config=config)


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
        logger.info(json.dumps(event))

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
        else:

            system_table.put_item(
                Key={
                    'Name': 'MaxConcurrentWorkflows'
                },
                Value={
                    DEFAULT_MAX_CONCURRENT_WORKFLOWS
                }
            )

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
                        queued_workflow_status = workflow_execution['Status']
                        workflow_execution['Status'] = awsmie.WORKFLOW_STATUS_STARTED

                        # Update the workflow status now to indicate we have taken it off the queue
                        update_workflow_execution_status(workflow_execution["Id"], awsmie.WORKFLOW_STATUS_STARTED, "")

                        # Resumed workflows state machines are already executing since they just paused
                        # to wait for some external action
                        if queued_workflow_status != awsmie.WORKFLOW_STATUS_RESUMED:
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

def start_wait_operation_lambda(event, context):
    '''
    Pause a workflow to wait for external processing

    event is
    - Operation input
    - Operation configuration

    returns:
    Operation output

    '''
    logger.info(json.dumps(event))

    operator_object = MediaInsightsOperationHelper(event)

    try:
        update_workflow_execution_status(operator_object.workflow_execution_id, awsmie.WORKFLOW_STATUS_WAITING, "")
    except Exception as e:
        operator_object.update_workflow_status("Error")
        operator_object.add_workflow_metadata(WaitError="Unable to set workflow status to Waiting {e}".format(e=str(e)))
        raise MasExecutionError(operator_object.return_output_object())

    return operator_object.return_output_object()

def check_wait_operation_lambda(event, context):
    '''
    Check if a workflow is still in a Waiting state.

    event is
    - Operation input
    - Operation configuration

    returns:
    Operation output

    '''
    logger.info(json.dumps(event))

    operator_object = MediaInsightsOperationHelper(event)
    execution_table = DYNAMO_RESOURCE.Table(WORKFLOW_EXECUTION_TABLE_NAME)

    response = execution_table.get_item(
            Key={
                'Id': operator_object.workflow_execution_id
            },
            ConsistentRead=True)

    if "Item" in response:
        workflow_execution = response["Item"]
    else:
        workflow_execution = None
        # raise ChaliceViewError(
        operator_object.update_workflow_status("Error")
        operator_object.add_workflow_metadata(WaitError="Unable to find Waiting workflow execution {} {e}".format(
            operator_object.workflow_execution_id, e=str(e)))
        raise MasExecutionError(operator_object.return_output_object())

    logger.info("workflow_execution: {}".format(
        json.dumps(workflow_execution)))

    if workflow_execution["Status"] == awsmie.WORKFLOW_STATUS_WAITING:
        operator_object.update_workflow_status("Executing")
        return operator_object.return_output_object()
    elif workflow_execution["Status"] == awsmie.WORKFLOW_STATUS_STARTED:
        operator_object.update_workflow_status("Complete")
    else:
        operator_object.update_workflow_status("Error")
        operator_object.add_workflow_metadata(WaitError="Unexpected workflow execution status {}".format(
            workflow_execution["Status"]))
        raise MasExecutionError(operator_object.return_output_object())

    return operator_object.return_output_object()

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
                        logger.info(mediaType)
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
                        logger.info(key)
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
        logger.info("START NEXT STAGE: stage_name {}".format(stage_name))

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
                logger.info(json.dumps(workitem))

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
    logger.info("Update workflow execution {} set status = {}".format(id, status))
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

# Find all of the execution error events for a state machine execution
def get_execution_errors(arn):

    try:

        executions = []
        paginator = SFN_CLIENT.get_paginator('get_execution_history')

        # return all the history
        page_iterator = paginator.paginate(executionArn=arn,
                maxResults= 20,
                reverseOrder=True)

        # return only the history with exceptions
        for page in page_iterator:
            for event in page["events"]:
              if (any(sub in event["type"] for sub in ['Failed', 'Aborted', 'TimedOut'])):
                  logger.info("Found error event: {}".format(event))
                  executions.append(event)

        return executions

    except:
        logger.error("Unable to retrieve execution history for state machine termination")
        raise

# Find the earliest error message in the executions and retrieve additonal info if available
def parse_execution_error(arn, executions, status):

    message = "Caught Step Function Execution Status Change event for execution: "+ arn +", status:"+ status

    # return the cause info from the most recent failure, if any
    for execution in executions:
      for key, value in execution.items():
        if (any(sub in key for sub in ['Failed', 'Aborted', 'TimedOut'])):
          if "cause" in value:
              message = message+", cause: "+value["cause"]
              break

    return message

# This lambda is invoked for Step Functions Execution Status Change events
# that contain the status [ERROR, ABORTED, TIME_OUT].  Failures that occur
# within the steps of a workflow state machine are handled by the
# OperotorFailed lambda function, but if the state machine service throws
# an exception that causes the state machine to terminate immediately,
# it can't be handled within the state machine because the execution
# is haulted.
#
# Info on events handled here:
#     https://docs.aws.amazon.com/step-functions/latest/dg/cw-events.html
#
# Propagate the error and cause to the workflow control plane to close off
# the workflow execution
def workflow_error_handler_lambda (event, context):

  try:

    logger.info("workflow_error_handler_lambda: {}".format(json.dumps(event)))

    if not ShortUUID:
        raise Exception('ShortUUID is not set in lambda environment.')

    logger.info("Process step function error event for stack with ShortUUID {}".format(ShortUUID))

    if not ("detail" in event):
        raise Exception('event.detail is missing.')
    if not "name" in event["detail"]:
        raise Exception('name is missing in event.detail.')
    if not "status" in event["detail"]:
        raise Exception('status is missing in event.detail.')
    if not "executionArn" in event["detail"]:
        raise Exception('status is missing in event.detail.')

    # only process events for state machines that are part of this stack
    if not event["detail"]["stateMachineArn"].find(ShortUUID):
        logger.info("Event not processed: This event is not from the stack with ShortUUID {}".format(ShortUUID))
        return {}

    executions = get_execution_errors(event["detail"]["executionArn"])

    message = parse_execution_error(event["detail"]["executionArn"], executions, event["detail"]["status"])

    #input = event.detail.input
    stateMachineExecution = event["detail"]["executionArn"]

    # Check the currently active workflows for this execution arn and set the
    # status to error if found.
    started_workflows = list_workflow_executions_by_status(awsmie.WORKFLOW_STATUS_STARTED)
    for workflow in started_workflows:
        if workflow["StateMachineExecutionArn"] == event["detail"]["executionArn"]:
            update_workflow_execution_status(workflow["Id"], awsmie.WORKFLOW_STATUS_ERROR, message)

    response = {
      "stateMachineExecution": stateMachineExecution,
      "errorMessage": message
    }

    logger.info("workflow_error_handler_lambda caught error: {}".format(json.dumps(response)))

    return response
  except Exception as e:
    logger.error("Unable to handle workflow step function error: {}".format(e))
    raise(e)
