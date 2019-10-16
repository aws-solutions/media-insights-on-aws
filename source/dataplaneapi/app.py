# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from chalice import Chalice
from chalice import NotFoundError, BadRequestError, ChaliceViewError, CognitoUserPoolAuthorizer
from botocore.client import ClientError
from decimal import Decimal
from botocore.config import Config

import boto3
import os
import uuid
import json
import logging
import datetime
import base64

# TODO: Add additional exception and response codes
# TODO: Narrow exception scopes
# TODO: Better way to bubble exceptions to lambda helper class
# TODO: Normalize pattern for referencing URI params inside a function
# TODO: Move global_attributes list to a top level variable

'''
except ClientError as e:
    print(e.response['Error']['Message'])
'''

formatter = logging.Formatter('{%(pathname)s:%(lineno)d} %(levelname)s - %(message)s')
handler = logging.StreamHandler()
handler.setFormatter(formatter)

logger = logging.getLogger('boto3')
logger.setLevel(logging.INFO)
logger.addHandler(handler)

app_name = 'dataplaneapi'
app = Chalice(app_name=app_name)

# DDB resources
dataplane_table_name = os.environ['DATAPLANE_TABLE_NAME']
dynamo_client = boto3.client('dynamodb')
dynamo_resource = boto3.resource('dynamodb')

# S3 resources
dataplane_s3_bucket = os.environ['DATAPLANE_BUCKET']

# Cognito resources
# From cloudformation stack
cognito_user_pool_arn = os.environ['USER_POOL_ARN']

# TODO: Should we add a variable for the upload bucket?

base_s3_uri = 'private/assets/'
s3_client = boto3.client('s3')
s3_resource = boto3.resource('s3')

authorizer = CognitoUserPoolAuthorizer(
    'MieUserPool', header='Authorization',
    provider_arns=[cognito_user_pool_arn])


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
        logger.info("Exception occurred while writing asset metadata to s3: {e}".format(e=error))
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
        logger.info("Exception occurred while reading asset metadata from s3: {e}".format(e=error))
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
        logger.info("Exception occurred while deleting asset metadata from s3: {e}".format(e=error))
        return {"Status": "Error", "Message": error}
    except Exception as e:
        logger.error("Exception occurred while deleting asset metadata from s3")
        return {"Status": "Error", "Message": e}
    else:
        return {"Status": "Success", "Message": response}


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
    if isinstance(metadata, list):
        return True
    else:
        return False


def next_page_valid(metadata, page_num):
    try:
        page = metadata[page_num]
        return True
    except IndexError:
        return False


# @app.lambda_function()
# def hello_world_function():
#     return {"Message": "Hello World!"}

@app.route('/')
def index():
    return {'hello': 'world'}


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
    print('/upload request: '+app.current_request.raw_body.decode())
    region = os.environ['AWS_REGION']
    s3 = boto3.client('s3', region_name=region, config = Config(signature_version = 's3v4', s3={'addressing_style': 'virtual'}))
    # limit uploads to 5GB
    max_upload_size = 5368709120
    try:
        response = s3.generate_presigned_post(
            Bucket=(app.current_request.json_body['S3Bucket']),
            Key=(app.current_request.json_body['S3Key']),
            Conditions=[["content-length-range", 0, max_upload_size ]],
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
    print('/download request: '+app.current_request.raw_body.decode())
    s3 = boto3.client('s3')
    # expire the URL in
    try:
        response = s3.generate_presigned_url('get_object',
                                             Params={'Bucket': app.current_request.json_body['S3Bucket'],
                                                     'Key': app.current_request.json_body['S3Key']},
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
                "S3Bucket": "{somenbucket}",
                "S3Key": "{somekey}"
            }
        }

    Returns:
        A dict containing the asset id and the location of the media object in the dataplane.
         .. code-block:: python

            {
                "AssetId": asset_id,
                "S3Bucket": dataplane_s3_bucket,
                "S3Key": key
            }
    Raises:
        ChaliceViewError - 500
    """

    table_name = dataplane_table_name
    bucket = dataplane_s3_bucket
    uri = base_s3_uri

    asset = app.current_request.json_body
    logger.info(asset)

    # create a uuid for the asset

    asset_id = str(uuid.uuid4())

    # check required inputs

    try:
        source_key = asset['Input']['S3Key']
        source_bucket = asset['Input']['S3Bucket']
    except KeyError as e:
        logger.error("Exception occurred during asset creation: {e}".format(e=e))
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
        logger.error("Exception occurred during asset creation: {e}".format(e=error))
        raise ChaliceViewError("Unable to create asset directory in the dataplane bucket: {e}".format(e=error))
    except Exception as e:
        logger.error("Exception occurred during asset creation: {e}".format(e=e))
        raise ChaliceViewError("Exception when creating dynamo item for asset: {e}".format(e=e))
    else:
        logger.info("Created asset directory structure: {directory}".format(directory=directory))

    # build key for new s3 object

    new_key = directory + 'input' + '/' + source_key

    # copy input media into newly created dataplane s3 directory

    try:
        s3_client.copy_object(
            Bucket=dataplane_s3_bucket,
            Key=new_key,
            CopySource={'Bucket': source_bucket, 'Key': source_key}
        )
    except ClientError as e:
        error = e.response['Error']['Message']
        logger.error("Exception occurred during asset creation: {e}".format(e=error))
        raise ChaliceViewError("Unable to copy input media to the dataplane bucket: {e}".format(e=error))
    except Exception as e:
        logger.error("Exception occurred during asset creation: {e}".format(e=e))
        raise ChaliceViewError("Exception when creating s3 object for asset: {e}".format(e=e))
    else:
        logger.info("Copied input media into dataplane bucket: {key}".format(key=new_key))

    # build ddb item of the asset

    ts = str(datetime.datetime.now().timestamp())

    try:
        table = dynamo_resource.Table(table_name)
        table.put_item(
            Item={
                "AssetId": asset_id,
                "S3Bucket": dataplane_s3_bucket,
                "S3Key": new_key,
                "Created": ts
            }
        )
    except ClientError as e:
        error = e.response['Error']['Message']
        logger.error("Exception occurred during asset creation: {e}".format(e=error))
        raise ChaliceViewError("Unable to create asset item in dynamo: {e}".format(e=error))
    except Exception as e:
        logger.error("Exception occurred during asset creation: {e}".format(e=e))
        raise ChaliceViewError("Exception when creating dynamo item for asset: {e}".format(e=e))
    else:
        logger.info("Completed asset creation for asset: {asset}".format(asset=asset_id))
        return {"AssetId": asset_id, "S3Bucket": dataplane_s3_bucket, "S3Key": new_key}


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
    table_name = dataplane_table_name
    asset = asset_id

    body = app.current_request.json_body
    query_params = app.current_request.query_params

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

    try:
        operator_name = body['OperatorName']
        workflow_id = body['WorkflowId']
        results = json.loads(json.dumps(body['Results']), parse_float=Decimal)
    except KeyError as e:
        logger.error("Exception occurred while storing metadata for {asset}: {e}".format(asset=asset, e=e))
        raise BadRequestError("Missing required inputs for storing metadata: {e}".format(e=e))
    except Exception as e:
        logger.error("Exception occurred while storing metadata for {asset}: {e}".format(asset=asset, e=e))
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

    # Key that we'll write the results too
    metadata_key = base_s3_uri + asset + '/' + 'workflows' + '/' + workflow_id + '/' + operator_name + '.json'

    # Verify asset exists before adding metadata and check if pointers exist for this operator

    # TODO: This check happens every time we have an additional call when storing paginated results,
    #  could likely refactor this to avoid that

    try:
        table = dynamo_resource.Table(table_name)
        response = table.get_item(
            Key={
                "AssetId": asset
            }
        )
    except ClientError as e:
        error = e.response['Error']['Message']
        logger.error("Exception occurred while storing metadata for {asset}: {e}".format(asset=asset, e=error))
        raise ChaliceViewError("Exception occurred while verifying asset exists: {e}".format(e=error))
    except Exception as e:
        logger.error("Exception occurred while storing metadata for {asset}: {e}".format(asset=asset, e=e))
        raise ChaliceViewError("Exception occurred while verifying asset exists: {e}".format(e=e))
    else:
        if 'Item' not in response:
            raise NotFoundError(
                "Exception occurred while verifying asset exists: {asset} does not exist".format(asset=asset))
        else:
            try:
                pointers = response['Item'][operator_name]
            except KeyError:
                logger.info("No pointers have been stored for this operator")
                pointers = []
            else:
                logger.info("Retrieved existing pointers")

    # We wont update dynamo unless we successfully write to s3

    wrote_to_s3 = False

    # write results to s3

    if paginated:
        # Check if the operator already generated metadata in this workflow execution
        check_existing = read_metadata_from_s3(bucket, metadata_key)
        if check_existing['Status'] == 'Error':
            # Write the first page directly, format it as a list
            logger.info("Operator has not stored results during this worfklow execution, writing first page to S3")
            formatted_result = [results]
            store_results = write_metadata_to_s3(bucket, metadata_key, formatted_result)
            if store_results['Status'] == 'Success':
                logging.info(
                    'Wrote {operator} metadata page to s3 for asset: {asset}'.format(asset=asset, operator=operator_name))
                wrote_to_s3 = True
            else:
                logging.error('Unable to write paginated metadata to s3 for asset: {asset}'.format(asset=asset))
                raise ChaliceViewError("Exception occurred while writing metadata to s3: {e}".format(e=store_results["Message"]))
        else:
            # Pull in the existing metadata
            existing_results = json.loads(check_existing['Object'])
            # Append new data
            existing_results.append(results)
            # Write back to s3
            store_results = write_metadata_to_s3(bucket, metadata_key, existing_results)
            if store_results['Status'] == 'Success':
                logging.info(
                    'Wrote {operator} metadata page to S3 for asset: {asset}'.format(asset=asset, operator=operator_name))
                wrote_to_s3 = True
            else:
                logging.error('Unable to write paginated metadata to s3 for asset: {asset}'.format(asset=asset))
                raise ChaliceViewError("Exception occurred while writing metadata to s3: {e}".format(e=store_results["Message"]))
    else:
        store_results = write_metadata_to_s3(bucket, metadata_key, results)
        if store_results['Status'] == 'Success':
            logging.info(
                'Wrote {operator} metadata to S3 for asset: {asset}'.format(asset=asset, operator=operator_name))
            wrote_to_s3 = True
        else:
            logging.error('Unable to write metadata to s3 for asset: {asset}'.format(asset=asset))
            raise ChaliceViewError(
                "Exception occurred while writing metadata to s3: {e}".format(e=store_results["Message"]))

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
            raise ChaliceViewError("Exception: {e}".format(e=e))
        else:
            logger.info("Successfully stored {operator} metadata for asset: {asset} in the dataplane".format(
                operator=operator_name, asset=asset_id))
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
    table_name = dataplane_table_name

    # Check if cursor is present, if not this is the first request

    query_params = app.current_request.query_params

    if query_params is None:
        first_call = True
    else:
        # TODO: Do I want to add another check here?
        cursor = app.current_request.query_params['cursor']
        first_call = False

    if first_call is True:
        try:
            table = dynamo_resource.Table(table_name)
            asset_item = table.get_item(
                Key={
                    'AssetId': asset_id
                }
            )
        except ClientError as e:
            error = e.response['Error']['Message']
            logger.error("Exception occurred while retreiving metadata for {asset}: {e}".format(asset=asset_id, e=error))
            raise ChaliceViewError("Unable to retrieve metadata: {e}".format(e=error))
        except Exception as e:
            logger.error(
                "Exception occurred while retreiving metadata for {asset}: {e}".format(asset=asset_id, e=e))
            raise ChaliceViewError("Unable to retrieve metadata: {e}".format(e=e))
        else:
            # TODO: Should clarify varaible names for first page in the context of the
            #  entire request vs. a page for a specific operator
            if "Item" in asset_item:
                asset_attributes = asset_item["Item"]
                global_attributes = ['S3Key', 'S3Bucket', 'AssetId', 'Created']
                remaining_attributes = list(set(asset_attributes.keys()) - set(global_attributes))
                remaining = []

                global_asset_info = {}

                for attr in global_attributes:
                    if attr == "AssetId":
                        pass
                    else:
                        global_asset_info[attr] = asset_attributes[attr]

                if not remaining_attributes:
                    response = {"asset_id": asset_id, "results": global_asset_info}

                else:
                    for attr in remaining_attributes:
                        attr_name = attr
                        attr_pointer = asset_attributes[attr_name][0]["pointer"]
                        remaining.append({attr_name: attr_pointer})

                    next = remaining[0]
                    next["page"] = 0

                    new_cursor = build_cursor_object(next, remaining)

                    # TODO: Maybe return the list of attributes in the response?
                    response = {"asset_id": asset_id,
                                "cursor": encode_cursor(new_cursor),
                                "results": global_asset_info}

                return response
    else:
        decoded_cursor = decode_cursor(cursor)
        # TODO: Can probably move this to an ordered dict, but this works for now
        operator_name = list(decoded_cursor["next"].keys())[0]
        pointer = decoded_cursor["next"][operator_name]
        page_num = decoded_cursor["next"]["page"]
        remaining = decoded_cursor["remaining"]

        s3_object = read_metadata_from_s3(dataplane_s3_bucket, pointer)
        # TODO: Add error handling for s3 call
        operator_metadata = json.loads(s3_object["Object"])
        if is_metadata_list(operator_metadata) is True:
            next_page_num = page_num + 1

            page_data = operator_metadata[page_num]

            if next_page_valid(operator_metadata, next_page_num) is True:
                next = {operator_name: pointer, "page": next_page_num}
                new_cursor = build_cursor_object(next, remaining)
                response = {"asset_id": asset_id, "operator": operator_name,
                            "cursor": encode_cursor(new_cursor),
                            "results": page_data}
            else:
                del remaining[0]

                if not remaining:
                    response = {"asset_id": asset_id, "operator": operator_name,
                                "results": page_data}
                else:
                    next = remaining[0]
                    next["page"] = 0
                    new_cursor = build_cursor_object(next, remaining)
                    response = {"asset_id": asset_id, "operator": operator_name, "cursor": encode_cursor(new_cursor),
                                "results": page_data}
            return response
        else:
            page = operator_metadata

            del remaining[0]

            if not remaining:
                response = {"asset_id": asset_id, "operator": operator_name,
                            "results": page}

            else:
                next = remaining[0]
                next["page"] = 0
                new_cursor = build_cursor_object(next, remaining)
                response = {"asset_id": asset_id, "operator": operator_name, "cursor": encode_cursor(new_cursor),
                            "results": page}
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
    table_name = dataplane_table_name

    # Check if cursor is present, if not this is the first request

    if app.current_request.query_params is None:
        first_call = True
    else:
        # TODO: Do I want to add another check here?
        cursor = app.current_request.query_params['cursor']
        first_call = False

    if first_call is True:
        projection_expression = "#attr"
        expression_attribute_names = {"#attr": operator_name}
        try:
            table = dynamo_resource.Table(table_name)
            asset_item = table.get_item(
                Key={
                    'AssetId': asset_id
                },
                ProjectionExpression=projection_expression,
                ExpressionAttributeNames=expression_attribute_names
            )
        except ClientError as e:
            error = e.response['Error']['Message']
            logger.error(
                "Exception occurred while retreiving metadata for {asset}: {e}".format(asset=asset_id, e=error))
            raise ChaliceViewError("Unable to retrieve metadata: {e}".format(e=error))
        except Exception as e:
            logger.error(
                "Exception occurred while retreiving metadata for {asset}: {e}".format(asset=asset_id, e=e))
            raise ChaliceViewError("Unable to retrieve metadata: {e}".format(e=e))
        else:
            if "Item" in asset_item:
                pointer = asset_item["Item"][operator_name][0]["pointer"]
                s3_object = read_metadata_from_s3(dataplane_s3_bucket, pointer)
                # TODO: Add error handling for s3 call
                operator_metadata = json.loads(s3_object["Object"])
                if is_metadata_list(operator_metadata) is True:
                    first_page_num = 0
                    next_page_num = first_page_num + 1

                    first_page_data = operator_metadata[first_page_num]

                    if next_page_valid(operator_metadata, next_page_num) is True:
                        next = {operator_name: pointer, "page": next_page_num}
                        # TODO: Do I really need this for getting results of a specific operator?
                        remaining = [operator_name]
                        new_cursor = build_cursor_object(next, remaining)
                        response = {"asset_id": asset_id, "operator": operator_name,
                                    "cursor": encode_cursor(new_cursor),
                                    "results": first_page_data}
                    else:
                        response = {"asset_id": asset_id, "operator": operator_name, "results": first_page_data}
                    return response
                else:
                    page = operator_metadata
                    response = {"asset_id": asset_id, "operator": operator_name, "results": page}
                    return response
            # TODO: Add else block to handle not finding an item
    else:
        decoded_cursor = decode_cursor(cursor)

        pointer = decoded_cursor["next"][operator_name]
        page_num = decoded_cursor["next"]["page"]

        next_page_num = page_num + 1

        # TODO: Add error handling for s3 call
        s3_object = read_metadata_from_s3(dataplane_s3_bucket, pointer)

        operator_metadata = json.loads(s3_object["Object"])
        page_data = operator_metadata[page_num]

        if next_page_valid(operator_metadata, next_page_num) is True:
            next = {operator_name: pointer, "page": next_page_num}
            remaining = [operator_name]
            new_cursor = build_cursor_object(next, remaining)
            response = {"asset_id": asset_id, "operator": operator_name,
                        "cursor": encode_cursor(new_cursor), "results": page_data}
        else:
            response = {"asset_id": asset_id, "operator": operator_name, "results": page_data}

        return response


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
        raise ChaliceViewError("Exception: {e}".format(e=e))
    else:
        if "Items" in assets:
            logger.info("Retrieved assets from the dataplane: ", assets)
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
        raise ChaliceViewError("Exception: {e}".format(e=e))
    else:
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
        else:
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
        logger.error("Exception occurred during request to delete asset: {e}".format(e=error))
        raise ChaliceViewError("Unable to delete asset: {e}".format(e=error))
    except Exception as e:
        logger.error("Exception deleting asset {e}".format(e=e))
        raise ChaliceViewError("Exception: {e}".format(e=e))
    else:
        try:
            attributes_to_delete = asset_item['Attributes']
        except KeyError as e:
            logger.error("Exception occurred during request to delete asset: {e}".format(e=e))
            raise ChaliceViewError("Unable to delete asset: {e}".format(e=e))
        else:
            global_attributes = ['S3Key', 'S3Bucket', 'AssetId', 'Created']
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
                logger.info("Delete metadata objects from s3")
                bucket = s3_resource.Bucket(dataplane_s3_bucket)
                asset_path = base_s3_uri + asset_id + '/'
                try:
                    logger.info("Cleaning up asset directory after metadata deletion")
                    bucket.objects.filter(Prefix=asset_path).delete()
                except ClientError as e:
                    error = e.response['Error']['Message']
                    logger.error("Exception occurred during request to delete asset: {e}".format(e=error))
                    raise ChaliceViewError("Unable to delete asset: {e}".format(e=error))
                else:
                    logger.info(
                        "Successfully deleted asset: {asset} from the dataplane".format(asset=asset))
                    return "Deleted asset: {asset} from the dataplane".format(asset=asset)
            else:
                logger.error("Unable to delete asset: {asset}".format(asset=asset))
                raise ChaliceViewError(
                    "Unable to delete asset from the dataplane: {error}".format(error=delete["Message"]))
