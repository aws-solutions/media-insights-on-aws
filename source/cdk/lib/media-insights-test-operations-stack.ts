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
    Duration,
    Fn,
    NestedStack,
    NestedStackProps,
    Stack,
} from 'aws-cdk-lib';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as util from './utils'

/**
 * Initialization props for the `TestResourcesStack` construct.
 *
 */
export interface TestResourcesStackProps extends NestedStackProps {
    /**
     * Media Insights lambda layer that contains basic python dependencies
     * for boto3, chalice, control plane and dataplane
     */
    readonly python39Layer: lambda.ILayerVersion;
}

/*
 * A nested CloudFormation stack for testing.
 *
 * When this stack is enabled, it deploys test resources that contain Lambda
 * functions required for integration and end-to-end testing. By default, this
 * capability is deactivated. But the capability can be enabled.
 */
export class TestResourcesStack extends NestedStack {
    constructor(scope: Construct, id: string, props: TestResourcesStackProps) {
        super(scope, id, { ...props, description: "media-insights-on-aws version %%VERSION%%. This AWS CloudFormation template  provisions operators, stages, and workflows used for testing the Media Insights on AWS" });
        this.templateOptions.templateFormatVersion = '2010-09-09';

        //
        // Cfn Parameters
        //

        const dataplaneEndpoint = new CfnParameter(this, 'DataplaneEndpoint', {
            type: 'String',
            description: "Lambda name of the dataplane handler",
        });

        const dataPlaneBucket = new CfnParameter(this, 'DataPlaneBucket', {
            type: 'String',
            description: "Bucket for the dataplane",
        });

        //
        // Cfn Mappings
        //

        const sourceCodeMap = new util.SourceCodeHelper(this);

        //
        // Cfn Resources
        //

        //
        // Service - IAM
        //

        const testExecutionRole = new iam.Role(this, 'TestExecutionRole', {
            assumedBy: new iam.ServicePrincipal('lambda.amazonaws.com'),
            inlinePolicies: {
                [`${Aws.STACK_NAME}-test-execution-lambda-role`]: new iam.PolicyDocument({
                    statements: [
                        new iam.PolicyStatement({
                            actions: [
                                "states:StartExecution",
                            ],
                            resources: [
                                Stack.of(this).formatArn({
                                    service: 'states',
                                    resource: 'stateMachine',
                                    resourceName: Fn.join('', [ Aws.STACK_NAME, '*' ]),
                                    arnFormat: ArnFormat.COLON_RESOURCE_NAME,
                                }),
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
                                    resourceName: '/aws/lambda/*',
                                    arnFormat: ArnFormat.COLON_RESOURCE_NAME,
                                }),
                            ],
                        }),
                    ],
                }),
            },
        });

        // cdk_nag
        util.setNagSuppressRules(testExecutionRole, {
            id: 'AwsSolutions-IAM5', reason: "Resource ARNs are not generated at the time of policy creation",
        });

        // Tag
        util.addMediaInsightsTag(testExecutionRole);

        //
        // Service - Lambda
        //

        function createTestLambda(scope: Construct, id: string, name: string, handler: string): lambda.Function {
            const func = new lambda.Function(scope, `TestLambda${id}`, {
                functionName: `${Aws.STACK_NAME}-${name}`,
                handler: `test.${handler}_lambda_handler`,
                code: sourceCodeMap.codeFromRegionalBucket("test_operations.zip"),
                layers: [
                    props.python39Layer,
                ],
                memorySize: 256,
                role: testExecutionRole,
                runtime: lambda.Runtime.PYTHON_3_9,
                timeout: Duration.seconds(900),
                environment: {
                    DataplaneEndpoint: dataplaneEndpoint.valueAsString,
                    DATAPLANE_BUCKET: dataPlaneBucket.valueAsString,
                },
            });

            // Tag
            util.addMediaInsightsTag(func);

            //
            // cfn_nag rules
            //

            util.setNagSuppressRules(func,
                {
                    id: 'W89',
                    reason: "This Lambda function does not need to access any resource provisioned within a VPC.",
                },
                {
                    id: 'W92',
                    reason: "This function does not require performance optimization, so the default concurrency limits suffice.",
                }
            );

            //
            // Outputs
            //

            util.createCfnOutput(scope, id, {
                value: func.functionArn,
            });

            return func;
        }

        createTestLambda(this, 'VideoSyncOKLambda', 'video-sync-ok', 'video_sync_ok');
        createTestLambda(this, 'VideoSyncFailLambda', 'video-sync-fail', 'video_sync_fail');
        createTestLambda(this, 'VideoAsyncOKLambda', 'video-async-ok', 'video_async_ok');
        createTestLambda(this, 'VideoAsyncOKMonitorLambda', 'video-async-ok-monitor', 'video_async_ok_monitor');
        createTestLambda(this, 'VideoAsyncFailMonitorLambda', 'video-async-fail-monitor', 'video_async_fail_monitor');
        createTestLambda(this, 'AudioSyncOKLambda', 'audio-sync-ok', 'audio_sync_ok');
        createTestLambda(this, 'AudioAsyncOKLambda', 'audio-async-ok', 'audio_async_ok');
        createTestLambda(this, 'AudioAsyncOKMonitorLambda', 'audio-async-ok-monitor', 'audio_async_ok_monitor');
        createTestLambda(this, 'ImageSyncOKLambda', 'image-sync-ok', 'image_sync_ok');
        createTestLambda(this, 'ImageAsyncOKLambda', 'image-async-ok', 'image_async_ok');
        createTestLambda(this, 'ImageAsyncOKMonitorLambda', 'image-async-ok-monitor', 'image_async_ok_monitor');
        createTestLambda(this, 'TextSyncOKLambda', 'text-sync-ok', 'text_sync_ok');
        createTestLambda(this, 'TextAsyncOKLambda', 'text-async-ok', 'text_async_ok');
        createTestLambda(this, 'TextAsyncOKMonitorLambda', 'text-async-ok-monitor', 'text_async_ok_monitor');

    }

    getLogicalId(element: CfnElement): string {
        return util.cleanUpLogicalId(super.getLogicalId(element));
    }
}
