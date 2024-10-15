# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from chalice import Chalice
from chalice import IAMAuthorizer
from chalice import NotFoundError, BadRequestError, ChaliceViewError, ConflictError
import boto3
from boto3 import resource
from botocore.client import ClientError
from boto3.dynamodb.conditions import Attr
from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.core import patch_all

import uuid
import logging
import os
from datetime import datetime
from operator import itemgetter
from botocore import config
import json
import decimal
from jsonschema import validate, ValidationError
from urllib.request import build_opener, HTTPHandler, Request
from MediaInsightsEngineLambdaHelper import DataPlane
from MediaInsightsEngineLambdaHelper import Status as awsmie

APP_NAME = "workflowapi"
API_STAGE = "dev"
app = Chalice(app_name=APP_NAME)
app.debug = True
API_VERSION = "3.0.0"
FRAMEWORK_VERSION = os.environ['FRAMEWORK_VERSION']

S_OUTPUTS = "$.Outputs"
S_STATUS = "$.Status"
ATT_NAME_WORKFLOW_NAME = '#workflow_name'
ATT_NAME_WORKFLOW_STATUS = '#workflow_status'
ATT_VALUE_WORKFLOW_STATUS = ':workflow_status'
CREATE = 'CREATE!'
UPDATE = 'UPDATE!'
DELETE = 'DELETE!'
FAILED = 'FAILED!'
RESOURCE_CREATE_SUCCESS = "Resource creation successful!"
RESOURCE_UPDATE_SUCCESS = "Resource update successful!"
RESOURCE_DELETE_SUCCESS = "Resource deletion successful!"
UNEXPECTED_CLOUD_FORMATION_EVENT = "Unexpected event received from CloudFormation"


def is_aws():
    return os.getenv('AWS_LAMBDA_FUNCTION_NAME') is not None


if is_aws():
    patch_all()

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

STACK_SHORT_UUID = os.environ["STACK_SHORT_UUID"]
SYSTEM_TABLE_NAME = os.environ["SYSTEM_TABLE_NAME"]
WORKFLOW_TABLE_NAME = os.environ["WORKFLOW_TABLE_NAME"]
STAGE_TABLE_NAME = os.environ["STAGE_TABLE_NAME"]
OPERATION_TABLE_NAME = os.environ["OPERATION_TABLE_NAME"]
WORKFLOW_EXECUTION_TABLE_NAME = os.environ["WORKFLOW_EXECUTION_TABLE_NAME"]
HISTORY_TABLE_NAME = os.environ["HISTORY_TABLE_NAME"]
STAGE_EXECUTION_QUEUE_URL = os.environ["STAGE_EXECUTION_QUEUE_URL"]
STAGE_EXECUTION_ROLE = os.environ["STAGE_EXECUTION_ROLE"]
STEP_FUNCTION_LOG_GROUP_ARN = os.environ["STEP_FUNCTION_LOG_GROUP_ARN"]
# TODO testing NoQ execution
COMPLETE_STAGE_LAMBDA_ARN = os.environ["COMPLETE_STAGE_LAMBDA_ARN"]
FILTER_OPERATION_LAMBDA_ARN = os.environ["FILTER_OPERATION_LAMBDA_ARN"]
OPERATOR_FAILED_LAMBDA_ARN = os.environ["OPERATOR_FAILED_LAMBDA_ARN"]
WORKFLOW_SCHEDULER_LAMBDA_ARN = os.environ["WORKFLOW_SCHEDULER_LAMBDA_ARN"]

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

# IAM resource
IAM_CLIENT = boto3.client('iam', config=config)
IAM_RESOURCE = boto3.resource('iam', config=config)

# Lambda
LAMBDA_CLIENT = boto3.client("lambda", config=config)

# Transcribe
TRANSCRIBE_CLIENT = None

# Translate
TRANSLATE_CLIENT = None

# Helper class to convert a DynamoDB item to JSON.

authorizer = IAMAuthorizer()


class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return str(o)
        return super(DecimalEncoder, self).default(o)


def check_required_input(key, dict, objectname):
    if key not in dict:
        raise BadRequestError("Key '%s' is required in '%s' input" % (
            key, objectname))


def load_apischema():
    schemata = {}
    schema_directory = os.path.dirname(__file__) + "/chalicelib/apischema/"
    for f in os.listdir(schema_directory):
        with open(schema_directory + f) as schema_file:
            schema = json.load(schema_file)
            schemata[schema['title']] = schema
            logger.info("Loaded schema: {}".format(json.dumps(schema)))
    return schemata


def log_exception(error):
    logger.error("Exception {}".format(error))


def log_bad_request_error(error):
    logger.error("got bad request error: {}".format(error))


def format_exception(error):
    return "Exception '%s'" % error


SCHEMA = load_apischema()


@app.route('/')
def index():
    """ Test the API endpoint

    Returns:

    .. code-block:: python

        {"hello":"world"}

    Raises:

        500: ChaliceViewError - internal server error
    """
    return {'hello': 'world'}


@app.route('/version', cors=True, methods=['GET'], authorizer=authorizer)
def version():
    """
    Get the workflow api and framework version numbers

    Returns:

    .. code-block:: python

        {"ApiVersion": "x.x.x", "FrameworkVersion": "vx.x.x"}
    """
    versions = {"ApiVersion": API_VERSION, "FrameworkVersion": FRAMEWORK_VERSION}
    return versions


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

    - Updates the system configuration with a new parameter or changes the value of
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
        500: ChaliceViewError - internal server error
    """

    try:
        config = json.loads(app.current_request.raw_body.decode())

        logger.info(json.loads(app.current_request.raw_body.decode()))
        system_table = DYNAMO_RESOURCE.Table(SYSTEM_TABLE_NAME)

        # Check allowed values for known configuration parameters
        if config["Name"] == "MaxConcurrentWorkflows":
            if config["Value"] < 1:
                raise BadRequestError("MaxConcurrentWorkflows must be a value > 1")

        system_table.put_item(Item=config)
    except Exception as e:
        log_exception(e)
        raise ChaliceViewError(format_exception(e))

    return {}

@app.route('/system/configuration', cors=True, methods=['GET'], authorizer=authorizer)
def get_system_configuration_api():
    """ Get the current system configuration

    - Gets the current system configuration parameter settings

    Returns:
        A list of dict containing the current MI system configuration key-value pairs.

        .. code-block:: python

            [
                {
                "Name": "Value"
                },
            ...]

    Raises:
        200: The system configuration was returned successfully.
        500: ChaliceViewError - internal server error
    """

    try:

        system_table = DYNAMO_RESOURCE.Table(SYSTEM_TABLE_NAME)

        # Check if any configuration has been added yet
        response = system_table.scan(
            ConsistentRead=True)

    except Exception as e:
        log_exception(e)
        raise ChaliceViewError(format_exception(e))
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

    For more information on how to implemenent lambdas to be used in MI operators, please
    refer to the MI Developer Quick Start.



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
            "MonitorLambdaArn":arn
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
        500: ChaliceViewError - internal server error
    """

    operation = None

    operation = json.loads(app.current_request.raw_body.decode())

    logger.info(json.loads(app.current_request.raw_body.decode()))

    operation = create_operation(operation)

    return operation


def create_operation(operation):

    try:
        operation_table = DYNAMO_RESOURCE.Table(OPERATION_TABLE_NAME)

        logger.info(operation)

        validate(instance=operation, schema=SCHEMA["create_operation_request"])
        logger.info("Operation schema is valid")

        name = operation["Name"]

        if operation["Type"] == "Async":
            check_required_input("MonitorLambdaArn", operation, "Operation monitoring lambda function ARN")

        # Check if this operation already exists
        response = operation_table.get_item(
            Key={
                'Name': name
            },
            ConsistentRead=True)

        if "Item" in response:
            raise ConflictError(
                "A operation with the name '%s' already exists" % name)

        # Build the operation state machine.

        operation_asl = ASYNC_OPERATION_ASL if operation["Type"] == "Async" else SYNC_OPERATION_ASL

        # Setup task parameters in step function.  This filters out the paramters from
        # the stage data structure that belong to this specific operation and passes the
        # result as input to the task lambda

        operation_asl_string = json.dumps(operation_asl)
        operation_asl_string = operation_asl_string.replace("%%OPERATION_NAME%%", operation["Name"])
        operation_asl_string = operation_asl_string.replace("%%OPERATION_MEDIA_TYPE%%",
                                                            operation["Configuration"]["MediaType"])

        if operation["Type"] == "Async":
            operation_asl_string = operation_asl_string.replace("%%OPERATION_MONITOR_LAMBDA%%",
                                                                operation["MonitorLambdaArn"])
        operation_asl_string = operation_asl_string.replace("%%OPERATION_START_LAMBDA%%", operation["StartLambdaArn"])
        operation_asl_string = operation_asl_string.replace("%%OPERATION_FAILED_LAMBDA%%", OPERATOR_FAILED_LAMBDA_ARN)
        operation["StateMachineAsl"] = operation_asl_string

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

        # TODO: Once IAM supports the ability to use tag-based policies for
        #  InvokeFunction, put that in the StepFunctionRole definition in
        #  media-insights-stack.yaml and remove the following code block. Inline
        #  policies have length limitations which will prevent users from adding
        #  more than about 35 new operators via the MI workflow api. Tag based
        #  policies will not have any such limitation.

        # Skip the inline policy creation for operators packaged with MI.
        # The inline policy is not needed for those operators because the
        # StepFunctionRole has already been defined with permission to invoke
        # those Lambdas (see media-insigts-stack.yaml).
        if not ("OperatorLibrary" in operation["StartLambdaArn"] or "start-wait-operation" in operation["StartLambdaArn"]):
            # If true then this is a new user-defined operator which needs to be added
            # to the StepFunctionRole.
            #
            # Create an IAM policy to allow InvokeFunction on the StartLambdaArn
            policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Action": "lambda:InvokeFunction",
                        "Resource": [
                            operation["StartLambdaArn"]
                        ]
                    }
                ]
            }
            # Add the MonitorLambdaArn to that policy for async operators
            if operation["Type"] == "Async":
                policy['Statement'][0]['Resource'].append(operation["MonitorLambdaArn"])
            # Attach that policy to the stage execution role as an inline policy
            IAM_CLIENT.put_role_policy(
                RoleName=STAGE_EXECUTION_ROLE.split('/')[1],
                PolicyName=operation["Name"],
                PolicyDocument=json.dumps(policy)
            )
    except ConflictError as e:
        logger.error("got ConflictError: {}".format(e))
        raise
    except ValidationError as e:
        log_bad_request_error(e)
        raise BadRequestError(e)
    except Exception as e:
        log_exception(e)
        operation = None
        raise ChaliceViewError(format_exception(e))

    logger.info("end create_operation: {}".format(json.dumps(operation, cls=DecimalEncoder)))
    return operation


def create_operation_asl(is_async):
    """ Creates a template structure defining a state machine for an operation.

    The template contains placeholders for %%OPERATION_NAME%% and %%STAGE_NAME%%.

    Returns:
        A dictionary defining an async state machine if is_async is True, otherwise
        a synchronous state machine.
    """

    # Name the states of the state machine
    state_filter = "Filter %%OPERATION_NAME%% Media Type? (%%STAGE_NAME%%)"
    state_skip = "Skip %%OPERATION_NAME%%? (%%STAGE_NAME%%)"
    state_no_start = "%%OPERATION_NAME%% Not Started (%%STAGE_NAME%%)"
    state_execute = "Execute %%OPERATION_NAME%% (%%STAGE_NAME%%)"
    state_async_wait = "%%OPERATION_NAME%% Wait (%%STAGE_NAME%%)"
    state_async_status = "Get %%OPERATION_NAME%% Status (%%STAGE_NAME%%)"
    state_check_complete = "Did %%OPERATION_NAME%% Complete (%%STAGE_NAME%%)"
    state_failed = "%%OPERATION_NAME%% Failed (%%STAGE_NAME%%)"
    state_succeeded = "%%OPERATION_NAME%% Succeeded (%%STAGE_NAME%%)"

    starting_state = state_filter

    # Avoid repeating a couple of structures we will use multiple times.
    retry = [{
        "ErrorEquals": [
            "Lambda.ServiceException",
            "Lambda.AWSLambdaException",
            "Lambda.SdkClientException",
            "Lambda.Unknown",
            "MasExecutionError"
        ],
        "IntervalSeconds": 2,
        "MaxAttempts": 2,
        "BackoffRate": 2
    }]

    catch = [{
        "ErrorEquals": ["States.ALL"],
        "Next": state_failed,
        "ResultPath": S_OUTPUTS
    }]

    # Build the states
    states = {
        state_filter: {
            "Type": "Task",
            "Parameters": {
                "StageName.$": "$.Name",
                "Name": "%%OPERATION_NAME%%",
                "Input.$": "$.Input",
                "Configuration.$": "$.Configuration.%%OPERATION_NAME%%",
                "AssetId.$": "$.AssetId",
                "WorkflowExecutionId.$": "$.WorkflowExecutionId",
                "Type": "%%OPERATION_MEDIA_TYPE%%",
                "Status": S_STATUS
            },
            "Resource": FILTER_OPERATION_LAMBDA_ARN,
            "ResultPath": S_OUTPUTS,
            "OutputPath": S_OUTPUTS,
            "Next": state_skip,
            "Retry": retry,
            "Catch": catch

        },
        state_skip: {
            "Type": "Choice",
            "Choices": [{
                "Variable": S_STATUS,
                "StringEquals": awsmie.OPERATION_STATUS_STARTED,
                "Next": state_execute
            }],
            "Default": state_no_start
        },
        state_no_start: {
            "Type": "Succeed"
        },
        state_execute: {
            "Type": "Task",
            "Resource": "%%OPERATION_START_LAMBDA%%",
            "ResultPath": S_OUTPUTS,
            "OutputPath": S_OUTPUTS,
            # Next state depends on whether this is async or not.
            "Next": state_async_wait if is_async else state_check_complete,
            "Retry": retry,
            "Catch": catch
        }
    }

    # There are two possible choices in completion check state but the first one
    # is only relevant if it is async. Default first choice is the second index.
    first_choice = 1
    choices = [
        {
            "Variable": S_STATUS,
            "StringEquals": "Executing",
            "Next": state_async_wait
        },
        {
            "Variable": S_STATUS,
            "StringEquals": "Complete",
            "Next": state_succeeded
        }
    ]

    # In async mode, we have to insert a wait state and a status check.
    if is_async:
        # Set the first choice index to 0, the first index in the array so we get
        # both choices in the completion check state.
        first_choice = 0

        states[state_async_wait] = {
            "Type": "Wait",
            "Seconds": 10,
            "Next": state_async_status
        }

        states[state_async_status] = {
            "Type": "Task",
            "Resource": "%%OPERATION_MONITOR_LAMBDA%%",
            "Next": state_check_complete,
            "Retry": retry,
            "Catch": catch
        }

    # Add the rest of the states needed by both sync and async mode.
    states[state_check_complete] = {
        "Type": "Choice",
        "Choices": choices[first_choice:2],
        "Default": state_failed
    }

    states[state_failed] = {
        "Type": "Task",
        "End": True,
        "Resource": "%%OPERATION_FAILED_LAMBDA%%",
        "ResultPath": "$",
        "Retry": retry
    }

    states[state_succeeded] = {
        "Type": "Succeed"
    }

    # Return the final result
    asl = {
        "StartAt": starting_state,
        "States": states
    }

    return asl


ASYNC_OPERATION_ASL = create_operation_asl(True)

SYNC_OPERATION_ASL = create_operation_asl(False)


@app.route('/workflow/operation', cors=True, methods=['PUT'], authorizer=authorizer)
def update_operation():
    """ Update operation NOT IMPLEMENTED

    """
    operation = {"Message": "Update on stages is not implemented"}
    return operation


@app.route('/workflow/operation', cors=True, methods=['GET'], authorizer=authorizer)
def list_operations():
    """ List all defined operators

    Returns:
        A list of operation definitions.

    Raises:
        200: All operations returned sucessfully.
        500: ChaliceViewError - internal server error
    """

    table = DYNAMO_RESOURCE.Table(OPERATION_TABLE_NAME)

    response = table.scan()
    operations = response['Items']
    while 'LastEvaluatedKey' in response:
        response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        operations.extend(response['Items'])

    return operations


@app.route('/workflow/operation/{name}', cors=True, methods=['GET'], authorizer=authorizer)
def get_operation_by_name(name):
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
            'Name': name
        })

    if "Item" in response:
        operation = response["Item"]
    else:
        raise NotFoundError(
            "Exception: operation '%s' not found" % name)

    return operation


@app.route('/workflow/operation/{name}', cors=True, methods=['DELETE'], authorizer=authorizer)
def delete_operation_api(name):
    """ Delete a an operation

    Returns:
        A dictionary contianing the operation definition.

    Raises:
        200: Operation deleted sucessfully.
        400: Bad Request - there are dependent workflows and query parameter force=false
        500: ChaliceViewError - internal server error
    """
    params = app.current_request.query_params

    force = params and params.get("force", "false") == "true"

    operation = delete_operation(name, force)

    return operation


def delete_operation(name, force):

    table = DYNAMO_RESOURCE.Table(OPERATION_TABLE_NAME)
    operation = {}

    logger.info("delete_stage({},{})".format(name, force))

    try:

        operation = {}
        response = table.get_item(
            Key={
                'Name': name
            },
            ConsistentRead=True)

        if "Item" not in response:
            operation["Message"] = "Warning: operation '{}' not found".format(name)
            return operation

        workflows = list_workflows_by_operator(name)

        if len(workflows) != 0 and not force:
            message = """Dependent workflows were found for operation {}.
                    Either delete the dependent workflows or set the query parameter
                    force=true to delete the stage anyhow.  Undeleted dependent workflows
                    will be kept but will contain the deleted definition of the stage.  To
                    find the workflow that depend on a stage use the following endpoint:
                    GET /workflow/list/operation/""".format(name)

            raise BadRequestError(message)

        operation = response["Item"]

        delete_stage(operation["StageName"], True)

        response = table.delete_item(
            Key={
                'Name': name
            })

        # TODO: Once IAM supports the ability to use tag-based policies for
        #  InvokeFunction, put that in the StepFunctionRole definition in
        #  media-insights-stack.yaml and remove the following code block. Inline
        #  policies have length limitations which will prevent users from adding
        #  more than about 35 new operators via the MI workflow api. Tag based
        #  policies will not have any such limitation.

        if len([k for k in ("OperatorLibrary", "start-wait-operation") if k in operation["StartLambdaArn"]]) == 0:
            # If true then this is a deleted operator has an inline policy which
            # need to be removed from the StepFunctionRole.

            # The policy name will be the same as the operator name.
            # Paginate thru list_role_policies() until we find
            # that policy, then delete it.
            role_name = STAGE_EXECUTION_ROLE.split('/')[1]
            response = IAM_CLIENT.list_role_policies(RoleName=role_name)
            policy_found = name in response['PolicyNames']
            while policy_found is False and response['IsTruncated'] is True:
                response = IAM_CLIENT.list_role_policies(RoleName=role_name, Marker=response['Marker'])
                policy_found = name in response['PolicyNames']
            # If the policy was found, then delete it.
            if policy_found:
                logger.info("Deleting policy " + name + " from role " + role_name)
                IAM_CLIENT.delete_role_policy(
                    RoleName=role_name,
                    PolicyName=name
                )

        # Flag dependent workflows
        flag_operation_dependent_workflows(name)

    except BadRequestError as e:
        log_bad_request_error(e)
        raise
    except Exception as e:

        operation = None
        log_exception(e)
        raise ChaliceViewError(format_exception(e))

    return operation


def flag_operation_dependent_workflows(operation_name):

    try:
        table = DYNAMO_RESOURCE.Table(WORKFLOW_TABLE_NAME)

        workflows = list_workflows_by_operator(operation_name)
        for workflow in workflows:
            table.update_item(
                Key={
                    'Name': workflow["Name"]
                },
                UpdateExpression="SET StaleOperations = list_append(StaleOperations, :i)",
                ExpressionAttributeValues={
                    ':i': [operation_name],
                },
                ReturnValues="UPDATED_NEW"
            )

    except Exception as e:
        logger.error("Exception flagging workflows dependent on dropped operations {}".format(e))
        raise ChaliceViewError(format_exception(e))

    return operation_name


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
        },
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
            }
        }

    Raises:
        200: The stage was created successfully.
        400: Bad Request - one of the input state machines was not found or was invalid
        409: Conflict
        500: ChaliceViewError - internal server error
    """

    stage = None

    stage = json.loads(app.current_request.raw_body.decode())

    logger.info(json.loads(app.current_request.raw_body.decode()))

    stage = create_stage(stage)

    return stage


def create_stage(stage):
    try:
        stage_table = DYNAMO_RESOURCE.Table(STAGE_TABLE_NAME)
        configuration = {}

        logger.info(stage)

        validate(instance=stage, schema=SCHEMA["create_stage_request"])
        logger.info("Stage schema is valid")

        name = stage["Name"]

        # Check if this stage already exists
        response = stage_table.get_item(
            Key={
                'Name': name
            },
            ConsistentRead=True)

        if "Item" in response:
            raise ConflictError(
                "A stage with the name '%s' already exists" % name)

        # Build the stage state machine.  The stage machine consists of a parallel state with
        # branches for each operator and a call to the stage completion lambda at the end.
        # The parallel state takes a stage object as input.  Each
        # operator returns and operatorOutput object. The outputs for each operator are
        # returned from the parallel state as elements of the "outputs" array.
        stage_asl = {
            "StartAt": "Preprocess Media",
            "States": {
                "Complete Stage {}".format(name): {
                    "Type": "Task",
                    # TODO - testing NoQ workflows
                    "Resource": COMPLETE_STAGE_LAMBDA_ARN,
                    "End": True
                }

            }
        }
        complete_stage = "Complete Stage {}".format(name)
        stage_asl["StartAt"] = name
        stage_asl["States"][name] = {
            "Type": "Parallel",
            "Next": complete_stage,
            "ResultPath": S_OUTPUTS,
            "Branches": [
            ],
            "Catch": [
                {
                    "ErrorEquals": ["States.ALL"],
                    "Next": complete_stage,
                    "ResultPath": S_OUTPUTS
                }
            ]
        }

        # Add a branch to the stage state machine for each operation, build up default
        # Configuration for the stage based on the operator Configuration

        for op in stage["Operations"]:
            # lookup base workflow
            operation = get_operation_by_name(op)
            logger.info(json.dumps(operation, cls=DecimalEncoder))

            stage_asl["States"][name]["Branches"].append(
                json.loads(operation["StateMachineAsl"]))
            configuration[op] = operation["Configuration"]

        stage_asl_string = json.dumps(stage_asl)
        stage_asl_string = stage_asl_string.replace("%%STAGE_NAME%%", stage["Name"])
        stage_asl = json.loads(stage_asl_string)
        logger.info(json.dumps(stage_asl))

        stage["Configuration"] = configuration

        # Build stage

        stage["Definition"] = json.dumps(stage_asl)
        stage["Version"] = "v0"
        stage["Id"] = str(uuid.uuid4())
        stage["Created"] = str(datetime.now().timestamp())
        stage["ResourceType"] = "STAGE"
        stage["ApiVersion"] = API_VERSION

        stage_table.put_item(Item=stage)

    except ValidationError as e:
        log_bad_request_error(e)
        raise BadRequestError(e)
    except Exception as e:
        log_exception(e)
        stage = None
        raise ChaliceViewError(format_exception(e))

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
        500: ChaliceViewError - internal server error
    """

    table = DYNAMO_RESOURCE.Table(STAGE_TABLE_NAME)

    response = table.scan()
    stages = response['Items']
    while 'LastEvaluatedKey' in response:
        response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        stages.extend(response['Items'])

    return stages


@app.route('/workflow/stage/{name}', cors=True, methods=['GET'], authorizer=authorizer)
def get_stage_by_name(name):
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
            'Name': name
        })

    if "Item" in response:
        stage = response["Item"]
    else:
        raise NotFoundError(
            "Exception: stage '%s' not found" % name)

    return stage


@app.route('/workflow/stage/{name}', cors=True, methods=['DELETE'], authorizer=authorizer)
def delete_stage_api(name):
    """ Delete a stage

    Returns:
        A dictionary contianing the stage definition.

    Raises:
        200: Stage deleted sucessfully.
        400: Bad Request - there are dependent workflows and query parameter force=False
        404: Not found
        500: ChaliceViewError - internal server error
    """
    params = app.current_request.query_params

    force = params and params.get("force", "false") == "true"

    stage = delete_stage(name, force)

    return stage


def delete_stage(name, force):

    table = DYNAMO_RESOURCE.Table(STAGE_TABLE_NAME)

    logger.info("delete_stage({},{})".format(name, force))

    try:

        stage = {}
        response = table.get_item(
            Key={
                'Name': name
            },
            ConsistentRead=True)

        if "Item" in response:

            workflows = list_workflows_by_stage(name)
            stage = response["Item"]

            if len(workflows) != 0 and not force:
                message = """Dependent workflows were found for stage {}.
                    Either delete the dependent workflows or set the query parameter
                    force=true to delete the stage anyhow.  Undeleted dependent workflows
                    will be kept but will contain the deleted definition of the stage.  To
                    find the workflow that depend on a stage use the following endpoint:
                    GET /workflow/list/stage/""".format(name)

                raise BadRequestError(message)

            response = table.delete_item(
                Key={
                    'Name': name
                })

            flag_stage_dependent_workflows(name)

        else:
            stage["Message"] = "Warning: stage '{}' not found".format(name)

    except BadRequestError as e:
        log_bad_request_error(e)
        raise
    except Exception as e:

        stage = None
        log_exception(e)
        raise ChaliceViewError(format_exception(e))

    return stage


def flag_stage_dependent_workflows(stage_name):

    try:
        table = DYNAMO_RESOURCE.Table(WORKFLOW_TABLE_NAME)

        workflows = list_workflows_by_stage(stage_name)
        for workflow in workflows:
            table.update_item(
                Key={
                    'Name': workflow["Name"]
                },
                UpdateExpression="SET StaleStages = list_append(StaleStages, :i)",
                ExpressionAttributeValues={
                    ':i': [stage_name],
                },
                ReturnValues="UPDATED_NEW"
            )

    except Exception as e:

        logger.error("Exception flagging workflows dependent on dropped stage {}".format(e))
        raise ChaliceViewError(format_exception(e))

    return stage_name

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
        500: ChaliceViewError - internal server error
    """

    workflow = json.loads(app.current_request.raw_body.decode())
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

        workflow_definition = "Workflow Definition"
        check_required_input("Name", workflow, workflow_definition)
        check_required_input("StartAt", workflow, workflow_definition)
        check_required_input("Stages", workflow, workflow_definition)

        workflow = build_workflow(workflow)

        # Build state machine
        response = SFN_CLIENT.create_state_machine(
            name=workflow["Name"] + "-" + STACK_SHORT_UUID,
            definition=json.dumps(workflow["WorkflowAsl"]),
            roleArn=STAGE_EXECUTION_ROLE,
            loggingConfiguration={
                'level': 'ALL',
                'includeExecutionData': False,
                'destinations': [
                    {
                        'cloudWatchLogsLogGroup': {
                            'logGroupArn': STEP_FUNCTION_LOG_GROUP_ARN
                        }
                    },
                ]
            },
            tags=[
                {
                    'key': 'environment',
                    'value': 'mie'
                },
            ]
        )

        workflow.pop("WorkflowAsl")
        workflow["StateMachineArn"] = response["stateMachineArn"]

        workflow_table.put_item(
            Item=workflow,
            ConditionExpression="attribute_not_exists({})".format(ATT_NAME_WORKFLOW_NAME),
            ExpressionAttributeNames={
                ATT_NAME_WORKFLOW_NAME: "Name"
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
        log_exception(e)
        workflow = None
        raise ChaliceViewError(format_exception(e))

    return workflow


def build_workflow(workflow):

    logger.info("Sanity Check for End of workflow")
    endcount = 0
    for name, stage in workflow["Stages"].items():

        # Stage must have an End or a Next key
        if stage.get("End", False):
            endcount += 1
        elif "Next" not in stage:
            raise BadRequestError("Stage %s must have either an 'End' or and 'Next' key" % (
                name))

    if endcount != 1:
        raise BadRequestError("Workflow %s must have exactly 1 'End' key within its stages" % (
            workflow["Name"]))

    logger.info("Get stage definitions")

    for name, stage in workflow["Stages"].items():
        s = get_stage_by_name(name)

        logger.info(json.dumps(s))

        s["stateMachineAsl"] = json.loads(s["Definition"])
        stage.update(s)

        # save the operators for this stage to the list of operators in the
        # workflow.  This list is maintained to make finding workflows that
        # use an operator easier later
        workflow["Operations"].extend(stage["Operations"])

        logger.info(json.dumps(s))

    # Build the workflow state machine.
    start_stage_asl = workflow["Stages"][workflow["StartAt"]]["stateMachineAsl"]
    start_at = start_stage_asl["StartAt"]
    logger.info(start_at)

    workflow_asl = {
        "StartAt": start_at,
        "States": {
        }
    }

    logger.info("Merge stages into workflow state machine")
    for workflow_stage in workflow["Stages"].values():
        logger.info("LOOP OVER WORKFLOW STAGES")
        logger.info(json.dumps(workflow_stage))

        # if this stage is not the end stage
        # - link the end of this stages ASL to the start of the next stages ASL
        if "Next" in workflow_stage:
            next_workflow_stage = workflow["Stages"][workflow_stage["Next"]]

            logger.info("NEXT STAGE")
            logger.info(json.dumps(next_workflow_stage))

            # Find the End state for this stages ASL and link it to the start of
            # the next stage ASL
            print(json.dumps(workflow_stage["stateMachineAsl"]["States"]))
            end_state = [k for k, v in workflow_stage["stateMachineAsl"]["States"].items() if "End" in v][0]

            logger.info("END STATE {}".format(end_state))

            workflow_stage["stateMachineAsl"]["States"][end_state]["Next"] = next_workflow_stage["stateMachineAsl"][
                "StartAt"]

            # Remove the end key from the end state
            workflow_stage["stateMachineAsl"]["States"][end_state].pop("End")

        workflow_asl["States"].update(workflow_stage["stateMachineAsl"]["States"])

        # Remove ASL from the stage since we rolled it into the workflow and ASL in saved in the stage defintition
        workflow_stage.pop("stateMachineAsl")

        logger.info("IN LOOP WORKFLOW")
        logger.info(json.dumps(workflow_asl))

    logger.info(json.dumps(workflow_asl))
    workflow["WorkflowAsl"] = workflow_asl

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
        500: ChaliceViewError - internal server error
    """
    workflow = json.loads(app.current_request.raw_body.decode())
    logger.info(json.dumps(workflow))

    return update_workflow(workflow)


def update_workflow(new_workflow):
    try:
        workflow_table = DYNAMO_RESOURCE.Table(WORKFLOW_TABLE_NAME)

        check_required_input("Name", new_workflow, "Workflow Definition")

        workflow = get_workflow_by_name(new_workflow["Name"])

        workflow["Operations"] = []
        workflow["StaleOperations"] = []
        workflow["StaleStages"] = []

        revisions = int(workflow["Revisions"])

        workflow["Version"] = "v" + str(revisions + 1)

        if "StartAt" in new_workflow:
            workflow["StartAt"] = new_workflow["StartAt"]

        if "Stages" in new_workflow:
            workflow["Stages"] = new_workflow["Stages"]

        logger.info(json.dumps(workflow))

        # We rebuild the workfow regardless of whether new stages were passed in.  This will update the workflow
        # with the most recent state machine definitions for operators and stages.
        workflow = build_workflow(workflow)

        # Update the workflow state machine
        SFN_CLIENT.update_state_machine(
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

        log_exception(e)
        workflow = None
        raise ChaliceViewError(format_exception(e))

    return workflow


@app.route('/workflow', cors=True, methods=['GET'], authorizer=authorizer)
def list_workflows():
    """ List all workflow defintions

    Returns:
        A list of workflow definitions.

    Raises:
        200: All workflows returned sucessfully.
        500: ChaliceViewError - internal server error
    """

    table = DYNAMO_RESOURCE.Table(WORKFLOW_TABLE_NAME)

    response = table.scan()
    workflows = response['Items']
    while 'LastEvaluatedKey' in response:
        response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        workflows.extend(response['Items'])

    return workflows

@app.route('/workflow/list/operation/{operator_name}', cors=True, methods=['GET'], authorizer=authorizer)
def list_workflows_by_operator(operator_name):
    """ List all workflow defintions that contain an operator

    Returns:
        A list of workflow definitions.

    Raises:
        200: All workflows returned sucessfully.
        500: Internal server error
    """

    table = DYNAMO_RESOURCE.Table(WORKFLOW_TABLE_NAME)

    response = table.scan(
        FilterExpression=Attr("Operations").contains(operator_name),
        ConsistentRead=True
    )
    workflows = response['Items']
    while 'LastEvaluatedKey' in response:
        response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        workflows.extend(response['Items'])

    return workflows


@app.route('/workflow/list/stage/{stage_name}', cors=True, methods=['GET'], authorizer=authorizer)
def list_workflows_by_stage(stage_name):
    """ List all workflow defintions that contain a stage

    Returns:
        A list of workflow definitions.

    Raises:
        200: All workflows returned sucessfully.
        500: ChaliceViewError - internal server error
    """

    table = DYNAMO_RESOURCE.Table(WORKFLOW_TABLE_NAME)

    response = table.scan(
        FilterExpression=Attr("Stages." + stage_name).exists(),
        ConsistentRead=True
    )
    workflows = response['Items']
    while 'LastEvaluatedKey' in response:
        response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        workflows.extend(response['Items'])

    return workflows


@app.route('/workflow/{name}', cors=True, methods=['GET'], authorizer=authorizer)
def get_workflow_by_name(name):
    """ Get a workflow definition by name

    Returns:
        A dictionary contianing the workflow definition.

    Raises:
        200: All workflows returned sucessfully.
        404: Not found
        500: ChaliceViewError - internal server error
    """
    table = DYNAMO_RESOURCE.Table(WORKFLOW_TABLE_NAME)
    workflow = None
    response = table.get_item(
        Key={
            'Name': name
        })

    if "Item" in response:
        workflow = response["Item"]
    else:
        raise NotFoundError(
            "Exception: workflow '%s' not found" % name)

    return workflow


@app.route('/workflow/configuration/{name}', cors=True, methods=['GET'], authorizer=authorizer)
def get_workflow_configuration_by_name(name):
    """ Get a workflow configruation object by name

    Returns:
        A dictionary contianing the workflow configuration.

    Raises:
        200: All workflows returned sucessfully.
        404: Not found
        500: ChaliceViewError - internal server error
    """
    table = DYNAMO_RESOURCE.Table(WORKFLOW_TABLE_NAME)
    workflow = None
    response = table.get_item(
        Key={
            'Name': name
        })

    if "Item" in response:
        workflow = response["Item"]
        configuration = {}
        for key, stage in workflow["Stages"].items():
            configuration[key] = stage["Configuration"]

    else:
        raise NotFoundError(
            "Exception: workflow '%s' not found" % name)

    return configuration


@app.route('/workflow/{name}', cors=True, methods=['DELETE'], authorizer=authorizer)
def delete_workflow_api(name):
    """ Delete a workflow

    Returns:

    Raises:
        200: Workflow deleted sucessfully.
        404: Not found
        500: ChaliceViewError - internal server error
    """

    stage = delete_workflow(name)

    return stage


def delete_workflow(name):

    table = DYNAMO_RESOURCE.Table(WORKFLOW_TABLE_NAME)

    try:

        workflow = {}
        response = table.get_item(
            Key={
                'Name': name
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
                    'Name': name
                })
        else:
            workflow["Message"] = "Workflow '%s' not found" % name

    except Exception as e:

        workflow = None
        log_exception(e)
        raise ChaliceViewError(format_exception(e))

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
        500: ChaliceViewError - internal server error
    """

    workflow_execution = json.loads(app.current_request.raw_body.decode())

    return create_workflow_execution("api", workflow_execution)


def create_workflow_execution(trigger, workflow_execution):
    execution_table = DYNAMO_RESOURCE.Table(WORKFLOW_EXECUTION_TABLE_NAME)
    dynamo_status_queued = False

    create_asset = None

    logger.info('create_workflow_execution workflow config: ' + str(workflow_execution))
    workflow_input = workflow_execution.get("Input", {})
    try:
        # Find AssetId then Media in Input (in that order). One or the other must exist.
        # If it is AssetId, we don't need to create an asset.
        # Otherwise, if it is only Media, we do need to reate an asset.
        # If neither exists, we'll get an IndexError when accessing the first item in the array.
        create_asset = [k for k in ("AssetId", "Media") if k in workflow_input][0] == "Media"
    except IndexError:
        raise BadRequestError('Input must contain either "AssetId" or "Media"')

    try:
        name = workflow_execution["Name"]

        configuration = workflow_execution.get("Configuration", {})

        # make an asset
        dataplane = DataPlane()
        if create_asset:
            try:
                media = workflow_input["Media"]
                media_type = list(media.keys())[0]
                s3bucket = media[media_type]["S3Bucket"]
                s3key = media[media_type]["S3Key"]
            except KeyError as e:
                log_exception(e)
                raise ChaliceViewError(format_exception(e))

            asset_creation = dataplane.create_asset(media_type, s3bucket, s3key)
            # If create_asset fails, then asset_creation will contain the error
            # string instead of the expected dict. So, we'll raise that error
            # if we get a KeyError in the following try block:
            try:
                asset_input = {
                    "Media": {
                        media_type: {
                            "S3Bucket": asset_creation["S3Bucket"],
                            "S3Key": asset_creation["S3Key"]
                        }
                    }
                }
                asset_id = asset_creation["AssetId"]
            except KeyError:
                logger.error("Error creating asset {}".format(asset_creation))
                raise ChaliceViewError("Error creating asset '%s'" % asset_creation)
        else:

            asset_id = workflow_input["AssetId"]

            workflow_execution_list = list_workflow_executions_by_assetid(asset_id)
            acceptable_status = [awsmie.WORKFLOW_STATUS_COMPLETE, awsmie.WORKFLOW_STATUS_ERROR]
            for workflow_execution in (workflow_execution
                                       for workflow_execution in workflow_execution_list
                                       if workflow_execution["Status"] not in acceptable_status):
                raise ConflictError("There is currently another workflow execution(Id = {}) active on AssetId {}.".format(
                    workflow_execution["Id"], asset_id))

            retrieve_asset = dataplane.retrieve_asset_metadata(asset_id)
            try:
                s3bucket = retrieve_asset["results"]["S3Bucket"]
                s3key = retrieve_asset["results"]["S3Key"]
                media_type = retrieve_asset["results"]["MediaType"]
                asset_input = {
                    "Media": {
                        media_type: {
                            "S3Bucket": s3bucket,
                            "S3Key": s3key
                        }
                    }
                }
            except KeyError:
                raise ChaliceViewError("Unable to retrieve asset: {e}".format(e=asset_id))

        workflow_execution = initialize_workflow_execution(trigger, name, asset_input, configuration, asset_id)

        execution_table.put_item(Item=workflow_execution)
        dynamo_status_queued = True

        # TODO - must set workflow status to error if this fails since we marked it as QUeued .  we had to do that to avoid
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
        log_exception(e)

        if dynamo_status_queued:
            update_workflow_execution_status(workflow_execution["Id"], awsmie.WORKFLOW_STATUS_ERROR, "Exception {}".format(e))

        raise ChaliceViewError(format_exception(e))

    return workflow_execution


def initialize_workflow_execution(trigger, name, input, configuration, asset_id):

    workflow_table = DYNAMO_RESOURCE.Table(WORKFLOW_TABLE_NAME)

    workflow_execution = {}
    workflow_execution["Id"] = str(uuid.uuid4())
    workflow_execution["Trigger"] = trigger
    workflow_execution["CurrentStage"] = None
    workflow_execution["Globals"] = {"Media": {}, "MetaData": {}}
    workflow_execution["Globals"].update(input)
    workflow_execution["Configuration"] = configuration
    workflow_execution["AssetId"] = asset_id
    workflow_execution["Version"] = "v0"
    workflow_execution["Created"] = str(datetime.now().timestamp())
    workflow_execution["ResourceType"] = "WORKFLOW_EXECUTION"
    workflow_execution["ApiVersion"] = API_VERSION

    # lookup base workflow
    response = workflow_table.get_item(
        Key={
            'Name': name
        },
        ConsistentRead=True)

    try:
        workflow = response["Item"]
    except KeyError:
        raise ChaliceViewError(
            "Exception: workflow name '%s' not found" % name)

    print(workflow)
    stages = workflow["Stages"]

    # Verify that all stages in the configuration are valid stages defined in the workflow
    for stage in (stage for stage in configuration.keys() if stage not in stages):
        # Report the first invalid stage we find.
        workflow_execution["Workflow"] = None
        raise ChaliceViewError("Exception: Invalid stage found in Configuration '%s'" % stage)

    # Override the default configuration with Configuration key-value pairs that are input to the
    # /workflow/execution API.  Update only keys that are passed in, leaving the
    # defaults for any key that is not specified
    for stage, operation, oconfig in ((stage, operation, oconfig)
                                      for stage, sconfig in configuration.items()
                                      for operation, oconfig in sconfig.items()):
        if operation not in stages[stage]["Configuration"]:
            workflow_execution["Workflow"] = None
            raise ChaliceViewError("Exception: Invalid operation '%s'" % operation)
        for key, value in oconfig.items():
            stages[stage]["Configuration"][operation][key] = value

    for stage, stage_definition in stages.items():
        stage_definition["Status"] = awsmie.STAGE_STATUS_NOT_STARTED
        stage_definition["Metrics"] = {}
        stage_definition["Name"] = stage
        stage_definition["AssetId"] = asset_id
        stage_definition["WorkflowExecutionId"] = workflow_execution["Id"]
        stage_definition.setdefault("MetaData", {})

    workflow_execution["Workflow"] = workflow

    # initialize top level workflow_execution state from the workflow
    workflow_execution["Status"] = awsmie.WORKFLOW_STATUS_QUEUED
    workflow_execution["CurrentStage"] = current_stage = workflow["StartAt"]

    # setup the current stage for execution
    workflow_execution["Workflow"]["Stages"][current_stage]["Input"] = workflow_execution["Globals"]

    workflow_execution["Workflow"]["Stages"][current_stage]["Status"] = awsmie.STAGE_STATUS_STARTED

    return workflow_execution


@app.route('/workflow/execution/{id}', cors=True, methods=['PUT'], authorizer=authorizer)
def update_workflow_execution(id):
    """ Update a workflow execution

       Options:

           Resume a workflow that is in a Waiting Status in a specific stage.

    Body:

    .. code-block:: python

        {
        "WaitingStageName":"<stage-name>"
        }


    Returns:
        A dict mapping keys to the corresponding workflow execution with its current status

        .. code-block:: python

            {
                "Id: string,
                "Status": "Resumed"
            }

    Raises:
        200: The workflow execution was updated successfully.
        400: Bad Request - the input stage was not found, the current stage did not match the WaitingStageName,
             or the Workflow Status was not "Waiting"
        500: ChaliceViewError - internal server error
    """
    response = {}
    params = json.loads(app.current_request.raw_body.decode())
    logger.info(json.dumps(params))

    if "WaitingStageName" in params:
        response = resume_workflow_execution(id, params["WaitingStageName"])

    return response


def resume_workflow_execution(id, waiting_stage_name):
    """
    Get the workflow execution by id from dyanamo and assign to this object
    :param id: The id of the workflow execution
    :param status: The new status of the workflow execution

    """
    print("Resume workflow execution {} waiting stage = {}".format(id, waiting_stage_name))
    execution_table = DYNAMO_RESOURCE.Table(WORKFLOW_EXECUTION_TABLE_NAME)

    workflow_execution = {}
    workflow_execution["Id"] = id
    workflow_execution["Status"] = awsmie.WORKFLOW_STATUS_RESUMED

    ATT_WORKFLOW_WAITING_STATUS = ':workflow_waiting_status'
    ATT_WAITING_STAGE_NAME = ':waiting_stage_name'

    try:
        response = execution_table.update_item(
            Key={
                'Id': id
            },
            UpdateExpression='SET {} = {}'.format(ATT_NAME_WORKFLOW_STATUS, ATT_VALUE_WORKFLOW_STATUS),
            ExpressionAttributeNames={
                ATT_NAME_WORKFLOW_STATUS: "Status"
            },
            ConditionExpression="{} = {} AND CurrentStage = {}".format(
                ATT_NAME_WORKFLOW_STATUS, ATT_WORKFLOW_WAITING_STATUS, ATT_WAITING_STAGE_NAME),
            ExpressionAttributeValues={
                ATT_WORKFLOW_WAITING_STATUS: awsmie.WORKFLOW_STATUS_WAITING,
                ATT_VALUE_WORKFLOW_STATUS: awsmie.WORKFLOW_STATUS_RESUMED,
                ATT_WAITING_STAGE_NAME: waiting_stage_name
            }
        )
    except ClientError as e:
        if e.response['Error']['Code'] == "ConditionalCheckFailedException":
            print(e.response['Error']['Message'])
            raise BadRequestError("Workflow status is not 'Waiting' or Current stage doesn't match the request")
        else:
            raise

    # Queue the resumed workflow so it can run when resources are available
    # TODO - must set workflow status to error if this fails since we marked it as QUeued .  we had to do that to avoid
    # race condition on status with the execution itself.  Once we hand it off to the state machine, we can't touch the status again.
    response = SQS_CLIENT.send_message(QueueUrl=STAGE_EXECUTION_QUEUE_URL, MessageBody=json.dumps(workflow_execution))
    # the response contains MD5 of the body, a message Id, MD5 of message attributes, and a sequence number (for FIFO queues)
    logger.info('Message ID : {}'.format(response['MessageId']))

    # We just queued a workflow so, Trigger the workflow_scheduler
    response = LAMBDA_CLIENT.invoke(
        FunctionName=WORKFLOW_SCHEDULER_LAMBDA_ARN,
        InvocationType='Event'
    )

    return workflow_execution


@app.route('/workflow/execution', cors=True, methods=['GET'], authorizer=authorizer)
def list_workflow_executions():
    """ List all workflow executions

    Returns:
        A list of workflow executions.

    Raises:
        200: All workflow executions returned sucessfully.
        500: ChaliceViewError - internal server error
    """

    table = DYNAMO_RESOURCE.Table(WORKFLOW_EXECUTION_TABLE_NAME)

    response = table.scan()
    workflow_executions = response['Items']
    while 'LastEvaluatedKey' in response:
        response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        workflow_executions.extend(response['Items'])

    return workflow_executions


@app.route('/workflow/execution/status/{status}', cors=True, methods=['GET'], authorizer=authorizer)
def list_workflow_executions_by_status(status):
    """ Get all workflow executions with the specified status

    Returns:
        A list of dictionaries containing the workflow executions with the requested status

    Raises:
        200: All workflows returned sucessfully.
        404: Not found
        500: Internal server error
    """
    table = DYNAMO_RESOURCE.Table(WORKFLOW_EXECUTION_TABLE_NAME)
    projection_expression = "Id, AssetId, CurrentStage, StateMachineExecutionArn, {}, Workflow.{}".format(
        ATT_NAME_WORKFLOW_STATUS, ATT_NAME_WORKFLOW_NAME)

    response = table.query(
        IndexName='WorkflowExecutionStatus',
        ExpressionAttributeNames={
            ATT_NAME_WORKFLOW_STATUS: "Status",
            ATT_NAME_WORKFLOW_NAME: "Name"
        },
        ExpressionAttributeValues={
            ATT_VALUE_WORKFLOW_STATUS: status
        },
        KeyConditionExpression='{} = {}'.format(ATT_NAME_WORKFLOW_STATUS, ATT_VALUE_WORKFLOW_STATUS),
        ProjectionExpression = projection_expression
        )

    workflow_executions = response['Items']
    while 'LastEvaluatedKey' in response:
        response = table.query(
            ExclusiveStartKey=response['LastEvaluatedKey'],
            IndexName='WorkflowExecutionStatus',
            ExpressionAttributeNames={
                ATT_NAME_WORKFLOW_STATUS: "Status",
                ATT_NAME_WORKFLOW_NAME: "Name"
            },
            ExpressionAttributeValues={
                ATT_VALUE_WORKFLOW_STATUS: status
            },
            KeyConditionExpression='{} = {}'.format(ATT_NAME_WORKFLOW_STATUS, ATT_VALUE_WORKFLOW_STATUS),
            ProjectionExpression = projection_expression
        )
        workflow_executions.extend(response['Items'])

    return workflow_executions

@app.route('/workflow/execution/asset/{asset_id}', cors=True, methods=['GET'], authorizer=authorizer)
def list_workflow_executions_by_assetid(asset_id):
    """ Get workflow executions by AssetId

    Returns:
        A list of dictionaries containing the workflow executions matching the AssetId.

    Raises:
        200: Workflow executions returned sucessfully.
        404: Not found
        500: ChaliceViewError - internal server error
    """
    table = DYNAMO_RESOURCE.Table(WORKFLOW_EXECUTION_TABLE_NAME)

    projection_expression = "Id, AssetId, CurrentStage, Created, StateMachineExecutionArn, {}, Workflow.{}".format(
        ATT_NAME_WORKFLOW_STATUS, ATT_NAME_WORKFLOW_NAME)

    response = table.query(
        IndexName='WorkflowExecutionAssetId',
        ExpressionAttributeNames={
            ATT_NAME_WORKFLOW_STATUS: "Status",
            ATT_NAME_WORKFLOW_NAME: "Name"
        },
        ExpressionAttributeValues={
            ':assetid': asset_id
        },
        KeyConditionExpression='AssetId = :assetid',
        ProjectionExpression = projection_expression
        )
    workflow_executions = response['Items']
    while 'LastEvaluatedKey' in response:
        response = table.query(
            ExclusiveStartKey=response['LastEvaluatedKey'],
            IndexName='WorkflowExecutionAssetId',
            ExpressionAttributeNames={
                ATT_NAME_WORKFLOW_STATUS: "Status",
                ATT_NAME_WORKFLOW_NAME: "Name"
            },
            ExpressionAttributeValues={
                ':assetid': asset_id
            },
            KeyConditionExpression='AssetId = :assetid',
            ProjectionExpression=projection_expression
        )
        workflow_executions.extend(response['Items'])

    sorted_executions = sorted(workflow_executions, key=itemgetter('Created'), reverse=True)
    return sorted_executions


@app.route('/workflow/execution/{id}', cors=True, methods=['GET'], authorizer=authorizer)
def get_workflow_execution_by_id(id):
    """ Get a workflow execution by id

    Returns:
        A dictionary containing the workflow execution.

    Raises:
        200: Workflow executions returned sucessfully.
        404: Not found
        500: ChaliceViewError - internal server error
    """
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

    return workflow_execution


@app.route('/workflow/execution/{id}', cors=True, methods=['DELETE'], authorizer=authorizer)
def delete_workflow_execution(id):
    """ Delete a workflow executions

    Returns:

    Raises:
        200: Workflow execution deleted sucessfully.
        404: Not found
        500: ChaliceViewError - internal server error
    """
    table = DYNAMO_RESOURCE.Table(WORKFLOW_EXECUTION_TABLE_NAME)

    try:
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

        response = table.delete_item(
            Key={
                'Id': id
            })

    except Exception as e:

        workflow_execution = None
        log_exception(e)
        raise ChaliceViewError(format_exception(e))

    return workflow_execution


def update_workflow_execution_status(id, status, message):
    """
    Get the workflow execution by id from dyanamo and assign to this object
    :param id: The id of the workflow execution
    :param status: The new status of the workflow execution

    """
    print("Update workflow execution {} set status = {}".format(id, status)) #nosec
    execution_table = DYNAMO_RESOURCE.Table(WORKFLOW_EXECUTION_TABLE_NAME)

    if status == awsmie.WORKFLOW_STATUS_ERROR:
        execution_table.update_item(
            Key={
                'Id': id
            },
            UpdateExpression='SET {} = {}, Message = :message'.format(ATT_NAME_WORKFLOW_STATUS, ATT_VALUE_WORKFLOW_STATUS),
            ExpressionAttributeNames={
                ATT_NAME_WORKFLOW_STATUS: "Status"
            },
            ExpressionAttributeValues={
                ATT_VALUE_WORKFLOW_STATUS: status,
                ':message': message

            }
        )
    else:
        execution_table.update_item(
            Key={
                'Id': id
            },
            UpdateExpression='SET {} = {}'.format(ATT_NAME_WORKFLOW_STATUS, ATT_VALUE_WORKFLOW_STATUS),
            ExpressionAttributeNames={
                ATT_NAME_WORKFLOW_STATUS: "Status"
            },
            ExpressionAttributeValues={
                ATT_VALUE_WORKFLOW_STATUS: status
            }
        )

    if status in [awsmie.WORKFLOW_STATUS_QUEUED, awsmie.WORKFLOW_STATUS_COMPLETE, awsmie.WORKFLOW_STATUS_ERROR]:
        # Trigger the workflow_scheduler
        LAMBDA_CLIENT.invoke(
            FunctionName=WORKFLOW_SCHEDULER_LAMBDA_ARN,
            InvocationType='Event'
        )

# ================================================================================================
#      ___        ______    ____                  _            ____                _
#     / \ \      / / ___|  / ___|  ___ _ ____   _(_) ___ ___  |  _ \ _ __ _____  _(_) ___ ___
#    / _ \ \ /\ / /\___ \  \___ \ / _ | '__\ \ / | |/ __/ _ \ | |_) | '__/ _ \ \/ | |/ _ / __|
#   / ___ \ V  V /  ___) |  ___) |  __| |   \ V /| | (_|  __/ |  __/| | | (_) >  <| |  __\__ \
#  /_/   \_\_/\_/  |____/  |____/ \___|_|    \_/ |_|\___\___| |_|   |_|  \___/_/\_|_|\___|___/
#
# ================================================================================================


def get_transcribe_client():
    global TRANSCRIBE_CLIENT
    if TRANSCRIBE_CLIENT is None:
        TRANSCRIBE_CLIENT = boto3.client('transcribe', region_name=os.environ['AWS_REGION'])
    return TRANSCRIBE_CLIENT


def get_translate_client():
    global TRANSLATE_CLIENT
    if TRANSLATE_CLIENT is None:
        TRANSLATE_CLIENT = boto3.client('translate', region_name=os.environ['AWS_REGION'])
    return TRANSLATE_CLIENT


@app.route('/service/transcribe/get_vocabulary', cors=True, methods=['POST'], content_types=['application/json'], authorizer=authorizer)
def get_vocabulary():
    """ Get the description for an Amazon Transcribe custom vocabulary.

    Returns:
        This is a proxy for boto3 get_vocabulary and returns the output from that SDK method.
        See `the boto3 documentation for details <https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/transcribe.html#TranscribeService.Client.get_vocabulary>`_

    Raises:
        See `the boto3 documentation for details <https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/transcribe.html#TranscribeService.Client.get_vocabulary>`_
    """
    print('get_vocabulary request: '+app.current_request.raw_body.decode())
    vocabulary_name = json.loads(app.current_request.raw_body.decode())['vocabulary_name']
    transcribe_client = get_transcribe_client()
    response = transcribe_client.get_vocabulary(VocabularyName=vocabulary_name)
    # Convert time field to a format that is JSON serializable
    response['LastModifiedTime'] = response['LastModifiedTime'].isoformat()
    return response


@app.route('/service/transcribe/download_vocabulary', cors=True, methods=['POST'], content_types=['application/json'], authorizer=authorizer)
def download_vocabulary():
    """ Get the contents of an Amazon Transcribe custom vocabulary.

    Body:

    .. code-block:: python

        {
            "vocabulary_name": string
        }


    Returns:
        A list of vocabulary terms.

        .. code-block:: python

            {
                "vocabulary": [{
                    "Phrase": string,
                    "IPA": string,
                    "SoundsLike": string,
                    "DisplayAs": string
                    },
                    ...
            }

    Raises:
        500: ChaliceViewError - internal server error
    """
    print('download_vocabulary request: '+app.current_request.raw_body.decode())
    transcribe_client = get_transcribe_client()
    vocabulary_name = json.loads(app.current_request.raw_body.decode())['vocabulary_name']
    url = transcribe_client.get_vocabulary(VocabularyName=vocabulary_name)['DownloadUri']
    import urllib.request
    vocabulary_file = urllib.request.urlopen(url).read().decode("utf-8") #nosec
    vocabulary_json = []
    vocabulary_fields = vocabulary_file.split('\n')[0].split('\t')
    for line in vocabulary_file.split('\n')[1:]:
        vocabulary_item_array = line.split('\t')
        vocabulary_item_json = {}
        # if vocab item is missing any fields, then skip it
        if len(vocabulary_item_array) == len(vocabulary_fields):
            i = 0
            for field in vocabulary_fields:
                vocabulary_item_json[field] = vocabulary_item_array[i]
                i = i + 1
        vocabulary_json.append(vocabulary_item_json)
    return {"vocabulary": vocabulary_json}


@app.route('/service/transcribe/list_vocabularies', cors=True, methods=['GET'], authorizer=authorizer)
def list_vocabularies():
    """ List all the available Amazon Transcribe custom vocabularies in this region.

    Returns:
        This is a proxy for boto3 list_vocabularies and returns the output from that SDK method.
        See `the boto3 documentation for details <https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/transcribe.html#TranscribeService.Client.list_vocabularies>`_

    Raises:
        See the boto3 documentation for details
        500: ChaliceViewError - internal server error
    """
    # List all custom vocabularies
    print('list_vocabularies request: '+app.current_request.raw_body.decode())
    transcribe_client = get_transcribe_client()
    response = transcribe_client.list_vocabularies(MaxResults=100)
    vocabularies = response['Vocabularies']
    while ('NextToken' in response):
        response = transcribe_client.list_vocabularies(MaxResults=100, NextToken=response['NextToken'])
        vocabularies = vocabularies + response['Vocabularies']
    # Convert time field to a format that is JSON serializable
    for item in vocabularies:
        item['LastModifiedTime'] = item['LastModifiedTime'].isoformat()
    return response


@app.route('/service/transcribe/delete_vocabulary', cors=True, methods=['POST'], content_types=['application/json'], authorizer=authorizer)
def delete_vocabulary():
    """ Delete an Amazon Transcribe custom vocabulary.

    Body:

        .. code-block:: python

            {
                'vocabulary_name': 'string'
            }

    Returns:

        This is a proxy for boto3 delete_vocabulary and returns the output from that SDK method.
        See `the boto3 documentation for details <https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/transcribe.html#TranscribeService.Client.delete_vocabulary>`_

    Raises:
        See the boto3 documentation for details
        500: ChaliceViewError - internal server error
    """
    # Delete the specified vocabulary if it exists
    print('delete_vocabulary request: '+app.current_request.raw_body.decode())
    vocabulary_name = json.loads(app.current_request.raw_body.decode())['vocabulary_name']
    transcribe_client = get_transcribe_client()
    response = transcribe_client.delete_vocabulary(VocabularyName=vocabulary_name)
    return response


@app.route('/service/transcribe/create_vocabulary', cors=True, methods=['POST'], content_types=['application/json'], authorizer=authorizer)
def create_vocabulary():
    """ Create an Amazon Transcribe custom vocabulary.

    Body:

        .. code-block:: python

            {
                'vocabulary_name'='string',
                'language_code'='af-ZA'|'ar-AE'|'ar-SA'|'cy-GB'|'da-DK'|'de-CH'|'de-DE'|'en-AB'|'en-AU'|'en-GB'|'en-IE'|'en-IN'|'en-US'|'en-WL'|'es-ES'|'es-US'|'fa-IR'|'fr-CA'|'fr-FR'|'ga-IE'|'gd-GB'|'he-IL'|'hi-IN'|'id-ID'|'it-IT'|'ja-JP'|'ko-KR'|'ms-MY'|'nl-NL'|'pt-BR'|'pt-PT'|'ru-RU'|'ta-IN'|'te-IN'|'tr-TR'|'zh-CN',
                's3uri'='string'
            }


    Returns:
        This is a proxy for boto3 create_vocabulary and returns the output from that SDK method.
        See `the boto3 documentation for details <https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/transcribe.html#TranscribeService.Client.create_vocabulary>`_

    Raises:
        See the boto3 documentation for details
        500: ChaliceViewError - internal server error
    """
    # Save the input vocab to a new vocabulary
    print('create_vocabulary request: '+app.current_request.raw_body.decode())
    vocabulary_name = json.loads(app.current_request.raw_body.decode())['vocabulary_name']
    language_code = json.loads(app.current_request.raw_body.decode())['language_code']
    transcribe_client = get_transcribe_client()
    response = transcribe_client.create_vocabulary(
        VocabularyName=vocabulary_name,
        LanguageCode=language_code,
        VocabularyFileUri=json.loads(app.current_request.raw_body.decode())['s3uri']
    )
    return response


@app.route('/service/transcribe/list_language_models', cors=True, methods=['GET'], authorizer=authorizer)
def list_language_models():
    """ Provides more information about the custom language models you've created. You can use the information in this list to find a specific custom language model. You can then use the describe_language_model operation to get more information about it.

    Returns:
        This is a proxy for boto3 list_language_models and returns the output from that SDK method.
        See `the boto3 documentation for details <https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/transcribe.html#TranscribeService.Client.list_language_models>`_

    Raises:
        See `the boto3 documentation for details <https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/transcribe.html#TranscribeService.Client.list_language_models>`_
    """
    print('list_language_models request: '+app.current_request.raw_body.decode())
    transcribe_client = get_transcribe_client()
    response = transcribe_client.list_language_models()
    models = response['Models']
    while ('NextToken' in response):
        response = transcribe_client.list_language_models(MaxResults=100, NextToken=response['NextToken'])
        models = models + response['Models']
    # Convert time field to a format that is JSON serializable
    for item in models:
        item['CreateTime'] = item['CreateTime'].isoformat()
        item['LastModifiedTime'] = item['LastModifiedTime'].isoformat()
    return response


@app.route('/service/transcribe/describe_language_model', cors=True, methods=['POST'], content_types=['application/json'], authorizer=authorizer)
def describe_language_model():
    """ Gets information about a single custom language model. 

    Body:

        .. code-block:: python

            {
                'ModelName': 'string'
            }

    Returns:
        This is a proxy for boto3 describe_language_model and returns the output from that SDK method.
        See `the boto3 documentation for details <https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/transcribe.html#TranscribeService.Client.describe_language_model>`_

    Raises:
        See `the boto3 documentation for details <https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/transcribe.html#TranscribeService.Client.describe_language_model>`_
    """
    print('describe_language_model request: '+app.current_request.raw_body.decode())
    request_payload = dict(json.loads(app.current_request.raw_body.decode()))
    transcribe_client = get_transcribe_client()
    response = transcribe_client.describe_language_model(**request_payload)
    # Convert time field to a format that is JSON serializable
    response['LanguageModel']['CreateTime'] = response['LanguageModel']['CreateTime'].isoformat()
    response['LanguageModel']['LastModifiedTime'] = response['LanguageModel']['LastModifiedTime'].isoformat()
    return response


@app.route('/service/translate/get_terminology', cors=True, methods=['POST'], content_types=['application/json'], authorizer=authorizer)
def get_terminology():
    """ Get a link to the CSV formatted description for an Amazon Translate parallel data.

    Body:

    .. code-block:: python

        {
            'terminology_name'='string'
        }

    Returns:
        This is a proxy for boto3 get_terminology and returns the output from that SDK method.
        See `the boto3 documentation for details <https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/translate.html#Translate.Client.get_terminology>`_

    Raises:
        See the boto3 documentation for details
        500: ChaliceViewError - internal server error
    """
    print('get_terminology request: '+app.current_request.raw_body.decode())
    terminology_name = json.loads(app.current_request.raw_body.decode())['terminology_name']
    translate_client = get_translate_client()
    response = translate_client.get_terminology(Name=terminology_name, TerminologyDataFormat='CSV')
    # Remove response metadata since we don't need it
    del response['ResponseMetadata']
    # Convert time field to a format that is JSON serializable
    response['TerminologyProperties']['CreatedAt'] = response['TerminologyProperties']['CreatedAt'].isoformat()
    response['TerminologyProperties']['LastUpdatedAt'] = response['TerminologyProperties']['LastUpdatedAt'].isoformat()
    return response


@app.route('/service/translate/download_terminology', cors=True, methods=['POST'], content_types=['application/json'], authorizer=authorizer)
def download_terminology():
    """ Get the CSV formated contents of an Amazon Translate terminology.

    Body:

    .. code-block:: python

        {
            'terminology_name'='string'
        }


    Returns:
        A string contining the CSV formatted Amazon Transcribe terminology

        .. code-block:: python

            {
                'terminology_csv': string
            }

    Raises:
        See the boto3 documentation for details
        500: ChaliceViewError - internal server error
    """
    # This function returns the specified terminology in CSV format, wrapped in a JSON formatted response.
    print('download_terminology request: '+app.current_request.raw_body.decode())
    translate_client = get_translate_client()
    terminology_name = json.loads(app.current_request.raw_body.decode())['terminology_name']
    url = translate_client.get_terminology(Name=terminology_name, TerminologyDataFormat='CSV')['TerminologyDataLocation']['Location']
    import urllib.request
    terminology_csv = urllib.request.urlopen(url).read().decode("utf-8") #nosec
    return {"terminology": terminology_csv}


@app.route('/service/translate/list_terminologies', cors=True, methods=['GET'], authorizer=authorizer)
def list_terminologies():
    """ Get the list of available Amazon Translate Terminologies for this region

    Returns:
        This is a proxy for boto3 get_terminology and returns the output from that SDK method.
        See `the boto3 documentation for details <https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/translate.html#Translate.Client.list_terminologies>`_

    Raises:
        See the boto3 documentation for details
        500: Internal server error
    """
    # This function returns a list of saved terminologies
    print('list_terminologies request: '+app.current_request.raw_body.decode())
    translate_client = get_translate_client()
    response = translate_client.list_terminologies(MaxResults=100)
    terminologies = response['TerminologyPropertiesList']
    while ('NextToken' in response):
        response = TRANSLATE_CLIENT.list_terminologies(MaxResults=100, NextToken=response['NextToken'])
        terminologies = terminologies + response['TerminologyPropertiesList']
    # Convert time field to a format that is JSON serializable
    for item in terminologies:
        item['CreatedAt'] = item['CreatedAt'].isoformat()
        item['LastUpdatedAt'] = item['LastUpdatedAt'].isoformat()
    return response


@app.route('/service/translate/delete_terminology', cors=True, methods=['POST'], content_types=['application/json'], authorizer=authorizer)
def delete_terminology():
    """ Delete an Amazon Translate Terminology

    Body:

    .. code-block:: python

        {
            'terminology_name': 'string'
        }


    Returns:

        This is a proxy for boto3 delete_terminology and returns the output from that SDK method.
        See `the boto3 documentation for details <https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/translate.html#Translate.Client.delete_terminology>`_


    Raises:
        See the boto3 documentation for details
        500: ChaliceViewError - internal server error
    """
    # Delete the specified terminology if it exists
    print('delete_terminology request: '+app.current_request.raw_body.decode())
    terminology_name = json.loads(app.current_request.raw_body.decode())['terminology_name']
    translate_client = get_translate_client()
    response = translate_client.delete_terminology(Name=terminology_name)
    return response


@app.route('/service/translate/create_terminology', cors=True, methods=['POST'], content_types=['application/json'], authorizer=authorizer)
def create_terminology():
    """ Create an Amazon Translate Terminology.  If the terminology already exists, overwrite the terminology with this new content.

    Body:

    .. code-block:: python

        {
            'terminology_name'='string',
            'terminology_csv'='string'
        }
    }


    Returns:
        This is a proxy for boto3 create_vocabulary and returns the output from that SDK method.
        See `the boto3 documentation for details <https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/translate.html#Translate.Client.import_terminology>`_

    Raises:
        See the boto3 documentation for details
        500: ChaliceViewError - internal server error
    """
    # Save the input terminology to a new terminology
    print('create_terminology request: '+app.current_request.raw_body.decode())
    terminology_name = json.loads(app.current_request.raw_body.decode())['terminology_name']
    terminology_csv = json.loads(app.current_request.raw_body.decode())['terminology_csv']
    translate_client = get_translate_client()
    response = translate_client.import_terminology(
        Name=terminology_name,
        MergeStrategy='OVERWRITE',
        TerminologyData={'File': terminology_csv, 'Format':'CSV'}
    )
    response['TerminologyProperties']['CreatedAt'] = response['TerminologyProperties']['CreatedAt'].isoformat()
    response['TerminologyProperties']['LastUpdatedAt'] = response['TerminologyProperties']['LastUpdatedAt'].isoformat()
    return response

# Parallel data funcitons for Active Custom Translation

@app.route('/service/translate/get_parallel_data', cors=True, methods=['POST'], content_types=['application/json'], authorizer=authorizer)
def get_parallel_data():
    """ Get a link to the CSV formatted description for an Amazon Translate Parallel Data Set.

    Body:

    .. code-block:: python

        {
            'Name'='string'
        }

    Returns:
        This is a proxy for boto3 get_parallel_data and returns the output from that SDK method.
        See `the boto3 documentation for details <https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/translate.html#Translate.Client.get_parallel_data>`_

    Raises:
        See the boto3 documentation for details
        500: ChaliceViewError - internal server error
    """
    print('get_parallel_data request: '+app.current_request.raw_body.decode())
    request_payload = dict(json.loads(app.current_request.raw_body.decode()))
    translate_client = get_translate_client()
    response = translate_client.get_parallel_data(**request_payload)

    # Convert time field to a format that is JSON serializable
    response['ParallelDataProperties']['CreatedAt'] = response['ParallelDataProperties']['CreatedAt'].isoformat()
    response['ParallelDataProperties']['LastUpdatedAt'] = response['ParallelDataProperties']['LastUpdatedAt'].isoformat()
    return response


@app.route('/service/translate/download_parallel_data', cors=True, methods=['POST'], content_types=['application/json'], authorizer=authorizer)
def download_parallel_data():
    """ Get the CSV formated contents of an Amazon Translate Parallel Data Set.

    Body:

    .. code-block:: python

        {
            'Name'='string'
        }


    Returns:
        A pre-signed url for the the CSV formatted Amazon Transcribe parallel_data

        .. code-block:: python

            {
                'parallel_data_csv': string
            }

    Raises:
        See the boto3 documentation for details
        500: ChaliceViewError - internal server error
    """
    # This function returns the specified parallel_data in CSV format, wrapped in a JSON formatted response.
    print('download_parallel_data request: '+app.current_request.raw_body.decode())
    translate_client = get_translate_client()
    request_payload = dict(json.loads(app.current_request.raw_body.decode()))
    url = translate_client.get_parallel_data(**request_payload)['DataLocation']['Location']
    import urllib.request
    parallel_data_csv = urllib.request.urlopen(url).read().decode("utf-8") #nosec
    return {"parallel_data_csv": parallel_data_csv}


@app.route('/service/translate/list_parallel_data', cors=True, methods=['GET'], authorizer=authorizer)
def list_parallel_data():
    """ Get the list of available Amazon Translate Parallel Data Sets for this region

    Returns:
        This is a proxy for boto3 get_parallel_data and returns the output from that SDK method.
        See `the boto3 documentation for details <https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/translate.html#Translate.Client.list_parallel_data>`_

    Raises:
        See the boto3 documentation for details
        500: Internal server error
    """
    # This function returns a list of saved parallel_data
    print('list_parallel_data request: '+app.current_request.raw_body.decode())
    translate_client = get_translate_client()
    response = translate_client.list_parallel_data(MaxResults=100)
    parallel_data = response['ParallelDataPropertiesList']
    while ('NextToken' in response):
        response = translate_client.list_parallel_data(MaxResults=100, NextToken=response['NextToken'])
        parallel_data = parallel_data + response['ParallelDataPropertiesList']
    # Convert time field to a format that is JSON serializable
    for item in parallel_data:
        item['CreatedAt'] = item['CreatedAt'].isoformat()
        item['LastUpdatedAt'] = item['LastUpdatedAt'].isoformat()
    return response


@app.route('/service/translate/delete_parallel_data', cors=True, methods=['POST'], content_types=['application/json'], authorizer=authorizer)
def delete_parallel_data():
    """ Delete an Amazon Translate Parallel Data

    Body:

    .. code-block:: python

        {
            'Name': 'string'
        }


    Returns:

        This is a proxy for boto3 delete_parallel_data and returns the output from that SDK method.
        See `the boto3 documentation for details <https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/translate.html#Translate.Client.delete_parallel_data>`_


    Raises:
        See the boto3 documentation for details
        500: ChaliceViewError - internal server error
    """
    # Delete the specified parallel_data if it exists
    print('delete_parallel_data request: '+app.current_request.raw_body.decode())
    request_payload = dict(json.loads(app.current_request.raw_body.decode()))
    translate_client = get_translate_client()
    response = translate_client.delete_parallel_data(**request_payload)
    return response


@app.route('/service/translate/create_parallel_data', cors=True, methods=['POST'], content_types=['application/json'], authorizer=authorizer)
def create_parallel_data():
    """ Create an Amazon Translate Parallel Data.  If the parallel_data already exists, overwrite the parallel data with this new content.

    Body:

    .. code-block:: python

        {
              "Name"="string",
              "Description"="string",
              "ParallelDataConfig"={
                  "S3Uri": "string",
                  "Format": "TSV"|"CSV"|"TMX"
              },
              "EncryptionKey"={
                  "Type": "KMS",
                  "Id": "string"
              },
              "ClientToken"="string"
        }

    Returns:
        This is a proxy for boto3 create_vocabulary and returns the output from that SDK method.
        See `the boto3 documentation for details <https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/translate.html#TranslateService.Client.create_parallel_data>`_

    Raises:
        See the boto3 documentation for details
        500: ChaliceViewError - internal server error
    """
    request_payload = dict(json.loads(app.current_request.raw_body.decode()))
    translate_client = get_translate_client()
    response = translate_client.create_parallel_data(**request_payload)
    return response

# ================================================================================================
#   ____          _                    ____
#   / ___|   _ ___| |_ ___  _ __ ___   |  _ \ ___  ___  ___  _   _ _ __ ___ ___
#  | |  | | | / __| __/ _ \| '_ ` _ \  | |_) / _ \/ __|/ _ \| | | | '__/ __/ _ \
#  | |__| |_| \__ \ || (_) | | | | | | |  _ <  __/\__ \ (_) | |_| | | | (_|  __/
#   \____\__,_|___/\__\___/|_| |_| |_| |_| \_\___||___/\___/ \__,_|_|  \___\___|
#
# ================================================================================================


@app.lambda_function(name="WorkflowCustomResource")
def workflow_custom_resource(event, context):
    '''Handle Lambda event from AWS CloudFormation'''
    # Setup alarm for remaining runtime minus a second
    # signal.alarm(int(context.get_remaining_time_in_millis() / 1000) - 1)

    # send_response(event, context, "SUCCESS",
    #                     {"Message": RESOURCE_DELETE_SUCCESS})
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
            logger.info(FAILED)
            send_response(event, context, "FAILED",
                          {"Message": "Unexpected resource type received from CloudFormation"})


    except Exception as e:

        logger.info(FAILED)
        send_response(event, context, "FAILED", {
            "Message": "Exception during processing: '%s'" % e})


def operation_resource(event, context):
    operation = {}

    if event['RequestType'] == 'Create':
        logger.info(CREATE)

        operation = event["ResourceProperties"]

        # boolean type comes in as text from cloudformation - must decode string or take string for anabled parameter
        operation["Configuration"]["Enabled"] = True if operation["Configuration"]["Enabled"] == 'true' else False
        operation = create_operation(operation)
        send_response(event, context, "SUCCESS",
                      {"Message": RESOURCE_CREATE_SUCCESS, "Name": event["ResourceProperties"]["Name"],
                       "StageName": operation["StageName"]})
    elif event['RequestType'] == 'Update':
        logger.info(UPDATE)
        send_response(event, context, "SUCCESS",
                      {"Message": RESOURCE_UPDATE_SUCCESS, "Name": event["ResourceProperties"]["Name"],
                       "StageName": operation["StageName"]})
    elif event['RequestType'] == 'Delete':
        logger.info(DELETE)

        name = event["ResourceProperties"]["Name"]

        operation = delete_operation(name, True)

        send_response(event, context, "SUCCESS",
                      {"Message": RESOURCE_DELETE_SUCCESS, "Name": event["ResourceProperties"]["Name"]})
    else:
        logger.info(FAILED)
        send_response(event, context, "FAILED",
                      {"Message": UNEXPECTED_CLOUD_FORMATION_EVENT})

    return operation


def stage_resource(event, context):
    stage = event["ResourceProperties"]

    if event['RequestType'] == 'Create':
        logger.info(CREATE)

        create_stage(stage)

        send_response(event, context, "SUCCESS",
                      {"Message": RESOURCE_CREATE_SUCCESS, "Name": event["ResourceProperties"]["Name"]})

    elif event['RequestType'] == 'Update':
        logger.info(UPDATE)
        send_response(event, context, "SUCCESS",
                      {"Message": RESOURCE_UPDATE_SUCCESS})
    elif event['RequestType'] == 'Delete':
        logger.info(DELETE)

        name = event["ResourceProperties"]["Name"]

        stage = delete_stage(name, True)

        send_response(event, context, "SUCCESS",
                      {"Message": RESOURCE_DELETE_SUCCESS})
    else:
        logger.info(FAILED)
        send_response(event, context, "FAILED",
                      {"Message": UNEXPECTED_CLOUD_FORMATION_EVENT})

    return stage


def workflow_resource(event, context):
    workflow = event["ResourceProperties"]

    logger.info(json.dumps(workflow))

    if event['RequestType'] == 'Create':
        logger.info(CREATE)

        workflow["Stages"] = json.loads(event["ResourceProperties"]["Stages"])

        create_workflow_response = create_workflow("custom-resource", workflow)

        send_response(event, context, "SUCCESS",
                      {
                          "Message": RESOURCE_CREATE_SUCCESS,
                          "Name": event["ResourceProperties"]["Name"],
                          "StateMachineArn": create_workflow_response["StateMachineArn"]
                      })
    elif event['RequestType'] == 'Update':
        logger.info(UPDATE)
        send_response(event, context, "SUCCESS",
                      {"Message": RESOURCE_UPDATE_SUCCESS})
    elif event['RequestType'] == 'Delete':
        logger.info(DELETE)

        name = event["ResourceProperties"]["Name"]

        delete_workflow(name)

        send_response(event, context, "SUCCESS",
                      {"Message": RESOURCE_DELETE_SUCCESS})
    else:
        logger.info(FAILED)
        send_response(event, context, "FAILED",
                      {"Message": UNEXPECTED_CLOUD_FORMATION_EVENT})

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
    data = response_body.encode('utf-8')
    request = Request(event['ResponseURL'], data=data)
    request.add_header('Content-Type', '')
    request.add_header('Content-Length', str(len(data)))
    request.get_method = lambda: 'PUT'
    response = opener.open(request)
    logger.info("Status code: %s", response.getcode())
    logger.info("Status message: %s", response.msg)
