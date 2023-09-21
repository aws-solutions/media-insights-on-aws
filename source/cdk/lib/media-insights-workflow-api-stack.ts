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
        STACK_SHORT_UUID: string;
        SYSTEM_TABLE_NAME: string;
        WORKFLOW_TABLE_NAME: string;
        STAGE_TABLE_NAME: string;
        WORKFLOW_EXECUTION_TABLE_NAME: string;
        HISTORY_TABLE_NAME: string;
        STAGE_EXECUTION_QUEUE_URL: string;
        OPERATION_TABLE_NAME: string;
        COMPLETE_STAGE_LAMBDA_ARN: string;
        FILTER_OPERATION_LAMBDA_ARN: string;
        WORKFLOW_SCHEDULER_LAMBDA_ARN: string;
        STAGE_EXECUTION_ROLE: string;
        STEP_FUNCTION_LOG_GROUP_ARN: string;
        DataplaneEndpoint: string;
        DATAPLANE_BUCKET: string;
        OPERATOR_FAILED_LAMBDA_ARN: string;
        USER_POOL_ARN: string;
        FRAMEWORK_VERSION?: string;
    };
}

/**
 * A nested CloudFormation stack representing the workflow API.
 */
export class WorkflowApiStack extends cdk.NestedStack {

    constructor(scope: Construct, id: string, props: cdk.NestedStackProps) {
        super(scope, id, { ...props, description: "media-insights-on-aws version %%VERSION%%. This AWS CloudFormation template provisions the REST API for the Media Insights on AWS control plane" });
        this.templateOptions.templateFormatVersion = '2010-09-09';


        //
        // Cfn Parameters
        //

        const botoConfig = new cdk.CfnParameter(this, 'botoConfig', {
            type: 'String',
            description: "Botocore config",
        });

        const deploymentPackageBucket = new cdk.CfnParameter(this, 'DeploymentPackageBucket', {
            type: 'String',
            description: "Bucket that contains the dataplane deployment package",
        });

        const deploymentPackageKey = new cdk.CfnParameter(this, 'DeploymentPackageKey', {
            type: 'String',
            description: "S3 Key of the dataplane deployment package",
        });

        const shortUUID = new cdk.CfnParameter(this, 'ShortUUID', {
            type: 'String',
            description: "A short UUID that is going to be appended to resource names",
        });

        const systemTableName = new cdk.CfnParameter(this, 'SystemTableName', {
            type: 'String',
            description: "Table used to store system configuration",
        });

        const workflowTableName = new cdk.CfnParameter(this, 'WorkflowTableName', {
            type: 'String',
            description: "Table used to store workflow definitions",
        });

        const stageTableName = new cdk.CfnParameter(this, 'StageTableName', {
            type: 'String',
            description: "Table used to store stage definitions",
        });

        const workflowExecutionTableName = new cdk.CfnParameter(this, 'WorkflowExecutionTableName', {
            type: 'String',
            description: "Table used to monitor Workflow executions",
        });

        const historyTableName = new cdk.CfnParameter(this, 'HistoryTableName', {
            type: 'String',
            description: "Table used to store workflow resource history",
        });

        const stageExecutionQueueUrl = new cdk.CfnParameter(this, 'StageExecutionQueueUrl', {
            type: 'String',
            description: "Queue used to post stage executions for processing",
        });

        const stepFunctionLogGroupArn = new cdk.CfnParameter(this, 'StepFunctionLogGroupArn', {
            type: 'String',
            description: "ARN of the log group used for logging step functions with Cloudwatch",
        });

        const stageExecutionRole = new cdk.CfnParameter(this, 'StageExecutionRole', {
            type: 'String',
            description: "ARN of the role used to execute a stage state machine",
        });

        const operationTableName = new cdk.CfnParameter(this, 'OperationTableName', {
            type: 'String',
            description: "Table used to store operations",
        });

        const completeStageLambdaArn = new cdk.CfnParameter(this, 'CompleteStageLambdaArn', {
            type: 'String',
            description: "Lambda that completes execution of a stage",
        });

        const filterOperationLambdaArn = new cdk.CfnParameter(this, 'FilterOperationLambdaArn', {
            type: 'String',
            description: "Lambda that checks if an operation should execute",
        });

        const workflowSchedulerLambdaArn = new cdk.CfnParameter(this, 'WorkflowSchedulerLambdaArn', {
            type: 'String',
            description: "Lambda that schedules workflows from the work queue",
        });

        const dataplaneEndpoint = new cdk.CfnParameter(this, 'DataplaneEndpoint', {
            type: 'String',
            description: "Rest endpoint for the dataplane",
        });

        const dataplaneHandlerArn = new cdk.CfnParameter(this, 'DataplaneHandlerArn', {
            type: 'String',
            description: "Arn for the dataplane lambda handler",
        });

        const dataplaneBucket = new cdk.CfnParameter(this, 'DataPlaneBucket', {
            type: 'String',
            description: "S3 bucket of the dataplane",
        });

        const operatorFailedHandlerLambdaArn = new cdk.CfnParameter(this, 'OperatorFailedHandlerLambdaArn', {
            type: 'String',
            description: "Lambda that handles failed operator states",
        });

        const sqsQueueArn = new cdk.CfnParameter(this, 'SqsQueueArn', {
            type: 'String',
            description: "Arn of the Media Insights on AWS workflow queue",
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
        // Cfn Template from Chalice
        //

        const template = new cfninc.CfnInclude(this, 'Template', {
            templateFile: path.join(__dirname, '../dist/media-insights-workflow-api-stack.template'),
        });

        // Override properties of Serverless API Handler

        function fixUpCfnFunction(id: string, includeFrameworkVersion: boolean): sam.CfnFunction {

            const cfnFunction = template.getResource(id) as sam.CfnFunction;

            // cfn_nag
            util.setNagSuppressRules(cfnFunction,
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
                },
            );

            if ((cfnFunction.environment as FunctionEnvironmentProperty).variables !== undefined) {
                const v = (cfnFunction.environment as FunctionEnvironmentProperty).variables;
                v.botoConfig = botoConfig.valueAsString;
                v.STACK_SHORT_UUID = shortUUID.valueAsString;
                v.SYSTEM_TABLE_NAME = systemTableName.valueAsString;
                v.WORKFLOW_TABLE_NAME = workflowTableName.valueAsString;
                v.WORKFLOW_EXECUTION_TABLE_NAME = workflowExecutionTableName.valueAsString;
                v.HISTORY_TABLE_NAME = historyTableName.valueAsString;
                v.STAGE_TABLE_NAME = stageTableName.valueAsString;
                v.STAGE_EXECUTION_QUEUE_URL = stageExecutionQueueUrl.valueAsString;
                v.OPERATION_TABLE_NAME = operationTableName.valueAsString;
                v.COMPLETE_STAGE_LAMBDA_ARN = completeStageLambdaArn.valueAsString;
                v.FILTER_OPERATION_LAMBDA_ARN = filterOperationLambdaArn.valueAsString;
                v.WORKFLOW_SCHEDULER_LAMBDA_ARN = workflowSchedulerLambdaArn.valueAsString;
                v.STAGE_EXECUTION_ROLE = stageExecutionRole.valueAsString;
                v.STEP_FUNCTION_LOG_GROUP_ARN = stepFunctionLogGroupArn.valueAsString;
                v.DataplaneEndpoint = dataplaneEndpoint.valueAsString;
                v.DATAPLANE_BUCKET = dataplaneBucket.valueAsString;
                v.OPERATOR_FAILED_LAMBDA_ARN = operatorFailedHandlerLambdaArn.valueAsString;
                if (includeFrameworkVersion) {
                    v.FRAMEWORK_VERSION = frameworkVersion.valueAsString;
                }
            }

            cfnFunction.runtime = cdk.aws_lambda.Runtime.PYTHON_3_11.name; // TODO: Remove this line once Chalice supports Python 3.11 (https://github.com/aws/chalice/issues/2053)
            cfnFunction.layers = [mediaInsightsOnAwsPython311Layer.valueAsString];
            cfnFunction.codeUri = {
                bucket: deploymentPackageBucket.valueAsString,
                key: deploymentPackageKey.valueAsString,
            };
            cfnFunction.tracing = tracingConfigMode.valueAsString;

            return cfnFunction;
        }

        fixUpCfnFunction('APIHandler', true);
        const workflowCustomResource = fixUpCfnFunction('WorkflowCustomResource', false);




        // Override properties of the API Handler Role

        const cfnApiHandlerRole = template.getResource('ApiHandlerRole') as iam.CfnRole;
        cfnApiHandlerRole.description = "This role is used by the workflow api lambda when invoked by API Gateway";

        // cfn_nag
        util.setNagSuppressRules(cfnApiHandlerRole,
            {
                id: "W11",
                id2: "AwsSolutions-IAM5",
                reason: "The X-Ray, Transcribe, and Translate policies cannot be scoped to a specific resource."
            },
            {
                id: "W76",
                reason: "The complexity of this policy document is necessary in order to avoid wildcards."
            },
        );

        const policyDynamodbAccess = {
            "Effect": "Allow",
            "Action": [
                "dynamodb:GetItem",
                "dynamodb:PutItem",
                "dynamodb:UpdateItem",
                "dynamodb:DeleteItem",
                "dynamodb:Scan",
                "dynamodb:Query"
            ],
            "Resource": [
                cdk.Stack.of(this).formatArn({
                    service: 'dynamodb',
                    resource: 'table',
                    resourceName: systemTableName.valueAsString,
                }),
                cdk.Stack.of(this).formatArn({
                    service: 'dynamodb',
                    resource: 'table',
                    resourceName: workflowTableName.valueAsString,
                }),
                cdk.Stack.of(this).formatArn({
                    service: 'dynamodb',
                    resource: 'table',
                    resourceName: workflowExecutionTableName.valueAsString,
                }),
                cdk.Stack.of(this).formatArn({
                    service: 'dynamodb',
                    resource: 'table',
                    resourceName: `${workflowExecutionTableName.valueAsString}/*`,
                }),
                cdk.Stack.of(this).formatArn({
                    service: 'dynamodb',
                    resource: 'table',
                    resourceName: historyTableName.valueAsString,
                }),
                cdk.Stack.of(this).formatArn({
                    service: 'dynamodb',
                    resource: 'table',
                    resourceName: operationTableName.valueAsString,
                }),
                cdk.Stack.of(this).formatArn({
                    service: 'dynamodb',
                    resource: 'table',
                    resourceName: stageTableName.valueAsString,
                }),
            ]
        };

        cfnApiHandlerRole.policies = [{
            policyDocument: {
              "Version": "2012-10-17",
              "Statement": [
                {
                  "Effect": "Allow",
                  "Action": [
                    "sqs:SendMessage"
                  ],
                  "Resource": sqsQueueArn.valueAsString
                },
                {
                  "Effect": "Allow",
                  "Action": [
                    "s3:GetObject"
                  ],
                  "Resource": cdk.Stack.of(this).formatArn({
                        service: 's3',
                        region: '',
                        account: '',
                        resource: dataplaneBucket.valueAsString,
                        resourceName: '*',
                  }),
                },
                {
                  "Effect": "Allow",
                  "Action": [
                    "states:ListStateMachines",
                    "states:TagResource",
                    "states:CreateStateMachine",
                    "states:DescribeStateMachine",
                    "states:UpdateStateMachine",
                    "states:DeleteStateMachine",
                    "states:UntagResource"
                  ],
                  "Resource": cdk.Stack.of(this).formatArn({
                    service: 'states',
                    resource: 'stateMachine',
                    resourceName: `*-${shortUUID.valueAsString}`,
                    arnFormat: cdk.ArnFormat.COLON_RESOURCE_NAME,
                  }),
                },
                {
                  "Effect": "Allow",
                  "Action": [
                    "iam:PassRole"
                  ],
                  "Resource": stageExecutionRole.valueAsString
                },
                {
                  "Effect": "Allow",
                  "Action": [
                    "lambda:InvokeFunction"
                  ],
                  "Resource": [
                    workflowSchedulerLambdaArn.valueAsString,
                    filterOperationLambdaArn.valueAsString,
                    completeStageLambdaArn.valueAsString,
                    operatorFailedHandlerLambdaArn.valueAsString,
                    dataplaneHandlerArn.valueAsString,
                  ]
                },
                policyDynamodbAccess,
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
                  "Effect": "Allow",
                  "Action": [
                    "transcribe:CreateVocabulary",
                    "transcribe:DeleteVocabulary",
                    "transcribe:GetVocabulary",
                    "transcribe:ListVocabularies",
                    "transcribe:ListLanguageModels",
                    "transcribe:DescribeLanguageModel"
                  ],
                  "Resource": "*"
                },
                {
                  "Effect": "Allow",
                  "Action": [
                    "translate:CreateTerminology",
                    "translate:DeleteTerminology",
                    "translate:GetTerminology",
                    "translate:ImportTerminology",
                    "translate:ListTerminologies",
                    "translate:CreateParallelData",
                    "translate:DeleteParallelData",
                    "translate:GetParallelData",
                    "translate:ImportParallelData",
                    "translate:ListParallelData"
                  ],
                  "Resource": "*"
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
                    "iam:ListRolePolicies",
                    "iam:PutRolePolicy",
                    "iam:DeleteRolePolicy"
                  ],
                  "Resource": stageExecutionRole.valueAsString
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
            policyName: "MieWorkflowApiHandlerRolePolicy",
        }];


        const cfnWorkflowCustomResourceRole = template.getResource('WorkflowCustomResourceRole') as iam.CfnRole;
        cfnWorkflowCustomResourceRole.description = "This role is used by the workflow api lambda when invoked by CloudFormation";

        // cfn_nag
        util.setNagSuppressRules(cfnWorkflowCustomResourceRole, {
            id: "W11",
            id2: "AwsSolutions-IAM5",
            reason: "The X-Ray policy uses actions that must be applied to all resources. See https://docs.aws.amazon.com/xray/latest/devguide/security_iam_id-based-policy-examples.html#xray-permissions-resources",
        });

        cfnWorkflowCustomResourceRole.policies = [{
            policyName: "MieWorkflowCustomResourceRolePolicy",
            policyDocument: {
              "Version": "2012-10-17",
              "Statement": [
                {
                  "Action": [
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents"
                  ],
                  "Resource": cdk.Stack.of(this).formatArn({
                    service: 'logs',
                    resource: 'log-group',
                    resourceName: '/aws/lambda/*-WorkflowCustomResource-*',
                    arnFormat: cdk.ArnFormat.COLON_RESOURCE_NAME,
                  }),
                  "Effect": "Allow",
                  "Sid": "Logging"
                },
                {
                  "Effect": "Allow",
                  "Action": [
                    "iam:PassRole"
                  ],
                  "Resource": stageExecutionRole.valueAsString
                },
                {
                  "Effect": "Allow",
                  "Action": [
                    "sqs:CreateQueue",
                    "sqs:ListQueues"
                  ],
                  "Resource": sqsQueueArn.valueAsString
                },
                policyDynamodbAccess,
                {
                  "Effect": "Allow",
                  "Action": [
                    "states:ListStateMachines",
                    "states:DescribeStateMachine",
                    "states:CreateStateMachine",
                    "states:UpdateStateMachine",
                    "states:DeleteStateMachine",
                    "states:TagResource",
                    "states:UntagResource"
                  ],
                  "Resource": cdk.Stack.of(this).formatArn({
                    service: 'states',
                    resource: 'stateMachine',
                    resourceName: `*-${shortUUID.valueAsString}`,
                    arnFormat: cdk.ArnFormat.COLON_RESOURCE_NAME,
                  }),
                },
                {
                  "Effect": "Allow",
                  "Action": [
                    "iam:ListRolePolicies",
                    "iam:PutRolePolicy",
                    "iam:DeleteRolePolicy"
                  ],
                  "Resource": stageExecutionRole.valueAsString
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
        }];


        util.createCfnOutput(this, 'WorkflowCustomResourceArn', {
            value: `${workflowCustomResource.getAtt('Arn')}`,
        });

    }

    getLogicalId(element: cdk.CfnElement): string {
        return util.cleanUpLogicalId(super.getLogicalId(element));
    }
}
