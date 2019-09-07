#!/usr/bin/python

# # Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import json
from pprint import pprint


def fix_chalice_sam_template():

    sam_json = json.load(open('./dist/sam.json'))
    # pprint(sam_json)

    #stack_inputs_json = json.load(open('./chalice-stack-inputs.json'))
    # pprint(stack_inputs_json)

    sam_json["Parameters"] = {
        "ApiIpList": {"Type": "String",
                      "Description": "List of IP that can access MIE APIs"
                      },
        "SystemTableName": {
            "Type": "String",
            "Description": "Table used to store system configuration"
        },
        "WorkflowTableName": {
            "Type": "String",
            "Description": "Table used to store workflow defintitions"
        },
        "StageTableName": {
            "Type": "String",
            "Description": "Table used to store stage definitions"
        },
        "WorkflowExecutionTableName": {
                "Type": "String",
                "Description": "Table used to monitor Workflow executions" 
                },
        "HistoryTableName": {
                "Type": "String",
                "Description": "Table used to store workflow resource history" 
                },
        "StageExecutionQueueUrl": {
            "Type": "String",
            "Description": "Queue used to post stage executions for processing"
        },
        "StageExecutionRole": {
            "Type": "String",
            "Description": "ARN of the role used to execute a stage state machine"
        },
        "OperationTableName": {
            "Type": "String",
            "Description": "Table used to store operations"
        },
        "CompleteStageLambdaArn": {
            "Type": "String",
            "Description": "Lambda that completes execution of a stage"
        },
        "FilterOperationLambdaArn": {
            "Type": "String",
            "Description": "Lambda that checks if an operation should execute"
        },
        "WorkflowSchedulerLambdaArn": {
                "Type": "String",
                "Description": "Lambda that schedules workflows from the work queue" 
                },
        "DataplaneEndpoint": {
            "Type": "String",
            "Description": "Rest endpoint for the dataplane"
        },
        "DataPlaneBucket": {
            "Type": "String",
            "Description": "S3 bucket of the dataplane"
        },
        "OperatorFailedHandlerLambdaArn": {
            "Type": "String",
            "Description": "Lambda that handles failed operator states"
        }
    }

    environment = {
        "Variables": {
                "SYSTEM_TABLE_NAME": {
                        "Ref":"SystemTableName"
                },
                "WORKFLOW_TABLE_NAME": {
                        "Ref":"WorkflowTableName"
                },
                "WORKFLOW_EXECUTION_TABLE_NAME": {
                        "Ref":"WorkflowExecutionTableName"
                },
                "HISTORY_TABLE_NAME": {
                        "Ref":"HistoryTableName"
                },
                "STAGE_TABLE_NAME": {
                        "Ref":"StageTableName"
                },
                "STAGE_EXECUTION_QUEUE_URL": {
                        "Ref":"StageExecutionQueueUrl"
                },
                "OPERATION_TABLE_NAME": {
                        "Ref":"OperationTableName"
                },
                "COMPLETE_STAGE_LAMBDA_ARN": {
                        "Ref":"CompleteStageLambdaArn"
                },
                "FILTER_OPERATION_LAMBDA_ARN": {
                        "Ref":"FilterOperationLambdaArn"
                },
                "WORKFLOW_SCHEDULER_LAMBDA_ARN": {
                        "Ref":"WorkflowSchedulerLambdaArn"
                },
                "STAGE_EXECUTION_ROLE": {
                        "Ref" : "StageExecutionRole"
                },
                "DataplaneEndpoint": {
                    "Ref": "DataplaneEndpoint"
                },
                "DATAPLANE_BUCKET": {
                    "Ref": "DataPlaneBucket"
                },
                "OPERATOR_FAILED_LAMBDA_ARN": {
                    "Ref": "OperatorFailedHandlerLambdaArn"
                }
            }
        }

    # Replace environment variables for all the lambdas
    # pprint(MediainfoRuleEngine_environment_json)
    for resourceName, resource in sam_json["Resources"].iteritems():
        if (resource["Type"] == "AWS::Serverless::Function"):
            sam_json["Resources"][resourceName]["Properties"]["Environment"] = environment

    # add lambdas to stack outputs
    for resourceName, resource in sam_json["Resources"].iteritems():
        if (resource["Type"] == "AWS::Serverless::Function"):
            sam_json["Resources"][resourceName]["Properties"]["Environment"] = environment

            outputName = resourceName+"Arn"
            sam_json["Outputs"][outputName] = {
                "Value": {"Fn::GetAtt": [resourceName, "Arn"]}}

    # Update the resource policy for the API
    resource_policy = {
        "Version": "2012-10-17", "Statement": [
            {
                "Effect": "Allow",
                "Principal": "*",
                "Action": "execute-api:Invoke",
                "Resource": [
                      {"Fn::Sub":
                      "arn:aws:execute-api:${AWS::Region}:${AWS::AccountId}:*/*/*/*"}
                ]
            },
            {
                "Effect": "Deny",
                "Principal": "*",
                "Action": "execute-api:Invoke",
                "Resource": [
                    {"Fn::Sub":
                     "arn:aws:execute-api:${AWS::Region}:${AWS::AccountId}:*/*/*/*"}
                ],
                "Condition": {
                    "NotIpAddress": {
                        "aws:SourceIp": [{"Fn::Sub": "${ApiIpList}"}]
                    }
                }
            } 
        ]
    }

    sam_json["Resources"]["RestAPI"]["Properties"]["DefinitionBody"]["x-amazon-apigateway-policy"] = resource_policy

    with open('./dist/sam.json', 'w') as outfile:
        json.dump(sam_json, outfile)


def add_policy(policy_file_location, sam_json):
    # READ RESOURCE POLICY FILE
    resource_policy_file = open(policy_file_location, 'r')
    resource_policy = json.load(resource_policy_file)
    resource_policy_file.close()

    # ADD RESOURCE POLICY TO SAM TEMPLATE
    sam_json["Resources"]["RestAPI"]["Properties"]["DefinitionBody"]["x-amazon-apigateway-policy"] = resource_policy

    return sam_json


def main():
    fix_chalice_sam_template()


if __name__ == '__main__':
    main()
