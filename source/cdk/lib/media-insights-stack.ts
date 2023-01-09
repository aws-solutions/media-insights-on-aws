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
import {
    ArnFormat,
    Aws,
    CfnCondition,
    CfnElement,
    CfnOutput,
    CfnParameter,
    CustomResource,
    Duration,
    Fn,
    RemovalPolicy,
    Stack,
    StackProps,
} from 'aws-cdk-lib';
import * as kms from 'aws-cdk-lib/aws-kms';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as logs from 'aws-cdk-lib/aws-logs';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as sns from 'aws-cdk-lib/aws-sns';
import * as subscriptions from 'aws-cdk-lib/aws-sns-subscriptions';
import * as sqs from 'aws-cdk-lib/aws-sqs';
import * as events from 'aws-cdk-lib/aws-events';
import * as targets from 'aws-cdk-lib/aws-events-targets';
import { DataplaneApiStack } from './media-insights-dataplane-api-stack';
import { WorkflowApiStack } from './media-insights-workflow-api-stack';
import { AnalyticsStack } from './media-insights-dataplane-streaming-stack';
import { OperatorLibraryStack } from './operator-library';
import { TestResourcesStack } from './media-insights-test-operations-stack';
import { NagSuppressions } from 'cdk-nag';
import * as util from './utils';

export interface MediaInsightsNestedStacks {
    readonly dataplaneApiStack: DataplaneApiStack,
    readonly workflowApiStack: WorkflowApiStack,
    readonly analyticsStack: AnalyticsStack,
    readonly operatorLibraryStack: OperatorLibraryStack,
    readonly testResourcesStack: TestResourcesStack,
}

/**
 * The root CloudFormation stack for the Media Insights Solution.
 */
export class MediaInsightsStack extends Stack {
    /**
     * All nested stacks.
     */
    readonly nestedStacks: MediaInsightsNestedStacks;

    constructor(scope: Construct, id: string, props?: StackProps) {
        super(scope, id, { ...props, description: '(SO0163) - aws-media-insights-engine version %%VERSION%%. This is the base AWS CloudFormation template that provisions Media Insights Engine services and provides parameters for user configurable MIE settings.' });
        this.templateOptions.templateFormatVersion = '2010-09-09';

        //
        // Cfn Parameters
        //

        const deployTestResources = new CfnParameter(this, 'DeployTestResources', {
            description: "Deploy test resources which contains lambdas required for integration and e2e testing",
            type: 'String',
            default: 'No',
            allowedValues: [ 'Yes', 'No' ],
        });
        const deployAnalyticsPipeline = new CfnParameter(this, 'DeployAnalyticsPipeline', {
            type: 'String',
            description: "Deploy a metadata streaming pipeline that can be consumed by downstream analytics plaforms",
            default: 'Yes',
            allowedValues: [ 'Yes', 'No' ],
        });
        const maxConcurrentWorkflows = new CfnParameter(this, 'MaxConcurrentWorkflows', {
            type: 'Number',
            description: "Maximum number of workflows to run concurrently.  When the maximum is reached, additional workflows are added to a wait queue.",
            default: 5,
            minValue: 1,
        });
        const enableXrayTrace = new CfnParameter(this, 'EnableXrayTrace', {
            description: "Turn on Xray tracing on all entry points to the stack",
            type: 'String',
            default: 'No',
            allowedValues: [ 'Yes', 'No' ],
        });
        const externalBucketArn = new CfnParameter(this, 'ExternalBucketArn', {
            description: "(Optional) If you intend to input media files from a bucket outside the MIE stack into MIE workflows, then specify the Amazon S3 ARN for those files here.",
            type: 'String',
            default: "",
        });
        const solutionId = new CfnParameter(this, 'SolutionId', {
            description: "(Optional) AWS Solution Id used for reporting purposes",
            type: 'String',
            default: 'SO0163',
        });
        const solutionVersion = new CfnParameter(this, 'SolutionVersion', {
            description: "(Optional) AWS Solution version used for reporting purposes",
            type: 'String',
            default: "%%VERSION%%",
        });
        const sendAnonymousData = new CfnParameter(this, 'SendAnonymousData', {
            description: "(Optional) Send anonymous data about MIE performance to AWS to help improve the quality of this solution.",
            type: 'String',
            default: 'Yes',
            allowedValues: [ 'Yes', 'No' ],
        });

        //
        // Cfn Metadata
        //
        this.addMetadata("AWS::CloudFormation::Interface", {
            ParameterGroups: [{
                Label: {
                    default: "System Configuration"
                },
                Parameters: [ "MaxConcurrentWorkflows" ],
            }]
        });

        //
        // Cfn Conditions
        //

        const deployTestResourcesCondition = new CfnCondition(this, 'DeployTestResourcesCondition', {
            expression: Fn.conditionEquals(deployTestResources.valueAsString, 'Yes'),
        });
        const deployAnalyticsCondition = new CfnCondition(this, 'DeployAnalyticsPipelineCondition', {
            expression: Fn.conditionEquals(deployAnalyticsPipeline.valueAsString, 'Yes'),
        });
        const enableTraceOnEntryPoints = new CfnCondition(this, 'EnableTraceOnEntryPoints', {
            expression: Fn.conditionEquals(enableXrayTrace.valueAsString, 'Yes'),
        });
        const enableAnonymousData = new CfnCondition(this, 'EnableAnonymousData', {
            expression: Fn.conditionEquals(sendAnonymousData.valueAsString, 'Yes'),
        });

        //
        // Cfn Mappings
        //

        const sourceCodeMap = new util.SourceCodeHelper(this, {
            GlobalS3Bucket: "%%GLOBAL_BUCKET_NAME%%",
            TemplateKeyPrefix: "aws-media-insights-engine/%%VERSION%%",
            FrameworkVersion: "%%VERSION%%",
        });

        //
        // Cfn Resources
        //

        const mieKey = new kms.Key(this, 'MieKey', {
            description: "MIE provided KMS key for encryption",
            enableKeyRotation: true,
            policy: new iam.PolicyDocument({
                statements: [
                    new iam.PolicyStatement({
                        effect: iam.Effect.ALLOW,
                        principals: [new iam.AccountRootPrincipal()],
                        actions: ['kms:*'],
                        resources: ['*'],
                    }),
                    new iam.PolicyStatement({
                        effect: iam.Effect.ALLOW,
                        principals: [
                            new iam.ServicePrincipal('s3.amazonaws.com'),
                            new iam.ServicePrincipal('sns.amazonaws.com'),
                            new iam.ServicePrincipal('sqs.amazonaws.com'),
                        ],
                        actions: [
                            'kms:Decrypt',
                            'kms:GenerateDataKey*',
                        ],
                        resources: ['*'],
                        conditions: {
                            StringEquals: {
                                "aws:SourceAccount": this.account
                            }
                        },
                    }),
                    new iam.PolicyStatement({
                        effect: iam.Effect.ALLOW,
                        principals: [new iam.ServicePrincipal('dynamodb.amazonaws.com')],
                        // https://docs.aws.amazon.com/kms/latest/developerguide/services-dynamodb.html#dynamodb-customer-cmk-policy
                        actions: [
                            'kms:Encrypt',
                            'kms:Decrypt',
                            'kms:ReEncrypt*',
                            'kms:GenerateDataKey*',
                            'kms:DescribeKey',
                            'kms:CreateGrant',
                        ],
                        resources: ['*'],
                        conditions: {
                            StringEquals: {
                                "aws:SourceAccount": this.account
                            }
                        },
                    }),
                    new iam.PolicyStatement({
                        effect: iam.Effect.ALLOW,
                        principals: [new iam.ServicePrincipal('rekognition.amazonaws.com')],
                        actions: [
                            'kms:Encrypt',
                            'kms:Decrypt',
                            'kms:ReEncrypt*',
                            'kms:GenerateDataKey*',
                            'kms:DescribeKey',
                        ],
                        resources: ['*'],
                        conditions: {
                            StringEquals: {
                                "aws:SourceAccount": this.account
                            }
                        },
                    }),
                ]
            }),
        });

        const keyAlias = mieKey.addAlias(`alias/${Aws.STACK_NAME}`);

        //
        // Services - Dynamodb
        //

        function createTable(scope: Construct, name: string, customProps?: dynamodb.TableProps): dynamodb.Table
        {
            const id = /Table$/.test(name) ? name : `${name}Table`;
            const props: dynamodb.TableProps = customProps || {
                partitionKey: {
                    name: 'Name',
                    type: dynamodb.AttributeType.STRING,
                }
            };
            const table = new dynamodb.Table(scope, id, {
                pointInTimeRecovery: true,
                removalPolicy: RemovalPolicy.DESTROY,
                encryptionKey: keyAlias,
                billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
                tableName: `${Aws.STACK_NAME}${name}`,
                ...props,
            });
            table.node.addDependency(keyAlias);

            // cfn_nag
            util.setNagSuppressRules(table, {
                id: 'W28',
                reason: "Table name is constructed with stack name. On update, we need to keep the existing table name.",
            });
            return table;
        }

        const systemTable = createTable(this, 'System');

        const workflowTable = createTable(this, 'Workflow');

        const stageTable = createTable(this, 'Stage');

        const operationTable = createTable(this, 'Operation');

        const historyTable = createTable(this, 'History', {
            partitionKey: {
                name: 'Id',
                type: dynamodb.AttributeType.STRING,
            },
            sortKey: {
                name: 'Version',
                type: dynamodb.AttributeType.STRING,
            },
        });

        const workflowExecutionTable = createTable(this, 'WorkflowExecution', {
            partitionKey: {
                name: 'Id',
                type: dynamodb.AttributeType.STRING,
            },
            stream: dynamodb.StreamViewType.NEW_AND_OLD_IMAGES,
        });

        workflowExecutionTable.addGlobalSecondaryIndex({
            indexName: 'WorkflowExecutionStatus',
            partitionKey: {
                name: 'Status',
                type: dynamodb.AttributeType.STRING,
            },
        });

        workflowExecutionTable.addGlobalSecondaryIndex({
            indexName: 'WorkflowExecutionAssetId',
            partitionKey: {
                name: 'AssetId',
                type: dynamodb.AttributeType.STRING,
            }
        });

        const dataplaneTable = createTable(this, 'DataplaneTable', {
            partitionKey: {
                name: 'AssetId',
                type: dynamodb.AttributeType.STRING,
            },
            stream: dynamodb.StreamViewType.NEW_AND_OLD_IMAGES,
        });

        dataplaneTable.addGlobalSecondaryIndex({
            indexName: 'LockIndex',
            partitionKey: {
                name: 'Locked',
                type: dynamodb.AttributeType.STRING,
            },
            sortKey: {
                name: 'LockedAt',
                type: dynamodb.AttributeType.NUMBER,
            },
            projectionType: dynamodb.ProjectionType.INCLUDE,
            nonKeyAttributes: ['LockedBy'],
        });


        //
        // Services - S3
        //

        const dataplaneLogsBucket = new s3.Bucket(this, 'DataplaneLogsBucket', {
            enforceSSL: true,
            accessControl: s3.BucketAccessControl.LOG_DELIVERY_WRITE,
            encryption: s3.BucketEncryption.S3_MANAGED,
            blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
        });

        // cfn_nag / cdk_nag
        util.setNagSuppressRules(dataplaneLogsBucket,
            { id: "W35", id2: "AwsSolutions-S1", reason: "Used to store access logs for other buckets" },
            { id: "W51", reason: "Bucket is private and does not need a bucket policy" },
        );

        const dataplaneBucket = new s3.Bucket(this, 'Dataplane', {
            enforceSSL: true,
            encryptionKey: keyAlias,
            blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
            serverAccessLogsBucket: dataplaneLogsBucket,
            serverAccessLogsPrefix: "access_logs/",
            cors: [{
                id: 'AllowUploadsFromWebApp',
                maxAge: 3000,
                allowedHeaders: ['*'],
                allowedOrigins: ['*'],
                allowedMethods: [
                    s3.HttpMethods.HEAD,
                    s3.HttpMethods.GET,
                    s3.HttpMethods.POST,
                    s3.HttpMethods.DELETE,
                    s3.HttpMethods.PUT,
                ],
                exposedHeaders: [
                    "x-amz-server-side-encryption",
                    "x-amz-request-id",
                    "x-amz-id-2",
                    "ETag",
                ],
            }],
            lifecycleRules: [
                {
                    id: "Keep access log for 10 days",
                    enabled: true,
                    prefix: "access_logs/",
                    expiration: Duration.days(10),
                    abortIncompleteMultipartUploadAfter: Duration.days(1),
                },
                {
                    id: "Keep cloudfront log for 10 days",
                    enabled: true,
                    prefix: "cf_logs/",
                    expiration: Duration.days(10),
                    abortIncompleteMultipartUploadAfter: Duration.days(1),
                }
            ],
        });

        dataplaneBucket.node.addDependency(dataplaneLogsBucket);


        //
        // Service - SNS
        //

        const workflowExecutionEventTopic = new sns.Topic(this, 'WorkflowExecutionEventTopic', {
            masterKey: keyAlias,
        });

        const workflowExecutionEventTopicPolicy = new sns.TopicPolicy(this, 'WorkflowExecutionEventTopicPolicy', {
            topics: [workflowExecutionEventTopic],
            policyDocument: new iam.PolicyDocument({
                statements: [
                    new iam.PolicyStatement({
                        principals: [new iam.AccountRootPrincipal()],
                        actions: [
                            "SNS:Subscribe",
                            "SNS:Receive",
                        ],
                        resources: [workflowExecutionEventTopic.topicArn],
                        conditions: {
                            StringEquals: {
                                ['AWS:SourceOwner']: Aws.ACCOUNT_ID,
                            }
                        },
                    }),
                ],
            }),
        });

        // cfn_nag
        util.setNagSuppressRules(workflowExecutionEventTopicPolicy, {
            id: 'W11',
            reason: "The topic permissions are scoped to the account using the condition",
        });

        //
        // Service - SQS
        //

        const workflowExecutionLambdaDeadLetterQueue = new sqs.Queue(this, 'WorkflowExecutionLambdaDeadLetterQueue', {
            queueName: `${Aws.STACK_NAME}-WorkflowExecLambdaDLQ`,
            retentionPeriod: Duration.hours(12),
            encryptionMasterKey: keyAlias,
            enforceSSL: true,
        });

        const stageExecutionDeadLetterQueue = new sqs.Queue(this, 'StageExecutionDeadLetterQueue', {
            queueName: `${Aws.STACK_NAME}-StageExecDLQ`,
            retentionPeriod: Duration.hours(12),
            encryptionMasterKey: keyAlias,
            enforceSSL: true,
        });


        // cdk_nag
        NagSuppressions.addResourceSuppressions([
            workflowExecutionLambdaDeadLetterQueue,
            stageExecutionDeadLetterQueue,
        ], [
            { id: 'AwsSolutions-SQS3', reason: "The SQS queue is a dead-letter queue (DLQ)" },
        ]);

        const workflowExecutionEventQueue = new sqs.Queue(this, 'WorkflowExecutionEventQueue', {
            deadLetterQueue: {
                queue: workflowExecutionLambdaDeadLetterQueue,
                maxReceiveCount: 1, // Don't retry if stage times out
            },
            encryptionMasterKey: keyAlias,
            enforceSSL: true,
        });

        const stageExecutionQueue = new sqs.Queue(this, 'StageExecutionQueue', {
            queueName: `${Aws.STACK_NAME}-StageExec`,
            visibilityTimeout: Duration.hours(12),
            receiveMessageWaitTime: Duration.seconds(20),
            deadLetterQueue: {
                queue: stageExecutionDeadLetterQueue,
                maxReceiveCount: 1, // Don't retry if stage times out
            },
            encryptionMasterKey: keyAlias,
            enforceSSL: true,
        });

        const sqsQueuePolicy = new sqs.QueuePolicy(this, 'SqsQueuePolicy', {
            queues: [workflowExecutionEventQueue],
        });
        sqsQueuePolicy.document.addStatements(
            new iam.PolicyStatement({
                principals: [new iam.ServicePrincipal('sns.amazonaws.com')],
                resources: [workflowExecutionEventQueue.queueArn],
                actions: ["sqs:SendMessage"],
                conditions: {
                    ArnEquals: {
                        ['aws:SourceArn']: workflowExecutionEventTopic.topicArn,
                    }
                },
            }),
        );

        // cfn_nag
        util.setNagSuppressRules(sqsQueuePolicy, {
            id: 'W11',
            reason: "The queue permissions are scoped to the SNS topic using the condition",
        });

        workflowExecutionEventTopic.addSubscription(new subscriptions.SqsSubscription(workflowExecutionEventQueue));

        //
        // IAM Roles
        //

        const helperExecutionRole = new iam.Role(this, 'MieHelperExecutionRole', {
            assumedBy: new iam.ServicePrincipal('lambda.amazonaws.com'),
            path: '/',
            inlinePolicies: {
                root: new iam.PolicyDocument({
                    statements: [
                        new iam.PolicyStatement({
                            effect: iam.Effect.ALLOW,
                            actions: [
                                'logs:CreateLogGroup',
                                'logs:CreateLogStream',
                                'logs:PutLogEvents',
                            ],
                            resources: [
                                Stack.of(this).formatArn({
                                    service: 'logs',
                                    resource: 'log-group',
                                    resourceName: '/aws/lambda/*',
                                    arnFormat: ArnFormat.COLON_RESOURCE_NAME,
                                })
                            ],
                        }),
                        new iam.PolicyStatement({
                            effect: iam.Effect.ALLOW,
                            actions: ['dynamodb:PutItem'],
                            resources: [systemTable.tableArn],
                        }),
                        new iam.PolicyStatement({
                            effect: iam.Effect.ALLOW,
                            actions: ['mediaconvert:DescribeEndpoints'],
                            resources: [
                                Stack.of(this).formatArn({
                                    service: 'mediaconvert',
                                    resource: 'endpoints',
                                    resourceName: '*',
                                })
                            ],
                        }),
                        new iam.PolicyStatement({
                            effect: iam.Effect.ALLOW,
                            actions: [
                                'kms:GenerateDataKey',
                                'kms:Decrypt',
                            ],
                            resources: [
                                mieKey.keyArn
                            ],
                        }),
                    ]
                }),
            },
        });

        // cdk_nag
        NagSuppressions.addResourceSuppressions(helperExecutionRole, [
            { id: 'AwsSolutions-IAM5', reason: "Resource ARNs are not generated at the time of policy creation", },
        ]);

        const stageExecutionRole = new iam.Role(this, 'StageExecutionRole', {
            assumedBy: new iam.ServicePrincipal('lambda.amazonaws.com'),
            inlinePolicies: {
                [`${Aws.STACK_NAME}-stage-execution-lambda`]: new iam.PolicyDocument({
                    statements: [
                        new iam.PolicyStatement({
                            effect: iam.Effect.ALLOW,
                            actions: ['states:StartExecution'],
                            resources: [
                                Stack.of(this).formatArn({
                                    service: 'states',
                                    resource: 'stateMachine',
                                    resourceName: '*',
                                    arnFormat: ArnFormat.COLON_RESOURCE_NAME,
                                })
                            ],
                            conditions: {
                                StringEquals: {
                                    ['aws:ResourceTag/environment']: 'mie'
                                }
                            }
                        }),
                        new iam.PolicyStatement({
                            effect: iam.Effect.ALLOW,
                            actions: [
                                "dynamodb:GetItem",
                                "dynamodb:Query",
                                "dynamodb:Scan",
                                "dynamodb:DescribeTable",
                                "dynamodb:BatchGetItem",
                                "dynamodb:GetRecords",
                                "dynamodb:DescribeLimits",
                                "dynamodb:PutItem",
                                "dynamodb:UpdateItem",
                                "dynamodb:DeleteItem",
                                "dynamodb:BatchWriteItem",
                            ],
                            resources: [
                                workflowTable.tableArn,
                                workflowExecutionTable.tableArn,
                                `${workflowExecutionTable.tableArn}/index/*`,
                                systemTable.tableArn,
                            ],
                        }),
                        new iam.PolicyStatement({
                            effect: iam.Effect.ALLOW,
                            actions: [
                                'logs:CreateLogGroup',
                                'logs:CreateLogStream',
                                'logs:PutLogEvents',
                            ],
                            resources: [
                                Stack.of(this).formatArn({
                                    service: 'logs',
                                    resource: 'log-group',
                                    resourceName: '/aws/lambda/*',
                                    arnFormat: ArnFormat.COLON_RESOURCE_NAME,
                                })
                            ],
                        }),
                        new iam.PolicyStatement({
                            effect: iam.Effect.ALLOW,
                            actions: [
                                "sqs:DeleteMessage",
                                "sqs:ListQueues",
                                "sqs:ChangeMessageVisibility",
                                "sqs:ReceiveMessage",
                                "sqs:SendMessage",
                            ],
                            resources: [
                                stageExecutionQueue.queueArn,
                                workflowExecutionLambdaDeadLetterQueue.queueArn,
                            ],
                        }),
                        new iam.PolicyStatement({
                            effect: iam.Effect.ALLOW,
                            actions: [
                                "xray:PutTraceSegments",
                                "xray:PutTelemetryRecords",
                            ],
                            resources: ['*'],
                        }),
                        new iam.PolicyStatement({
                            effect: iam.Effect.ALLOW,
                            actions: ['kms:Decrypt'],
                            resources: [
                                mieKey.keyArn
                            ],
                        }),
                    ]
                })
            }
        });

        const stepFunctionRole = new iam.Role(this, 'StepFunctionRole', {
            assumedBy: new iam.ServicePrincipal('states.amazonaws.com'),
            inlinePolicies: {
                [`${Aws.STACK_NAME}-sfn-lambda-exec`]: new iam.PolicyDocument({
                    statements: [
                        new iam.PolicyStatement({
                            effect: iam.Effect.ALLOW,
                            actions: [
                                "lambda:InvokeFunction",
                            ],
                            resources: [
                                "arn:aws:lambda:*:*:function:*OperatorLibrary*",
                                "arn:aws:lambda:*:*:function:*start-wait-operation",
                                "arn:aws:lambda:*:*:function:*check-wait-operation",
                                "arn:aws:lambda:*:*:function:*CompleteStageLambda*",
                                "arn:aws:lambda:*:*:function:*OperatorFailedLambda*",
                                "arn:aws:lambda:*:*:function:*FilterOperationLambda*",
                            ],
                        }),
                        new iam.PolicyStatement({
                            effect: iam.Effect.ALLOW,
                            actions: [
                                "xray:PutTraceSegments",
                                "xray:PutTelemetryRecords",
                                "xray:GetSamplingRules",
                                "xray:GetSamplingTargets",
                            ],
                            resources: ['*'],
                        }),
                        new iam.PolicyStatement({
                            effect: iam.Effect.ALLOW,
                            actions: [
                                "logs:CreateLogDelivery",
                                "logs:GetLogDelivery",
                                "logs:UpdateLogDelivery",
                                "logs:DeleteLogDelivery",
                                "logs:ListLogDeliveries",
                                "logs:PutResourcePolicy",
                                "logs:DescribeResourcePolicies",
                                "logs:DescribeLogGroups",
                            ],
                            resources: ['*'],
                        }),
                    ]
                })
            }
        });

        const operatorFailedRole = new iam.Role(this, 'operatorFailedRole', {
            assumedBy: new iam.ServicePrincipal('lambda.amazonaws.com'),
            inlinePolicies: {
                [`${Aws.STACK_NAME}-operator-failed`]: new iam.PolicyDocument({
                    statements: [
                        new iam.PolicyStatement({
                            effect: iam.Effect.ALLOW,
                            actions: [
                                "logs:CreateLogGroup",
                                "logs:CreateLogStream",
                                "logs:PutLogEvents",
                            ],
                            resources: [
                                Stack.of(this).formatArn({
                                    service: 'logs',
                                    region: '*',
                                    account: '*',
                                    resource: '*',
                                    resourceName: '*',
                                    arnFormat: ArnFormat.COLON_RESOURCE_NAME,
                                }),
                            ],
                        }),
                        new iam.PolicyStatement({
                            effect: iam.Effect.ALLOW,
                            actions: [
                                "xray:PutTraceSegments",
                                "xray:PutTelemetryRecords",
                            ],
                            resources: ['*'],
                        }),
                    ]
                })
            }
        });

        const workflowExecutionStreamLambdaRole = new iam.Role(this, 'WorkflowExecutionStreamLambdaRole', {
            assumedBy: new iam.ServicePrincipal('lambda.amazonaws.com'),
            inlinePolicies: {
                [`${Aws.STACK_NAME}-WorkflowExecutionLambdaStreamAccessPolicy`]: new iam.PolicyDocument({
                    statements: [
                        new iam.PolicyStatement({
                            effect: iam.Effect.ALLOW,
                            actions: [
                                "dynamodb:DescribeStream",
                                "dynamodb:GetRecords",
                                "dynamodb:GetShardIterator",
                                "dynamodb:ListStreams",
                            ],
                            resources: [
                                workflowExecutionTable.tableStreamArn!,
                            ],
                        }),
                        new iam.PolicyStatement({
                            effect: iam.Effect.ALLOW,
                            actions: [
                                "sns:Publish",
                            ],
                            resources: [
                                workflowExecutionEventTopic.topicArn,
                            ],
                        }),
                        new iam.PolicyStatement({
                            effect: iam.Effect.ALLOW,
                            actions: [
                                'logs:CreateLogGroup',
                                'logs:CreateLogStream',
                                'logs:PutLogEvents',
                            ],
                            resources: [
                                Stack.of(this).formatArn({
                                    service: 'logs',
                                    resource: 'log-group',
                                    resourceName: '/aws/lambda/*',
                                    arnFormat: ArnFormat.COLON_RESOURCE_NAME,
                                })
                            ],
                        }),
                        new iam.PolicyStatement({
                            effect: iam.Effect.ALLOW,
                            actions: [
                                "kms:GenerateDataKey",
                                "kms:Decrypt",
                            ],
                            resources: [
                                mieKey.keyArn
                            ],
                        }),
                    ]
                })
            }
        });

        const anonymousDataCustomResourceRole = new iam.Role(this, 'AnonymousDataCustomResourceRole', {
            assumedBy: new iam.ServicePrincipal('lambda.amazonaws.com'),
            path: '/',
            inlinePolicies: {
                [`${Aws.STACK_NAME}-anonymous-data-logger`]: new iam.PolicyDocument({
                    statements: [
                        new iam.PolicyStatement({
                            effect: iam.Effect.ALLOW,
                            actions: [
                                'logs:CreateLogGroup',
                                'logs:CreateLogStream',
                                'logs:PutLogEvents',
                            ],
                            resources: [
                                Stack.of(this).formatArn({
                                    service: 'logs',
                                    resource: 'log-group',
                                    resourceName: '/aws/lambda/*',
                                    arnFormat: ArnFormat.COLON_RESOURCE_NAME,
                                })
                            ],
                        }),
                        new iam.PolicyStatement({
                            effect: iam.Effect.ALLOW,
                            actions: ['ssm:PutParameter'],
                            resources: [
                                Stack.of(this).formatArn({
                                    service: 'ssm',
                                    resource: 'parameter',
                                    resourceName: '*',
                                })
                            ],
                        }),
                    ]
                }),
            },
        });

        // cdk_nag
        NagSuppressions.addResourceSuppressions(anonymousDataCustomResourceRole, [
            { id: 'AwsSolutions-IAM5', reason: "Resource ARNs are not generated at the time of policy creation", },
        ]);


        //
        // Lambda Layers
        //

        function codeFromRegionalBucket(name: string): lambda.Code {
            return sourceCodeMap.codeFromRegionalBucket(name);
        }

        function createLambdaLayerVersion(scope: Construct, runtime: lambda.Runtime): lambda.LayerVersion {
            // e.g., "python3.9"
            const runtimeStr = `${runtime}`;
            // e.g., "python39"
            const langXY = runtimeStr.replace('.','');
            // e.g., "Python39"
            const LangXY = langXY.replace(/^[a-z]/, x => x.toUpperCase());
            // e.g., "Python 3.9"
            const Lang_X_Y = runtimeStr.replace(/[0-9]/, x => ` ${x}`).replace(/^[a-z]/, x => x.toUpperCase());

            return new lambda.LayerVersion(scope, `MediaInsightsEngine${LangXY}Layer`, {
                removalPolicy: RemovalPolicy.RETAIN,
                compatibleRuntimes: [runtime],
                code: codeFromRegionalBucket(`media_insights_engine_lambda_layer_${runtime}.zip`),
                description: `Boto3 and MediaInsightsEngineLambdaHelper packages for ${Lang_X_Y}`,
                layerVersionName: `media-insights-engine-${langXY}`,
                license: "Apache-2.0",
            });
        }

        const python39Layer = createLambdaLayerVersion(this, lambda.Runtime.PYTHON_3_9);
        const python38Layer = createLambdaLayerVersion(this, lambda.Runtime.PYTHON_3_8);
        const python37Layer = createLambdaLayerVersion(this, lambda.Runtime.PYTHON_3_7);


        //
        // Services - Lambda
        //

        const STAGE_EXECUTION_QUEUE_URL = stageExecutionQueue.queueUrl;
        const STAGE_TABLE_NAME = stageTable.tableName;
        const OPERATION_TABLE_NAME = operationTable.tableName;
        const WORKFLOW_EXECUTION_TABLE_NAME = workflowExecutionTable.tableName;
        const WORKFLOW_TABLE_NAME = workflowTable.tableName;
        const SYSTEM_TABLE_NAME = systemTable.tableName;
        const DEFAULT_MAX_CONCURRENT_WORKFLOWS = maxConcurrentWorkflows.valueAsString;
        const botoConfig = `{"user_agent_extra": "AwsSolution/${solutionId.valueAsString}/${solutionVersion.valueAsString}"}`;

        const helperFunction = new lambda.Function(this, 'MieHelperFunction', {
            environment: {
                SYSTEM_TABLE_NAME,
                DEFAULT_MAX_CONCURRENT_WORKFLOWS,
            },
            handler: "index.handler",
            runtime: lambda.Runtime.PYTHON_3_9,
            code: helperFunctionCode,
            role: helperExecutionRole,
        });

        helperFunction.addPermission('Permissions', {
            principal: new iam.ServicePrincipal('cloudformation.amazonaws.com')
        });

        const getShortUUID = new CustomResource(this, 'GetShortUUID', {
            resourceType: "Custom::CustomResource",
            serviceToken: helperFunction.functionArn,
            properties: {
                FunctionKey: "get_short_uuid"
            },
        });

        const ShortUUID = getShortUUID.getAttString('Data');

        const initSystemTable = new CustomResource(this, 'InitSystemTable', {
            resourceType: "Custom::CustomResource",
            serviceToken: helperFunction.functionArn,
            properties: {
                FunctionKey: "init_system_table"
            },
        })

        const getMediaConvertEndpoint = new CustomResource(this, 'GetMediaConvertEndpoint', {
            resourceType: "Custom::CustomResource",
            serviceToken: helperFunction.functionArn,
            properties: {
                FunctionKey: "get_mediaconvert_endpoint"
            },
        });

        const workflowSchedulerLambda = new lambda.Function(this, 'WorkflowSchedulerLambda', {
            environment: {
                STAGE_EXECUTION_QUEUE_URL,
                STAGE_TABLE_NAME,
                OPERATION_TABLE_NAME,
                WORKFLOW_EXECUTION_TABLE_NAME,
                WORKFLOW_TABLE_NAME,
                SYSTEM_TABLE_NAME,
                DEFAULT_MAX_CONCURRENT_WORKFLOWS,
                botoConfig,
            },
            handler: "app.workflow_scheduler_lambda",
            tracing: `${Fn.conditionIf(enableTraceOnEntryPoints.logicalId, lambda.Tracing.ACTIVE, lambda.Tracing.PASS_THROUGH)}` as lambda.Tracing,
            code: codeFromRegionalBucket('workflow.zip'),
            layers: [ python39Layer ],
            memorySize: 256,
            role: stageExecutionRole,
            runtime: lambda.Runtime.PYTHON_3_9,
            timeout: Duration.seconds(900),
            reservedConcurrentExecutions: 1,
            deadLetterQueue: workflowExecutionLambdaDeadLetterQueue,
        });

        new events.Rule(this, 'LambdaSchedule', {
            description: "A schedule for the Lambda function..",
            schedule: events.Schedule.rate(Duration.minutes(1)),
            targets: [
                new targets.LambdaFunction(workflowSchedulerLambda)
            ],
        }).node.addDependency(workflowSchedulerLambda);

        const WORKFLOW_SCHEDULER_LAMBDA_ARN = workflowSchedulerLambda.functionArn;

        const operationLambdaExecutionRole = new iam.Role(this, 'OperationLambdaExecutionRole', {
            assumedBy: new iam.ServicePrincipal('lambda.amazonaws.com'),
            inlinePolicies: {
                [`${Aws.STACK_NAME}-operation-lambda`]: new iam.PolicyDocument({
                    statements: [
                        new iam.PolicyStatement({
                            effect: iam.Effect.ALLOW,
                            actions: [
                                "states:DescribeExecution",
                                "states:GetExecutionHistory",
                                "states:StopExecution",
                            ],
                            resources: [
                                Stack.of(this).formatArn({
                                    service: 'states',
                                    resource: 'execution',
                                    resourceName: '*:*',
                                    arnFormat: ArnFormat.COLON_RESOURCE_NAME,
                                })
                            ],
                        }),
                        new iam.PolicyStatement({
                            effect: iam.Effect.ALLOW,
                            actions: ['states:StartExecution'],
                            resources: [
                                Stack.of(this).formatArn({
                                    service: 'states',
                                    resource: 'stateMachine',
                                    resourceName: '*',
                                    arnFormat: ArnFormat.COLON_RESOURCE_NAME,
                                })
                            ],
                            conditions: {
                                StringEquals: {
                                    ['aws:ResourceTag/environment']: 'mie'
                                }
                            }
                        }),
                        new iam.PolicyStatement({
                            effect: iam.Effect.ALLOW,
                            actions: [
                                "dynamodb:GetItem",
                                "dynamodb:Query",
                                "dynamodb:Scan",
                                "dynamodb:DescribeTable",
                                "dynamodb:BatchGetItem",
                                "dynamodb:GetRecords",
                                "dynamodb:DescribeLimits",
                                "dynamodb:PutItem",
                                "dynamodb:UpdateItem",
                                "dynamodb:DeleteItem",
                                "dynamodb:BatchWriteItem",
                            ],
                            resources: [
                                workflowTable.tableArn,
                                workflowExecutionTable.tableArn,
                                `${workflowExecutionTable.tableArn}/index/*`,
                                systemTable.tableArn,
                            ],
                        }),
                        new iam.PolicyStatement({
                            effect: iam.Effect.ALLOW,
                            actions: [
                                'logs:CreateLogGroup',
                                'logs:CreateLogStream',
                                'logs:PutLogEvents',
                            ],
                            resources: [
                                Stack.of(this).formatArn({
                                    service: 'logs',
                                    resource: 'log-group',
                                    resourceName: '/aws/lambda/*',
                                    arnFormat: ArnFormat.COLON_RESOURCE_NAME,
                                })
                            ],
                        }),
                        new iam.PolicyStatement({
                            effect: iam.Effect.ALLOW,
                            actions: [
                                "sqs:DeleteMessage",
                                "sqs:ListQueues",
                                "sqs:ChangeMessageVisibility",
                                "sqs:ReceiveMessage",
                                "sqs:SendMessage",
                            ],
                            resources: [
                                stageExecutionQueue.queueArn,
                                workflowExecutionLambdaDeadLetterQueue.queueArn,
                            ],
                        }),
                        new iam.PolicyStatement({
                            effect: iam.Effect.ALLOW,
                            actions: [
                                "lambda:InvokeFunction",
                            ],
                            resources: [
                                workflowSchedulerLambda.functionArn,
                            ],
                        }),
                        new iam.PolicyStatement({
                            effect: iam.Effect.ALLOW,
                            actions: [
                                "xray:PutTraceSegments",
                                "xray:PutTelemetryRecords",
                            ],
                            resources: ['*'],
                        }),
                        new iam.PolicyStatement({
                            effect: iam.Effect.ALLOW,
                            actions: ['kms:Decrypt'],
                            resources: [
                                mieKey.keyArn
                            ],
                        }),
                    ]
                })
            }
        });

        const workflowErrorHandlerLambda = new lambda.Function(this, 'WorkflowErrorHandlerLambda', {
            environment: {
                STAGE_EXECUTION_QUEUE_URL,
                STAGE_TABLE_NAME,
                OPERATION_TABLE_NAME,
                WORKFLOW_EXECUTION_TABLE_NAME,
                WORKFLOW_TABLE_NAME,
                SYSTEM_TABLE_NAME,
                DEFAULT_MAX_CONCURRENT_WORKFLOWS,
                ShortUUID,
                WORKFLOW_SCHEDULER_LAMBDA_ARN,
            },
            handler: "app.workflow_error_handler_lambda",
            tracing: `${Fn.conditionIf(enableTraceOnEntryPoints.logicalId, lambda.Tracing.ACTIVE, lambda.Tracing.PASS_THROUGH)}` as lambda.Tracing,
            code: codeFromRegionalBucket('workflow.zip'),
            layers: [ python39Layer ],
            memorySize: 256,
            role: operationLambdaExecutionRole,
            runtime: lambda.Runtime.PYTHON_3_9,
            timeout: Duration.seconds(900),
            reservedConcurrentExecutions: 1,
            deadLetterQueue: workflowExecutionLambdaDeadLetterQueue,
        });

        new events.Rule(this, 'StateMachineErrorCloudWatchEvent', {
            ruleName: `${Aws.STACK_NAME}-state-error-handler`,
            description: "state machine error handler",
            eventPattern: {
                source: ["aws.states"],
                detailType: ["Step Functions Execution Status Change"],
                detail: {
                    status: [
                        "FAILED",
                        "ABORTED",
                        "TIMED_OUT",
                    ],
                },
            },
            targets: [
                new targets.LambdaFunction(workflowErrorHandlerLambda)
            ],
        }).node.addDependency(workflowErrorHandlerLambda);

        const completeStageLambda = new lambda.Function(this, 'CompleteStageLambda', {
            environment: {
                botoConfig,
                STAGE_EXECUTION_QUEUE_URL,
                STAGE_TABLE_NAME,
                OPERATION_TABLE_NAME,
                WORKFLOW_EXECUTION_TABLE_NAME,
                WORKFLOW_TABLE_NAME,
                SYSTEM_TABLE_NAME,
                WORKFLOW_SCHEDULER_LAMBDA_ARN,
            },
            handler: "app.complete_stage_execution_lambda",
            tracing: lambda.Tracing.PASS_THROUGH,
            code: codeFromRegionalBucket('workflow.zip'),
            layers: [ python39Layer ],
            memorySize: 256,
            role: operationLambdaExecutionRole,
            runtime: lambda.Runtime.PYTHON_3_9,
            timeout: Duration.seconds(900),
        });
        completeStageLambda.node.addDependency(workflowSchedulerLambda);

        const filterOperationLambda = new lambda.Function(this, 'FilterOperationLambda', {
            environment: {
                botoConfig,
                STAGE_EXECUTION_QUEUE_URL,
                STAGE_TABLE_NAME,
                OPERATION_TABLE_NAME,
                WORKFLOW_EXECUTION_TABLE_NAME,
                WORKFLOW_TABLE_NAME,
            },
            handler: "app.filter_operation_lambda",
            tracing: lambda.Tracing.PASS_THROUGH,
            code: codeFromRegionalBucket('workflow.zip'),
            layers: [ python39Layer ],
            memorySize: 256,
            role: operationLambdaExecutionRole,
            runtime: lambda.Runtime.PYTHON_3_9,
            timeout: Duration.seconds(900),
        });

        const operatorFailedLambda = new lambda.Function(this, 'OperatorFailedLambda', {
            handler: "operator_failed.lambda_handler",
            tracing: lambda.Tracing.PASS_THROUGH,
            code: codeFromRegionalBucket('operator_failed.zip'),
            layers: [ python39Layer ],
            role: operatorFailedRole,
            runtime: lambda.Runtime.PYTHON_3_9,
        });

        const startWaitOperationLambda = new lambda.Function(this, 'StartWaitOperationLambda', {
            functionName: `${Aws.STACK_NAME}-start-wait-operation`,
            environment: {
                botoConfig,
                STAGE_EXECUTION_QUEUE_URL,
                STAGE_TABLE_NAME,
                OPERATION_TABLE_NAME,
                WORKFLOW_EXECUTION_TABLE_NAME,
                WORKFLOW_TABLE_NAME,
            },
            handler: "app.start_wait_operation_lambda",
            code: codeFromRegionalBucket('workflow.zip'),
            layers: [ python39Layer ],
            memorySize: 256,
            role: operationLambdaExecutionRole,
            runtime: lambda.Runtime.PYTHON_3_9,
            timeout: Duration.seconds(900),
        });

        const checkWaitOperationLambda = new lambda.Function(this, 'CheckWaitOperationLambda', {
            functionName: `${Aws.STACK_NAME}-check-wait-operation`,
            environment: {
                botoConfig,
                STAGE_EXECUTION_QUEUE_URL,
                STAGE_TABLE_NAME,
                OPERATION_TABLE_NAME,
                WORKFLOW_EXECUTION_TABLE_NAME,
                WORKFLOW_TABLE_NAME,
            },
            handler: "app.check_wait_operation_lambda",
            code: codeFromRegionalBucket('workflow.zip'),
            layers: [ python39Layer ],
            memorySize: 256,
            role: operationLambdaExecutionRole,
            runtime: lambda.Runtime.PYTHON_3_9,
            timeout: Duration.seconds(900),
        });

        const workflowExecutionStreamingFunction = new lambda.Function(this, 'WorkflowExecutionStreamingFunction', {
            environment: {
                botoConfig,
                TOPIC_ARN: workflowExecutionEventTopic.topicArn,
            },
            handler: "workflowstream.lambda_handler",
            code: codeFromRegionalBucket('workflowstream.zip'),
            role: workflowExecutionStreamLambdaRole,
            runtime: lambda.Runtime.PYTHON_3_9,
        });

        const anonymousDataCustomResource = new lambda.Function(this, 'AnonymousDataCustomResource', {
            functionName: `${Aws.STACK_NAME}-anonymous-data`,
            description: "Used to send anonymous data",
            handler: "anonymous-data-logger.handler",
            code: codeFromRegionalBucket('anonymous-data-logger.zip'),
            role: anonymousDataCustomResourceRole,
            runtime: lambda.Runtime.PYTHON_3_9,
            timeout: Duration.seconds(180),
        });

        // cfn_nag
        [
            helperFunction,
            workflowSchedulerLambda,
            workflowErrorHandlerLambda,
            completeStageLambda,
            filterOperationLambda,
            operatorFailedLambda,
            startWaitOperationLambda,
            checkWaitOperationLambda,
            workflowExecutionStreamingFunction,
            anonymousDataCustomResource,
        ].forEach(l => util.setNagSuppressRules(l,
            {
                id: 'W89',
                reason: "This Lambda function does not need to access any resource provisioned within a VPC.",
            },
            {
                id: 'W92',
                reason: "This function does not require performance optimization, so the default concurrency limits suffice.",
            },
        ));


        // stream event mapping for lambda

        workflowExecutionStreamingFunction.addEventSourceMapping('EventMapping', {
            eventSourceArn: workflowExecutionTable.tableStreamArn!,
            startingPosition: lambda.StartingPosition.LATEST,
        });

        //
        // LogGroup
        //

        const stepFunctionLogGroup = new logs.LogGroup(this, 'StepFunctionLogGroup', {
            retention: logs.RetentionDays.TWO_WEEKS,
            logGroupName: `/aws/vendedlogs/states/${Aws.STACK_NAME}-StepFunctionLogGroup-${ShortUUID}`,
        });

        // cfn_nag
        util.setNagSuppressRules(stepFunctionLogGroup, {
            id: 'W84',
            reason: "Log group data is encrypted by default in CloudWatch",
        });

        // Tag Resources

        [
            helperFunction,
            helperExecutionRole,
            stageExecutionRole,
            operationLambdaExecutionRole,
            stepFunctionLogGroup,
            stepFunctionRole,
            operatorFailedRole,
            systemTable,
            workflowTable,
            stageTable,
            operationTable,
            historyTable,
            workflowExecutionTable,
            dataplaneTable,
            dataplaneLogsBucket,
            dataplaneBucket,
            workflowExecutionLambdaDeadLetterQueue,
            stageExecutionDeadLetterQueue,
            stageExecutionQueue,
            workflowSchedulerLambda,
            workflowErrorHandlerLambda,
            completeStageLambda,
            filterOperationLambda,
            operatorFailedLambda,
            startWaitOperationLambda,
            checkWaitOperationLambda,
            workflowExecutionStreamingFunction,
        ].forEach(util.addMediaInsightsTag);

        //
        // Nested Stacks
        //

        const dataplaneApiStack = new DataplaneApiStack(this, 'MediaInsightsDataplaneApiStack', {
            parameters: {
                botoConfig,
                DataplaneTableName: dataplaneTable.tableName,
                ExternalBucketArn: externalBucketArn.valueAsString,
                DataplaneBucketName: dataplaneBucket.bucketName,
                DeploymentPackageBucket: sourceCodeMap.getRegionalS3BucketName(),
                TracingConfigMode: `${Fn.conditionIf(enableTraceOnEntryPoints.logicalId, lambda.Tracing.ACTIVE, lambda.Tracing.PASS_THROUGH)}`,
                DeploymentPackageKey: sourceCodeMap.getSourceCodeKey("dataplaneapi.zip"),
                MediaInsightsEnginePython39Layer: python39Layer.layerVersionArn,
                FrameworkVersion: sourceCodeMap.findInMap("FrameworkVersion"),
                KmsKeyId: mieKey.keyId,
            },
        });
        initSystemTable.node.addDependency(dataplaneApiStack);

        const workflowApiStack = new WorkflowApiStack(this, 'MediaInsightsWorkflowApi', {
            parameters: {
                botoConfig,
                ShortUUID,
                StageExecutionQueueUrl: stageExecutionQueue.queueUrl,
                StageExecutionRole: stepFunctionRole.roleArn,
                StepFunctionLogGroupArn: stepFunctionLogGroup.logGroupArn,
                OperationTableName: operationTable.tableName,
                StageTableName: stageTable.tableName,
                WorkflowExecutionTableName: workflowExecutionTable.tableName,
                WorkflowTableName: workflowTable.tableName,
                HistoryTableName: historyTable.tableName,
                SystemTableName: systemTable.tableName,
                SqsQueueArn: stageExecutionQueue.queueArn,
                MediaInsightsEnginePython39Layer: python39Layer.layerVersionArn,
                TracingConfigMode: `${Fn.conditionIf(enableTraceOnEntryPoints.logicalId, lambda.Tracing.ACTIVE, lambda.Tracing.PASS_THROUGH)}`,
                CompleteStageLambdaArn: completeStageLambda.functionArn,
                FilterOperationLambdaArn: filterOperationLambda.functionArn,
                WorkflowSchedulerLambdaArn: workflowSchedulerLambda.functionArn,
                DataplaneEndpoint: `${dataplaneApiStack.nestedStackResource!.getAtt('Outputs.APIHandlerName')}`,
                DataplaneHandlerArn: `${dataplaneApiStack.nestedStackResource!.getAtt('Outputs.APIHandlerArn')}`,
                DataPlaneBucket: dataplaneBucket.bucketName,
                OperatorFailedHandlerLambdaArn: operatorFailedLambda.functionArn,
                DeploymentPackageBucket: sourceCodeMap.getRegionalS3BucketName(),
                DeploymentPackageKey: sourceCodeMap.getSourceCodeKey("workflowapi.zip"),
                FrameworkVersion: sourceCodeMap.findInMap("FrameworkVersion"),
                KmsKeyId: mieKey.keyId,
            },
        });

        const analyticsStack = new AnalyticsStack(this, 'Analytics', {
            kmsKey: mieKey,
            dynamoStream: dataplaneTable,
            parameters: {
                botoConfig,
            },
        });
        util.setCondition(analyticsStack, deployAnalyticsCondition);
        analyticsStack.node.addDependency(workflowApiStack);
        analyticsStack.node.addDependency(dataplaneApiStack);

        const operatorLibraryStack = new OperatorLibraryStack(this, 'OperatorLibrary', {
            python39Layer,
            python38Layer,
            python37Layer,
            kmsKey: mieKey,
            parameters: {
                DataPlaneBucket: dataplaneBucket.bucketName,
                ExternalBucketArn: externalBucketArn.valueAsString,
                DataPlaneEndpoint: `${dataplaneApiStack.nestedStackResource!.getAtt('Outputs.APIHandlerName')}`,
                DataPlaneHandlerArn: `${dataplaneApiStack.nestedStackResource!.getAtt('Outputs.APIHandlerArn')}`,
                WorkflowCustomResourceArn: `${workflowApiStack.nestedStackResource!.getAtt('Outputs.WorkflowCustomResourceArn')}`,
                StartWaitOperationLambda: startWaitOperationLambda.functionArn,
                CheckWaitOperationLambda: checkWaitOperationLambda.functionArn,
                MediaConvertEndpoint: getMediaConvertEndpoint.getAttString('Data'),
                Boto3UserAgent: botoConfig,
            },
        });
        operatorLibraryStack.addDependency(workflowApiStack);
        operatorLibraryStack.addDependency(dataplaneApiStack);

        const testResourcesStack = new TestResourcesStack(this, 'TestResources', {
            python39Layer,
            parameters: {
                DataplaneEndpoint: `${dataplaneApiStack.nestedStackResource!.getAtt('Outputs.APIHandlerName')}`,
                DataPlaneBucket: dataplaneBucket.bucketName,
            },
        });
        util.setCondition(testResourcesStack, deployTestResourcesCondition);
        testResourcesStack.addDependency(workflowApiStack);
        testResourcesStack.addDependency(dataplaneApiStack);
        testResourcesStack.addDependency(operatorLibraryStack);


        this.nestedStacks = {
            dataplaneApiStack,
            workflowApiStack,
            analyticsStack,
            operatorLibraryStack,
            testResourcesStack,
        };

        // SendAnonymousData
        const anonymousDataUuid = new CustomResource(this, 'AnonymousDataUuid', {
            resourceType: "Custom::UUID",
            serviceToken: anonymousDataCustomResource.functionArn,
            properties: {
                Resource: 'UUID',
            },
        });

        const anonymousMetric = new CustomResource(this, 'AnonymousMetric', {
            resourceType: "Custom::AnonymousMetric",
            serviceToken: anonymousDataCustomResource.functionArn,
            properties: {
                Resource: 'AnonymousMetric',
                SolutionId: "SO0163",
                UUID: anonymousDataUuid.getAttString('UUID'),
                Version: sourceCodeMap.findInMap("FrameworkVersion"),
            },
        });

        [anonymousDataUuid, anonymousMetric].forEach(c => util.setCondition(c, enableAnonymousData));

        //
        // cfn_nag rules
        //

        // cfn_nag
        [stageExecutionRole, operationLambdaExecutionRole, operatorFailedRole]
            .forEach(role => util.setNagSuppressRules(role, {
                id: 'W11',
                id2: 'AwsSolutions-IAM5',
                reason: "The X-Ray policy uses actions that must be applied to all resources. See https://docs.aws.amazon.com/xray/latest/devguide/security_iam_id-based-policy-examples.html#xray-permissions-resources",
            }));

        // cfn_nag
        util.setNagSuppressRules(stepFunctionRole, {
            id: 'W11',
            id2: 'AwsSolutions-IAM5',
            reason: "The X-Ray and Cloudwatch policies use actions that must be applied to all resources. See https://docs.aws.amazon.com/xray/latest/devguide/security_iam_id-based-policy-examples.html#xray-permissions-resources and https://docs.aws.amazon.com/service-authorization/latest/reference/list_amazoncloudwatchlogs.html",
        });

        // cfn_nag
        util.setNagSuppressRules(workflowExecutionStreamLambdaRole, {
            id: 'W11',
            id2: 'AwsSolutions-IAM5',
            reason: "Lambda requires ability to write to cloudwatch *, as configured in the default AWS lambda execution role.",
        });

        //
        // Outputs
        //

        new CfnOutput(this, 'OperatorLibraryStack', {
            description: "Nested cloudformation stack that contains the MIE operator library",
            value: operatorLibraryStack.stackName,
            exportName: Fn.join(':', [Aws.STACK_NAME, 'OperatorLibraryStack']),
        });
        new CfnOutput(this, 'DataplaneBucket', {
            description: "Bucket used to store transfomred media object from workflow execution",
            value: dataplaneBucket.bucketName,
            exportName: Fn.join(':', [Aws.STACK_NAME, 'DataplaneBucket']),
        });
        new CfnOutput(this, 'DataplaneApiEndpoint', {
            description: "Endpoint for data persistence API",
            value:  `${dataplaneApiStack.nestedStackResource!.getAtt('Outputs.EndpointURL')}`,
            exportName: Fn.join(':', [Aws.STACK_NAME, 'DataplaneApiEndpoint']),
        });
        new CfnOutput(this, 'DataPlaneHandlerArn', {
            description: "API Handler Lambda ARN for dataplane.",
            value:  `${dataplaneApiStack.nestedStackResource!.getAtt('Outputs.APIHandlerArn')}`,
            exportName: Fn.join(':', [Aws.STACK_NAME, 'DataPlaneHandlerArn']),
        });
        new CfnOutput(this, 'DataplaneApiRestID', {
            description: "REST API ID for dataplane API",
            value: `${dataplaneApiStack.nestedStackResource!.getAtt('Outputs.RestAPIId')}`,
            exportName: Fn.join(':', [Aws.STACK_NAME, 'DataplaneApiId']),
        });workflowApiStack
        new CfnOutput(this, 'WorkflowCustomResourceArn', {
            description: "Custom resource for creating operations, stages and workflows using CloudFormation",
            value: `${workflowApiStack.nestedStackResource!.getAtt('Outputs.WorkflowCustomResourceArn')}`,
            exportName: Fn.join(':', [Aws.STACK_NAME, 'WorkflowCustomResourceArn']),
        });
        new CfnOutput(this, 'WorkflowApiEndpoint', {
            description: "Endpoint for workflow Creation, Execution and Monitoring API",
            value: `${workflowApiStack.nestedStackResource!.getAtt('Outputs.EndpointURL')}`,
            exportName: Fn.join(':', [Aws.STACK_NAME, 'WorkflowApiEndpoint']),
        });
        new CfnOutput(this, 'WorkflowApiRestID', {
            description: "REST API ID for workflow API",
            value: `${workflowApiStack.nestedStackResource!.getAtt('Outputs.RestAPIId')}`,
            exportName: Fn.join(':', [Aws.STACK_NAME, 'WorkflowApiId']),
        });
        new CfnOutput(this, 'MediaInsightsEnginePython39LayerArn', {
            description: "Lambda layer for Python libraries",
            value: python39Layer.layerVersionArn,
            exportName: Fn.join(':', [Aws.STACK_NAME, 'MediaInsightsEnginePython39Layer']),
        });
        new CfnOutput(this, 'AnalyticsStreamArn', {
            description: "Arn of the dataplane pipeline",
            value: analyticsStack.analyticsStream.streamArn,
            exportName: Fn.join(':', [Aws.STACK_NAME, 'AnalyticsStreamArn']),
        });
        new CfnOutput(this, 'TestStack', {
            condition: deployTestResourcesCondition,
            value: testResourcesStack.stackId,
        });
        new CfnOutput(this, 'Version', {
            description: "Media Insights Engine Version",
            value: sourceCodeMap.findInMap("FrameworkVersion"),
            exportName: Fn.join(':', [Aws.STACK_NAME, 'Version']),
        });
        new CfnOutput(this, 'MieKMSArn', {
            description: "ARN of the MIE KMS Key",
            value: mieKey.keyArn,
            exportName: Fn.join(':', [Aws.STACK_NAME, 'MieKMSArn']),
        });
        new CfnOutput(this, 'MieKMSId', {
            description: "ID of the MIE KMS Key",
            value: mieKey.keyId,
            exportName: Fn.join(':', [Aws.STACK_NAME, 'MieKMSId']),
        });
        new CfnOutput(this, 'MieKMSAlias', {
            description: "Alias of the MIE KMS Key",
            value: keyAlias.aliasName,
            exportName: Fn.join(':', [Aws.STACK_NAME, 'MieKMSAlias']),
        });
        new CfnOutput(this, 'MieSNSTopic', {
            description: "ARN of the MIE SNS Workflow Execution Topic",
            value: workflowExecutionEventTopic.topicArn,
            exportName: Fn.join(':', [Aws.STACK_NAME, 'MieSNSTopic']),
        });
        new CfnOutput(this, 'MieSQSQueue', {
            description: "ARN of the MIE Workflow Execution Queue",
            value: workflowExecutionEventQueue.queueArn,
            exportName: Fn.join(':', [Aws.STACK_NAME, 'MieSQSQueue']),
        });

    }

    getLogicalId(element: CfnElement): string {
        return util.cleanUpLogicalId(super.getLogicalId(element));
    }
}


const helperFunctionCode = new lambda.InlineCode(
`import string
import cfnresponse
import random
import boto3
import os
def id_generator(size=6, chars=string.ascii_lowercase + string.digits):
  return "".join(random.choices(chars, k=size))
def get_mediaconvert_endpoint():
  mediaconvert_client = boto3.client("mediaconvert", region_name=os.environ['AWS_REGION'])
  response = mediaconvert_client.describe_endpoints()
  mediaconvert_endpoint = response["Endpoints"][0]["Url"]
  response_data = {'Data': mediaconvert_endpoint}
  return response_data
def init_system_table():
  dynamodb_client = boto3.resource("dynamodb")
  SYSTEM_TABLE_NAME = os.environ["SYSTEM_TABLE_NAME"]
  DEFAULT_MAX_CONCURRENT_WORKFLOWS = int(os.environ["DEFAULT_MAX_CONCURRENT_WORKFLOWS"])
  system_table = dynamodb_client.Table(SYSTEM_TABLE_NAME)
  config={"Name":"MaxConcurrentWorkflows", "Value":DEFAULT_MAX_CONCURRENT_WORKFLOWS}
  return system_table.put_item(Item=config)
def handler(event, context):
  print("We got the following event:\\n", event)
  if event['ResourceProperties']['FunctionKey'] == 'get_short_uuid':
    response_data = {'Data': id_generator()}
    cfnresponse.send(event, context, cfnresponse.SUCCESS, response_data, "CustomResourcePhysicalID")
  elif event['ResourceProperties']['FunctionKey'] == 'init_system_table':
    response_data = init_system_table()
    cfnresponse.send(event, context, cfnresponse.SUCCESS, response_data, "CustomResourcePhysicalID")
  elif event['ResourceProperties']['FunctionKey'] == 'get_mediaconvert_endpoint':
      response_data = get_mediaconvert_endpoint()
      cfnresponse.send(event, context, cfnresponse.SUCCESS, response_data, "CustomResourcePhysicalID")
`);
