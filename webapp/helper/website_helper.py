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


def perform_variable_replacement(event, context, old_variables, new_variables, bucket, key):
    file_to_search = read_from_s3(event, context, bucket, key)
    for k, v in old_variables.items():
        LOGGER.info("Searching for the following variable: {k}".format(k=k))
        if v in file_to_search:
            LOGGER.info("Replacing {k}: {ov}  with: {nv}".format(k=key, ov=v, nv=new_variables[k]))
            file_to_search = file_to_search.replace(v, new_variables[k])
            write_to_s3(event, context, bucket, key, file_to_search)
        else:
            pass


def retrieve_compiled_env_variables(event, context, source_bucket, source_key):
    env_key = source_key + '/' + '.env'
    env_file = read_from_s3(event, context, source_bucket, env_key)
    try:
        vars_to_replace = {}
        for item in env_file.split('\n'):
            if item != '' and not item.startswith('#'):
                vars_to_replace[item.split('=')[0]] = item.split('=')[1]
            else:
                pass
    except Exception as e:
        LOGGER.info('Unable to determine what variables to replace: {e}'.format(e=e))
        send_response(event, context, "FAILED",
                      {"Unable to determine what variables to replace"})
    else:
        LOGGER.info("Retrieved the existing variables: {k}".format(k=vars_to_replace))
        return vars_to_replace


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
                new_variables = {"VUE_APP_ELASTICSEARCH_ENDPOINT": elastic, "VUE_APP_WORKFLOW_API_ENDPOINT": workflow,
                                 "VUE_APP_DATAPLANE_API_ENDPOINT": dataplane, "VUE_APP_DATAPLANE_BUCKET": dataplane_bucket, "VUE_APP_AWS_REGION": region, "VUE_APP_USER_POOL_ID": user_pool_id, "VUE_APP_USER_POOL_CLIENT_ID": client_id, "VUE_APP_IDENTITY_POOL_ID": identity_id}
                old_variables = retrieve_compiled_env_variables(event, context, source_bucket, source_key)
                replace_env_variables = True
                LOGGER.info(
                    "New variables: {v}".format(v=new_variables))

                deployment_bucket = s3.Bucket(website_bucket)

                objects = s3.Bucket(name=source_bucket).objects.filter(Prefix='{k}/'.format(k=source_key))

                for s3_object in objects:
                    old_key = s3_object.key
                    LOGGER.info(old_key)
                    file_type = old_key.split('.')[-1]
                    try:
                        new_key = old_key.split('website/')[1]
                    # Only pickup items under the "website" prefix
                    except IndexError:
                        pass
                    else:
                        source = {"Bucket": source_bucket, "Key": old_key}
                        deployment_bucket.copy(source, '{key}'.format(key=new_key))
                        if replace_env_variables is True and file_type == "js":
                            perform_variable_replacement(event, context, old_variables, new_variables, website_bucket, new_key)
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
