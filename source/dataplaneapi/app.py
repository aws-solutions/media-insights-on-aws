# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from chalice import Chalice
from chalice import IAMAuthorizer
from chalice import NotFoundError, BadRequestError, ChaliceViewError
from botocore.client import ClientError
from decimal import Decimal
from botocore.config import Config
from aws_xray_sdk.core import patch_all

import boto3
import os
import uuid
import json
import logging
import datetime
import base64


def is_aws():
    if os.getenv('AWS_LAMBDA_FUNCTION_NAME') is None:
        return False
    else:
        return True


if is_aws():
    patch_all()

# TODO: Address the following items
#   *   Add additional exception and response codes
#   *   Narrow exception scopes
#   *   Better way to bubble exceptions to lambda helper class
#   *   Normalize pattern for referencing URI params inside a function
#   *   Move global_attributes list to a top level variable

'''
except ClientError as e:
    print(e.response['Error']['Message'])
'''

mie_config = json.loads(os.environ['botoConfig'])
config = Config(**mie_config)

formatter = logging.Formatter('{%(pathname)s:%(lineno)d} %(levelname)s - %(message)s')
handler = logging.StreamHandler()
handler.setFormatter(formatter)

logger = logging.getLogger('boto3')
logger.setLevel(logging.INFO)
logger.addHandler(handler)

app_name = 'dataplaneapi'
app = Chalice(app_name=app_name)
api_version = "3.0.0"
framework_version = os.environ['FRAMEWORK_VERSION']

# DDB resources
dataplane_table_name = os.environ['DATAPLANE_TABLE_NAME']
dynamo_client = boto3.client('dynamodb', config=config)
dynamo_resource = boto3.resource('dynamodb', config=config)

# S3 resources
dataplane_s3_bucket = os.environ['DATAPLANE_BUCKET']

# Cognito resources
# From cloudformation stack
authorizer = IAMAuthorizer()

# TODO: Should we add a variable for the upload bucket?

base_s3_uri = 'private/assets/'
s3_client = boto3.client('s3', config=config)
s3_resource = boto3.resource('s3', config=config)


class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)
            # Let the base class default method raise the TypeError
        return json.JSONEncoder.default(self, obj)


def check_required_input(key, dict, objectname):
    if key not in dict:
        raise BadRequestError("Key '%s' is required in '%s' input" % (
            key, objectname))


def write_metadata_to_s3(bucket, key, data):
    encoded = json.dumps(data, cls=DecimalEncoder)
    try:
        s3_client.put_object(Bucket=bucket, Key=key, Body=encoded)
    except ClientError as e:
        error = e.response['Error']['Message']
        logger.error("Exception occurred while writing asset metadata to s3: {e}".format(e=error))
        return {"Status": "Error", "Message": error}
    except Exception as e:
        logger.error("Exception occurred while writing asset metadata to s3")
        return {"Status": "Error", "Message": e}
    else:
        logger.info("Wrote asset metadata to s3")
        return {"Status": "Success"}


def read_metadata_from_s3(bucket, key):
    try:
        obj = s3_client.get_object(
            Bucket=bucket,
            Key=key
        )
    except ClientError as e:
        error = e.response['Error']['Message']
        logger.error("Exception occurred while reading asset metadata from s3: {e}".format(e=error))
        return {"Status": "Error", "Message": error}
    except Exception as e:
        logger.error("Exception occurred while reading asset metadata from s3")
        return {"Status": "Error", "Message": e}
    else:
        results = obj['Body'].read().decode('utf-8')
        return {"Status": "Success", "Object": results}


def delete_s3_objects(keys):
    objects = []
    for key in keys:
        objects.append({"Key": key})
    try:
        response = s3_client.delete_objects(
            Bucket=dataplane_s3_bucket,
            Delete={
                'Objects': objects
            }
        )
    except ClientError as e:
        error = e.response['Error']['Message']
        logger.error("Exception occurred while deleting asset metadata from s3: {e}".format(e=error))
        return {"Status": "Error", "Message": error}
    except Exception as e:
        logger.error("Exception occurred while deleting asset metadata from s3")
        return {"Status": "Error", "Message": e}
    else:
        return {"Status": "Success", "Message": response}


def read_asset_from_db(asset_id, **kwargs):
    def log_exception_retreiving_metadata_for_asset(asset_id, error):
        logger.error("Exception occurred while retreiving metadata for {asset}: {e}".format(asset=asset_id, e=error))

    def format_unable_to_retrieve_metadata_error(error):
        return "Unable to retrieve metadata: {e}".format(e=error)

    table_name = dataplane_table_name

    try:
        table = dynamo_resource.Table(table_name)
        asset_item = table.get_item(
            Key={
                "AssetId": asset_id
            },
            **kwargs
        )
    except ClientError as e:
        error = e.response['Error']['Message']
        log_exception_retreiving_metadata_for_asset(asset_id, error)
        raise ChaliceViewError(format_unable_to_retrieve_metadata_error(error))
    except Exception as e:
        log_exception_retreiving_metadata_for_asset(asset_id, e)
        raise ChaliceViewError(format_unable_to_retrieve_metadata_error(e))

    if "Item" not in asset_item:
        raise NotFoundError(
            "Exception occurred while verifying asset exists: {asset} does not exist".format(asset=asset_id))

    return asset_item["Item"]


def build_cursor_object(next_object, remaining):
    cursor = {
        "next": next_object,
        "remaining": remaining
    }
    return cursor


def encode_cursor(cursor):
    cursor = json.dumps(cursor)
    encoded = base64.urlsafe_b64encode(cursor.encode('UTF-8')).decode('ascii')
    return encoded


def decode_cursor(cursor):
    decoded = json.loads(base64.b64decode(cursor).decode('utf-8'))
    return decoded


def is_metadata_list(metadata):
    return isinstance(metadata, list)


def next_page_valid(metadata, page_num):
    try:
        metadata[page_num]
        return True
    except IndexError:
        return False


def format_exception(e):
    return "Exception: {e}".format(e=e)


@app.route('/')
def index():
    """ Test the API endpoint

    Returns:

    .. code-block:: python

        {"hello":"world"}

    Raises:

        ChaliceViewError - 500
    """
    return {'hello': 'world'}


@app.route('/version', cors=True, methods=['GET'], authorizer=authorizer)
def version():
    """
    Get the dataplane api and framework version numbers

    Returns:

    .. code-block:: python

        {"ApiVersion": "x.x.x", "FrameworkVersion": "vx.x.x"}
    """
    versions = {"ApiVersion": api_version, "FrameworkVersion": framework_version}
    return versions


# TODO: Change the name of this method - "upload" is too vague

@app.route('/upload', cors=True, methods=['POST'], content_types=['application/json'], authorizer=authorizer)
def upload():
    """
    Generate a pre-signed URL that can be used to upload media files to S3 from a web application

    Returns:
        Pre-signed S3 URL for uploading files to S3 from a web application
    Raises:
        ChaliceViewError - 500
    """
    print('/upload request: ' + app.current_request.raw_body.decode())
    region = os.environ['AWS_REGION']
    s3 = boto3.client('s3', region_name=region, config=Config(signature_version='s3v4', s3={'addressing_style': 'virtual'}))
    # limit uploads to 5GB
    max_upload_size = 5368709120
    try:
        response = s3.generate_presigned_post(
            Bucket=(json.loads(app.current_request.raw_body.decode())['S3Bucket']),
            Key=(json.loads(app.current_request.raw_body.decode())['S3Key']),
            Conditions=[["content-length-range", 0, max_upload_size]],
            ExpiresIn=3600
        )
    except ClientError as e:
        logging.info(e)
        raise ChaliceViewError(
            "Unable to generate pre-signed S3 URL for uploading media: {error}".format(error=e))
    except Exception as e:
        logging.info(e)
        raise ChaliceViewError(
            "Unable to generate pre-signed S3 URL for uploading media: {error}".format(error=e))
    else:
        print("presigned url generated: ", response)
        return response

# TODO: Change the name of this method - "download" is too vague


@app.route('/download', cors=True, methods=['POST'], content_types=['application/json'], authorizer=authorizer)
def download():
    """
    Generate a pre-signed URL that can be used to download media files from S3.

    Returns:
        Pre-signed S3 URL for downloading files from S3 to a web application.
    Raises:
        ChaliceViewError - 500
    """
    print('/download request: ' + app.current_request.raw_body.decode())
    region = os.environ['AWS_REGION']
    s3 = boto3.client('s3', region_name=region, config=Config(signature_version='s3v4', s3={'addressing_style': 'virtual'}))
    # expire the URL in
    try:
        response = s3.generate_presigned_url('get_object',
                                             Params={'Bucket': json.loads(app.current_request.raw_body.decode())['S3Bucket'],
                                                     'Key': json.loads(app.current_request.raw_body.decode())['S3Key']},
                                             ExpiresIn=3600)
    except ClientError as e:
        logging.info(e)
        raise ChaliceViewError(
            "Unable to generate pre-signed S3 URL for downloading media: {error}".format(error=e))
    except Exception as e:
        logging.info(e)
        raise ChaliceViewError(
            "Unable to generate pre-signed S3 URL for downloading media: {error}".format(error=e))
    else:
        return response

# TODO: Change the name of this method


@app.route('/mediapath/{asset_id}/{workflow_id}', cors=True, methods=['GET'], authorizer=authorizer)
def media_upload_path(asset_id, workflow_id):
    """
    Generate a media storage path in the dataplane S3 bucket.

    Returns:
         Dictionary containing the S3 bucket and key for uploading a given asset media object to the dataplane.
    Raises:
        ChaliceViewError - 500
    """
    try:
        response = {
            "S3Bucket": dataplane_s3_bucket,
            "S3Key": 'private/assets/' + asset_id + "/workflows/" + workflow_id + "/"
        }
    except Exception as e:
        logging.info(e)
        raise ChaliceViewError(
            "Unable to generate media storage path for asset: {asset} from workflow: {workflow}\n{error}".format(
                asset=asset_id, workflow=workflow_id, error=e))
    else:
        return response


@app.route('/create', cors=True, methods=['POST'], authorizer=authorizer)
def create_asset():
    """
    Create an asset in the dataplane from a json input composed of the input key and bucket of the object.

    Body:

    .. code-block:: python

        {
            "Input": {
                "MediaType": "{media type}",
                "S3Bucket": "{source bucket}",
                "S3Key": "{source key}"
            }
        }

    Returns:
        A dict containing the asset id and the Amazon S3 bucket and key describing where its media file was sourced from.
         .. code-block:: python

            {
                "AssetId": asset_id,
                "MediaType": media_type,
                "S3Bucket": source_bucket,
                "S3Key": source_key
            }
    Raises:
        ChaliceViewError - 500
    """

    table_name = dataplane_table_name
    bucket = dataplane_s3_bucket
    uri = base_s3_uri

    asset = json.loads(app.current_request.raw_body.decode())
    logger.info(asset)

    # create a uuid for the asset

    asset_id = str(uuid.uuid4())

    # check required inputs

    def log_exception_occurred_during_asset_creation(error):
        logger.error("Exception occurred during asset creation: {e}".format(e=error))

    try:
        media_type = asset['Input']['MediaType']
        source_key = asset['Input']['S3Key']
        source_bucket = asset['Input']['S3Bucket']
    except KeyError as e:
        log_exception_occurred_during_asset_creation(e)
        raise BadRequestError("Missing required inputs for asset creation: {e}".format(e=e))
    else:
        logger.info("Creating an asset from: {bucket}/{key}".format(bucket=source_bucket, key=source_key))

    # create directory structure in s3 dataplane bucket for the asset
    directory = uri + asset_id + "/"

    try:
        s3_client.put_object(
            Bucket=bucket,
            Key=directory
        )
    except ClientError as e:
        error = e.response['Error']['Message']
        log_exception_occurred_during_asset_creation(error)
        raise ChaliceViewError("Unable to create asset directory in the dataplane bucket: {e}".format(e=error))
    except Exception as e:
        log_exception_occurred_during_asset_creation(e)
        raise ChaliceViewError("Exception when creating dynamo item for asset: {e}".format(e=e))
    else:
        logger.info("Created asset directory structure: {directory}".format(directory=directory))

    ts = str(datetime.datetime.now().timestamp())

    try:
        table = dynamo_resource.Table(table_name)
        table.put_item(
            Item={
                "AssetId": asset_id,
                "MediaType": media_type,
                "S3Bucket": source_bucket,
                "S3Key": source_key,
                "Created": ts
            }
        )
    except ClientError as e:
        error = e.response['Error']['Message']
        log_exception_occurred_during_asset_creation(error)
        raise ChaliceViewError("Unable to create asset item in dynamo: {e}".format(e=error))
    except Exception as e:
        log_exception_occurred_during_asset_creation(e)
        raise ChaliceViewError("Exception when creating dynamo item for asset: {e}".format(e=e))
    else:
        logger.info("Completed asset creation for asset: {asset}".format(asset=asset_id))
        return {"AssetId": asset_id, "MediaType": media_type, "S3Bucket": source_bucket, "S3Key": source_key}


def parse_paginate_settings(query_params):
    paginated = False
    end_pagination = False

    if query_params is not None:
        try:
            paginated = query_params["paginated"]
        except KeyError:
            raise BadRequestError("Must pass required query parameter: paginated")
        else:
            if paginated == "true":
                paginated = True

    if paginated is True:
        try:
            end_pagination = query_params["end"]
        except KeyError:
            logger.info("Not the end of paginated results")
        else:
            if end_pagination == "true":
                logger.info("Storing the last page of results")
                end_pagination = True
            else:
                raise BadRequestError("Query param end only supports a value of: true")

    return paginated, end_pagination


def log_exception_while_storing_metadata_for_asset(asset, error):
    logger.error("Exception occurred while storing metadata for {asset}: {e}".format(asset=asset, e=error))


def parse_operator_workflow_and_result_from_body(body, asset):
    try:
        operator_name = body['OperatorName']
        workflow_id = body['WorkflowId']
        results = json.loads(json.dumps(body['Results']), parse_float=Decimal)
    except KeyError as e:
        log_exception_while_storing_metadata_for_asset(asset, e)
        raise BadRequestError("Missing required inputs for storing metadata: {e}".format(e=e))
    except Exception as e:
        log_exception_while_storing_metadata_for_asset(asset, e)
        raise ChaliceViewError("Unknown exception when storing asset metadata: {e}".format(e=e))
    else:
        # check that results is dict
        if not isinstance(results, dict):
            logger.error("Exception occurred while storing metadata for {asset}".format(asset=asset))
            raise BadRequestError(
                "Exception occurred while storing metadata for {asset}: results are not the required data type, dict".format(
                    asset=asset))
        else:
            logger.info("Storing metadata for {asset}".format(asset=asset))

    return operator_name, workflow_id, results


# Verify asset exists before adding metadata and check if pointers exist for this operator
def get_pointers_for_operator(asset, operator_name):
    asset_item = read_asset_from_db(asset)

    try:
        pointers = asset_item[operator_name]
    except KeyError:
        logger.info("No pointers have been stored for this operator")
        pointers = []
    else:
        logger.info("Retrieved existing pointers")

    return pointers


@app.route('/metadata/{asset_id}', cors=True, methods=['POST'], authorizer=authorizer)
def put_asset_metadata(asset_id):
    """
    Adds operation metadata for an asset.

    If the results are in a paginated format, such as from Rekognition, you must set the paginate query param to
    "true" for each page of metadata a put metadata call is made for. For the final page of results,
    the "end" query param must be set to "true", which will tell the dataplane that the paginated session is
    over and update the pointer for that metadata type.

    Query String Params:
    :param paginate: Boolean to tell dataplane that the results will come in as pages.
    :param end: Boolean to declare the last page in a set of paginated results.

    Body:

    .. code-block:: python

        {
            "OperatorName": "{some_operator}",
            "Results": "{json_formatted_results}",
            "WorkflowId": "workflow-id"
        }

    Returns:

        Dictionary containing the status of the PUT metadata operation. If a pointer is updated, the response will also
        include the S3 Bucket and S3 Key that the data was written to.

        .. code-block:: python

            {
                "Status": "$status", "Bucket": $bucket, "Key": $metadata_key
            }

    Raises:
        BadRequestError - 400
        ChaliceViewError - 500
    """

    # TODO: Maybe add some enforcement around only being able to end paginated calls if called from the same workflow

    bucket = dataplane_s3_bucket
    asset = asset_id

    body = json.loads(app.current_request.raw_body.decode())
    query_params = app.current_request.query_params

    paginated, end_pagination = parse_paginate_settings(query_params)

    operator_name, workflow_id, results = parse_operator_workflow_and_result_from_body(body, asset)

    # Key that we'll write the results too
    metadata_key = base_s3_uri + asset + '/' + 'workflows' + '/' + workflow_id + '/' + operator_name + '.json'

    # Verify asset exists before adding metadata and check if pointers exist for this operator

    # TODO: This check happens every time we have an additional call when storing paginated results,
    #  could likely refactor this to avoid that

    pointers = get_pointers_for_operator(asset, operator_name)

    # We wont update dynamo unless we successfully write to s3

    wrote_to_s3 = False

    # write results to s3

    str_page = ''
    str_paginated = ''

    if paginated:
        str_page = ' page'
        str_paginated = ' paginated'

        # Check if the operator already generated metadata in this workflow execution
        check_existing = read_metadata_from_s3(bucket, metadata_key)
        if check_existing['Status'] == 'Error':
            # Write the first page directly, format it as a list
            logger.info("Operator has not stored results during this worfklow execution, writing first page to S3")
            formatted_result = [results]
            # Overwrite results so it will get written to s3
            results = formatted_result
        else:
            # Pull in the existing metadata
            existing_results = json.loads(check_existing['Object'])
            # Append new data
            existing_results.append(results)
            # Overwrite results so it will get written back to s3
            results = existing_results

    store_results = write_metadata_to_s3(bucket, metadata_key, results)
    if store_results['Status'] == 'Success':
        logging.info(
            'Wrote {operator} metadata{page} to S3 for asset: {asset}'.format(asset=asset, operator=operator_name, page=str_page))
        wrote_to_s3 = True
    else:
        logging.error('Unable to write{paginated} metadata to s3 for asset: {asset}'.format(asset=asset, paginated=str_paginated))
        raise ChaliceViewError("Exception occurred while writing metadata to s3: {e}".format(e=store_results["Message"]))

    # Update pointer for results
    return update_pointer_for_operator(asset, operator_name, pointers, workflow_id, metadata_key,
                                       paginated, end_pagination, wrote_to_s3)


def update_pointer_for_operator(asset, operator_name, pointers, workflow_id, metadata_key,
                                paginated, end_pagination, wrote_to_s3):
    bucket = dataplane_s3_bucket
    table_name = dataplane_table_name

    # We only update pointer for results if all the pages are written successfully
    if not paginated and wrote_to_s3 or end_pagination and wrote_to_s3:
        # update the pointer list in dynamo

        # we store pointers as list to keep reference of results from different executions for the same operator

        pointer = {"workflow": workflow_id, "pointer": metadata_key}
        pointers.insert(0, pointer)

        update_expression = "SET #operator_result = :result"
        expression_attr_name = {"#operator_result": operator_name}
        expression_attr_val = {":result": pointers}

        try:
            table = dynamo_resource.Table(table_name)
            table.update_item(
                Key={
                    "AssetId": asset
                },
                UpdateExpression=update_expression,
                ExpressionAttributeNames=expression_attr_name,
                ExpressionAttributeValues=expression_attr_val,
            )
        except ClientError as e:
            error = e.response['Error']['Message']
            logger.error("Exception occurred during metadata pointer update: {e}".format(e=error))
            raise ChaliceViewError("Unable to update metadata pointer: {e}".format(e=error))
        except Exception as e:
            logger.error("Exception updating pointer in dynamo {e}".format(e=e))
            raise ChaliceViewError(format_exception(e))
        else:
            logger.info("Successfully stored {operator} metadata for asset: {asset} in the dataplane".format(
                operator=operator_name, asset=asset))
            return {"Status": "Success", "Bucket": bucket, "Key": metadata_key}
    elif paginated and not end_pagination and wrote_to_s3:
        return {"Status": "Success"}
    else:
        return {"Status": "Failed"}


@app.route('/metadata/{asset_id}', cors=True, methods=['GET'], authorizer=authorizer)
def get_asset_metadata(asset_id):
    """
    Retrieves all of the metadata for a specified asset.

    The first call to this method will return a dictionary containing the asset_id, a results key containing
    global asset information, and a cursor to iterate through each stored metadata type.

    To receive the additional metadata, make additional calls to this endpoint and pass in the value of the cursor
    response key as the value for the cursor query parameter.

    Once all results have been retrieved, no cursor key will be present in the response.

    Returns:
        All asset metadata

        .. code-block:: python

            {
                "asset_id": asset_id,
                "operator": operator_name,
                "cursor": encoded_cursor_value,
                "results": global_asset_info (if first call) / operator metadata
            }

    Raises:
        ChaliceViewError - 500
    """

    logging.info("Returning all metadata for asset: {asset_id}".format(asset_id=asset_id))

    def create_response(asset_id, results, remaining, operator_name=None):
        response = {"asset_id": asset_id}

        if operator_name:
            response["operator"] = operator_name

        if remaining:
            next_page = remaining[0]
            next_page["page"] = 0
            new_cursor = build_cursor_object(next_page, remaining)

            # Add page cursor to the response
            response["cursor"] = encode_cursor(new_cursor)

        response["results"] = results

        return response

    # Check if cursor is present, if not this is the first request

    query_params = app.current_request.query_params

    first_call = query_params is None

    if first_call:
        asset_attributes = read_asset_from_db(asset_id)

        # TODO: Should clarify varaible names for first page in the context of the
        #  entire request vs. a page for a specific operator
        global_attributes = ['MediaType', 'S3Key', 'S3Bucket', 'AssetId', 'Created']
        remaining_attributes = list(set(asset_attributes.keys()) - set(global_attributes))

        global_asset_info = dict([(attr, asset_attributes[attr]) for attr in global_attributes if attr != "AssetId"])

        remaining = [{attr: asset_attributes[attr][0]["pointer"]}
                     for attr in remaining_attributes
                     if attr not in ("Locked", "LockedAt", "LockedBy")]

        # Create the response
        response = create_response(asset_id, global_asset_info, remaining)

        return response

    cursor = query_params['cursor']
    decoded_cursor = decode_cursor(cursor)
    operator_name = [k for k in decoded_cursor["next"].keys() if k != "page"][0]
    pointer = decoded_cursor["next"][operator_name]
    page_num = decoded_cursor["next"]["page"]
    remaining = decoded_cursor["remaining"]

    # TODO: Add error handling for s3 call
    s3_object = read_metadata_from_s3(dataplane_s3_bucket, pointer)

    operator_metadata = json.loads(s3_object["Object"])
    if is_metadata_list(operator_metadata):
        next_page_num = page_num + 1

        page_data = operator_metadata[page_num]

        if next_page_valid(operator_metadata, next_page_num):
            next_page = {operator_name: pointer, "page": next_page_num}
            new_cursor = build_cursor_object(next_page, remaining)
            response = {"asset_id": asset_id, "operator": operator_name,
                        "cursor": encode_cursor(new_cursor),
                        "results": page_data}
        else:
            del remaining[0]
            response = create_response(asset_id, page_data, remaining, operator_name=operator_name)

        return response

    page = operator_metadata

    del remaining[0]
    response = create_response(asset_id, page, remaining, operator_name=operator_name)

    return response


# TODO: I need to do some bugfixing, this method works but I think I'm sending the last page back twice
@app.route('/metadata/{asset_id}/{operator_name}', cors=True, methods=['GET'], authorizer=authorizer)
def get_asset_metadata_operator(asset_id, operator_name):
    """
    Retrieves specified operator metadata for a given asset.

    If the results are paginated, the first call to this method will include a cursor in the response.

    To receive the remaining paginated data, make additional calls to this endpoint and pass in the value of the cursor
    response key as the value for the cursor query parameter.

    Once all results have been retrieved, no cursor key will be present in the response.

    Returns:

        Metadata that a specific operator created

        .. code-block:: python

            {
                "asset_id": asset_id,
                "operator": operator_name,
                "cursor": encoded_cursor_value,
                "results": first_page_data
            }

    Raises:
        ChaliceViewError - 500
    """
    logging.info(
        "Returning {operator} metadata for asset: {asset_id}".format(asset_id=asset_id, operator=operator_name))

    # Check if cursor is present, if not this is the first request

    first_call = app.current_request.query_params is None

    if first_call:
        projection_expression = "#attr"
        expression_attribute_names = {"#attr": operator_name}
        asset_attributes = read_asset_from_db(
            asset_id,
            ProjectionExpression=projection_expression,
            ExpressionAttributeNames=expression_attribute_names
        )

        pointer = asset_attributes[operator_name][0]["pointer"]
        s3_object = read_metadata_from_s3(dataplane_s3_bucket, pointer)
        # TODO: Add error handling for s3 call
        operator_metadata = json.loads(s3_object["Object"])
        if is_metadata_list(operator_metadata):
            first_page_num = 0
            next_page_num = first_page_num + 1

            first_page_data = operator_metadata[first_page_num]

            if next_page_valid(operator_metadata, next_page_num):
                next_page = {operator_name: pointer, "page": next_page_num}
                # TODO: Do I really need this for getting results of a specific operator?
                remaining = [operator_name]
                new_cursor = build_cursor_object(next_page, remaining)
                response = {"asset_id": asset_id, "operator": operator_name,
                            "cursor": encode_cursor(new_cursor),
                            "results": first_page_data}
            else:
                response = {"asset_id": asset_id, "operator": operator_name, "results": first_page_data}
        else:
            page = operator_metadata
            response = {"asset_id": asset_id, "operator": operator_name, "results": page}

        return response

    cursor = app.current_request.query_params['cursor']
    decoded_cursor = decode_cursor(cursor)

    pointer = decoded_cursor["next"][operator_name]
    page_num = decoded_cursor["next"]["page"]

    next_page_num = page_num + 1

    # TODO: Add error handling for s3 call
    s3_object = read_metadata_from_s3(dataplane_s3_bucket, pointer)

    operator_metadata = json.loads(s3_object["Object"])
    page_data = operator_metadata[page_num]

    if next_page_valid(operator_metadata, next_page_num) is True:
        next_page = {operator_name: pointer, "page": next_page_num}
        remaining = [operator_name]
        new_cursor = build_cursor_object(next_page, remaining)
        response = {"asset_id": asset_id, "operator": operator_name,
                    "cursor": encode_cursor(new_cursor), "results": page_data}
    else:
        response = {"asset_id": asset_id, "operator": operator_name, "results": page_data}

    return response


@app.route('/checkout/{asset_id}', cors=True, methods=['POST'], authorizer=authorizer)
def lock_asset(asset_id):
    """
    Adds LockedAt and LockedBy attributes to an asset item in the Dataplane table.
    This is intended to help applications implement mutual exclusion between users that
    can modify asset data.

    Body:

    .. code-block:: python

        {
            "LockedBy": "{some_user_id}"
        }

    Returns:

        Dictionary of lock info added to the asset.

        .. code-block:: python

            {
                "AssetId": asset_id,
                "LockedBy": user_name,
                "LockedAt": timestamp
            }

    Raises:
        BadRequestError - 400
        ChaliceViewError - 500
    """
    asset = asset_id
    user_name = (json.loads(app.current_request.raw_body.decode())['LockedBy'])
    timestamp = int(datetime.datetime.now().timestamp())

    try:
        logger.info("Attempting to record a lock for asset {asset} by user {user_name} at time {timestamp}".format(asset=asset, user_name=user_name, timestamp=timestamp))
        response = dynamo_client.update_item(
            TableName=dataplane_table_name,
            Key={'AssetId': {'S': asset}},
            UpdateExpression='set Locked = :locked, LockedBy = :lockedby, LockedAt = :timestamp',
            ExpressionAttributeValues={':locked': {'S': 'true'}, ':lockedby': {'S': user_name}, ':timestamp': {'N': str(timestamp)}},
            ConditionExpression='attribute_not_exists(LockedBy) and attribute_not_exists(LockedAt)'
        )
        logger.info("Update item response code: " + str(response['ResponseMetadata']['HTTPStatusCode']))
    except ClientError as e:
        error = e.response['Error']['Message']
        logger.error("Exception occurred during request to lock asset: {e}".format(e=error))
        raise ChaliceViewError("Unable to lock asset: {e}".format(e=error))
    except Exception as e:
        logger.error("Exception locking asset {e}".format(e=e))
        raise ChaliceViewError(format_exception(e))
    else:
        logger.info("Successfully recorded lock for asset {asset} by user {user_name} at time {timestamp}".format(asset=asset, user_name=user_name, timestamp=timestamp))
        return {'AssetId': asset, 'LockedBy': user_name, 'LockedAt': timestamp}


@app.route('/checkin/{asset_id}', cors=True, methods=['POST'], authorizer=authorizer)
def unlock_asset(asset_id):
    """
    Removes LockedAt and LockedBy attributes from an asset item in the Dataplane table.
    This is intended to help applications implement mutual exclusion between users that
    can modify asset data.

    Returns:

        Unlocked asset {asset}

    Raises:
        BadRequestError - 400
        ChaliceViewError - 500
    """
    asset = asset_id

    try:
        logger.info("Attempting to remove lock attributes for asset {asset}".format(asset=asset))
        response = dynamo_client.update_item(
            TableName=dataplane_table_name,
            Key={'AssetId': {'S': asset}},
            UpdateExpression='remove Locked, LockedAt, LockedBy',
            ConditionExpression='attribute_exists(Locked) and attribute_exists(LockedBy) and attribute_exists(LockedAt)'
        )
        logger.info("Update item response code: " + str(response['ResponseMetadata']['HTTPStatusCode']))
    except ClientError as e:
        error = e.response['Error']['Message']
        logger.error("Exception occurred during request to unlock asset: {e}".format(e=error))
        raise ChaliceViewError("Unable to unlock asset: {e}".format(e=error))
    except Exception as e:
        logger.error("Exception unlocking asset {e}".format(e=e))
        raise ChaliceViewError(format_exception(e))
    else:
        logger.info("Successfully removed lock attributes for asset {asset}".format(asset=asset))
        return "Unlocked asset {asset}".format(asset=asset)


@app.route('/checkouts', cors=True, methods=['GET'], authorizer=authorizer)
def list_all_locked_assets():
    """
    Returns:
        Dict containing a list of all locked assets with their corresponding LockedBy, LockedAt, and AssetId attributes. The list returns empty if no assets have been locked.

        .. code-block:: python
            {
                "locks": [
                {'LockedAt': 1641411425}, 'AssetId': 'e69ba549-34f3-46f4-882c-6dafc3d74ca6'}, 'LockedBy': 'user1@example.com'}},
                {'LockedAt': 1641411742}, 'AssetId': '1c745641-d9fd-4634-949b-34c9d4b3d847'}, 'LockedBy': 'user2@example.com'}},
                ...
                ]
            }
    Raises:
        ChaliceViewError - 500
    """

    logging.info("Returning a list of all locked assets")
    table_name = dataplane_table_name

    try:
        # Get every row indexed by the GSI.
        #
        #   A scan would be more efficient than query here since the query
        #   has to evaluate the KeyConditionExpression for every row but we've opted
        #   to use query in order to predispose software developers looking here for code
        #   samples, to use query instead of scan, since query is generally more efficient
        #   than scan.
        #
        # response = dynamo_client.scan(
        #     TableName=table_name,
        #     IndexName="LockIndex"
        # )
        response = dynamo_client.query(
            TableName=table_name,
            IndexName="LockIndex",
            KeyConditionExpression='Locked=:locked',
            ExpressionAttributeValues={":locked": {"S": "true"}}
        )
        data = response['Items']
    except ClientError as e:
        error = e.response['Error']['Message']
        logger.error("Exception occurred during request to list locked assets: {e}".format(e=error))
        raise ChaliceViewError("Unable to list locked assets: {e}".format(e=error))
    except Exception as e:
        logger.error("Exception listing locked assets {e}".format(e=e))
        raise ChaliceViewError(format_exception(e))
    else:
        locks = []
        if len(data) > 0:
            logger.info("Retrieved " + str(len(data)) + " locked assets from the dataplane.")
            for item in data:
                locks.append({
                    "AssetId": item['AssetId'].get('S'),
                    "LockedBy": item['LockedBy'].get('S'),
                    "LockedAt": item['LockedAt'].get('N')
                })
            logger.info(str(locks))
        else:
            logger.info("There are no locked assets.")
        return {"locks": locks}


@app.route('/metadata', cors=True, methods=['GET'], authorizer=authorizer)
def list_all_assets():
    """
    Returns:
        Dict containing a list of all assets by their asset_id. The list returns empty if no assets have been created.

        .. code-block:: python
            {
                "assets": ["$asset_id_1", "$asset_id_2"...]
            }
    Raises:
        ChaliceViewError - 500
    """

    logging.info("Returning a list of all assets")
    table_name = dataplane_table_name

    try:
        table = dynamo_resource.Table(table_name)
        assets = table.scan(
            Select='SPECIFIC_ATTRIBUTES',
            AttributesToGet=[
                'AssetId',
            ]
        )
    except ClientError as e:
        error = e.response['Error']['Message']
        logger.error("Exception occurred during request to list assets: {e}".format(e=error))
        raise ChaliceViewError("Unable to list assets: {e}".format(e=error))
    except Exception as e:
        logger.error("Exception listing assets {e}".format(e=e))
        raise ChaliceViewError(format_exception(e))
    else:
        if "Items" in assets:
            logger.info("Retrieved assets from the dataplane: {}".format(assets))
            asset_ids = []
            for asset in assets["Items"]:
                asset_ids.append(asset["AssetId"])
            response = {"assets": asset_ids}

            return response
        else:
            logger.info("No assets have been created in the dataplane")
            response = {"assets": ""}
            return response


@app.route('/metadata/{asset_id}/{operator_name}', cors=True, methods=['DELETE'], authorizer=authorizer)
def delete_operator_metadata(asset_id, operator_name):
    """
    Deletes the specified operator metadata from an asset.

    Returns:
        Deletion status from dataplane.
    Raises:
        NotFoundError - 404
        ChaliceViewError - 500
        ...
    """

    # TODO: It would be nice to add functionality for moving an object to glacier or S3 IA instead of a hard delete

    asset = asset_id
    operator = operator_name
    table_name = dataplane_table_name

    update_expression = "REMOVE #operator"
    expression_attr_name = {"#operator": operator}

    try:
        table = dynamo_resource.Table(table_name)
        asset_item = table.update_item(
            Key={
                "AssetId": asset
            },
            UpdateExpression=update_expression,
            ExpressionAttributeNames=expression_attr_name,
            ReturnValues='UPDATED_OLD'
        )
    except ClientError as e:
        error = e.response['Error']['Message']
        logger.error("Exception occurred during request to delete metadata: {e}".format(e=error))
        raise ChaliceViewError("Unable to delete metadata pointer: {e}".format(e=error))
    except Exception as e:
        logger.error("Exception deleting metadata {e}".format(e=e))
        raise ChaliceViewError(format_exception(e))

    logger.info("Successfully deleted {operator} metadata pointer for asset: {asset}".format(
        operator=operator, asset=asset))
    # TODO: How should we delete from S3? Maybe store pointers in a list, element 0 is active...
    #  on delete loop thru list marking each s3 object expired
    try:
        deleted_pointers = asset_item['Attributes'][operator]
    except KeyError:
        logger.error(
            "Execution error occurred during request to delete metadata: pointer does not exist for {operator}".format(
                operator=operator))
        raise NotFoundError(
            "Unable to delete metadata, pointer does not exist for {operator}".format(operator=operator))

    keys = []
    for item in deleted_pointers:
        for pointer in item.values():
            keys.append(pointer)
    delete = delete_s3_objects(keys)
    if delete["Status"] == "Success":
        logger.info(
            "Successfully deleted {operator} metadata for {asset}".format(operator=operator, asset=asset))
        return delete['Message']
    else:
        logger.error("Unable to delete {operator} metadata for {asset}".format(operator=operator, asset=asset))
        raise ChaliceViewError("Unable to delete metadata: {error}".format(error=delete["Message"]))


@app.route('/metadata/{asset_id}', cors=True, methods=['DELETE'], authorizer=authorizer)
def delete_asset(asset_id):
    """
    Deletes an asset and all metadata from the dataplane.

    Returns:
        Deletion status from dataplane.
    Raises:
        ChaliceViewError - 500
    """
    def format_unable_to_delete_asset_error(error):
        logger.error("Exception occurred during request to delete asset: {e}".format(e=error))
        return "Unable to delete asset: {e}".format(e=error)

    asset = asset_id
    table_name = dataplane_table_name

    try:
        table = dynamo_resource.Table(table_name)
        asset_item = table.delete_item(
            Key={
                "AssetId": asset
            },
            ReturnValues="ALL_OLD"
        )
    except ClientError as e:
        error = e.response['Error']['Message']
        raise ChaliceViewError(format_unable_to_delete_asset_error(error))
    except Exception as e:
        logger.error("Exception deleting asset {e}".format(e=e))
        raise ChaliceViewError(format_exception(e))

    try:
        attributes_to_delete = asset_item['Attributes']
    except KeyError as e:
        raise ChaliceViewError(format_unable_to_delete_asset_error(e))

    global_attributes = ['MediaType', 'S3Key', 'S3Bucket', 'AssetId', 'Created']
    remaining_attributes = list(set(attributes_to_delete.keys()) - set(global_attributes))

    # Build list of all s3 objects that the asset had pointers to
    keys = []
    for attr in remaining_attributes:
        attr_pointers = attributes_to_delete[attr]
        for item in attr_pointers:
            for pointer in item.values():
                keys.append(pointer)
    keys.append(attributes_to_delete['S3Key'])

    # Delete all the objects from S3
    logger.info("Deleting the metadata objects from s3")
    delete = delete_s3_objects(keys)
    if delete["Status"] == "Success":
        # Now delete the assets directory
        logger.info("Deleted metadata objects from s3")
        asset_path = base_s3_uri + asset_id + '/'
        try:
            logger.info("Cleaning up asset directory after metadata deletion")
            s3_resource.Object(dataplane_s3_bucket, asset_path).delete()
        except ClientError as e:
            error = e.response['Error']['Message']
            raise ChaliceViewError(format_unable_to_delete_asset_error(error))

        logger.info(
            "Successfully deleted asset: {asset} from the dataplane".format(asset=asset))
        return "Deleted asset: {asset} from the dataplane".format(asset=asset)

    logger.error("Unable to delete asset: {asset}".format(asset=asset))
    raise ChaliceViewError(
        "Unable to delete asset from the dataplane: {error}".format(error=delete["Message"]))
