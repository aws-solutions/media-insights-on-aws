import pytest
import boto3
import json
import time
import math
import requests
import urllib3
import logging
from botocore.exceptions import ClientError
import re
import os
from jsonschema import validate

REGION = os.environ['REGION']
BUCKET_NAME = os.environ['BUCKET_NAME']
MIE_STACK_NAME = os.environ['MIE_STACK_NAME']
VIDEO_FILENAME = os.environ['VIDEO_FILENAME']
IMAGE_FILENAME = os.environ['IMAGE_FILENAME']
AUDIO_FILENAME = os.environ['AUDIO_FILENAME']
TEXT_FILENAME = os.environ['TEXT_FILENAME']

def set_max_concurrent_request(stack_resources, max_concurrent):

    headers = {"Content-Type": "application/json"}
    body = {
        "Name":"MaxConcurrentWorkflows",
        "Value": max_concurrent
    } 

    print ("POST /system/configuration {}".format(json.dumps(body)))
    set_configuration_response = requests.post(stack_resources["WorkflowApiEndpoint"]+'/system/configuration', headers=headers, json=body, verify=False)

    return set_configuration_response

def get_configuration_request(stack_resources):
    
    get_configuration_response = requests.get(stack_resources["WorkflowApiEndpoint"]+'/system/configuration', verify=False)

    return get_configuration_response

def create_operation_request(config, stack_resources):
    
    start_lambda = config["Input"]+config["Type"]+config["Status"]+"Lambda"
    
    headers = {"Content-Type": "application/json"}
    body = {
        "StartLambdaArn": stack_resources[start_lambda],
        "Configuration": {
            "MediaType": config["Input"],
            "Enabled": True
        },
        "StateMachineExecutionRoleArn": stack_resources["StepFunctionRole"],
        "Type": config["Type"],
        "Name": config["Name"]
    }   

    if (config["Type"] == "Async"):
        monitor_lambda = config["Input"]+config["Type"]+config["Status"]+"MonitorLambda"
        body["MonitorLambdaArn"] = stack_resources[monitor_lambda]

    if "OutputMediaType" in config:
        body["Configuration"]["OutputMediaType"] = config["OutputMediaType"]

    if "TestCustomConfig" in config:
        body["Configuration"]["TestCustomConfig"] = config["TestCustomConfig"]


    print ("POST /workflow/operation {}".format(json.dumps(body)))
    create_operation_response = requests.post(stack_resources["WorkflowApiEndpoint"]+'/workflow/operation', headers=headers, json=body, verify=False)

    return create_operation_response


def get_operation_request(operation, stack_resources):
    
    get_operation_response = requests.get(stack_resources["WorkflowApiEndpoint"]+'/workflow/operation/'+operation["Name"], verify=False)

    return get_operation_response


def delete_operation_request(operation, stack_resources):
    
    delete_operation_response = requests.delete(stack_resources["WorkflowApiEndpoint"]+'/workflow/operation/'+operation["Name"], verify=False)

    return delete_operation_response


def create_operation_workflow_request(operation, stack_resources):

    headers = {"Content-Type": "application/json"}
    body = {
        "Name":"_testoperation"+operation["Name"],
        "StartAt": operation["StageName"],
        "Stages": {
            operation["StageName"]: {
                "End": True
                
            }
        }
    } 

    print ("POST /workflow {}".format(json.dumps(body)))
    create_workflow_response = requests.post(stack_resources["WorkflowApiEndpoint"]+'/workflow', headers=headers, json=body, verify=False)

    return create_workflow_response



def delete_operation_workflow_request(workflow, stack_resources):
    
    delete_workflow_response = requests.delete(stack_resources["WorkflowApiEndpoint"]+'/workflow/'+workflow["Name"], verify=False)

    return delete_workflow_response


def create_workflow_execution_request(workflow, config, stack_resources):
    
    headers = {"Content-Type": "application/json"}
    
    body = {
        "Name": workflow["Name"],
        "Input": {
            "Media": {
                
            }
        }
        
    }

    if "WorkflowConfiguration" in config:
        body["Configuration"] = config["WorkflowConfiguration"]

    if config["Input"] == "Video":
        body["Input"]["Media"]["Video"] = {}
        body["Input"]["Media"]["Video"]["S3Bucket"] = BUCKET_NAME
        body["Input"]["Media"]["Video"]["S3Key"] = VIDEO_FILENAME
    elif config["Input"] == "Audio": 
        body["Input"]["Media"]["Audio"] = {}
        body["Input"]["Media"]["Audio"]["S3Bucket"] = BUCKET_NAME
        body["Input"]["Media"]["Audio"]["S3Key"] = AUDIO_FILENAME
    elif config["Input"] == "Image": 
        body["Input"]["Media"]["Image"] = {}
        body["Input"]["Media"]["Image"]["S3Bucket"] = BUCKET_NAME
        body["Input"]["Media"]["Image"]["S3Key"] = IMAGE_FILENAME
    elif config["Input"] == "Text": 
        body["Input"]["Media"]["Text"] = {}
        body["Input"]["Media"]["Text"]["S3Bucket"] = BUCKET_NAME
        body["Input"]["Media"]["Text"]["S3Key"] = TEXT_FILENAME

    print ("POST /workflow/execution {}".format(json.dumps(body)))
    
    create_workflow_execution_response = requests.post(stack_resources["WorkflowApiEndpoint"]+'/workflow/execution', headers=headers, json=body, verify=False)

    return create_workflow_execution_response


def wait_for_workflow_execution(workflow_execution, stack_resources, wait_seconds):
    
    # disable unsigned HTTPS certificate warnings
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    workflow_id = workflow_execution['Id']

    # It might take a few seconds for the step function to start, so we'll try to get the execution arn a few times
    # before giving up
    retries=0
    # FIXME retry_limit = ceil(wait_seconds/5)
    retry_limit = 20
    while(retries<retry_limit):
        retries+=1
        print("Checking workflow execution status for workflow {}".format(workflow_id))
        workflow_execution_response = requests.get(stack_resources["WorkflowApiEndpoint"]+'/workflow/execution/'+workflow_id, verify=False)
        workflow_execution = workflow_execution_response.json()
        assert workflow_execution_response.status_code == 200
        if workflow_execution["Status"] in ["Complete", "Error"]:
            break
        time.sleep(5)

    return workflow_execution


def create_stage_request(config, stack_resources):
    
    headers = {"Content-Type": "application/json"}
    body = {
        "Name": config["Name"],
        "Operations": config["Operations"]
    }
        
    print ("POST /workflow/stage {}".format(json.dumps(body)))
    create_stage_response = requests.post(stack_resources["WorkflowApiEndpoint"]+'/workflow/stage', headers=headers, json=body, verify=False)

    return create_stage_response


def get_stage_request(stage, stack_resources):
    
    get_stage_response = requests.get(stack_resources["WorkflowApiEndpoint"]+'/workflow/stage/'+stage["Name"], verify=False)

    return get_stage_response


def delete_stage_request(stage, stack_resources):
    
    delete_stage_response = requests.delete(stack_resources["WorkflowApiEndpoint"]+'/workflow/stage/'+stage["Name"], verify=False)

    return delete_stage_response


def create_stage_workflow_request(stage, stack_resources):

    headers = {"Content-Type": "application/json"}
    body = {
        "Name":"_teststage"+stage["Name"],
        "StartAt": stage["Name"],
        "Stages": {
            stage["Name"]: {
                "End": True
                
            }
        }
    } 

    print ("POST /workflow {}".format(json.dumps(body)))
    create_workflow_response = requests.post(stack_resources["WorkflowApiEndpoint"]+'/workflow', headers=headers, json=body, verify=False)

    return create_workflow_response

def create_workflow_request(workflow_config, stack_resources):

    stages = workflow_config["Stages"]
    headers = {"Content-Type": "application/json"}
    body = {
        "Name": workflow_config["Name"],
        "StartAt": stages[0],
    } 

    workflow_stages = {}
    num_stages = len(stages)
    i = 1
    for stage in stages:
        if i == num_stages:
            workflow_stages[stage] = {
                "End": True
                }
        else:
            workflow_stages[stage] = {
                "Next": stages[i]
                }
        i = i + 1
        
    body["Stages"] = workflow_stages
    
    print ("POST /workflow {}".format(json.dumps(body)))
    create_workflow_response = requests.post(stack_resources["WorkflowApiEndpoint"]+'/workflow', headers=headers, json=body, verify=False)

    return create_workflow_response

def get_workflow_configuration_request(workflow, stack_resources):
    
    get_workflow_configuration_response = requests.get(stack_resources["WorkflowApiEndpoint"]+'/workflow/configuration/'+workflow["Name"], verify=False)

    return get_workflow_configuration_response


def delete_stage_workflow_request(workflow, stack_resources):
    
    delete_workflow_response = requests.delete(stack_resources["WorkflowApiEndpoint"]+'/workflow/'+workflow["Name"], verify=False)

    return delete_workflow_response

# dataplane methods


def create_asset(stack_resources, bucket, key):
    headers = {"Content-Type": "application/json"}
    body = {
        "Input": {
            "S3Bucket": bucket,
            "S3Key": key
        }
    }

    print("POST /create")
    create_asset_response = requests.post(stack_resources["DataplaneApiEndpoint"] + '/create', headers=headers,
                                          json=body, verify=False)
    return create_asset_response


def post_metadata(stack_resources, asset_id, metadata, paginate=False, end=False):
    if paginate is True and end is True:
        url = stack_resources["DataplaneApiEndpoint"] + 'metadata/' + asset_id + "?paginated=true&end=true"
    elif paginate is True and end is False:
        url = stack_resources["DataplaneApiEndpoint"] + 'metadata/' + asset_id + "?paginated=true"
    else:
        url = stack_resources["DataplaneApiEndpoint"] + 'metadata/' + asset_id

    headers = {"Content-Type": "application/json"}
    body = metadata
    print("POST /metadata/{asset}".format(asset=asset_id))
    nonpaginated_metadata_response = requests.post(url, headers=headers, json=body, verify=False)
    return nonpaginated_metadata_response


def get_all_metadata(stack_resources, asset_id, cursor=None):
    if cursor is None:
        url = stack_resources["DataplaneApiEndpoint"] + 'metadata/' + asset_id
    else:
        url = stack_resources["DataplaneApiEndpoint"] + 'metadata/' + asset_id + "?cursor=" + cursor
    headers = {"Content-Type": "application/json"}
    print("GET /metadata/{asset}".format(asset=asset_id))
    metadata_response = requests.get(url, headers=headers, verify=False)
    return metadata_response


def get_single_metadata_field(stack_resources, asset_id, operator):
    metadata_field = operator["OperatorName"]
    url = stack_resources["DataplaneApiEndpoint"] + 'metadata/' + asset_id + "/" + metadata_field
    headers = {"Content-Type": "application/json"}
    print("GET /metadata/{asset}/{operator}".format(asset=asset_id, operator=operator["OperatorName"]))
    single_metadata_response = requests.get(url, headers=headers, verify=False)
    return single_metadata_response


def delete_single_metadata_field(stack_resources, asset_id, operator):
    metadata_field = operator["OperatorName"]
    url = stack_resources["DataplaneApiEndpoint"] + 'metadata/' + asset_id + "/" + metadata_field
    headers = {"Content-Type": "application/json"}
    print("DELETE /metadata/{asset}/{operator}".format(asset=asset_id, operator=operator["OperatorName"]))
    delete_single_metadata_response = requests.delete(url, headers=headers, verify=False)
    return delete_single_metadata_response


def delete_asset(stack_resources, asset_id):
    url = stack_resources["DataplaneApiEndpoint"] + 'metadata/' + asset_id
    headers = {"Content-Type": "application/json"}
    print("DELETE /metadata/{asset}".format(asset=asset_id))
    delete_asset_response = requests.delete(url, headers=headers, verify=False)
    return delete_asset_response
