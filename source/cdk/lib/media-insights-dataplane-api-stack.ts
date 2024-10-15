/**
 *  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 *
 *  Licensed under the Apache License, Version 2.0 (the "License"). You may not use this file except in compliance
 *  with the License. A copy of the License is located at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 *  or in the 'license' file accompanying this file. This file is distributed on an 'AS IS' BASIS, WITHOUT WARRANTIES
 *  OR CONDITIONS OF ANY KIND, express or implied. See the License for the specific language governing permissions
 *  and limitations under the License.
 */

import { Construct } from 'constructs';
import * as cdk from 'aws-cdk-lib';
import * as cfninc from 'aws-cdk-lib/cloudformation-include';
import * as sam  from 'aws-cdk-lib/aws-sam';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as path from 'path';
import * as util from './utils'


interface FunctionEnvironmentProperty {
    readonly variables: {
        botoConfig: string;
        DATAPLANE_TABLE_NAME: string;
        DATAPLANE_BUCKET: string;
        FRAMEWORK_VERSION: string;
    };
}

/**
 * A nested CloudFormation stack representing the dataplane API.
 */
export class DataplaneApiStack extends cdk.NestedStack {

    constructor(scope: Construct, id: string, props: cdk.NestedStackProps) {
        super(scope, id, { ...props, description: "media-insights-on-aws. This AWS CloudFormation template provisions the REST API for the Media Insights on AWS data plane. Version %%VERSION%%" });
        this.templateOptions.templateFormatVersion = '2010-09-09';


        //
        // Cfn Parameters
        //

        const botoConfig = new cdk.CfnParameter(this, 'botoConfig', {
            type: 'String',
            description: "Botocore config",
        });

        const dataplaneTableName = new cdk.CfnParameter(this, 'DataplaneTableName', {
            type: 'String',
            description: "Table used for storing asset metadata",
        });

        const externalBucketArn = new cdk.CfnParameter(this, 'ExternalBucketArn', {
            type: 'String',
            description: "The ARN for Amazon S3 resources that exist outside the stack which may need to be used as inputs to the workflows.",
        });

        const dataplaneBucketName = new cdk.CfnParameter(this, 'DataplaneBucketName', {
            type: 'String',
            description: "Bucket used to store asset media",
        });

        const deploymentPackageBucket = new cdk.CfnParameter(this, 'DeploymentPackageBucket', {
            type: 'String',
            description: "Bucket that contains the dataplane deployment package",
        });

        const deploymentPackageKey = new cdk.CfnParameter(this, 'DeploymentPackageKey', {
            type: 'String',
            description: "S3 Key of the dataplane deployment package",
        });

        const mediaInsightsOnAwsPython311Layer = new cdk.CfnParameter(this, 'MediaInsightsOnAwsPython311Layer', {
            type: 'String',
            description: "Arn of the Media Insights on AWS Python 3.11 lambda layer",
        });

        const tracingConfigMode = new cdk.CfnParameter(this, 'TracingConfigMode', {
            type: 'String',
            description: "Sets tracing mode for stack entry points.  Allowed values: Active, PassThrough",
        });

        const frameworkVersion = new cdk.CfnParameter(this, 'FrameworkVersion', {
            type: 'String',
            description: "Version of the Media Insights on AWS Framework",
        });

        const kmsKeyId = new cdk.CfnParameter(this, 'KmsKeyId', {
            type: 'String',
            description: "ID of the stack KMS Key",
        });

        //
        // Cfn Conditions
        //

        const allowAccessToExternalBucket = new cdk.CfnCondition(this, 'AllowAccessToExternalBucket', {
            expression: cdk.Fn.conditionNot(cdk.Fn.conditionEquals(externalBucketArn.valueAsString, '')),
        });

        //
        // Cfn Template from Chalice
        //

        const template = new cfninc.CfnInclude(this, 'Template', {
            templateFile: path.join(__dirname, '../dist/media-insights-dataplane-api-stack.template'),
        });

        // Override properties of Serverless API Handler

        const cfnApiHandler = template.getResource('APIHandler') as sam.CfnFunction;

        // cfn_nag
        util.setNagSuppressRules(cfnApiHandler,
            {
                id: 'W89',
                reason: "This Lambda function does not need to access any resource provisioned within a VPC.",
            },
            {

                id: 'W92',
                reason: "This function does not require performance optimization, so the default concurrency limits suffice.",
            },
            {
                id: 'AwsSolutions-L1',
                reason: "Latest lambda version not supported at this time.",
            }
        );

        if ((cfnApiHandler.environment as FunctionEnvironmentProperty).variables !== undefined) {
            const v = (cfnApiHandler.environment as FunctionEnvironmentProperty).variables;
            v.botoConfig = botoConfig.valueAsString;
            v.DATAPLANE_TABLE_NAME = dataplaneTableName.valueAsString;
            v.DATAPLANE_BUCKET = dataplaneBucketName.valueAsString;
            v.FRAMEWORK_VERSION = frameworkVersion.valueAsString;
        }

        cfnApiHandler.runtime = cdk.aws_lambda.Runtime.PYTHON_3_11.name; // TODO: Remove this line once Chalice supports Python 3.11 (https://github.com/aws/chalice/issues/2053)
        cfnApiHandler.layers = [mediaInsightsOnAwsPython311Layer.valueAsString];
        cfnApiHandler.codeUri = {
            bucket: deploymentPackageBucket.valueAsString,
            key: deploymentPackageKey.valueAsString,
        };
        cfnApiHandler.tracing = tracingConfigMode.valueAsString;

        // Override properties of the API Handler Role

        const cfnApiHandlerRole = template.getResource('ApiHandlerRole') as iam.CfnRole;

        // cfn_nag / cdk_nag
        cfnApiHandlerRole.cfnOptions.metadata = {
            Comment: "This role contains two policies that provide GetObject permission for DataplaneBucketName. This duplication is necessary in order to avoid a syntax error when the user-specified ExternalBucketArn parameter is empty.",
        };
        util.setNagSuppressRules(cfnApiHandlerRole, {
            id: 'W11',
            id2: 'AwsSolutions-IAM5',
            reason: "The X-Ray policy uses actions that must be applied to all resources. See https://docs.aws.amazon.com/xray/latest/devguide/security_iam_id-based-policy-examples.html#xray-permissions-resources",
        });

        cfnApiHandlerRole.policies = [{
            policyDocument: {
              "Version": "2012-10-17",
              "Statement": [
                {
                  "Effect": "Allow",

                  "Action": [
                    "s3:GetObject"
                  ],
                  "Resource": cdk.Fn.conditionIf(allowAccessToExternalBucket.logicalId,
                                                 externalBucketArn.valueAsString,
                                                 cdk.Stack.of(this).formatArn({
                                                    service: 's3',
                                                    region: '',
                                                    account: '',
                                                    resource: dataplaneBucketName.valueAsString,
                                                    resourceName: '*',
                  })),
                },
                {
                  "Effect": "Allow",
                  "Action": [
                    "s3:ReplicateObject",
                    "s3:PutObject",
                    "s3:GetObject",
                    "s3:RestoreObject",
                    "s3:GetObjectVersionAcl",
                    "s3:ListBucket",
                    "s3:DeleteObject",
                    "s3:HeadBucket",
                    "s3:PutObjectAcl",
                    "s3:GetObjectVersion",
                    "s3:DeleteObjectVersion"
                  ],
                  "Resource": cdk.Stack.of(this).formatArn({
                    service: 's3',
                    region: '',
                    account: '',
                    resource: dataplaneBucketName.valueAsString,
                    resourceName: '*',
                  }),
                },
                {
                  "Effect": "Allow",
                  "Action": "s3:ListBucket",
                  "Resource": cdk.Stack.of(this).formatArn({
                    service: 's3',
                    region: '',
                    account: '',
                    resource: dataplaneBucketName.valueAsString,
                  }),
                },
                {
                  "Effect": "Allow",
                  "Action": [
                    "dynamodb:GetItem",
                    "dynamodb:PutItem",
                    "dynamodb:DeleteItem",
                    "dynamodb:UpdateItem",
                    "dynamodb:Scan"
                  ],
                  "Resource": cdk.Stack.of(this).formatArn({
                    service: 'dynamodb',
                    resource: 'table',
                    resourceName: dataplaneTableName.valueAsString,
                  }),
                },
                {
                  "Effect": "Allow",
                  "Action": [
                    "dynamodb:Query"
                  ],
                  "Resource": cdk.Stack.of(this).formatArn({
                    service: 'dynamodb',
                    resource: 'table',
                    resourceName: `${dataplaneTableName.valueAsString}/index/LockIndex`,
                  }),
                },
                {
                  "Effect": "Allow",
                  "Action": [
                      "xray:PutTraceSegments",
                      "xray:PutTelemetryRecords"
                  ],
                  "Resource": [
                      "*"
                  ]
                },
                {
                  "Action": [
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents"
                  ],
                  "Resource": cdk.Stack.of(this).formatArn({
                    service: 'logs',
                    resource: 'log-group',
                    resourceName: '/aws/lambda/*-APIHandler-*',
                    arnFormat: cdk.ArnFormat.COLON_RESOURCE_NAME,
                  }),
                  "Effect": "Allow",
                  "Sid": "Logging"
                },
                {
                  "Effect": "Allow",
                  "Action": [
                    "kms:Decrypt",
                    "kms:GenerateDataKey"
                  ],
                  "Resource": cdk.Stack.of(this).formatArn({
                    service: 'kms',
                    resource: 'key',
                    resourceName: kmsKeyId.valueAsString,
                  }),
                }
              ]
            },
            policyName: "MieDataplaneApiHandlerRolePolicy",
        }];
    }

    getLogicalId(element: cdk.CfnElement): string {
        return util.cleanUpLogicalId(super.getLogicalId(element));
    }
}
