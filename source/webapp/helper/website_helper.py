import boto3
import json
import logging
import os
from urllib.request import build_opener, HTTPHandler, Request


LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)

s3 = boto3.resource('s3')
s3_client = boto3.client('s3')

replace_env_variables = False


def send_response(event, context, response_status, response_data):
    """
    Send a resource manipulation status response to CloudFormation
    """
    response_body = json.dumps({
        "Status": response_status,
        "Reason": "See the details in CloudWatch Log Stream: " + context.log_stream_name,
        "PhysicalResourceId": context.log_stream_name,
        "StackId": event['StackId'],
        "RequestId": event['RequestId'],
        "LogicalResourceId": event['LogicalResourceId'],
        "Data": response_data
    })

    LOGGER.info('ResponseURL: {s}'.format(s=event['ResponseURL']))
    LOGGER.info('ResponseBody: {s}'.format(s=response_body))

    opener = build_opener(HTTPHandler)
    request = Request(event['ResponseURL'], data=response_body.encode('utf-8'))
    request.add_header('Content-Type', '')
    request.add_header('Content-Length', len(response_body))
    request.get_method = lambda: 'PUT'
    response = opener.open(request)
    LOGGER.info("Status code: {s}".format(s=response.getcode))
    LOGGER.info("Status message: {s}".format(s=response.msg))


def write_to_s3(event, context, bucket, key, body):
    try:
        s3_client.put_object(Bucket=bucket, Key=key, Body=body)
    except Exception as e:
        LOGGER.info('Unable to write file to s3: {e}'.format(e=e))
        send_response(event, context, "FAILED",
                      {"Message": "Failed to write file to s3 after variable replacement"})
    else:
        LOGGER.info('Wrote file back to s3 after variable replacement')


def read_from_s3(event, context, bucket, key):
    try:
        obj = s3_client.get_object(
            Bucket=bucket,
            Key=key
        )
    except Exception as e:
        LOGGER.info(
            'Unable to read key: {key} in from s3 bucket: {bucket}. Error: {e}'.format(e=e, key=key, bucket=bucket))
        send_response(event, context, "FAILED",
                      {"Message": "Failed to read file from s3"})
    else:
        results = obj['Body'].read().decode('utf-8')
        return results


def copy_source(event, context):
    try:
        source_bucket = event["ResourceProperties"]["WebsiteCodeBucket"]
        source_key = event["ResourceProperties"]["WebsiteCodePrefix"]
        website_bucket = event["ResourceProperties"]["DeploymentBucket"].split('.')[0]
    except KeyError as e:
        LOGGER.info("Failed to retrieve required values from the CloudFormation event: {e}".format(e=e))
        send_response(event, context, "FAILED", {"Message": "Failed to retrieve required values from the CloudFormation event"})
    else:
        try:
            LOGGER.info("Checking if custom environment variables are present")

            try:
                elastic = 'https://'+os.environ['ElasticEndpoint']
                dataplane = os.environ['DataplaneEndpoint']
                workflow = os.environ['WorkflowEndpoint']
                dataplane_bucket = os.environ['DataplaneBucket']
                user_pool_id = os.environ['UserPoolId']
                region = os.environ['AwsRegion']
                client_id = os.environ['PoolClientId']
                identity_id = os.environ['IdentityPoolId']
            except KeyError:
                replace_env_variables = False
            else:
                new_variables = {"ELASTICSEARCH_ENDPOINT": elastic, "WORKFLOW_API_ENDPOINT": workflow,
                                 "DATAPLANE_API_ENDPOINT": dataplane, "DATAPLANE_BUCKET": dataplane_bucket, "AWS_REGION": region,
                                 "USER_POOL_ID": user_pool_id, "USER_POOL_CLIENT_ID": client_id, "IDENTITY_POOL_ID": identity_id}
                replace_env_variables = True
                LOGGER.info(
                    "New variables: {v}".format(v=new_variables))

                deployment_bucket = s3.Bucket(website_bucket)

                objects = s3.Bucket(name=source_bucket).objects.filter(Prefix='{k}/'.format(k=source_key))

                for s3_object in objects:
                    old_key = s3_object.key
                    LOGGER.info(old_key)
                    try:
                        new_key = old_key.split('website/')[1]
                    # Only pickup items under the "website" prefix
                    except IndexError:
                        pass
                    else:
                        source = {"Bucket": source_bucket, "Key": old_key}
                        deployment_bucket.copy(source, '{key}'.format(key=new_key))
                        if replace_env_variables is True and new_key == "runtimeConfig.json":
                            LOGGER.info("updating runtimeConfig.json")
                            write_to_s3(event, context, website_bucket, new_key, json.dumps(new_variables))
        except Exception as e:
            LOGGER.info("Unable to copy website source code into the website bucket: {e}".format(e=e))
            send_response(event, context, "FAILED", {"Message": "Unexpected event received from CloudFormation"})
        else:
            send_response(event, context, "SUCCESS",
                          {"Message": "Resource creation successful!"})


def lambda_handler(event, context):
    """
    Handle Lambda event from AWS
    """
    try:
        LOGGER.info('REQUEST RECEIVED:\n {s}'.format(s=event))
        LOGGER.info('REQUEST RECEIVED:\n {s}'.format(s=context))
        if event['RequestType'] == 'Create':
            LOGGER.info('CREATE!')
            copy_source(event, context)
        elif event['RequestType'] == 'Update':
            LOGGER.info('UPDATE!')
            copy_source(event, context)
        elif event['RequestType'] == 'Delete':
            LOGGER.info('DELETE!')
            send_response(event, context, "SUCCESS",
                          {"Message": "Resource deletion successful!"})
        else:
            LOGGER.info('FAILED!')
            send_response(event, context, "FAILED", {"Message": "Unexpected event received from CloudFormation"})
    except Exception as e:
        LOGGER.info('FAILED!')
        send_response(event, context, "FAILED", {"Message": "Exception during processing: {e}".format(e=e)})
