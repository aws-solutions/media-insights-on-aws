#!/usr/bin/python

# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import json
from pprint import pprint


def fix_chalice_sam_template():

    sam_json = json.load(open('./dist/sam.json'))
    # pprint(sam_json)

    #stack_inputs_json = json.load(open('./chalice-stack-inputs.json'))
    # pprint(stack_inputs_json)

    sam_json["Parameters"] = {
        "ApiIpList": {
            "Type": "String",
            "Description": "List of IP that can access MIE APIs"
        },
        "DataplaneTableName": {
            "Type": "String",
            "Description": "Table used for storing asset metadata"
        },
        "DataplaneBucketName": {
            "Type": "String",
            "Description": "Bucket used to store asset media"
        }
    }

    environment = {
        "Variables": {
            "DATAPLANE_TABLE_NAME": {
                "Ref": "DataplaneTableName"
            },
            "DATAPLANE_BUCKET": {
                "Ref": "DataplaneBucketName"
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
    resource_policy =    resource_policy = {
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


def main():
    fix_chalice_sam_template()


if __name__ == '__main__':
    main()
