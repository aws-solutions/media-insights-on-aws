# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from chalice import Chalice
from chalice import NotFoundError, BadRequestError, ChaliceViewError, Response, ConflictError, CognitoUserPoolAuthorizer
import boto3
from boto3 import resource
from botocore.client import ClientError
from boto3.dynamodb.conditions import Key, Attr

import uuid
import logging
import os
# from datetime import date
# from datetime import time
from datetime import datetime
import json
import time
import decimal
import signal
from jsonschema import validate, ValidationError
# from urllib2 import build_opener, HTTPHandler, Request
from urllib.request import build_opener, HTTPHandler, Request
from MediaInsightsEngineLambdaHelper import DataPlane
from MediaInsightsEngineLambdaHelper import Status as awsmie
import os

APP_NAME = "workflowapi"
API_STAGE = "dev"
app = Chalice(app_name=APP_NAME)
app.debug = True
API_VERSION = "1.0.0"



# Setup logging
# Logging Configuration
# extra = {'requestid': app.current_request.context}
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

SYSTEM_TABLE_NAME = os.environ["SYSTEM_TABLE_NAME"]
WORKFLOW_TABLE_NAME = os.environ["WORKFLOW_TABLE_NAME"]
STAGE_TABLE_NAME = os.environ["STAGE_TABLE_NAME"]
OPERATION_TABLE_NAME = os.environ["OPERATION_TABLE_NAME"]
WORKFLOW_EXECUTION_TABLE_NAME = os.environ["WORKFLOW_EXECUTION_TABLE_NAME"]
HISTORY_TABLE_NAME = os.environ["HISTORY_TABLE_NAME"]
STAGE_EXECUTION_QUEUE_URL = os.environ["STAGE_EXECUTION_QUEUE_URL"]
STAGE_EXECUTION_ROLE = os.environ["STAGE_EXECUTION_ROLE"]
# FIXME testing NoQ execution
COMPLETE_STAGE_LAMBDA_ARN = os.environ["COMPLETE_STAGE_LAMBDA_ARN"] 
FILTER_OPERATION_LAMBDA_ARN = os.environ["FILTER_OPERATION_LAMBDA_ARN"]
OPERATOR_FAILED_LAMBDA_ARN = os.environ["OPERATOR_FAILED_LAMBDA_ARN"]
WORKFLOW_SCHEDULER_LAMBDA_ARN = os.environ["WORKFLOW_SCHEDULER_LAMBDA_ARN"]

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
# Helper class to convert a DynamoDB item to JSON.

# cognito
cognito_user_pool_arn = os.environ['USER_POOL_ARN']

authorizer = CognitoUserPoolAuthorizer(
    'MieUserPool', header='Authorization',
    provider_arns=[cognito_user_pool_arn])



class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return str(o)
        return super(DecimalEncoder, self).default(o)


def checkRequiredInput(key, dict, objectname):
    if key not in dict:
        raise BadRequestError("Key '%s' is required in '%s' input" % (
            key, objectname))


def load_apischema():
    schemata = {}
    schema_directory = os.path.dirname(__file__) + "/chalicelib/apischema/"
    for f in os.listdir(schema_directory):
        with open(schema_directory +f) as schema_file:
            schema = json.load(schema_file)
            schemata[schema['title']] = schema
            logger.info("Loaded schema: {}".format(json.dumps(schema)))
    return schemata

SCHEMA = load_apischema()

@app.route('/')
def index():
    return {'hello': 'world'}

############################################################################## 
#   ____            _                   ____       _               
#  / ___| _   _ ___| |_ ___ _ __ ___   / ___|  ___| |_ _   _ _ __  
#  \___ \| | | / __| __/ _ \ '_ ` _ \  \___ \ / _ \ __| | | | '_ \ 
#   ___) | |_| \__ \ ||  __/ | | | | |  ___) |  __/ |_| |_| | |_) |
#  |____/ \__, |___/\__\___|_| |_| |_| |____/ \___|\__|\__,_| .__/ 
#         |___/                                             |_|    
#
##############################################################################
@app.route('/system/configuration', cors=True, methods=['POST'], authorizer=authorizer)
def create_system_configuration_api():
    """ Add a new system configuration parameter
    
    - Updates the MIE system configuration with a new parameter or changes the value of
      existing parameters 
    
    Body:

    .. code-block:: python

        {
            "Name": "ParameterName",
            "Value": "ParameterValue" 
        }

    Supported parameters:

        MaxConcurrentWorkflows
            
            Sets the maximum number of workflows that are allowed to run concurrently.
            Any new workflows that are added after MaxConcurrentWorkflows is reached are
            placed on a queue until capacity is freed by completing workflows.  Use this
            to help avoid throttling in service API calls from workflow operators.

            This setting is checked each time the WorkflowSchedulerLambda is run and may
            take up to 60 seconds to take effect.

    Returns:
        None

    Raises:
        200: The system configuration was set successfully successfully.
        400: Bad Request 
             - an input value is invalid
        500: Internal server error 
    """

    try:
        config = app.current_request.json_body

        logger.info(app.current_request.json_body)
        system_table = DYNAMO_RESOURCE.Table(SYSTEM_TABLE_NAME)

        # Check allowed values for known configuration parameters
        if config["Name"] == "MaxConcurrentWorkflows":
            if config["Value"] < 1:
                raise BadRequestError("MaxConcurrentWorkflows must be a value > 1")

        system_table.put_item(Item=config)
    except Exception as e:
        logger.info("Exception {}".format(e))
        raise ChaliceViewError("Exception '%s'" % e)

    return {}

@app.route('/system/configuration', cors=True, methods=['GET'], authorizer=authorizer)
def get_system_configuration_api():
    """ Get the current MIE system configuration
    
    - Gets the current MIE system configuration parameter settings

    Returns:
        A list of dict containing the current MIE system configuration key-value pairs. 

        .. code-block:: python

            [
                {
                "Name": "Value"
                },
            ...]

    Raises:
        200: The system configuration was returned successfully.
        500: Internal server error 
    """

    try:

        system_table = DYNAMO_RESOURCE.Table(SYSTEM_TABLE_NAME)

        # Check if any configuration has been added yet
        response = system_table.scan(
            ConsistentRead=True)
    
    except Exception as e:
        logger.info("Exception {}".format(e))
        operation = None
        raise ChaliceViewError("Exception '%s'" % e)
    return response["Items"]

##############################################################################
#    ___                       _
#   / _ \ _ __   ___ _ __ __ _| |_ ___  _ __ ___
#  | | | | '_ \ / _ \ '__/ _` | __/ _ \| '__/ __|
#  | |_| | |_) |  __/ | | (_| | || (_) | |  \__ \
#   \___/| .__/ \___|_|  \__,_|\__\___/|_|  |___/
#        |_|
#
##############################################################################

@app.route('/workflow/operation', cors=True, methods=['POST'], authorizer=authorizer)
def create_operation_api():
    """ Create a new operation
    
    - Generates an operation state machine using the operation lambda(s) provided 
    - Creates a singleton operator stage that can be used to run the operator as a single-operator 
      stage in a workflow.

    Operators can be synchronous (Sync) or asynchronous (Async). Synchronous operators complete 
    before returning control to the invoker, while asynchronous operators return control to the invoker 
    when the operation is successfully initiated, but not complete. Asynchronous operators require 
    an additional monitoring task to check the status of the operation.

    For more information on how to implemenent lambdas to be used in MIE operators, please
    refer to the MIE Developer Quick Start.
      
       
    
    Body:

    .. code-block:: python

        {
            "Name":"operation-name",
            "Type": ["Async"|"Sync"],
            "Configuration" : {
                    "MediaType": "Video",
                    "Enabled:": True,
                    "configuration1": "value1",
                    "configuration2": "value2",
                    ...
                }
            "StartLambdaArn":arn,
            "MonitorLambdaArn":arn,
            "SfnExecutionRole": arn
            }

    Returns:
        A dict mapping keys to the corresponding operation. 

        .. code-block:: python

            {
                "Name": string,
                "Type": ["Async"|"Sync"],
                "Configuration" : {
                    "MediaType": "Video|Frame|Audio|Text|...",
                    "Enabled:": boolean,
                    "configuration1": "value1",
                    "configuration2": "value2",
                    ...
                }
                "StartLambdaArn":arn,
                "MonitorLambdaArn":arn,
                "StateMachineExecutionRoleArn": arn,
                "StateMachineAsl": ASL-string
                "StageName": string
            }

    Raises:
        200: The operation and stage was created successfully.
        400: Bad Request 
             - one of the input lambdas was not found
             - one or more of the required input keys is missing
             - an input value is invalid
        409: Conflict
        500: Internal server error 
    """

    operation = None

    operation = app.current_request.json_body

    logger.info(app.current_request.json_body)

    operation = create_operation(operation)

    return operation


def create_operation(operation):

    try:
        operation_table = DYNAMO_RESOURCE.Table(OPERATION_TABLE_NAME)

        logger.info(operation)

        validate(instance=operation, schema=SCHEMA["create_operation_request"])
        logger.info("Operation schema is valid")
        
        Name = operation["Name"]

        # FIXME - can jsonschema validate this?
        if operation["Type"] == "Async":
            checkRequiredInput("MonitorLambdaArn", operation, "Operation monitoring lambda function ARN")
        elif operation["Type"] == "Sync":
            pass
        else:
            raise BadRequestError('Operation Type must in ["Async"|"Sync"]')

        # Check if this operation already exists
        response = operation_table.get_item(
            Key={
                'Name': Name
            },
            ConsistentRead=True)

        if "Item" in response:
            raise ConflictError(
                "A operation with the name '%s' already exists" % Name)

        # Build the operation state machine. 

        if operation["Type"] == "Async":
            operationAsl = ASYNC_OPERATION_ASL
        elif operation["Type"] == "Sync":
            operationAsl = SYNC_OPERATION_ASL

        # Setup task parameters in step function.  This filters out the paramters from
        # the stage data structure that belong to this specific operation and passes the
        # result as input to the task lmbda
        # FIXME - remove this if hardcoded one works
        # params = TASK_PARAMETERS_ASL
        # params["OperationName"] = Name
        # params["Configuration.$"] = "$.Configuration." + Name
        # for k,v in operationAsl["States"].items():
        #     if v["Type"] == "Task":
        #         v["Parameters"] = params

        operationAslString = json.dumps(operationAsl)
        operationAslString = operationAslString.replace("%%OPERATION_NAME%%", operation["Name"])
        operationAslString = operationAslString.replace("%%OPERATION_MEDIA_TYPE%%",
                                                        operation["Configuration"]["MediaType"])

        if operation["Type"] == "Async":
            operationAslString = operationAslString.replace("%%OPERATION_MONITOR_LAMBDA%%",
                                                            operation["MonitorLambdaArn"])
        operationAslString = operationAslString.replace("%%OPERATION_START_LAMBDA%%", operation["StartLambdaArn"])
        operationAslString = operationAslString.replace("%%OPERATION_FAILED_LAMBDA%%", OPERATOR_FAILED_LAMBDA_ARN)
        operation["StateMachineAsl"] = operationAslString

        logger.info(json.dumps(operation["StateMachineAsl"]))

        operation["Version"] = "v0"
        operation["Id"] = str(uuid.uuid4())
        operation["Created"] = str(datetime.now().timestamp())
        operation["ResourceType"] = "OPERATION"
        operation["ApiVersion"] = API_VERSION

        operation_table.put_item(Item=operation)

        # build a singleton stage for this operation
        try:
            stage = {}
            stage["Name"] = "_" + operation["Name"]
            stage["Operations"] = []
            stage["Operations"].append(operation["Name"])

            # Build stage
            response = create_stage(stage)

            operation["StageName"] = stage["Name"]

            operation_table.put_item(Item=operation)

        
        except Exception as e:
            logger.error("Error creating default stage for operation {}: {}".format(operation["Name"], e))
            response = operation_table.delete_item(
                Key={
                    'Name': operation["Name"]
                }
            )
            raise

    except ConflictError as e:
        logger.error ("got CoonflictError: {}".format (e))
        raise 
    except ValidationError as e:
        logger.error("got bad request error: {}".format(e))
        raise BadRequestError(e) 
    except Exception as e:
        logger.info("Exception {}".format(e))
        operation = None
        raise ChaliceViewError("Exception '%s'" % e)

    logger.info("end create_operation: {}".format(json.dumps(operation, cls=DecimalEncoder)))
    return operation

# FIXME - dead code?
TASK_PARAMETERS_ASL = {
    "StageName.$": "$.Name",
    "Name":"%%OPERATION_NAME%%",
    "Input.$":"$.Input",
    "Configuration.$":"$.Configuration.%%OPERATION_NAME%%",
    "AssetId.$":"$.AssetId",
    "WorkflowExecutionId.$":"$.WorkflowExecutionId"
}

ASYNC_OPERATION_ASL =         {
    "StartAt": "Filter %%OPERATION_NAME%% Media Type? (%%STAGE_NAME%%)",
    "States": {
        "Filter %%OPERATION_NAME%% Media Type? (%%STAGE_NAME%%)": {
            "Type": "Task",
            "Parameters": {
                "StageName.$": "$.Name",
                "Name":"%%OPERATION_NAME%%",
                "Input.$":"$.Input",
                "Configuration.$":"$.Configuration.%%OPERATION_NAME%%",
                "AssetId.$":"$.AssetId",
                "WorkflowExecutionId.$":"$.WorkflowExecutionId",
                "Type": "%%OPERATION_MEDIA_TYPE%%",
                "Status": "$.Status"
            },
            "Resource": FILTER_OPERATION_LAMBDA_ARN,
            "ResultPath": "$.Outputs",
            "OutputPath": "$.Outputs",
            "Next": "Skip %%OPERATION_NAME%%? (%%STAGE_NAME%%)",
            "Retry": [ {
                "ErrorEquals": ["Lambda.ServiceException", "Lambda.AWSLambdaException", "Lambda.SdkClientException", "Lambda.Unknown", "MasExecutionError"],
                "IntervalSeconds": 2,
                "MaxAttempts": 2,
                "BackoffRate": 2
            }
            ],
            "Catch": [
            {
                "ErrorEquals": ["States.ALL"],
                "Next": "%%OPERATION_NAME%% Failed (%%STAGE_NAME%%)",
                "ResultPath": "$.Outputs"
            }
            ]
            
        },
        "Skip %%OPERATION_NAME%%? (%%STAGE_NAME%%)": {
            "Type": "Choice",
            "Choices": [{
                "Variable": "$.Status",
                "StringEquals": awsmie.OPERATION_STATUS_STARTED,
                "Next": "Execute %%OPERATION_NAME%% (%%STAGE_NAME%%)"
            }],
            "Default": "%%OPERATION_NAME%% Not Started (%%STAGE_NAME%%)"
        },
        "%%OPERATION_NAME%% Not Started (%%STAGE_NAME%%)": {
            "Type": "Succeed"
        },
        "Execute %%OPERATION_NAME%% (%%STAGE_NAME%%)": {
            "Type": "Task",
            "Resource": "%%OPERATION_START_LAMBDA%%",
            "ResultPath": "$.Outputs",
            "OutputPath": "$.Outputs",
            "Next": "%%OPERATION_NAME%% Wait (%%STAGE_NAME%%)",
            "Retry": [ {
                "ErrorEquals": ["Lambda.ServiceException", "Lambda.AWSLambdaException", "Lambda.SdkClientException", "Lambda.Unknown", "MasExecutionError"],
                "IntervalSeconds": 2,
                "MaxAttempts": 2,
                "BackoffRate": 2
            }
            ],
            "Catch": [
            {
                "ErrorEquals": ["States.ALL"],
                "Next": "%%OPERATION_NAME%% Failed (%%STAGE_NAME%%)",
                "ResultPath": "$.Outputs"
            }
            ]
        },
        "%%OPERATION_NAME%% Wait (%%STAGE_NAME%%)": {
            "Type": "Wait",
            "Seconds": 10,
            "Next": "Get %%OPERATION_NAME%% Status (%%STAGE_NAME%%)"
        },
        "Get %%OPERATION_NAME%% Status (%%STAGE_NAME%%)": {
            "Type": "Task",
            "Resource": "%%OPERATION_MONITOR_LAMBDA%%",
            "Next": "Did %%OPERATION_NAME%% Complete (%%STAGE_NAME%%)",
            "Retry": [ {
                "ErrorEquals": ["Lambda.ServiceException", "Lambda.AWSLambdaException", "Lambda.SdkClientException", "Lambda.Unknown", "MasExecutionError"],
                "IntervalSeconds": 2,
                "MaxAttempts": 2,
                "BackoffRate": 2
            }
            ],
            "Catch": [
            {
                "ErrorEquals": ["States.ALL"],
                "Next": "%%OPERATION_NAME%% Failed (%%STAGE_NAME%%)",
                "ResultPath": "$.Outputs"
            }
            ]
        },
        "Did %%OPERATION_NAME%% Complete (%%STAGE_NAME%%)": {
            "Type": "Choice",
            "Choices": [{
                    "Variable": "$.Status",
                    "StringEquals": "Executing",
                    "Next": "%%OPERATION_NAME%% Wait (%%STAGE_NAME%%)"
                },
                {
                    "Variable": "$.Status",
                    "StringEquals": "Complete",
                    "Next": "%%OPERATION_NAME%% Succeeded (%%STAGE_NAME%%)"
                }
            ],
            "Default": "%%OPERATION_NAME%% Failed (%%STAGE_NAME%%)"
        },
        "%%OPERATION_NAME%% Failed (%%STAGE_NAME%%)": {
            "Type": "Task",
            "End": True,
            "Resource": "%%OPERATION_FAILED_LAMBDA%%",
            "ResultPath": "$",
            "Retry": [{
                "ErrorEquals": ["Lambda.ServiceException", "Lambda.AWSLambdaException", "Lambda.SdkClientException", "Lambda.Unknown", "MasExecutionError"],
                "IntervalSeconds": 2,
                "MaxAttempts": 2,
                "BackoffRate": 2
            }]
        },
        "%%OPERATION_NAME%% Succeeded (%%STAGE_NAME%%)": {
            "Type": "Succeed"
        }
    }
}

SYNC_OPERATION_ASL = {
    "StartAt": "Filter %%OPERATION_NAME%% Media Type? (%%STAGE_NAME%%)",
    "States": {
        "Filter %%OPERATION_NAME%% Media Type? (%%STAGE_NAME%%)": {
            "Type": "Task",
            "Parameters": {
                "StageName.$": "$.Name",
                "Name":"%%OPERATION_NAME%%",
                "Input.$":"$.Input",
                "Configuration.$":"$.Configuration.%%OPERATION_NAME%%",
                "AssetId.$":"$.AssetId",
                "WorkflowExecutionId.$":"$.WorkflowExecutionId",
                "Type": "%%OPERATION_MEDIA_TYPE%%",
                "Status": "$.Status"
            },
            "Resource": FILTER_OPERATION_LAMBDA_ARN,
            "ResultPath": "$.Outputs",
            "OutputPath": "$.Outputs",
            "Next": "Skip %%OPERATION_NAME%%? (%%STAGE_NAME%%)",
            "Retry": [ {
                "ErrorEquals": ["Lambda.ServiceException", "Lambda.AWSLambdaException", "Lambda.SdkClientException", "Lambda.Unknown", "MasExecutionError"],
                "IntervalSeconds": 2,
                "MaxAttempts": 2,
                "BackoffRate": 2
            }
            ],
            "Catch": [
            {
                "ErrorEquals": ["States.ALL"],
                "Next": "%%OPERATION_NAME%% Failed (%%STAGE_NAME%%)",
                "ResultPath": "$.Outputs"
            }
            ]
            
        },
        "Skip %%OPERATION_NAME%%? (%%STAGE_NAME%%)": {
            "Type": "Choice",
            "Choices": [{
                "Variable": "$.Status",
                "StringEquals": awsmie.OPERATION_STATUS_STARTED,
                "Next": "Execute %%OPERATION_NAME%% (%%STAGE_NAME%%)"
            }],
            "Default": "%%OPERATION_NAME%% Not Started (%%STAGE_NAME%%)"
        },
        "%%OPERATION_NAME%% Not Started (%%STAGE_NAME%%)": {
            "Type": "Succeed"
        },
        "Execute %%OPERATION_NAME%% (%%STAGE_NAME%%)": {
            "Type": "Task",
            "Resource": "%%OPERATION_START_LAMBDA%%",
            "ResultPath": "$.Outputs",
            "OutputPath": "$.Outputs",
            "Next": "Did %%OPERATION_NAME%% Complete (%%STAGE_NAME%%)",
            "Retry": [ {
                "ErrorEquals": ["Lambda.ServiceException", "Lambda.AWSLambdaException", "Lambda.SdkClientException", "Lambda.Unknown", "MasExecutionError"],
                "IntervalSeconds": 2,
                "MaxAttempts": 2,
                "BackoffRate": 2
            }
            ],
            "Catch": [
            {
                "ErrorEquals": ["States.ALL"],
                "Next": "%%OPERATION_NAME%% Failed (%%STAGE_NAME%%)",
                "ResultPath": "$.Outputs"
            }
            ]
        },
        "Did %%OPERATION_NAME%% Complete (%%STAGE_NAME%%)": {
            "Type": "Choice",
            "Choices": [
                {
                    "Variable": "$.Status",
                    "StringEquals": "Complete",
                    "Next": "%%OPERATION_NAME%% Succeeded (%%STAGE_NAME%%)"
                }
            ],
            "Default": "%%OPERATION_NAME%% Failed (%%STAGE_NAME%%)"
        },
        "%%OPERATION_NAME%% Failed (%%STAGE_NAME%%)": {
            "Type": "Task",
            "End": True,
            "Resource": "%%OPERATION_FAILED_LAMBDA%%",
            "ResultPath": "$",
            "Retry": [{
                "ErrorEquals": ["Lambda.ServiceException", "Lambda.AWSLambdaException", "Lambda.SdkClientException", "Lambda.Unknown", "MasExecutionError"],
                "IntervalSeconds": 2,
                "MaxAttempts": 2,
                "BackoffRate": 2
            }]
        },
        "%%OPERATION_NAME%% Succeeded (%%STAGE_NAME%%)": {
            "Type": "Succeed"
        }
    }
}


@app.route('/workflow/operation', cors=True, methods=['PUT'], authorizer=authorizer)
def update_operation():
    """ Update operation NOT IMPLEMENTED 

    """
    operation = {"Message": "Update on stages in not implemented"}
    return operation


@app.route('/workflow/operation', cors=True, methods=['GET'], authorizer=authorizer)
def list_operations():
    """ List all defined operators

    Returns:
        A list of operation definitions.

    Raises:
        200: All operations returned sucessfully.
        500: Internal server error 
    """

    table = DYNAMO_RESOURCE.Table(OPERATION_TABLE_NAME)

    response = table.scan()
    operations = response['Items']
    while 'LastEvaluatedKey' in response:
        response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        operations.extend(response['Items'])

    return operations


@app.route('/workflow/operation/{Name}', cors=True, methods=['GET'], authorizer=authorizer)
def get_operation_by_name(Name):
    """ Get an operation definition by name

    Returns:
        A dictionary containing the operation definition.

    Raises:
        200: All operations returned sucessfully.
        404: Not found
        500: Internal server error 
    """
    operation_table = DYNAMO_RESOURCE.Table(OPERATION_TABLE_NAME)
    operation = None
    response = operation_table.get_item(
        Key={
            'Name': Name
        })

    if "Item" in response:
        operation = response["Item"]
    else:
        raise NotFoundError(
            "Exception: operation '%s' not found" % Name)

    return operation


@app.route('/workflow/operation/{Name}', cors=True, methods=['DELETE'], authorizer=authorizer)
def delete_operation_api(Name):
    """ Delete a an operation

    Returns:  

    Raises:
        200: Operation deleted sucessfully.
        400: Bad Request - there are dependent workflows and query parameter force=false
        500: Internal server error 
    """
    Force = False
    params = app.current_request.query_params

    if params and "force" in params and params["force"] == "true":
        Force = True

    operation = delete_operation(Name, Force)

    return operation

    
def delete_operation(Name, Force):

    table = DYNAMO_RESOURCE.Table(OPERATION_TABLE_NAME)
    operation = {}

    logger.info("delete_stage({},{})".format(Name, Force))

    try:

        operation = {}
        response = table.get_item(
            Key={
                'Name': Name
            },
            ConsistentRead=True)

        if "Item" in response:

            workflows = list_workflows_by_operator(Name)

            if len(workflows) != 0 and Force == False:
                Message = """Dependent workflows were found for operation {}.
                    Either delete the dependent workflows or set the query parameter
                    force=true to delete the stage anyhow.  Undeleted dependent workflows 
                    will be kept but will contain the deleted definition of the stage.  To 
                    find the workflow that depend on a stage use the following endpoint: 
                    GET /workflow/list/operation/""".format(Name)

                raise BadRequestError(Message)

            operation = response["Item"]

            delete_stage(operation["StageName"], True)  

            response = table.delete_item(
                Key={
                    'Name': Name
                })

            # Flag dependent workflows 
            flag_operation_dependent_workflows(Name)

        else:

            operation["Message"] = "Warning: operation '{}' not found".format(Name)
            # raise NotFoundError(
            #    "Exception: operation '%s' not found" % Name) 

    except BadRequestError as e:
        logger.error("got bad request error: {}".format(e))
        raise 
    except Exception as e:

        operation = None
        logger.info("Exception {}".format(e))
        raise ChaliceViewError("Exception: '%s'" % e)

    return operation

def flag_operation_dependent_workflows(OperationName):

    try:
        table = DYNAMO_RESOURCE.Table(WORKFLOW_TABLE_NAME)

        workflows = list_workflows_by_operator(OperationName)
        for workflow in workflows:
            result = table.update_item(
                Key={
                    'Name': workflow["Name"]
                },
                UpdateExpression="SET StaleOperations = list_append(StaleOperations, :i)",
                ExpressionAttributeValues={
                    ':i': [OperationName],
                },
                ReturnValues="UPDATED_NEW"
            )
        
    except Exception as e:

        
        logger.info("Exception flagging workflows dependent on dropped operations {}".format(e))
        raise ChaliceViewError("Exception: '%s'" % e)

    return OperationName

################################################################################################
#   ____  _
#  / ___|| |_ __ _  __ _  ___ ___
#  \___ \| __/ _` |/ _` |/ _ / __|
#   ___) | || (_| | (_| |  __\__ \
#  |____/ \__\__,_|\__, |\___|___/
#                  |___/
#
################################################################################################

@app.route('/workflow/stage', cors=True, methods=['POST'], authorizer=authorizer)
def create_stage_api():
    """ Create a stage state machine from a list of existing operations.  
    
    A stage is a set of operations that are grouped so they can be executed in parallel.
    When the stage is executed as part of a workflow, operations within a stage are executed as
    branches in a parallel Step Functions state.  The generated state machines status is tracked by the 
    workflow engine control plane during execution.

    An optional Configuration for each operator in the stage can be input to override the
    default configuration for the stage.

    Body:

    .. code-block:: python

            {
            "Name":"stage-name",
            "Operations": ["operation-name1", "operation-name2", ...]
            }

    Returns:
        A dict mapping keys to the corresponding stage created including 
        the ARN of the state machine created. 

        {
            "Name": string,
            "Operations": [
                "operation-name1",
                "operation-name2", 
                ...
            ],
            "Configuration": {
                "operation-name1": operation-configuration-object1,
                "operation-name2": operation-configuration-object1,
                ...
            }
            "StateMachineArn": ARN-string
        }
        {
            "Name": "TestStage",
            "Operations": [
                "TestOperator"
            ],
            "Configuration": {
                "TestOperator": {
                    "MediaType": "Video",
                    "Enabled": true
                }
            },
            "StateMachineArn": "arn:aws:states:us-west-2:123456789123:stateMachine:TestStage"
        }

    Raises:
        200: The stage was created successfully.
        400: Bad Request - one of the input state machines was not found or was invalid
        409: Conflict
        500: Internal server error 
    """

    stage = None

    stage = app.current_request.json_body

    logger.info(app.current_request.json_body)

    stage = create_stage(stage)

    return stage


def create_stage(stage):
    try:
        stage_table = DYNAMO_RESOURCE.Table(STAGE_TABLE_NAME)
        Configuration = {}

        logger.info(stage)
        
        validate(instance=stage, schema=SCHEMA["create_stage_request"])
        logger.info("Stage schema is valid")

        Name = stage["Name"]

        # Check if this stage already exists
        response = stage_table.get_item(
            Key={
                'Name': Name
            },
            ConsistentRead=True)

        if "Item" in response:
            raise ConflictError(
                "A stage with the name '%s' already exists" % Name)

        # Build the stage state machine.  The stage machine consists of a parallel state with 
        # branches for each operator and a call to the stage completion lambda at the end.  
        # The parallel state takes a stage object as input.  Each
        # operator returns and operatorOutput object. The outputs for each operator are 
        # returned from the parallel state as elements of the "outputs" array.    
        stageAsl = {
            "StartAt": "Preprocess Media",
            "States": {
                "Complete Stage {}".format(Name): {
                    "Type": "Task",
                    # FIXME - testing NoQ workflows
                    #"Resource": COMPLETE_STAGE_LAMBDA_ARN,
                    "Resource": COMPLETE_STAGE_LAMBDA_ARN,
                    "End": True
                }
            }
        }
        stageAsl["StartAt"] = Name
        stageAsl["States"][Name] = {
            "Type": "Parallel",
            "Next": "Complete Stage {}".format(Name),
            "ResultPath": "$.Outputs",
            "Branches": [
            ]
        }

        # Add a branch to the stage state machine for each operation, build up default 
        # Configuration for the stage based on the operator Configuration

        for op in stage["Operations"]:
            # lookup base workflow
            operation = get_operation_by_name(op)
            logger.info(json.dumps(operation, cls=DecimalEncoder))

            stageAsl["States"][Name]["Branches"].append(
                json.loads(operation["StateMachineAsl"]))
            Configuration[op] = operation["Configuration"]

            stageStateMachineExecutionRoleArn = operation["StateMachineExecutionRoleArn"]
        
        stageAslString = json.dumps(stageAsl)
        stageAslString = stageAslString.replace("%%STAGE_NAME%%", stage["Name"])
        stageAsl = json.loads(stageAslString)
        logger.info(json.dumps(stageAsl))

        stage["Configuration"] = Configuration

        # Build stage
        response = SFN_CLIENT.create_state_machine(
            name=Name,
            definition=json.dumps(stageAsl),
            roleArn=stageStateMachineExecutionRoleArn
        )

        stage["StateMachineArn"] = response["stateMachineArn"]

        stage["Version"] = "v0"
        stage["Id"] = str(uuid.uuid4())
        stage["Created"] = str(datetime.now().timestamp())
        stage["ResourceType"] = "STAGE"
        stage["ApiVersion"] = API_VERSION

        stage_table.put_item(Item=stage)
    
    except ValidationError as e:
        logger.error("got bad request error: {}".format(e))
        raise BadRequestError(e)
    except Exception as e:
        logger.info("Exception {}".format(e))
        stage = None
        raise ChaliceViewError("Exception '%s'" % e)

    return stage


@app.route('/workflow/stage', cors=True, methods=['PUT'], authorizer=authorizer)
def update_stage():
    """ Update a stage NOT IMPLEMENTED 

    XXX

    """
    stage = {"Message": "NOT IMPLEMENTED"}
    return stage


@app.route('/workflow/stage', cors=True, methods=['GET'], authorizer=authorizer)
def list_stages():
    """ List all stage defintions

    Returns:
        A list of operation definitions.

    Raises:
        200: All operations returned sucessfully.
        500: Internal server error 
    """

    table = DYNAMO_RESOURCE.Table(STAGE_TABLE_NAME)

    response = table.scan()
    stages = response['Items']
    while 'LastEvaluatedKey' in response:
        response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        stages.extend(response['Items'])

    return stages


@app.route('/workflow/stage/{Name}', cors=True, methods=['GET'], authorizer=authorizer)
def get_stage_by_name(Name):
    """ Get a stage definition by name

    Returns:
        A dictionary contianing the stage definition.

    Raises:
        200: All stages returned sucessfully.
        404: Not found
        500: Internal server error 
    """
    stage_table = DYNAMO_RESOURCE.Table(STAGE_TABLE_NAME)
    stage = None
    response = stage_table.get_item(
        Key={
            'Name': Name
        })

    if "Item" in response:
        stage = response["Item"]
    else:
        raise NotFoundError(
            "Exception: stage '%s' not found" % Name)

    return stage


@app.route('/workflow/stage/{Name}', cors=True, methods=['DELETE'], authorizer=authorizer)
def delete_stage_api(Name):
    """ Delete a stage

    Returns:  

    Raises:
        200: Stage deleted sucessfully.
        400: Bad Request - there are dependent workflows and query parameter force=False
        404: Not found
        500: Internal server error 
    """
    Force = False
    params = app.current_request.query_params

    if params and "force" in params and params["force"] == "true":
        Force = True

    stage = delete_stage(Name, Force)

    return stage


def delete_stage(Name, Force):

    table = DYNAMO_RESOURCE.Table(STAGE_TABLE_NAME)

    logger.info("delete_stage({},{})".format(Name, Force))

    try:

        stage = {}
        response = table.get_item(
            Key={
                'Name': Name
            },
            ConsistentRead=True)

        if "Item" in response:

            workflows = list_workflows_by_stage(Name)
            stage = response["Item"]

            if len(workflows) != 0 and Force == False:
                Message = """Dependent workflows were found for stage {}.
                    Either delete the dependent workflows or set the query parameter
                    force=true to delete the stage anyhow.  Undeleted dependent workflows 
                    will be kept but will contain the deleted definition of the stage.  To 
                    find the workflow that depend on a stage use the following endpoint: 
                    GET /workflow/list/stage/""".format(Name)

                raise BadRequestError(Message)

            

            # Delete the stage state machine 
            response = SFN_CLIENT.delete_state_machine(
                stateMachineArn=stage["StateMachineArn"]
            )

            response = table.delete_item(
                Key={
                    'Name': Name
                })

            flag_stage_dependent_workflows(Name)

        else:
            stage["Message"] = "Warning: stage '{}' not found".format(Name)

    except BadRequestError as e:
        logger.error("got bad request error: {}".format(e))
        raise 
    except Exception as e:

        stage = None
        logger.info("Exception {}".format(e))
        raise ChaliceViewError("Exception: '%s'" % e)

    return stage

def flag_stage_dependent_workflows(StageName):

    try:
        table = DYNAMO_RESOURCE.Table(WORKFLOW_TABLE_NAME)

        workflows = list_workflows_by_stage(StageName)
        for workflow in workflows:
            result = table.update_item(
                Key={
                    'Name': workflow["Name"]
                },
                UpdateExpression="SET StaleStages = list_append(StaleStages, :i)",
                ExpressionAttributeValues={
                    ':i': [StageName],
                },
                ReturnValues="UPDATED_NEW"
            )
        
    except Exception as e:

        logger.info("Exception flagging workflows dependent on dropped stage {}".format(e))
        raise ChaliceViewError("Exception: '%s'" % e)

    return StageName

###############################################################################
#  __        __         _     __ _
#  \ \      / /__  _ __| | __/ _| | _____      _____
#   \ \ /\ / / _ \| '__| |/ / |_| |/ _ \ \ /\ / / __|
#    \ V  V / (_) | |  |   <|  _| | (_) \ V  V /\__ \
#     \_/\_/ \___/|_|  |_|\_\_| |_|\___/ \_/\_/ |___/
#
###############################################################################

@app.route('/workflow', cors=True, methods=['POST'], authorizer=authorizer)
def create_workflow_api():
    """ Create a workflow from a list of existing stages.  
    
    A workflow is a pipeline of stages that are executed sequentially to transform and 
    extract metadata for a set of MediaType objects.  Each stage must contain either a 
    "Next" key indicating the next stage to execute or and "End" key indicating it
    is the last stage.

    Body:

    .. code-block:: python

        {
            "Name": string,
            "StartAt": string - name of starting stage,
            "Stages": {
                "stage-name": {
                    "Next": "string - name of next stage"
                },
                ...,
                "stage-name": {
                    "End": true
                }
            }
        }
    

    Returns:
        A dict mapping keys to the corresponding workflow created including the 
        AWS resources used to execute each stage.        

        .. code-block:: python

            {
                "Name": string,
                "StartAt": string - name of starting stage,
                "Stages": {
                    "stage-name": {
                        "Resource": queueARN,
                        "StateMachine": stateMachineARN,
                        "Configuration": stageConfigurationObject,
                        "Next": "string - name of next stage"
                    },
                    ...,
                    "stage-name": {
                        "Resource": queueARN,
                        "StateMachine": stateMachineARN,
                        "Configuration": stageConfigurationObject,
                        "End": true
                    }
                }
            }
        

    Raises:
        200: The workflow was created successfully.
        400: Bad Request - one of the input stages was not found or was invalid
        500: Internal server error 
    """

    workflow = app.current_request.json_body
    logger.info(json.dumps(workflow))

    return create_workflow("api", workflow)


def create_workflow(trigger, workflow):
    try:
        workflow_table = DYNAMO_RESOURCE.Table(WORKFLOW_TABLE_NAME)

        workflow["Trigger"] = trigger
        workflow["Operations"] = []
        workflow["StaleOperations"] = []
        workflow["StaleStages"] = []
        workflow["Version"] = "v0"
        workflow["Id"] = str(uuid.uuid4())
        workflow["Created"] = str(datetime.now().timestamp())
        workflow["Revisions"] = str(1)
        workflow["ResourceType"] = "WORKFLOW"
        workflow["ApiVersion"] = API_VERSION

        logger.info(json.dumps(workflow))

        # Validate inputs

        checkRequiredInput("Name", workflow, "Workflow Definition")
        checkRequiredInput("StartAt", workflow, "Workflow Definition")
        checkRequiredInput("Stages", workflow, "Workflow Definition")

        workflow = build_workflow(workflow)
            
        # Build state machine
        response = SFN_CLIENT.create_state_machine(
            name=workflow["Name"],
            definition=json.dumps(workflow["WorkflowAsl"]),
            roleArn=STAGE_EXECUTION_ROLE
        )    

        workflow.pop("WorkflowAsl")
        workflow["StateMachineArn"] = response["stateMachineArn"]

        
        workflow_table.put_item(
            Item=workflow,
            ConditionExpression="attribute_not_exists(#workflow_name)",
            ExpressionAttributeNames={
                '#workflow_name': "Name"
            })

    except ClientError as e:
        # Ignore the ConditionalCheckFailedException, bubble up
        # other exceptions.
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            raise ConflictError("Workflow with Name {} already exists".format(workflow["Name"]))
        else:
            raise

    except Exception as e:

        if "StateMachineArn" in workflow:
            response = SFN_CLIENT.delete_state_machine(
            workflow["StateMachineArn"]
        ) 
        logger.info("Exception {}".format(e))
        workflow = None
        raise ChaliceViewError("Exception '%s'" % e)

    return workflow

def build_workflow(workflow):

    logger.info("Sanity Check for End of workflow")
    endcount = 0
    for Name, stage in workflow["Stages"].items():

        # Stage must have an End or a Next key
        if "End" in stage and stage["End"] == True:
            endcount += 1
        elif "Next" in stage:
            pass
        else:
            raise BadRequestError("Stage %s must have either an 'End' or and 'Next' key" % (
                Name))

    if endcount != 1:
        raise BadRequestError("Workflow %s must have exactly 1 'End' key within its stages" % (
            workflow["Name"]))

    logger.info("Get stage state machines")
    for Name, stage in workflow["Stages"].items():
        s = get_stage_by_name(Name)

        logger.info(json.dumps(s))

        response = SFN_CLIENT.describe_state_machine(
            stateMachineArn=s["StateMachineArn"]
        )

        s["stateMachineAsl"] = json.loads(response["definition"])
        stage.update(s)

        # save the operators for this stage to the list of operators in the 
        # workflow.  This list is maintained to make finding workflows that
        # use an operator easier later
        workflow["Operations"].extend(stage["Operations"])

        logger.info(json.dumps(s))

    # Build the workflow state machine.
    startStageAsl = workflow["Stages"][workflow["StartAt"]]["stateMachineAsl"]
    startAt = startStageAsl["StartAt"]
    logger.info(startAt)

    workflowAsl = {
        "StartAt": startAt,
        "States": {
        }
    }

    logger.info("Merge stages into workflow state machine")
    for workflowStageName, workflowStage in workflow["Stages"].items():
        logger.info("LOOP OVER WORKFLOW STAGES")
        logger.info(json.dumps(workflowStage))


        # if this stage is not the end stage
        # - link the end of this stages ASL to the start of the next stages ASL
        if "Next" in workflowStage:
            nextWorkflowStageName = workflowStage["Next"]
            nextWorkflowStage = workflow["Stages"][workflowStage["Next"]]

            logger.info("NEXT STAGE")
            logger.info(json.dumps(nextWorkflowStage))

            # Find the End state for this stages ASL and link it to the start of
            # the next stage ASL
            print(json.dumps(workflowStage["stateMachineAsl"]["States"]))
            for k, v in workflowStage["stateMachineAsl"]["States"].items():
                print(k)
                if ("End" in v):
                    endState = k

            # endState = find("End", workflowStage["stateMachineAsl"]["States"])

            logger.info("END STATE {}".format(endState))

            workflowStage["stateMachineAsl"]["States"][endState]["Next"] = nextWorkflowStage["stateMachineAsl"][
                "StartAt"]

            # Remove the end key from the end state
            workflowStage["stateMachineAsl"]["States"][endState].pop("End")

        workflowAsl["States"].update(workflowStage["stateMachineAsl"]["States"])

        # Remove ASL from the stage since we rolled it into the workflow and ASL in saved in the stage defintition
        workflowStage.pop("stateMachineAsl")

        logger.info("IN LOOP WORKFLOW")
        logger.info(json.dumps(workflowAsl))

    logger.info(json.dumps(workflowAsl))  
    workflow["WorkflowAsl"] = workflowAsl

    return workflow

@app.route('/workflow', cors=True, methods=['PUT'], authorizer=authorizer)
def update_workflow_api():
    """ Update a workflow from a list of existing stages.  
    
    Update the definition of an existing workflow.


    Body:

    .. code-block:: python

        {
            "Name": string - name of the workflow to modify,
            "StartAt": string - name of starting stage,
            "Stages": {
                "stage-name": {
                    "Next": "string - name of next stage"
                },
                ...,
                "stage-name": {
                    "End": true
                }
            }
        }
    

    Returns:
        A dict mapping keys to the corresponding workflow updated including the 
        AWS resources used to execute each stage.        

        .. code-block:: python

            {
                "Name": string - name of the workflow to modify,
                "Configuration": Configuration object.  Contains the default configuration for the workflow.  Use the
                    GET /workflow/donfiguration/{WorkflowName} API to get the current setting for this object.
                "StartAt": string - name of starting stage,
                "Stages": {
                    "stage-name": {
                        "Resource": queueARN,
                        "StateMachine": stateMachineARN,
                        "Configuration": stageConfigurationObject,
                        "Next": "string - name of next stage"
                    },
                    ...,
                    "stage-name": {
                        "Resource": queueARN,
                        "StateMachine": stateMachineARN,
                        "Configuration": stageConfigurationObject,
                        "End": true
                    }
                }
            }
        

    Raises:
        200: The workflow was updated successfully.
        400: Bad Request - one of the input stages was not found or was invalid
        500: Internal server error 
    """
    workflow = app.current_request.json_body
    logger.info(json.dumps(workflow))

    return update_workflow("api", workflow)

def update_workflow(trigger, new_workflow):

    
    try:
        workflow_table = DYNAMO_RESOURCE.Table(WORKFLOW_TABLE_NAME)
        history_table = DYNAMO_RESOURCE.Table(HISTORY_TABLE_NAME)

        checkRequiredInput("Name", new_workflow, "Workflow Definition")

        workflow = get_workflow_by_name(new_workflow["Name"])
        
        workflow["Operations"] = []
        workflow["StaleOperations"] = []
        workflow["StaleStages"] = []
        
        revisions = int(workflow["Revisions"])

        old_version = workflow["Version"]
        workflow["Version"] = "v"+str(revisions+1)

        if "StartAt" in new_workflow:
            workflow["StartAt"] = new_workflow["StartAt"]

        if "Stages" in new_workflow:
            workflow["Stages"] = new_workflow["Stages"]

        logger.info(json.dumps(workflow))

        # We rebuild the workfow regardless of whether new stages were passed in.  This will update the workflow 
        # with the most recent state machine definitions for operators and stages.
        workflow = build_workflow(workflow)

        # Update the workflow state machine
        response = SFN_CLIENT.update_state_machine(
            stateMachineArn=workflow["StateMachineArn"],
            definition=json.dumps(workflow["WorkflowAsl"]),
            roleArn=STAGE_EXECUTION_ROLE
        )    

        # We saved the Asl in the state machine and we can generate it too. declutter.
        workflow.pop("WorkflowAsl")
            
        workflow_table.put_item(
            Item=workflow
            # ,
            # ConditionExpression="Version = :old_version",
            # ExpressionAttributeNames={
            #     "#workflow_name": "Name",
            #     "#version": "Version"
            # },
            # ExpressionAttributeValues={
            #     ":old_version": old_version
            # }
            )

    except ClientError as e:
        # Ignore the ConditionalCheckFailedException, bubble up
        # other exceptions.
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            raise ConflictError("Workflow with Name {} already exists".format(workflow["Name"]))
        else:
            raise

    except Exception as e:

        logger.info("Exception {}".format(e))
        workflow = None
        raise ChaliceViewError("Exception '%s'" % e)

    return workflow


@app.route('/workflow', cors=True, methods=['GET'], authorizer=authorizer)
def list_workflows():
    """ List all workflow defintions

    Returns:
        A list of workflow definitions.

    Raises:
        200: All workflows returned sucessfully.
        500: Internal server error 
    """

    table = DYNAMO_RESOURCE.Table(WORKFLOW_TABLE_NAME)

    response = table.scan()
    workflows = response['Items']
    while 'LastEvaluatedKey' in response:
        response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        workflows.extend(response['Items'])

    return workflows

@app.route('/workflow/list/operation/{OperatorName}', cors=True, methods=['GET'], authorizer=authorizer)
def list_workflows_by_operator(OperatorName):
    """ List all workflow defintions that contain an operator

    Returns:
        A list of workflow definitions.

    Raises:
        200: All workflows returned sucessfully.
        500: Internal server error 
    """

    table = DYNAMO_RESOURCE.Table(WORKFLOW_TABLE_NAME)

    response = table.scan(
        FilterExpression=Attr("Operations").contains(OperatorName),
        ConsistentRead=True
    )
    workflows = response['Items']
    while 'LastEvaluatedKey' in response:
        response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        workflows.extend(response['Items'])

    return workflows

@app.route('/workflow/list/stage/{StageName}', cors=True, methods=['GET'], authorizer=authorizer)
def list_workflows_by_stage(StageName):
    """ List all workflow defintions that contain a stage

    Returns:
        A list of workflow definitions.

    Raises:
        200: All workflows returned sucessfully.
        500: Internal server error 
    """

    table = DYNAMO_RESOURCE.Table(WORKFLOW_TABLE_NAME)

    response = table.scan(
        FilterExpression=Attr("Stages."+StageName).exists(),
        ConsistentRead=True
    )
    workflows = response['Items']
    while 'LastEvaluatedKey' in response:
        response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        workflows.extend(response['Items'])

    return workflows



@app.route('/workflow/{Name}', cors=True, methods=['GET'], authorizer=authorizer)
def get_workflow_by_name(Name):
    """ Get a workflow definition by name

    Returns:
        A dictionary contianing the workflow definition.

    Raises:
        200: All workflows returned sucessfully.
        404: Not found
        500: Internal server error 
    """
    table = DYNAMO_RESOURCE.Table(WORKFLOW_TABLE_NAME)
    workflow = None
    response = table.get_item(
        Key={
            'Name': Name
        })

    if "Item" in response:
        workflow = response["Item"]
    else:
        raise NotFoundError(
            "Exception: workflow '%s' not found" % Name)

    return workflow


@app.route('/workflow/configuration/{Name}', cors=True, methods=['GET'], authorizer=authorizer)
def get_workflow_configuration_by_name(Name):
    """ Get a workflow configruation object by name

    Returns:
        A dictionary contianing the workflow configuration.

    Raises:
        200: All workflows returned sucessfully.
        404: Not found
        500: Internal server error 
    """
    table = DYNAMO_RESOURCE.Table(WORKFLOW_TABLE_NAME)
    workflow = None
    response = table.get_item(
        Key={
            'Name': Name
        })

    if "Item" in response:
        workflow = response["Item"]
        Configuration = {}
        for Name, stage in workflow["Stages"].items():
            Configuration[Name] = stage["Configuration"]

    else:
        raise NotFoundError(
            "Exception: workflow '%s' not found" % Name)

    return Configuration


@app.route('/workflow/{Name}', cors=True, methods=['DELETE'], authorizer=authorizer)
def delete_workflow_api(Name):
    """ Delete a workflow

    Returns:  

    Raises:
        200: Workflow deleted sucessfully.
        404: Not found
        500: Internal server error 
    """

    stage = delete_workflow(Name)

    return stage

def delete_workflow(Name):

    table = DYNAMO_RESOURCE.Table(WORKFLOW_TABLE_NAME)

    try:

        workflow = {}
        response = table.get_item(
            Key={
                'Name': Name
            },
            ConsistentRead=True)

        if "Item" in response:
            workflow = response["Item"]

            # Delete the stage state machine 
            response = SFN_CLIENT.delete_state_machine(
                stateMachineArn=workflow["StateMachineArn"]
            )

            response = table.delete_item(
                Key={
                    'Name': Name
                })
        else:
            workflow["Message"] = "Workflow '%s' not found" % Name

    except Exception as e:

        workflow = None
        logger.info("Exception {}".format(e))
        raise ChaliceViewError("Exception: '%s'" % e)

    return workflow


# ================================================================================================
#  __        __         _     __ _                 _____                     _   _
#  \ \      / /__  _ __| | __/ _| | _____      __ | ____|_  _____  ___ _   _| |_(_) ___  _ __  ___
#   \ \ /\ / / _ \| '__| |/ / |_| |/ _ \ \ /\ / / |  _| \ \/ / _ \/ __| | | | __| |/ _ \| '_ \/ __|
#    \ V  V / (_) | |  |   <|  _| | (_) \ V  V /  | |___ >  <  __/ (__| |_| | |_| | (_) | | | \__ \
#     \_/\_/ \___/|_|  |_|\_\_| |_|\___/ \_/\_/   |_____/_/\_\___|\___|\__,_|\__|_|\___/|_| |_|___/
#
# ================================================================================================
def find(key, dictionary):
    for k, v in dictionary.iteritems():
        if k == key:
            return v


@app.route('/workflow/execution', cors=True, methods=['POST'], authorizer=authorizer)
def create_workflow_execution_api():
    """ Execute a workflow.  
    
    The Body contains the name of the workflow to execute, at least one input 
    media type within the media object.  A dictionary of stage configuration 
    objects can be passed in to override the default configuration of the operations
    within the stages.

    Body:

    .. code-block:: python

        {
        "Name":"Default",
        "Input": media-object
        "Configuration": {
            {
            "stage-name": {
                "Operations": {
                    "SplitAudio": {
                       "Enabled": True,
                       "MediaTypes": {
                           "Video": True/False,
                           "Audio": True/False,
                           "Frame": True/False
                       }
                   },
               },
           }
           ...
           }
        }
    

    Returns:
        A dict mapping keys to the corresponding workflow execution created including 
        the WorkflowExecutionId, the AWS queue and state machine resources assiciated with
        the workflow execution and the current execution status of the workflow. 

        .. code-block:: python

            {
                "Name": string,
                "StartAt": "Preprocess",
                "Stages": {
                    "stage-name": {
                        "Type": "NestedQueue",
                        "Resource": queueARN,
                        "StateMachine": stateMachineARN,
                        "Next": "Analysis"
                    },
                    ...,
                    "stage-name: {
                        "Type": "NestedQueue",
                        "Resource": queueARN,
                        "StateMachine": stateMachineARN,
                        "End": true
                    }
                }
            }

    Raises:
        200: The workflow execution was created successfully.
        400: Bad Request - the input workflow was not found or was invalid
        500: Internal server error  
    """

    logger.info(app.current_request.json_body)
    workflow_execution = app.current_request.json_body

    return create_workflow_execution("api", workflow_execution)


def create_workflow_execution(trigger, workflow_execution):
    execution_table = DYNAMO_RESOURCE.Table(WORKFLOW_EXECUTION_TABLE_NAME)
    dynamo_status_queued = False

    create_asset = None


    if "Media" in workflow_execution["Input"]:
        create_asset = True
    else:
        create_asset = False

    try:
        Name = workflow_execution["Name"]

        Configuration = workflow_execution["Configuration"] if "Configuration" in workflow_execution  else {}
        
        # BRANDON - make an asset
        dataplane = DataPlane()
        if create_asset is True:
            try:
                input = workflow_execution["Input"]["Media"]
                media_type = list(input.keys())[0]
                s3bucket = input[media_type]["S3Bucket"]
                s3key = input[media_type]["S3Key"]
            except KeyError as e:
                logger.info("Exception {}".format(e))
                raise ChaliceViewError("Exception '%s'" % e)
            else:
                asset_creation = dataplane.create_asset(s3bucket, s3key)
                asset_input = {
                    "Media": {
                        media_type: {
                            "S3Bucket": asset_creation["S3Bucket"],
                            "S3Key": asset_creation["S3Key"]
                        }
                    }
                }
                asset_id = asset_creation["AssetId"]
        else:
            # TODO: Probably just accept the media type as input parameter
            data_type_mapping = {"mp4": "Video", "mp3": "Audio", "txt": "Text", "json": "Text", "ogg": "Video"}
            try:
                input = workflow_execution["Input"]["AssetId"]
            except KeyError as e:
                logger.info("Exception {}".format(e))
                raise ChaliceViewError("Exception '%s'" % e)
            else:
                asset_id = input
                retrieve_asset = dataplane.retrieve_asset_metadata(asset_id)
                if "results" in retrieve_asset:
                    s3key = retrieve_asset["results"]["S3Key"]
                    media_type = s3key.split('.')[-1]
                    s3bucket = retrieve_asset["results"]["S3Bucket"]

                    if media_type.lower() not in data_type_mapping:
                        raise ChaliceViewError("Unsupported media type for input asset: {e}".format(e=media_type))
                    else:
                        asset_input = {
                            "Media": {
                                data_type_mapping[media_type.lower()]: {
                                    "S3Bucket": s3bucket,
                                    "S3Key": s3key
                                }
                            }
                        }
                else:
                    raise ChaliceViewError("Unable to retrieve asset: {e}".format(e=asset_id))

        workflow_execution = initialize_workflow_execution(trigger, Name, asset_input, Configuration, asset_id)

        execution_table.put_item(Item=workflow_execution)
        dynamo_status_queued = True

        # FIXME - must set workflow status to error if this fails since we marked it as QUeued .  we had to do that to avoid
        # race condition on status with the execution itself.  Once we hand it off to the state machine, we can't touch the status again.
        response = SQS_CLIENT.send_message(QueueUrl=STAGE_EXECUTION_QUEUE_URL, MessageBody=json.dumps(workflow_execution))
        # the response contains MD5 of the body, a message Id, MD5 of message attributes, and a sequence number (for FIFO queues)
        logger.info('Message ID : {}'.format(response['MessageId']))

        # Trigger the workflow_scheduler
        response = LAMBDA_CLIENT.invoke(
            FunctionName=WORKFLOW_SCHEDULER_LAMBDA_ARN,
            InvocationType='Event'
        )

    except Exception as e:
        logger.info("Exception {}".format(e))

        if dynamo_status_queued:
            update_workflow_execution_status(workflow_execution["Id"], awsmie.WORKFLOW_STATUS_ERROR, "Exception {}".format(e))

        raise ChaliceViewError("Exception '%s'" % e)

    return workflow_execution


def initialize_workflow_execution(trigger, Name, input, Configuration, asset_id):
    
    workflow_table = DYNAMO_RESOURCE.Table(WORKFLOW_TABLE_NAME)

    workflow_execution = {}
    workflow_execution["Id"] = str(uuid.uuid4())
    workflow_execution["Trigger"] = trigger
    workflow_execution["CurrentStage"] = None
    workflow_execution["Globals"] = {"Media": {}, "MetaData": {}}
    workflow_execution["Globals"].update(input)
    workflow_execution["Configuration"] = Configuration
    workflow_execution["AssetId"] = asset_id
    workflow_execution["Version"] = "v0"
    workflow_execution["Created"] = str(datetime.now().timestamp())
    workflow_execution["ResourceType"] = "WORKFLOW_EXECUTION"
    workflow_execution["ApiVersion"] = API_VERSION

    # lookup base workflow
    response = workflow_table.get_item(
        Key={
            'Name': Name
        },
        ConsistentRead=True)

    if "Item" in response:
        workflow = response["Item"]
    else:
        raise ChaliceViewError(
            "Exception: workflow name '%s' not found" % Name)

    print(workflow)
    # Override the default configuration with Configuration key-value pairs that are input to the 
    # /workflow/execution API.  Update only keys that are passed in, leaving the 
    # defaults for any key that is not specified
    for stage, sconfig in Configuration.items():
        if stage in workflow["Stages"]:
            for operation, oconfig in sconfig.items():
                    if operation in workflow["Stages"][stage]["Configuration"]:
                        for key, value in oconfig.items():
                            workflow["Stages"][stage]["Configuration"][operation][key] = value
                    else:
                        workflow_execution["Workflow"] = None
                        raise ChaliceViewError("Exception: Invalid operation '%s'" % operation)     
        else:
            workflow_execution["Workflow"] = None
            raise ChaliceViewError("Exception: Invalid stage found in Configuration '%s'" % stage)

    for stage in workflow["Stages"]:
        workflow["Stages"][stage]["Status"] = awsmie.STAGE_STATUS_NOT_STARTED
        workflow["Stages"][stage]["Metrics"] = {}
        workflow["Stages"][stage]["Name"] = stage
        workflow["Stages"][stage]["AssetId"] = asset_id
        workflow["Stages"][stage]["WorkflowExecutionId"] = workflow_execution["Id"]
        if "MetaData" not in workflow["Stages"][stage]:
            workflow["Stages"][stage]["MetaData"] = {}

    workflow_execution["Workflow"] = workflow

    # initialize top level workflow_execution state from the workflow
    workflow_execution["Status"] = awsmie.WORKFLOW_STATUS_QUEUED
    workflow_execution["CurrentStage"] = current_stage = workflow["StartAt"]

    # setup the current stage for execution
    workflow_execution["Workflow"]["Stages"][current_stage]["Input"] = workflow_execution["Globals"]
    
    workflow_execution["Workflow"]["Stages"][current_stage]["Status"] = awsmie.STAGE_STATUS_STARTED

    return workflow_execution


@app.route('/workflow/execution', cors=True, methods=['PUT'], authorizer=authorizer)
def update_workflow_execution():
    """ Update a workflow execution NOT IMPLEMENTED 

    XXX

    """
    stage = {"Message": "UPDATE WORKFLOW EXECUTION NOT IMPLEMENTED"}
    return stage


@app.route('/workflow/execution', cors=True, methods=['GET'], authorizer=authorizer)
def list_workflow_executions():
    """ List all workflow executions

    Returns:
        A list of workflow executions.

    Raises:
        200: All workflow executions returned sucessfully.
        500: Internal server error 
    """

    table = DYNAMO_RESOURCE.Table(WORKFLOW_EXECUTION_TABLE_NAME)

    response = table.scan()
    workflow_executions = response['Items']
    while 'LastEvaluatedKey' in response:
        response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        workflow_executions.extend(response['Items'])

    return workflow_executions

@app.route('/workflow/execution/status/{Status}', cors=True, methods=['GET'], authorizer=authorizer)
def list_workflow_executions_by_status(Status):
    """ Get all workflow executions with the specified status

    Returns:
        A list of dictionaries containing the workflow executions with the requested status

    Raises:
        200: All workflows returned sucessfully.
        404: Not found
        500: Internal server error 
    """
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

@app.route('/workflow/execution/asset/{AssetId}', cors=True, methods=['GET'], authorizer=authorizer)
def list_workflow_executions_by_assetid(AssetId):
    """ Get workflow executions by AssetId

    Returns:
        A list of dictionaries containing the workflow executions matching the AssetId.

    Raises:
        200: Workflow executions returned sucessfully.
        404: Not found
        500: Internal server error 
    """
    table = DYNAMO_RESOURCE.Table(WORKFLOW_EXECUTION_TABLE_NAME)

    projection_expression = "Id, AssetId, CurrentStage, StateMachineExecutionArn, #workflow_status, Workflow.#workflow_name"

    response = table.query(
        IndexName='WorkflowExecutionAssetId', 
        ExpressionAttributeNames={
            '#workflow_status': "Status",
            '#workflow_name': "Name"
        },
        ExpressionAttributeValues={
            ':assetid': AssetId
        },
        KeyConditionExpression='AssetId = :assetid',
        ProjectionExpression = projection_expression
        )
    
    workflow_executions = response['Items']
    while 'LastEvaluatedKey' in response:
        response = table.query(ExclusiveStartKey=response['LastEvaluatedKey'])
        workflow_executions.extend(response['Items'])

    return workflow_executions

@app.route('/workflow/execution/{Id}', cors=True, methods=['GET'], authorizer=authorizer)
def get_workflow_execution_by_id(Id):
    """ Get a workflow execution by id

    Returns:
        A dictionary containing the workflow execution.

    Raises:
        200: Workflow executions returned sucessfully.
        404: Not found
        500: Internal server error 
    """
    table = DYNAMO_RESOURCE.Table(WORKFLOW_EXECUTION_TABLE_NAME)
    workflow_execution = None
    response = table.get_item(
        Key={
            'Id': Id
        },
        ConsistentRead=True)

    if "Item" in response:
        workflow_execution = response["Item"]
    else:
        raise NotFoundError(
            "Exception: workflow execution '%s' not found" % Id)

    return workflow_execution


@app.route('/workflow/execution/{Id}', cors=True, methods=['DELETE'], authorizer=authorizer)
def delete_workflow_execution(Id):
    """ Delete a workflow executions

    Returns:  

    Raises:
        200: Workflow execution deleted sucessfully.
        404: Not found
        500: Internal server error 
    """
    table = DYNAMO_RESOURCE.Table(WORKFLOW_EXECUTION_TABLE_NAME)

    try:
        workflow_execution = None
        response = table.get_item(
            Key={
                'Id': Id
            },
            ConsistentRead=True)

        if "Item" in response:
            workflow_execution = response["Item"]
        else:
            raise NotFoundError(
                "Exception: workflow execution '%s' not found" % Id)

        response = table.delete_item(
            Key={
                'Id': Id
            })

    except Exception as e:

        workflow_execution = None
        logger.info("Exception {}".format(e))
        raise ChaliceViewError("Exception: '%s'" % e)

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


# ================================================================================================
#   ____          _                    ____                                    
#   / ___|   _ ___| |_ ___  _ __ ___   |  _ \ ___  ___  ___  _   _ _ __ ___ ___ 
#  | |  | | | / __| __/ _ \| '_ ` _ \  | |_) / _ \/ __|/ _ \| | | | '__/ __/ _ \
#  | |__| |_| \__ \ || (_) | | | | | | |  _ <  __/\__ \ (_) | |_| | | | (_|  __/
#   \____\__,_|___/\__\___/|_| |_| |_| |_| \_\___||___/\___/ \__,_|_|  \___\___|
#
# ================================================================================================


@app.lambda_function()
def workflow_custom_resource(event, context):
    '''Handle Lambda event from AWS CloudFormation'''
    # Setup alarm for remaining runtime minus a second
    signal.alarm(int(context.get_remaining_time_in_millis() / 1000) - 1)

    # send_response(event, context, "SUCCESS",
    #                     {"Message": "Resource deletion successful!"})
    try:
        logger.info('REQUEST RECEIVED:\n %s', event)
        logger.info('REQUEST RECEIVED:\n %s', context)

        if event["ResourceProperties"]["ResourceType"] == "Operation":
            logger.info("Operation!!")
            operation_resource(event, context)

        elif event["ResourceProperties"]["ResourceType"] == "Stage":
            stage_resource(event, context)

        elif event["ResourceProperties"]["ResourceType"] == "Workflow":
            workflow_resource(event, context)
        else:
            logger.info('FAILED!')
            send_response(event, context, "FAILED",
                          {"Message": "Unexpected resource type received from CloudFormation"})


    except Exception as e:

        logger.info('FAILED!')
        send_response(event, context, "FAILED", {
            "Message": "Exception during processing: '%s'" % e})


def operation_resource(event, context):
    operation = {}

    if event['RequestType'] == 'Create':
        logger.info('CREATE!')

        operation = event["ResourceProperties"]

        # boolean type comes in as text from cloudformation - must decode string or take string for anabled parameter
        operation["Configuration"]["Enabled"] = bool(operation["Configuration"]["Enabled"])
        operation = create_operation(operation)
        send_response(event, context, "SUCCESS",
                      {"Message": "Resource creation successful!", "Name": event["ResourceProperties"]["Name"],
                       "StageName": operation["StageName"]})
    elif event['RequestType'] == 'Update':
        logger.info('UPDATE!')
        send_response(event, context, "SUCCESS",
                      {"Message": "Resource update successful!", "Name": event["ResourceProperties"]["Name"],
                       "StageName": operation["StageName"]})
    elif event['RequestType'] == 'Delete':
        logger.info('DELETE!')

        Name = event["ResourceProperties"]["Name"]

        operation = delete_operation(Name, True)

        send_response(event, context, "SUCCESS",
                      {"Message": "Resource deletion successful!", "Name": event["ResourceProperties"]["Name"]})
    else:
        logger.info('FAILED!')
        send_response(event, context, "FAILED",
                      {"Message": "Unexpected event received from CloudFormation"})

    return operation


def stage_resource(event, context):
    stage = event["ResourceProperties"]

    if event['RequestType'] == 'Create':
        logger.info('CREATE!')

        create_stage(stage)

        send_response(event, context, "SUCCESS",
                      {"Message": "Resource creation successful!", "Name": event["ResourceProperties"]["Name"],
                       "StateMachineArn": event["ResourceProperties"]["StateMachineArn"]})

    elif event['RequestType'] == 'Update':
        logger.info('UPDATE!')
        send_response(event, context, "SUCCESS",
                      {"Message": "Resource update successful!"})
    elif event['RequestType'] == 'Delete':
        logger.info('DELETE!')

        Name = event["ResourceProperties"]["Name"]

        stage = delete_stage(Name, True)

        send_response(event, context, "SUCCESS",
                      {"Message": "Resource deletion successful!"})
    else:
        logger.info('FAILED!')
        send_response(event, context, "FAILED",
                      {"Message": "Unexpected event received from CloudFormation"})

    return stage


def workflow_resource(event, context):
    workflow = event["ResourceProperties"]

    logger.info(json.dumps(workflow))

    if event['RequestType'] == 'Create':
        logger.info('CREATE!')

        workflow["Stages"] = json.loads(event["ResourceProperties"]["Stages"])

        create_workflow("custom-resource", workflow)

        send_response(event, context, "SUCCESS",
                      {"Message": "Resource creation successful!", "Name": event["ResourceProperties"]["Name"]})
    elif event['RequestType'] == 'Update':
        logger.info('UPDATE!')
        send_response(event, context, "SUCCESS",
                      {"Message": "Resource update successful!"})
    elif event['RequestType'] == 'Delete':
        logger.info('DELETE!')

        Name = event["ResourceProperties"]["Name"]

        delete_workflow(Name)

        send_response(event, context, "SUCCESS",
                      {"Message": "Resource deletion successful!"})
    else:
        logger.info('FAILED!')
        send_response(event, context, "FAILED",
                      {"Message": "Unexpected event received from CloudFormation"})

    return workflow


def send_response(event, context, response_status, response_data):
    '''Send a resource manipulation status response to CloudFormation'''
    response_body = json.dumps({
        "Status": response_status,
        "Reason": "See the details in CloudWatch Log Stream: " + context.log_stream_name,
        "PhysicalResourceId": context.log_stream_name,
        "StackId": event['StackId'],
        "RequestId": event['RequestId'],
        "LogicalResourceId": event['LogicalResourceId'],
        "Data": response_data
    })

    logger.info('ResponseURL: %s', event['ResponseURL'])
    logger.info('ResponseBody: %s', response_body)

    opener = build_opener(HTTPHandler)
    request = Request(event['ResponseURL'], data=response_body.encode('utf-8'))
    request.add_header('Content-Type', '')
    request.add_header('Content-Length', len(response_body))
    request.get_method = lambda: 'PUT'
    response = opener.open(request)
    logger.info("Status code: %s", response.getcode())
    logger.info("Status message: %s", response.msg)


def timeout_handler(_signal, _frame):
    '''Handle SIGALRM'''
    raise Exception('Time exceeded')



        

        
            



