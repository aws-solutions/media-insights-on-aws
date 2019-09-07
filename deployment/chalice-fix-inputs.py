# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0


#!/usr/bin/python
import json
from pprint import pprint

def fix_chalice_sam_template():
    
    sam_json = json.load(open('./dist/sam.json'))
    # pprint(sam_json)

    #stack_inputs_json = json.load(open('./chalice-stack-inputs.json'))
    #pprint(stack_inputs_json)

    sam_json["Parameters"] = {
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
        "StageExecutionQueueUrl": {
                "Type": "String",
                "Description": "Queue used to post stage executions for processing" 
                },
        }

    environment = {
        "Variables": {
                "WORKFLOW_TABLE_NAME": {
                        "Ref":"WorkflowTableName"
                },
                "WORKFLOW_EXECUTION_TABLE_NAME": {
                        "Ref":"WorkflowExecutionTableName"
                },
                "STAGE_EXECUTION_QUEUE_URL": {
                        "Ref":"StageExecutionQueueUrl"
                }
            }
        }

    
    # Replace environment variables for all the lambdas
    #pprint(MediainfoRuleEngine_environment_json)
    for resourceName, resource in sam_json["Resources"].iteritems():
        if (resource["Type"] == "AWS::Serverless::Function"):
            sam_json["Resources"][resourceName]["Properties"]["Environment"] = environment
    

    with open('./dist/sam.json', 'w') as outfile:
        json.dump(sam_json, outfile)

    pprint(json.dumps(sam_json))

def main():
    fix_chalice_sam_template()


if __name__ == '__main__':
    main()