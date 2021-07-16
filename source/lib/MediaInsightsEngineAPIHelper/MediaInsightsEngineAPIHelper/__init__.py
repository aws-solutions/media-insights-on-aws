import requests
import json
import os
import logging
import boto3
import re
import urllib3
from requests_aws4auth import AWS4Auth

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def env_variables():
    try:
        env_vars = {
            'REGION': os.environ['MIE_REGION'],
            'MIE_STACK_NAME': os.environ['MIE_STACK_NAME'],
            'ACCESS_KEY': os.environ['AWS_ACCESS_KEY_ID'],
            'SECRET_KEY': os.environ['AWS_SECRET_ACCESS_KEY']
            }
    except KeyError as e:
        logging.error("ERROR: Missing a required environment variable: {variable}".format(variable=e))
        raise Exception(e)
    else:
        return env_vars


def stack_resources(env_variables):
    resources = {}
    # is the workflow api and operator library present?

    client = boto3.client('cloudformation', region_name=env_variables['REGION'])
    response = client.describe_stacks(StackName=env_variables['MIE_STACK_NAME'])
    outputs = response['Stacks'][0]['Outputs']

    for output in outputs:
        resources[output["OutputKey"]] = output["OutputValue"]

    assert "WorkflowApiEndpoint" in resources
    assert "DataplaneApiEndpoint" in resources

    api_endpoint_regex = ".*.execute-api."+env_variables['REGION']+".amazonaws.com/api/.*"

    assert re.match(api_endpoint_regex, resources["WorkflowApiEndpoint"])

    response = client.describe_stacks(StackName=resources["OperatorLibraryStack"])
    outputs = response['Stacks'][0]['Outputs']
    for output in outputs:
        resources[output["OutputKey"]] = output["OutputValue"]

    return resources


class MIE:
    def __init__(self):
        self.env_vars = env_variables()
        self.stack_resources = stack_resources(self.env_vars)
        self.auth = AWS4Auth(self.env_vars['ACCESS_KEY'], self.env_vars['SECRET_KEY'],
                             self.env_vars['REGION'], 'execute-api')

    # Workflow Methods

    def create_workflow(self, body):
        headers = {"Content-Type": "application/json"}
        logging.info("POST /workflow {}".format(json.dumps(body)))
        create_workflow_response = requests.post(self.stack_resources["WorkflowApiEndpoint"]+'/workflow', headers=headers, json=body, verify=True, auth=self.auth)

        return create_workflow_response

    def delete_workflow(self, workflow):
        headers = {"Content-Type": "application/json"}
        logging.info("DELETE /workflow {}".format(workflow))
        delete_workflow_response = requests.delete(self.stack_resources["WorkflowApiEndpoint"]+'/workflow/'+workflow, verify=True, auth=self.auth, headers=headers)
        return delete_workflow_response

    # Stage Methods

    def create_stage(self, body):
        headers = {"Content-Type": "application/json"}
        logging.info("POST /workflow/stage {}".format(json.dumps(body)))
        create_stage_response = requests.post(self.stack_resources["WorkflowApiEndpoint"]+'/workflow/stage', headers=headers, json=body, verify=True, auth=self.auth)

        return create_stage_response

    def delete_stage(self, stage):
        delete_stage_response = requests.delete(self.stack_resources["WorkflowApiEndpoint"]+'/workflow/stage/'+stage, verify=True, auth=self.auth)

        return delete_stage_response

    # Workflow execution methods

    def start_workflow(self, body):
        headers = {"Content-Type": "application/json"}
        logging.info("POST /workflow/execution")
        create_workflow_execution_response = requests.post(self.stack_resources["WorkflowApiEndpoint"]+'/workflow/execution', headers=headers, json=body, verify=True, auth=self.auth)

        return create_workflow_execution_response

    def get_workflow_execution(self, id):
        logging.info("GET /workflow/execution/{}".format(id))
        get_workflow_execution_response = requests.get(self.stack_resources["WorkflowApiEndpoint"]+'/workflow/execution/' + id, verify=True, auth=self.auth)

        return get_workflow_execution_response
