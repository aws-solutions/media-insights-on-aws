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
    CfnElement,
    CfnParameter,
    NestedStack,
    NestedStackProps,
    Stack,
} from 'aws-cdk-lib';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as kinesis from 'aws-cdk-lib/aws-kinesis';
import * as kms from 'aws-cdk-lib/aws-kms';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import { DynamoEventSource } from 'aws-cdk-lib/aws-lambda-event-sources';
import * as util from './utils'

/**
 * Initialization props for the `AnalyticsStack` construct.
 *
 */
export interface AnalyticsStackProps extends NestedStackProps {
    /**
     * KMS Key ID for encryption
     */
    readonly kmsKey: kms.Key;
    /**
     * For access to the Arn of the Dataplane Dynamo DB Stream
     */
    readonly dynamoStream: dynamodb.ITable;
}

/**
 * A nested CloudFormation stack for data streaming.
 *
 * When this stack is enabled, it deploys a data streaming pipeline that
 * can be consumed by external applications. By default, this capability is
 * activated when the solution is deployed. But the capability can be disabled.
 *
 */
export class AnalyticsStack extends NestedStack {
    /**
     * Dataplane pipeline stream
     */
    readonly analyticsStream: kinesis.Stream;

    constructor(scope: Construct, id: string, props: AnalyticsStackProps) {
        super(scope, id, { ...props, description: "media-insights-on-aws version %%VERSION%%. This AWS CloudFormation template defines resources for the analytics streaming pipeline." });
        this.templateOptions.templateFormatVersion = '2010-09-09';

        //
        // Cfn Parameters
        //

        const kinesisShardCount = new CfnParameter(this, 'KinesisShardCount', {
            type: 'Number',
            default: 1,
        });
        const botoConfig = new CfnParameter(this, 'botoConfig', {
            type: 'String',
            description: "Botocore config"
        });

        //
        // Cfn Mappings
        //

        const sourceCodeMap = new util.SourceCodeHelper(this);

        //
        // Cfn Resources
        //

        const analyticsStream = new kinesis.Stream(this, 'AnalyticsStream', {
            shardCount: kinesisShardCount.valueAsNumber,
            encryption: kinesis.StreamEncryption.KMS,
            encryptionKey: props.kmsKey,
        });
        this.analyticsStream = analyticsStream;


        const lambdaStreamRole = new iam.Role(this, 'LambdaStreamRole', {
            assumedBy: new iam.ServicePrincipal('lambda.amazonaws.com'),
            inlinePolicies: {
                [`${Aws.STACK_NAME}-LambdaStreamAccessPolicy`]: new iam.PolicyDocument({
                    statements: [
                        new iam.PolicyStatement({
                            actions: [
                                "kinesis:ListShards",
                                "kinesis:DescribeStream",
                                "kinesis:GetRecords",
                                "kinesis:GetShardIterator",
                                "kinesis:ListStreams",
                                "kinesis:DescribeStreamSummary",
                                "kinesis:PutRecord",
                                "kinesis:PutRecords",
                            ],
                            resources: [
                                analyticsStream.streamArn,
                            ],
                        }),
                        new iam.PolicyStatement({
                            actions: [
                                "dynamodb:DescribeStream",
                                "dynamodb:GetRecords",
                                "dynamodb:GetShardIterator",
                                "dynamodb:ListStreams",
                            ],
                            resources: [
                                props.dynamoStream.tableStreamArn!,
                            ],
                        }),
                        new iam.PolicyStatement({
                            actions: [
                                "xray:PutTraceSegments",
                                "xray:PutTelemetryRecords",
                            ],
                            resources: [
                                "*",
                            ],
                        }),
                        new iam.PolicyStatement({
                            actions: [
                                "logs:CreateLogGroup",
                                "logs:CreateLogStream",
                                "logs:PutLogEvents",
                            ],
                            resources: [
                                Stack.of(this).formatArn({
                                    service: 'logs',
                                    resource: 'log-group',
                                    resourceName: '/aws/lambda/*-DynamoDBStream*',
                                    arnFormat: ArnFormat.COLON_RESOURCE_NAME,
                                }),
                            ],
                        }),
                        new iam.PolicyStatement({
                            actions: [
                                "kms:GenerateDataKey",
                                "kms:Decrypt",
                            ],
                            resources: [
                                props.kmsKey.keyArn,
                            ],
                        }),
                    ],
                }),
            },
        });

        const dynamoDBStreamingFunction = new lambda.Function(this, 'DynamoDBStreamingFunction', {
            handler: "stream.lambda_handler",
            role: lambdaStreamRole,
            tracing: lambda.Tracing.PASS_THROUGH,
            code: sourceCodeMap.codeFromRegionalBucket("ddbstream.zip"),
            runtime: lambda.Runtime.PYTHON_3_11,
            environment: {
                StreamName: analyticsStream.streamName,
                botoConfig: botoConfig.valueAsString,
            },
        });

        dynamoDBStreamingFunction.addEventSource(new DynamoEventSource(props.dynamoStream, {
            startingPosition: lambda.StartingPosition.LATEST,
        }));

        util.setNagSuppressRules(dynamoDBStreamingFunction,
            {
                id: 'AwsSolutions-L1',
                reason: "Latest lambda version not supported at this time.",
            }
        );

        //
        // Tags
        //

        [
            analyticsStream,
            dynamoDBStreamingFunction,
            lambdaStreamRole,
        ].forEach(util.addMediaInsightsTag);

        //
        // cfn_nag / cdk_nag rules
        //

        util.setNagSuppressRules(dynamoDBStreamingFunction,
            {
                id: 'W89',
                reason: "This Lambda function does not need to access any resource provisioned within a VPC.",
            },
            {
                id: 'W92',
                reason: "This function does not require performance optimization, so the default concurrency limits suffice.",
            }
        );

        util.setNagSuppressRules(lambdaStreamRole, {
            id: 'W11',
            id2: 'AwsSolutions-IAM5',
            reason: "The policy applies to all resources - can't be scoped to a specific resource",
        });

        util.setNagSuppressRules(analyticsStream, {
            id: 'AwsSolutions-KDS3',
            reason: "Customer managed key is being used to encrypt Kinesis Data Stream",
        });
    }

    getLogicalId(element: CfnElement): string {
        return util.cleanUpLogicalId(super.getLogicalId(element));
    }
}
