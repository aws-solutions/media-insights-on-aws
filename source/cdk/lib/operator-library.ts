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
    CfnParameter,
    CustomResource,
    Duration,
    Fn,
    NestedStack,
    NestedStackProps,
    Stack,
} from 'aws-cdk-lib';
import * as kms from 'aws-cdk-lib/aws-kms';
import * as sns from 'aws-cdk-lib/aws-sns';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as util from './utils'

/**
 * Initialization props for the `OperatorLibraryStack` construct.
 *
 */
export interface OperatorLibraryStackProps extends NestedStackProps {
    /**
     * KMS Key for encryption
     */
    readonly kmsKey: kms.Key;
    /**
     * Media insights on AWS lambda layer (python3.9) containing basic python
     * dependencies for boto3, chalice, control plane and dataplane
     */
    readonly python39Layer: lambda.ILayerVersion;
    /**
     * Media insights on AWS lambda layer (python3.8) containing basic python
     * dependencies for boto3, chalice, control plane and dataplane
     */
    readonly python38Layer: lambda.ILayerVersion;
    /**
     * Media insights on AWS lambda layer (python3.7) containing basic python
     * dependencies for boto3, chalice, control plane and dataplane
     */
    readonly python37Layer: lambda.ILayerVersion;
}

/**
 * A nested CloudFormation stack containing Lambda Functions representing operators.
 */
export class OperatorLibraryStack extends NestedStack {
    constructor(scope: Construct, id: string, props: OperatorLibraryStackProps) {
        super(scope, id, { ...props, description: "media-insights-on-aws version %%VERSION%%. This AWS CloudFormation template provisions the Media Insights on AWS operator library." });
        this.templateOptions.templateFormatVersion = '2010-09-09';

        //
        // Cfn Mappings
        //

        const sourceCodeMap = new util.SourceCodeHelper(this);

        //
        // Cfn Parameters
        //

        const dataPlaneEndpoint = new CfnParameter(this, 'DataPlaneEndpoint', {
            type: 'String',
            description: "Name of the dataplane handler lambda function",
        });
        const dataPlaneBucket = new CfnParameter(this, 'DataPlaneBucket', {
            type: 'String',
            description: "Bucket for the dataplane",
        });
        const externalBucketArn = new CfnParameter(this, 'ExternalBucketArn', {
            type: 'String',
            description: "The ARN for Amazon S3 resources that exist outside the stack which may need to be used as inputs to the workflows",
        });
        const dataPlaneHandlerArn = new CfnParameter(this, 'DataPlaneHandlerArn', {
            type: 'String',
            description: "Arn of dataplane lambda handler",
        });
        const workflowCustomResourceArn = new CfnParameter(this, 'WorkflowCustomResourceArn', {
            type: 'String',
            description: "ARN of the Media insights on AWS custom resource that handles creating operations, stages and workflows",
        });
        const startWaitOperationLambda = new CfnParameter(this, 'StartWaitOperationLambda', {
            type: 'String',
            description: "ARN of control plane lambda function to set a workflow to Waiting state",
        });
        const checkWaitOperationLambda = new CfnParameter(this, 'CheckWaitOperationLambda', {
            type: 'String',
            description: "ARN of control plane lambda function to if a workflow is in Waiting state",
        });
        const mediaConvertEndpoint = new CfnParameter(this, 'MediaConvertEndpoint', {
            type: 'String',
            description: "Account-specific endpoint URL for MediaConvert",
        });
        const boto3UserAgent = new CfnParameter(this, 'Boto3UserAgent', {
            type: 'String',
            description: "Boto3 user agent string",
        });


        //
        // Cfn Conditions
        //

        const allowAccessToExternalBucket = new CfnCondition(this, 'AllowAccessToExternalBucket', {
            expression: Fn.conditionNot(Fn.conditionEquals(externalBucketArn.valueAsString, '')),
        });

        //
        // Cfn Resources
        //


        //
        // Service - SNS
        //

        //  SNS topic for storing the output of async Rekognition jobs:
        const snsRekognitionTopic = new sns.Topic(this, 'snsRekognitionTopic', {
            displayName: "SNS Role for Rekognition",
            masterKey: props.kmsKey,
        });


        //
        // IAM Roles
        //

        const policyS3ReadOnly = new iam.PolicyStatement({
            actions: [
                's3:GetObject',
            ],
            resources: [
                Stack.of(this).formatArn({
                    service: 's3',
                    region: '',
                    account: '',
                    resource: dataPlaneBucket.valueAsString,
                    resourceName: '*',
                })
            ],
        });
        const policyS3ReadWrite = new iam.PolicyStatement({
            actions: [
                's3:GetObject',
                's3:PutObject',
            ],
            resources: [
                Stack.of(this).formatArn({
                    service: 's3',
                    region: '',
                    account: '',
                    resource: dataPlaneBucket.valueAsString,
                    resourceName: '*',
                })
            ],
        });
        const policyS3List = new iam.PolicyStatement({
            actions: [
                's3:ListBucket',
            ],
            resources: [
                Stack.of(this).formatArn({
                    service: 's3',
                    region: '',
                    account: '',
                    resource: dataPlaneBucket.valueAsString,
                })
            ],
        });
        const policyS3Read = new iam.PolicyStatement({
            actions: [
                's3:GetObject',
            ],
            resources: [
                `${Fn.conditionIf(allowAccessToExternalBucket.logicalId,
                    externalBucketArn.valueAsString,
                    Stack.of(this).formatArn({
                        service: 's3',
                        region: '',
                        account: '',
                        resource: dataPlaneBucket.valueAsString,
                        resourceName: '*',
                    })
                )}`
            ],
        });
        const policyInvokeDataPlaneHandler = new iam.PolicyStatement({
            actions: ['lambda:InvokeFunction'],
            resources: [dataPlaneHandlerArn.valueAsString],
        });
        const policyXRay = new iam.PolicyStatement({
            actions: [
                'xray:PutTraceSegments',
                'xray:PutTelemetryRecords',
            ],
            resources: ['*'],
        });
        const policyKmsDecrypt = new iam.PolicyStatement({
            actions: [
                'kms:Decrypt',
                'kms:GenerateDataKey',
            ],
            resources: [
                props.kmsKey.keyArn
            ],
        });
        const policyKmsDecryptGrant = new iam.PolicyStatement({
            actions: [
                'kms:Decrypt',
                "kms:CreateGrant",
                'kms:GenerateDataKey',
            ],
            resources: [
                props.kmsKey.keyArn
            ],
        });
        const policyKmsEncryptDecrypt = new iam.PolicyStatement({
            actions: [
                "kms:Decrypt",
                "kms:GenerateDataKey",
                "kms:Encrypt",
                "kms:ReEncrypt*",
                "kms:GenerateDataKey*",
                "kms:DescribeKey",
            ],
            resources: [
                props.kmsKey.keyArn
            ],
        });
        const policyLogEvents = new iam.PolicyStatement({
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
                })
            ],
        });

        const genericDataLookupLambdaRole = new iam.Role(this, 'genericDataLookupLambdaRole', {
            assumedBy: new iam.ServicePrincipal('lambda.amazonaws.com'),
            managedPolicies: [
                iam.ManagedPolicy.fromAwsManagedPolicyName('service-role/AWSLambdaBasicExecutionRole'),
                iam.ManagedPolicy.fromAwsManagedPolicyName('AmazonS3ReadOnlyAccess'),
            ],
            inlinePolicies: {
                GenericDataLookupLambdaAccess: new iam.PolicyDocument({
                    statements: [
                        policyLogEvents,
                        policyS3ReadWrite,
                        policyS3Read,
                        policyInvokeDataPlaneHandler,
                        policyXRay,
                        policyKmsDecrypt,
                    ]
                }),
            },
        });

        const mediainfoLambdaRole = new iam.Role(this, 'mediainfoLambdaRole', {
            assumedBy: new iam.ServicePrincipal('lambda.amazonaws.com'),
            managedPolicies: [
                iam.ManagedPolicy.fromAwsManagedPolicyName('service-role/AWSLambdaBasicExecutionRole'),
                iam.ManagedPolicy.fromAwsManagedPolicyName('AmazonS3ReadOnlyAccess'),
            ],
            inlinePolicies: {
                mediainfoLambdaAccess: new iam.PolicyDocument({
                    statements: [
                        policyLogEvents,
                        policyS3ReadWrite,
                        policyS3Read,
                        policyInvokeDataPlaneHandler,
                        policyXRay,
                        policyKmsDecrypt,
                    ]
                }),
            },
        });

        const mediaConvertS3Role = new iam.Role(this, 'mediaConvertS3Role', {
            assumedBy: new iam.ServicePrincipal('mediaconvert.amazonaws.com'),
            inlinePolicies: {
                MediaconvertAllowS3: new iam.PolicyDocument({
                    statements: [
                        policyS3ReadWrite,
                        policyS3Read,
                        policyKmsEncryptDecrypt,
                    ]
                }),
            },
        });

        const mediaConvertLambdaRole = new iam.Role(this, 'mediaConvertLambdaRole', {
            assumedBy: new iam.ServicePrincipal('lambda.amazonaws.com'),
            inlinePolicies: {
                MediaConvertLambdaAccess: new iam.PolicyDocument({
                    statements: [
                        new iam.PolicyStatement({
                            actions: [
                                "mediaconvert:GetJob",
                                "mediaconvert:ListJobs",
                                "mediaconvert:DescribeEndpoints",
                                "mediaconvert:CreateJob",
                            ],
                            resources: ['*'],
                        }),
                        policyLogEvents,
                        new iam.PolicyStatement({
                            actions: [
                                "iam:PassRole",
                            ],
                            resources: [
                                mediaConvertS3Role.roleArn,
                            ],
                        }),
                        policyS3ReadWrite,
                        policyS3Read,
                        policyInvokeDataPlaneHandler,
                        policyXRay,
                        policyKmsEncryptDecrypt,
                    ]
                }),
            },
        });

        const transcribeRole = new iam.Role(this, 'transcribeRole', {
            assumedBy: new iam.ServicePrincipal('lambda.amazonaws.com'),
            inlinePolicies: {
                TranscribeAccess: new iam.PolicyDocument({
                    statements: [
                        new iam.PolicyStatement({
                            actions: [
                                "transcribe:GetVocabulary",
                                "transcribe:GetTranscriptionJob",
                                "transcribe:CreateVocabulary",
                                "transcribe:StartStreamTranscription",
                                "transcribe:StartTranscriptionJob",
                                "transcribe:UpdateVocabulary",
                                "transcribe:ListTranscriptionJobs",
                                "transcribe:ListVocabularies",
                            ],
                            // These actions only support Resource: "*"
                            resources: ['*'],
                        }),
                        policyLogEvents,
                        policyS3ReadWrite,
                        policyS3Read,
                        policyInvokeDataPlaneHandler,
                        policyXRay,
                        policyKmsDecrypt,
                    ]
                }),
            },
        });

        const captionsRole = new iam.Role(this, 'captionsRole', {
            assumedBy: new iam.ServicePrincipal('lambda.amazonaws.com'),
            inlinePolicies: {
                CaptionsAccess: new iam.PolicyDocument({
                    statements: [
                        policyLogEvents,
                        policyS3ReadWrite,
                        policyS3Read,
                        policyInvokeDataPlaneHandler,
                        policyXRay,
                        policyKmsDecrypt,
                    ]
                }),
            },
        });

        const translateS3Role = new iam.Role(this, 'translateS3Role', {
            assumedBy: new iam.ServicePrincipal('translate.amazonaws.com'),
            inlinePolicies: {
                TranslateAllowS3: new iam.PolicyDocument({
                    statements: [
                        policyS3ReadWrite,
                        policyS3Read,
                        policyS3List,
                        policyKmsDecrypt,
                    ]
                }),
            },
        });

        const translateRole = new iam.Role(this, 'translateRole', {
            assumedBy: new iam.ServicePrincipal('lambda.amazonaws.com'),
            inlinePolicies: {
                TranslateAccess: new iam.PolicyDocument({
                    statements: [
                        new iam.PolicyStatement({
                            actions: [
                                "iam:PassRole",
                            ],
                            resources: [
                                translateS3Role.roleArn,
                            ],
                        }),
                        new iam.PolicyStatement({
                            actions: [
                                "translate:GetTerminology",
                                "translate:ListTerminologies",
                                "translate:ImportTerminology",
                                "translate:TranslateText",
                                "translate:DescribeTextTranslationJob",
                                "translate:StartTextTranslationJob",
                            ],
                            // These actions only support Resource: "*"
                            resources: ['*'],
                        }),
                        policyLogEvents,
                        policyS3ReadWrite,
                        policyS3Read,
                        policyS3List,
                        policyInvokeDataPlaneHandler,
                        policyXRay,
                        policyKmsDecrypt,
                    ]
                }),
            },
        });

        const pollyRole = new iam.Role(this, 'pollyRole', {
            assumedBy: new iam.CompositePrincipal(
                new iam.ServicePrincipal('lambda.amazonaws.com'),
                new iam.ServicePrincipal('comprehend.amazonaws.com'),
            ),
            inlinePolicies: {
                PollyAccess: new iam.PolicyDocument({
                    statements: [
                        new iam.PolicyStatement({
                            actions: [
                                "polly:SynthesizeSpeech",
                                "polly:StartSpeechSynthesisTask",
                                "polly:ListLexicons",
                                "polly:GetSpeechSynthesisTask",
                                "polly:ListSpeechSynthesisTasks",
                                "comprehend:DetectDominantLanguage",
                                "polly:GetLexicon",
                                "polly:DescribeVoices",
                            ],
                            // These actions only support Resource: "*"
                            resources: ['*'],
                        }),
                        policyLogEvents,
                        policyS3ReadWrite,
                        policyS3Read,
                        policyInvokeDataPlaneHandler,
                        policyXRay,
                        policyKmsDecrypt,
                    ]
                }),
            },
        });

        const comprehendS3Role = new iam.Role(this, 'comprehendS3Role', {
            assumedBy: new iam.ServicePrincipal('comprehend.amazonaws.com'),
            inlinePolicies: {
                ComprehendAllowS3: new iam.PolicyDocument({
                    statements: [
                        policyS3ReadWrite,
                        policyS3Read,
                        policyS3List,
                        policyXRay,
                        policyKmsDecryptGrant,
                    ]
                }),
            },
        });

        const comprehendRole = new iam.Role(this, 'comprehendRole', {
            assumedBy: new iam.ServicePrincipal('lambda.amazonaws.com'),
            inlinePolicies: {
                comprehendAccess: new iam.PolicyDocument({
                    statements: [
                        new iam.PolicyStatement({
                            actions: [
                                "iam:PassRole",
                            ],
                            resources: [
                                comprehendS3Role.roleArn,
                            ],
                        }),
                        policyLogEvents,
                        policyS3ReadWrite,
                        policyS3Read,
                        new iam.PolicyStatement({
                            actions: [
                                "comprehend:StartEntitiesDetectionJob",
                                "comprehend:DetectSentiment",
                                "comprehend:DescribeEntityRecognizer",
                                "comprehend:ListTopicsDetectionJobs",
                                "comprehend:DescribeDominantLanguageDetectionJob",
                                "comprehend:StopTrainingEntityRecognizer",
                                "comprehend:DescribeDocumentClassificationJob",
                                "comprehend:StopSentimentDetectionJob",
                                "comprehend:StartDominantLanguageDetectionJob",
                                "comprehend:StartTopicsDetectionJob",
                                "comprehend:DetectDominantLanguage",
                                "comprehend:CreateDocumentClassifier",
                                "comprehend:ListEntityRecognizers",
                                "comprehend:ListSentimentDetectionJobs",
                                "comprehend:BatchDetectSyntax",
                                "comprehend:StartSentimentDetectionJob",
                                "comprehend:ListDominantLanguageDetectionJobs",
                                "comprehend:ListDocumentClassifiers",
                                "comprehend:DescribeKeyPhrasesDetectionJob",
                                "comprehend:CreateEntityRecognizer",
                                "comprehend:ListKeyPhrasesDetectionJobs",
                                "comprehend:DescribeSentimentDetectionJob",
                                "comprehend:DescribeTopicsDetectionJob",
                                "comprehend:StopDominantLanguageDetectionJob",
                                "comprehend:BatchDetectSentiment",
                                "comprehend:StartKeyPhrasesDetectionJob",
                                "comprehend:BatchDetectEntities",
                                "comprehend:BatchDetectKeyPhrases",
                                "comprehend:ListEntitiesDetectionJobs",
                                "comprehend:StopKeyPhrasesDetectionJob",
                                "comprehend:ListDocumentClassificationJobs",
                                "comprehend:DetectSyntax",
                                "comprehend:DescribeEntitiesDetectionJob",
                                "comprehend:StopTrainingDocumentClassifier",
                                "comprehend:ListTagsForResource",
                                "comprehend:DescribeDocumentClassifier",
                                "comprehend:StopEntitiesDetectionJob",
                                "comprehend:BatchDetectDominantLanguage",
                                "comprehend:StartDocumentClassificationJob",
                                "comprehend:DetectEntities",
                                "comprehend:DetectKeyPhrases",
                            ],
                            // These actions only support Resource: "*"
                            resources: ['*'],
                        }),
                        policyInvokeDataPlaneHandler,
                        policyXRay,
                        policyKmsDecryptGrant,
                    ]
                }),
            },
        });

        const rekognitionSNSRole = new iam.Role(this, 'rekognitionSNSRole', {
            assumedBy: new iam.ServicePrincipal('rekognition.amazonaws.com'),
            inlinePolicies: {
                RekognitionSNSPublishPolicy: new iam.PolicyDocument({
                    statements: [
                        new iam.PolicyStatement({
                            actions: [
                                "sns:Publish",
                            ],
                            resources: [
                                snsRekognitionTopic.topicArn,
                            ],
                        }),
                        policyXRay,
                        policyKmsDecrypt,
                    ]
                }),
            },
        });

        const rekognitionLambdaRole = new iam.Role(this, 'rekognitionLambdaRole', {
            assumedBy: new iam.ServicePrincipal('lambda.amazonaws.com'),
            inlinePolicies: {
                rekognitionAccess: new iam.PolicyDocument({
                    statements: [
                        new iam.PolicyStatement({
                            actions: [
                                "iam:PassRole",
                            ],
                            resources: [
                                rekognitionSNSRole.roleArn,
                            ],
                        }),
                        policyInvokeDataPlaneHandler,
                        policyLogEvents,
                        policyS3ReadOnly,
                        policyS3Read,
                        new iam.PolicyStatement({
                            actions: [
                                "rekognition:DetectFaces",
                                "rekognition:DetectLabels",
                                "rekognition:DetectText",
                                "rekognition:DetectModerationLabels",
                                "rekognition:GetCelebrityRecognition",
                                "rekognition:GetContentModeration",
                                "rekognition:GetFaceDetection",
                                "rekognition:GetFaceSearch",
                                "rekognition:GetLabelDetection",
                                "rekognition:GetPersonTracking",
                                "rekognition:RecognizeCelebrities",
                                "rekognition:StartCelebrityRecognition",
                                "rekognition:StartContentModeration",
                                "rekognition:StartFaceDetection",
                                "rekognition:StartFaceSearch",
                                "rekognition:StartLabelDetection",
                                "rekognition:StartPersonTracking",
                                "rekognition:StartTextDetection",
                                "rekognition:GetTextDetection",
                                "rekognition:StartSegmentDetection",
                                "rekognition:GetSegmentDetection",
                            ],
                            // These Rekognition actions do not support resource-level permissions, so we must use Resource: *
                            resources: ['*'],
                        }),
                        new iam.PolicyStatement({
                            actions: [
                                "rekognition:DescribeCollection",
                                "rekognition:SearchFaces",
                                "rekognition:SearchFacesByImage",
                            ],
                            resources: [
                                Stack.of(this).formatArn({
                                    service: 'rekognition',
                                    resource: 'collection',
                                    resourceName: '*',
                                })
                            ],
                        }),
                        policyXRay,
                        policyKmsDecrypt,
                    ]
                }),
            },
        });


        //
        // Lambda functions
        //

        // Environment variables
        const REKOGNITION_SNS_TOPIC_ARN = snsRekognitionTopic.topicArn;
        const REKOGNITION_ROLE_ARN = rekognitionSNSRole.roleArn;
        const mediaconvertRole = mediaConvertS3Role.roleArn;
        const DataplaneEndpoint = dataPlaneEndpoint.valueAsString;
        const DATAPLANE_BUCKET = dataPlaneBucket.valueAsString;
        const MEDIACONVERT_ENDPOINT = mediaConvertEndpoint.valueAsString;
        const LD_LIBRARY_PATH = "/opt/python/";
        const botoConfig = boto3UserAgent.valueAsString;
        const KmsId = props.kmsKey.keyId;

        interface ICreateLambdaFunctionProps {
            readonly handler: string;
            readonly role: iam.IRole;
            readonly tracing?: lambda.Tracing;
            readonly memorySize?: number;
            readonly environment: { [key: string]: string; }
        }
        const pythonLayers = {
            [`${lambda.Runtime.PYTHON_3_9}`]: props.python39Layer,
            [`${lambda.Runtime.PYTHON_3_8}`]: props.python38Layer,
            [`${lambda.Runtime.PYTHON_3_7}`]: props.python37Layer,
        };
        function createLambdaFunction(scope: Construct, id: string, codeArchive: string,
                                      timeout: number, props: ICreateLambdaFunctionProps,
                                      runtime: lambda.Runtime = lambda.Runtime.PYTHON_3_9): lambda.Function {
            const layer = pythonLayers[`${runtime}`];
            const func = new lambda.Function(scope, id, {
                ...props,
                layers: [layer],
                code: sourceCodeMap.codeFromRegionalBucket(codeArchive),
                runtime,
                timeout: Duration.seconds(timeout),
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

            return func;
        }


        // This is a generic Lambda function for getting metadata from JSON file in S3:
        const startGenericDataLookup = createLambdaFunction(this, 'startGenericDataLookup', "generic_data_lookup.zip", 300, {
            handler: "generic_data_lookup.lambda_handler",
            role: genericDataLookupLambdaRole,
            tracing: lambda.Tracing.PASS_THROUGH,
            environment: {
                OPERATOR_NAME: "GenericDataLookup",
                DataplaneEndpoint,
                DataLookupRole: genericDataLookupLambdaRole.roleArn,
                botoConfig,
            }
        });

        // Mediainfo

        const Mediainfo = createLambdaFunction(this, 'Mediainfo', "mediainfo.zip", 300, {
            handler: "mediainfo.lambda_handler",
            role: mediainfoLambdaRole,
            tracing: lambda.Tracing.PASS_THROUGH,
            environment: {
                OPERATOR_NAME: "Mediainfo",
                DataplaneEndpoint,
                DataLookupRole: mediainfoLambdaRole.roleArn,
                LD_LIBRARY_PATH,
                botoConfig,
            }
        }, lambda.Runtime.PYTHON_3_7);

        // Comprehend

        const startKeyPhrases = createLambdaFunction(this, 'startKeyPhrases', "start_key_phrases.zip", 300, {
            handler: "start_key_phrases.lambda_handler",
            role: comprehendRole,
            tracing: lambda.Tracing.PASS_THROUGH,
            environment: {
                OPERATOR_NAME: "comprehendStartKeyPhrases",
                DataplaneEndpoint,
                comprehendRole: comprehendS3Role.roleArn,
                botoConfig,
                KmsId,
            }
        });

        const getKeyPhrases = createLambdaFunction(this, 'getKeyPhrases', "get_key_phrases.zip", 300, {
            handler: "get_key_phrases.lambda_handler",
            role: comprehendRole,
            tracing: lambda.Tracing.PASS_THROUGH,
            environment: {
                OPERATOR_NAME: "comprehendGetKeyPhrases",
                DataplaneEndpoint,
                comprehendRole: comprehendS3Role.roleArn,
                botoConfig,
                KmsId,
            }
        });

        const startEntityDetection = createLambdaFunction(this, 'startEntityDetection', "start_entity_detection.zip", 300, {
            handler: "start_entity_detection.lambda_handler",
            role: comprehendRole,
            tracing: lambda.Tracing.PASS_THROUGH,
            environment: {
                OPERATOR_NAME: "comprehendStartEntityDetection",
                DataplaneEndpoint,
                comprehendRole: comprehendS3Role.roleArn,
                botoConfig,
                KmsId,
            }
        });

        const getEntityDetection = createLambdaFunction(this, 'getEntityDetection', "get_entity_detection.zip", 300, {
            handler: "get_entity_detection.lambda_handler",
            role: comprehendRole,
            tracing: lambda.Tracing.PASS_THROUGH,
            environment: {
                OPERATOR_NAME: "comprehendEntityDetection",
                DataplaneEndpoint,
                comprehendRole: comprehendS3Role.roleArn,
                botoConfig,
                KmsId,
            }
        });

        // Rekognition

        const startTechnicalCueDetection = createLambdaFunction(this, 'startTechnicalCueDetection', "start_rekognition.zip", 120, {
            handler: "start_rekognition.start_technical_cue_detection",
            role: rekognitionLambdaRole,
            tracing: lambda.Tracing.PASS_THROUGH,
            environment: {
                REKOGNITION_SNS_TOPIC_ARN,
                REKOGNITION_ROLE_ARN,
                OPERATOR_NAME: "technicalCueDetection",
                DataplaneEndpoint,
                DATAPLANE_BUCKET,
                botoConfig,
            }
        });

        const checkTechnicalCueDetection = createLambdaFunction(this, 'checkTechnicalCueDetection', "check_rekognition_status.zip", 120, {
            handler: "check_rekognition_status.check_technical_cue_status",
            role: rekognitionLambdaRole,
            tracing: lambda.Tracing.PASS_THROUGH,
            environment: {
                REKOGNITION_SNS_TOPIC_ARN,
                REKOGNITION_ROLE_ARN,
                OPERATOR_NAME: "technicalCueDetection",
                DataplaneEndpoint,
                DATAPLANE_BUCKET,
                botoConfig,
            }
        });

        const startShotDetection = createLambdaFunction(this, 'startShotDetection', "start_rekognition.zip", 120, {
            handler: "start_rekognition.start_shot_detection",
            role: rekognitionLambdaRole,
            tracing: lambda.Tracing.PASS_THROUGH,
            environment: {
                REKOGNITION_SNS_TOPIC_ARN,
                REKOGNITION_ROLE_ARN,
                OPERATOR_NAME: "shotDetection",
                DataplaneEndpoint,
                DATAPLANE_BUCKET,
                botoConfig,
            }
        });

        const checkShotDetection = createLambdaFunction(this, 'checkShotDetection', "check_rekognition_status.zip", 120, {
            handler: "check_rekognition_status.check_shot_detection_status",
            role: rekognitionLambdaRole,
            tracing: lambda.Tracing.PASS_THROUGH,
            environment: {
                REKOGNITION_SNS_TOPIC_ARN,
                REKOGNITION_ROLE_ARN,
                OPERATOR_NAME: "shotDetection",
                DataplaneEndpoint,
                DATAPLANE_BUCKET,
                botoConfig,
            }
        });

        const startCelebrityRecognition = createLambdaFunction(this, 'startCelebrityRecognition', "start_rekognition.zip", 120, {
            handler: "start_rekognition.start_celebrity_recognition",
            role: rekognitionLambdaRole,
            tracing: lambda.Tracing.PASS_THROUGH,
            environment: {
                REKOGNITION_SNS_TOPIC_ARN,
                REKOGNITION_ROLE_ARN,
                OPERATOR_NAME: "celebrityRecognition",
                DataplaneEndpoint,
                DATAPLANE_BUCKET,
                botoConfig,
            }
        });

        const checkCelebrityRecognition = createLambdaFunction(this, 'checkCelebrityRecognition', "check_rekognition_status.zip", 120, {
            handler: "check_rekognition_status.check_celebrity_recognition_status",
            role: rekognitionLambdaRole,
            tracing: lambda.Tracing.PASS_THROUGH,
            environment: {
                REKOGNITION_ROLE_ARN,
                OPERATOR_NAME: "celebrityRecognition",
                DataplaneEndpoint,
                DATAPLANE_BUCKET,
                botoConfig,
            }
        });

        const startContentModeration = createLambdaFunction(this, 'startContentModeration', "start_rekognition.zip", 120, {
            handler: "start_rekognition.start_content_moderation",
            role: rekognitionLambdaRole,
            tracing: lambda.Tracing.PASS_THROUGH,
            environment: {
                REKOGNITION_SNS_TOPIC_ARN,
                REKOGNITION_ROLE_ARN,
                OPERATOR_NAME: "contentModeration",
                DataplaneEndpoint,
                DATAPLANE_BUCKET,
                botoConfig,
            }
        });

        const checkContentModeration = createLambdaFunction(this, 'checkContentModeration', "check_rekognition_status.zip", 120, {
            handler: "check_rekognition_status.check_content_moderation_status",
            role: rekognitionLambdaRole,
            tracing: lambda.Tracing.PASS_THROUGH,
            environment: {
                REKOGNITION_ROLE_ARN,
                OPERATOR_NAME: "contentModeration",
                DataplaneEndpoint,
                DATAPLANE_BUCKET,
                botoConfig,
            }
        });

        const startFaceDetection = createLambdaFunction(this, 'startFaceDetection', "start_rekognition.zip", 120, {
            handler: "start_rekognition.start_face_detection",
            role: rekognitionLambdaRole,
            tracing: lambda.Tracing.PASS_THROUGH,
            memorySize: 256,
            environment: {
                REKOGNITION_SNS_TOPIC_ARN,
                REKOGNITION_ROLE_ARN,
                OPERATOR_NAME: "faceDetection",
                DataplaneEndpoint,
                DATAPLANE_BUCKET,
                botoConfig,
            }
        });

        const checkFaceDetection = createLambdaFunction(this, 'checkFaceDetection', "check_rekognition_status.zip", 300, {
            handler: "check_rekognition_status.check_face_detection_status",
            role: rekognitionLambdaRole,
            tracing: lambda.Tracing.PASS_THROUGH,
            memorySize: 512,
            environment: {
                REKOGNITION_ROLE_ARN,
                OPERATOR_NAME: "faceDetection",
                DataplaneEndpoint,
                DATAPLANE_BUCKET,
                botoConfig,
            }
        });

        const startFaceSearch = createLambdaFunction(this, 'startFaceSearch', "start_face_search.zip", 120, {
            handler: "start_face_search.lambda_handler",
            role: rekognitionLambdaRole,
            tracing: lambda.Tracing.PASS_THROUGH,
            memorySize: 256,
            environment: {
                REKOGNITION_SNS_TOPIC_ARN,
                REKOGNITION_ROLE_ARN,
                OPERATOR_NAME: "faceSearch",
                DataplaneEndpoint,
                DATAPLANE_BUCKET,
                botoConfig,
            }
        });

        const checkFaceSearch = createLambdaFunction(this, 'checkFaceSearch', "check_rekognition_status.zip", 120, {
            handler: "check_rekognition_status.check_face_search_status",
            role: rekognitionLambdaRole,
            tracing: lambda.Tracing.PASS_THROUGH,
            memorySize: 256,
            environment: {
                REKOGNITION_ROLE_ARN,
                OPERATOR_NAME: "faceSearch",
                DataplaneEndpoint,
                DATAPLANE_BUCKET,
                botoConfig,
            }
        });

        const startTextDetection = createLambdaFunction(this, 'startTextDetection', "start_rekognition.zip", 120, {
            handler: "start_rekognition.start_text_detection",
            role: rekognitionLambdaRole,
            tracing: lambda.Tracing.PASS_THROUGH,
            environment: {
                REKOGNITION_SNS_TOPIC_ARN,
                REKOGNITION_ROLE_ARN,
                OPERATOR_NAME: "textDetection",
                DataplaneEndpoint,
                DATAPLANE_BUCKET,
                botoConfig,
            }
        });

        const checkTextDetection = createLambdaFunction(this, 'checkTextDetection', "check_rekognition_status.zip", 240, {
            handler: "check_rekognition_status.check_text_detection_status",
            role: rekognitionLambdaRole,
            tracing: lambda.Tracing.PASS_THROUGH,
            memorySize: 256,
            environment: {
                REKOGNITION_ROLE_ARN,
                OPERATOR_NAME: "textDetection",
                DataplaneEndpoint,
                DATAPLANE_BUCKET,
                botoConfig,
            }
        });

        const startLabelDetection = createLambdaFunction(this, 'startLabelDetection', "start_rekognition.zip", 120, {
            handler: "start_rekognition.start_label_detection",
            role: rekognitionLambdaRole,
            tracing: lambda.Tracing.PASS_THROUGH,
            environment: {
                REKOGNITION_SNS_TOPIC_ARN,
                REKOGNITION_ROLE_ARN,
                OPERATOR_NAME: "labelDetection",
                DataplaneEndpoint,
                DATAPLANE_BUCKET,
                botoConfig,
            }
        });

        const checkLabelDetection = createLambdaFunction(this, 'checkLabelDetection', "check_rekognition_status.zip", 240, {
            handler: "check_rekognition_status.check_label_detection_status",
            role: rekognitionLambdaRole,
            tracing: lambda.Tracing.PASS_THROUGH,
            memorySize: 256,
            environment: {
                REKOGNITION_ROLE_ARN,
                OPERATOR_NAME: "labelDetection",
                DataplaneEndpoint,
                DATAPLANE_BUCKET,
                botoConfig,
            }
        });

        const startPersonTracking = createLambdaFunction(this, 'startPersonTracking', "start_rekognition.zip", 120, {
            handler: "start_rekognition.start_person_tracking",
            role: rekognitionLambdaRole,
            tracing: lambda.Tracing.PASS_THROUGH,
            environment: {
                REKOGNITION_SNS_TOPIC_ARN,
                REKOGNITION_ROLE_ARN,
                OPERATOR_NAME: "personTracking",
                botoConfig,
            }
        });

        const checkPersonTracking = createLambdaFunction(this, 'checkPersonTracking', "check_rekognition_status.zip", 120, {
            handler: "check_rekognition_status.check_person_tracking_status",
            role: rekognitionLambdaRole,
            tracing: lambda.Tracing.PASS_THROUGH,
            memorySize: 256,
            environment: {
                REKOGNITION_ROLE_ARN,
                OPERATOR_NAME: "personTracking",
                DataplaneEndpoint,
                DATAPLANE_BUCKET,
                botoConfig,
            }
        });

        // Mediaconvert Lambdas

        const StartMediaConvertFunction = createLambdaFunction(this, 'StartMediaConvertFunction', "start_media_convert.zip", 60, {
            handler: "start_media_convert.lambda_handler",
            role: mediaConvertLambdaRole,
            tracing: lambda.Tracing.PASS_THROUGH,
            environment: {
                mediaconvertRole,
                DataplaneEndpoint,
                DATAPLANE_BUCKET,
                MEDIACONVERT_ENDPOINT,
                botoConfig,
            }
        });

        const StartThumbnailFunction = createLambdaFunction(this, 'StartThumbnailFunction', "start_thumbnail.zip", 60, {
            handler: "start_thumbnail.lambda_handler",
            role: mediaConvertLambdaRole,
            tracing: lambda.Tracing.PASS_THROUGH,
            environment: {
                mediaconvertRole,
                DataplaneEndpoint,
                DATAPLANE_BUCKET,
                MEDIACONVERT_ENDPOINT,
                botoConfig,
            }
        });

        const CheckThumbnailFunction = createLambdaFunction(this, 'CheckThumbnailFunction', "check_thumbnail.zip", 60, {
            handler: "check_thumbnail.lambda_handler",
            role: mediaConvertLambdaRole,
            tracing: lambda.Tracing.PASS_THROUGH,
            environment: {
                mediaconvertRole,
                DataplaneEndpoint,
                DATAPLANE_BUCKET,
                MEDIACONVERT_ENDPOINT,
                botoConfig,
            }
        });

        const CheckMediaConvertFunction = createLambdaFunction(this, 'CheckMediaConvertFunction', "get_media_convert.zip", 60, {
            handler: "get_media_convert.lambda_handler",
            role: mediaConvertLambdaRole,
            tracing: lambda.Tracing.PASS_THROUGH,
            environment: {
                DataplaneEndpoint,
                DATAPLANE_BUCKET,
                MEDIACONVERT_ENDPOINT,
                botoConfig,
            }
        });

        // Transcribe Lambdas

        const StartTranscribeFunction = createLambdaFunction(this, 'StartTranscribeFunction', "start_transcribe.zip", 120, {
            handler: "start_transcribe.lambda_handler",
            role: transcribeRole,
            tracing: lambda.Tracing.PASS_THROUGH,
            environment: {
                DataplaneEndpoint,
                DATAPLANE_BUCKET,
                botoConfig,
            }
        });

        const CheckTranscribeFunction = createLambdaFunction(this, 'CheckTranscribeFunction', "get_transcribe.zip", 120, {
            handler: "get_transcribe.lambda_handler",
            role: transcribeRole,
            tracing: lambda.Tracing.PASS_THROUGH,
            memorySize: 256,
            environment: {
                DataplaneEndpoint,
                DATAPLANE_BUCKET,
                botoConfig,
            }
        });

        // Create Web Captions Lambda

        const WebCaptionsFunction = createLambdaFunction(this, 'WebCaptionsFunction', "webcaptions.zip", 300, {
            handler: "webcaptions.web_captions",
            role: captionsRole,
            tracing: lambda.Tracing.PASS_THROUGH,
            memorySize: 256,
            environment: {
                DataplaneEndpoint,
                DATAPLANE_BUCKET,
                botoConfig,
            }
        });

        // Create Time Series Lambda

        const CreateSRTCaptionsFunction = createLambdaFunction(this, 'CreateSRTCaptionsFunction', "webcaptions.zip", 300, {
            handler: "webcaptions.create_srt",
            role: captionsRole,
            tracing: lambda.Tracing.PASS_THROUGH,
            environment: {
                DataplaneEndpoint,
                DATAPLANE_BUCKET,
                botoConfig,
            }
        });

        const CreateVTTCaptionsFunction = createLambdaFunction(this, 'CreateVTTCaptionsFunction', "webcaptions.zip", 300, {
            handler: "webcaptions.create_vtt",
            role: captionsRole,
            tracing: lambda.Tracing.PASS_THROUGH,
            environment: {
                DataplaneEndpoint,
                DATAPLANE_BUCKET,
                botoConfig,
            }
        });

        const WebToSRTCaptionsFunction = createLambdaFunction(this, 'WebToSRTCaptionsFunction', "webcaptions.zip", 300, {
            handler: "webcaptions.create_srt",
            role: captionsRole,
            tracing: lambda.Tracing.PASS_THROUGH,
            environment: {
                DataplaneEndpoint,
                DATAPLANE_BUCKET,
                botoConfig,
            }
        });

        const WebToVTTCaptionsFunction = createLambdaFunction(this, 'WebToVTTCaptionsFunction', "webcaptions.zip", 300, {
            handler: "webcaptions.create_vtt",
            role: captionsRole,
            tracing: lambda.Tracing.PASS_THROUGH,
            environment: {
                DataplaneEndpoint,
                DATAPLANE_BUCKET,
                botoConfig,
            }
        });

        // Translate Lambdas

        const TranslateFunction = createLambdaFunction(this, 'TranslateFunction', "start_translate.zip", 300, {
            handler: "start_translate.lambda_handler",
            role: translateRole,
            tracing: lambda.Tracing.PASS_THROUGH,
            memorySize: 256,
            environment: {
                DataplaneEndpoint,
                DATAPLANE_BUCKET,
                botoConfig,
            }
        });

        const StartTranslateWebcaptionsFunction = createLambdaFunction(this, 'StartTranslateWebcaptionsFunction', "webcaptions.zip", 300, {
            handler: "webcaptions.start_translate_webcaptions",
            role: translateRole,
            environment: {
                translateRole: translateS3Role.roleArn,
                DataplaneEndpoint,
                DATAPLANE_BUCKET,
                botoConfig,
            }
        });

        const CheckTranslateWebcaptionsFunction = createLambdaFunction(this, 'CheckTranslateWebcaptionsFunction', "webcaptions.zip", 300, {
            handler: "webcaptions.check_translate_webcaptions",
            role: translateRole,
            environment: {
                DataplaneEndpoint,
                DATAPLANE_BUCKET,
                botoConfig,
            }
        });

        // WebCaptions Polly tracks
        const StartPollyWebCaptionsFunction = createLambdaFunction(this, 'StartPollyWebCaptionsFunction', "webcaptions.zip", 300, {
            handler: "webcaptions.start_polly_webcaptions",
            role: pollyRole,
            environment: {
                DataplaneEndpoint,
                DATAPLANE_BUCKET,
                botoConfig,
            }
        });

        const CheckPollyWebCaptionsFunction = createLambdaFunction(this, 'CheckPollyWebCaptionsFunction', "webcaptions.zip", 300, {
            handler: "webcaptions.check_polly_webcaptions",
            role: pollyRole,
            environment: {
                DataplaneEndpoint,
                DATAPLANE_BUCKET,
                botoConfig,
            }
        });

        // Polly Lambdas

        const StartPollyFunction = createLambdaFunction(this, 'StartPollyFunction', "start_polly.zip", 120, {
            handler: "start_polly.lambda_handler",
            role: pollyRole,
            tracing: lambda.Tracing.PASS_THROUGH,
            environment: {
                DataplaneEndpoint,
                DATAPLANE_BUCKET,
                botoConfig,
            }
        });

        const CheckPollyFunction = createLambdaFunction(this, 'CheckPollyFunction', "get_polly.zip", 120, {
            handler: "get_polly.lambda_handler",
            role: pollyRole,
            tracing: lambda.Tracing.PASS_THROUGH,
            environment: {
                DataplaneEndpoint,
                DATAPLANE_BUCKET,
                botoConfig,
            }
        });

        interface ICustomResourceProps {
            readonly Name: string;
            readonly Description: string;
            readonly Async: boolean;
            readonly Configuration: { [key: string]: any; };
            readonly StartLambdaArn: string,
            readonly MonitorLambdaArn?: string,
            readonly OutputName?: string,
            readonly ExportName?: string,

        }
        function createCustomResource(scope: Construct, id: string, props: ICustomResourceProps): void {
            const outputName: string = props.OutputName || id;
            const exportName: string = props.ExportName || props.Name.replace(/^[a-z]/, s => s.toUpperCase());

            // Register as operators in the control plane

            const properties: { [key: string]: any; } = {
                ResourceType: "Operation",
                Name: props.Name,
                Type: props.Async ? "Async": "Sync",
                Configuration: props.Configuration,
                StartLambdaArn: props.StartLambdaArn,
                MonitorLambdaArn: props.MonitorLambdaArn,
            };

            const custom = new CustomResource(scope, id === outputName ? `CustomResource${id}` : id, {
                resourceType: "Custom::CustomResource",
                serviceToken: workflowCustomResourceArn.valueAsString,
                properties,
            });

            // Export operator names as outputs

            util.createCfnOutput(scope, outputName, {
                description: props.Description,
                value: `${custom.getAtt('Name')}`,
                exportName: Fn.join(':', [Aws.STACK_NAME, exportName]),
            });
        }


        createCustomResource(this, 'GenericDataLookupOperation', {
            Name: "GenericDataLookup",
            Description: "Operation name of GenericDataLookup",
            Async: false,
            Configuration: { MediaType: "Video", Enabled: false },
            StartLambdaArn: startGenericDataLookup.functionArn,
        });

        createCustomResource(this, 'MediainfoOperation', {
            Name: "Mediainfo",
            Description: "Operation name of Mediainfo",
            Async: false,
            Configuration: { MediaType: "Video", Enabled: true },
            StartLambdaArn: Mediainfo.functionArn,
        });

        createCustomResource(this, 'MediainfoOperationImage', {
            Name: "MediainfoImage",
            Description: "Operation name of MediainfoImage",
            Async: false,
            Configuration: { MediaType: "Image", Enabled: true },
            StartLambdaArn: Mediainfo.functionArn,
        });

        createCustomResource(this, 'MediaconvertOperation', {
            Name: "Mediaconvert",
            Description: "Operation name of mediaconvert",
            Async: true,
            Configuration: { MediaType: "Video", Enabled: true },
            StartLambdaArn: StartMediaConvertFunction.functionArn,
            MonitorLambdaArn: CheckMediaConvertFunction.functionArn,
        });

        createCustomResource(this, 'ThumbnailOperation', {
            Name: "Thumbnail",
            Description: "Operation name of thumbnail",
            Async: true,
            Configuration: { MediaType: "Video", Enabled: true },
            StartLambdaArn: StartThumbnailFunction.functionArn,
            MonitorLambdaArn: CheckThumbnailFunction.functionArn,
        });

        createCustomResource(this, 'TranscribeAudioOperation', {
            Name: "TranscribeAudio",
            Description: "Operation name of transcribe for audio",
            Async: true,
            Configuration: { TranscribeLanguage: "en-US", MediaType: "Audio", Enabled: true },
            StartLambdaArn: StartTranscribeFunction.functionArn,
            MonitorLambdaArn: CheckTranscribeFunction.functionArn,
        });

        createCustomResource(this, 'TranscribeVideoOperation', {
            Name: "TranscribeVideo",
            Description: "Operation name of transcribe for video",
            Async: true,
            Configuration: { TranscribeLanguage: "en-US", MediaType: "Video", Enabled: true },
            StartLambdaArn: StartTranscribeFunction.functionArn,
            MonitorLambdaArn: CheckTranscribeFunction.functionArn,
        });

        createCustomResource(this, 'WebCaptionsOperation', {
            Name: "WebCaptions",
            Description: "Operation to create web captions",
            Async: false,
            Configuration: { MediaType: "MetadataOnly", SourceLanguageCode: "en", Enabled: true },
            StartLambdaArn: WebCaptionsFunction.functionArn,
        });

        createCustomResource(this, 'PollyWebCaptionsOperation', {
            Name: "PollyWebCaptions",
            Description: "Operation to create audio tracks from webcaptions collection transcripts",
            Async: true,
            Configuration: { MediaType: "MetadataOnly", SourceLanguageCode: "en", Enabled: true },
            StartLambdaArn: StartPollyWebCaptionsFunction.functionArn,
            MonitorLambdaArn: CheckPollyWebCaptionsFunction.functionArn,
        });

        createCustomResource(this, 'CreateSRTCaptionsOperation', {
            Name: "CreateSRTCaptions",
            Description: "Operation to create SRT captions",
            Async: false,
            Configuration: { MediaType: "Text", Enabled: true },
            StartLambdaArn: CreateSRTCaptionsFunction.functionArn,
        });

        createCustomResource(this, 'CreateVTTCaptionsOperation', {
            Name: "CreateVTTCaptions",
            Description: "Operation to create VTT captions",
            Async: false,
            Configuration: { MediaType: "Text", Enabled: true },
            StartLambdaArn: CreateVTTCaptionsFunction.functionArn,
        });

        createCustomResource(this, 'WebToSRTCaptionsOperation', {
            Name: "WebToSRTCaptions",
            Description: "Operation to convert web captions to SRT format",
            Async: false,
            Configuration: { MediaType: "MetadataOnly", TargetLanguageCodes: ["en"], Enabled: true },
            StartLambdaArn: WebToSRTCaptionsFunction.functionArn,
        });

        createCustomResource(this, 'WebToVTTCaptionsOperation', {
            Name: "WebToVTTCaptions",
            Description: "Operation to convert web captions to VTT format",
            Async: false,
            Configuration: { MediaType: "MetadataOnly", TargetLanguageCodes: ["en"], Enabled: true },
            StartLambdaArn: WebToVTTCaptionsFunction.functionArn,
        });

        createCustomResource(this, 'TranslateOperation', {
            Name: "Translate",
            Description: "Operation name of translate",
            Async: false,
            Configuration: { MediaType: "Text", TargetLanguageCode: "ru", Enabled: true, SourceLanguageCode: "en", },
            StartLambdaArn: TranslateFunction.functionArn,
        });

        createCustomResource(this, 'TranslateWebCaptionsOperation', {
            Name: "TranslateWebCaptions",
            Description: "Operation name of translate WebCaptions",
            Async: true,
            Configuration: { MediaType: "MetadataOnly", TargetLanguageCodes: ["es"], Enabled: true, SourceLanguageCode: "en", },
            StartLambdaArn: StartTranslateWebcaptionsFunction.functionArn,
            MonitorLambdaArn: CheckTranslateWebcaptionsFunction.functionArn,
        });

        createCustomResource(this, 'PollyOperation', {
            Name: "Polly",
            Description: "Operation name of polly",
            Async: true,
            Configuration: { MediaType: "Text", Enabled: false },
            StartLambdaArn: StartPollyFunction.functionArn,
            MonitorLambdaArn: CheckPollyFunction.functionArn,
        });

        createCustomResource(this, 'comprehendPhrasesOperation', {
            Name: "ComprehendKeyPhrases",
            ExportName: "ComprehendPhrases",
            Description: "Operation name of polly",
            Async: true,
            Configuration: { MediaType: "Text", Enabled: true },
            StartLambdaArn: startKeyPhrases.functionArn,
            MonitorLambdaArn: getKeyPhrases.functionArn,
        });

        createCustomResource(this, 'comprehendEntitiesOperation', {
            Name: "ComprehendEntities",
            Description: "Operation name of polly",
            Async: true,
            Configuration: { MediaType: "Text", Enabled: true },
            StartLambdaArn: startEntityDetection.functionArn,
            MonitorLambdaArn: getEntityDetection.functionArn,
        });

        createCustomResource(this, 'celebrityRecognitionOperation', {
            Name: "celebrityRecognition",
            OutputName: "CelebRecognition",
            ExportName: "CelebRecognition",
            Description: "CelebRecognition operator",
            Async: true,
            Configuration: { MediaType: "Video", Enabled: true },
            StartLambdaArn: startCelebrityRecognition.functionArn,
            MonitorLambdaArn: checkCelebrityRecognition.functionArn,
        });

        createCustomResource(this, 'celebrityRecognitionOperationImage', {
            Name: "celebrityRecognitionImage",
            OutputName: "CelebrityRecognitionOperationImage",
            ExportName: "CelebRecognitionImage",
            Description: "CelebRecognition image operator",
            Async: false,
            Configuration: { MediaType: "Image", Enabled: true },
            StartLambdaArn: startCelebrityRecognition.functionArn,
        });

        createCustomResource(this, 'contentModerationOperation', {
            Name: "contentModeration",
            OutputName: "ContentModeration",
            Description: "Content moderation operator",
            Async: true,
            Configuration: { MediaType: "Video", Enabled: true },
            StartLambdaArn: startContentModeration.functionArn,
            MonitorLambdaArn: checkContentModeration.functionArn,
        });

        createCustomResource(this, 'contentModerationOperationImage', {
            Name: "contentModerationImage",
            OutputName: "ContentModerationOperationImage",
            Description: "Content moderation image operator",
            Async: false,
            Configuration: { MediaType: "Image", Enabled: true },
            StartLambdaArn: startContentModeration.functionArn,
        });

        createCustomResource(this, 'faceDetectionOperation', {
            Name: "faceDetection",
            OutputName: "FaceDetection",
            Description: "Face detection operator",
            Async: true,
            Configuration: { MediaType: "Video", Enabled: true },
            StartLambdaArn: startFaceDetection.functionArn,
            MonitorLambdaArn: checkFaceDetection.functionArn,
        });

        createCustomResource(this, 'faceDetectionOperationImage', {
            Name: "faceDetectionImage",
            OutputName: "FaceDetectionOperationImage",
            Description: "Face detection image operator",
            Async: false,
            Configuration: { MediaType: "Image", Enabled: true },
            StartLambdaArn: startFaceDetection.functionArn,
        });

        createCustomResource(this, 'faceSearchOperation', {
            Name: "faceSearch",
            OutputName: "FaceSearch",
            Description: "Face search operator",
            Async: true,
            Configuration: { MediaType: "Video", Enabled: false, CollectionId: "" },
            StartLambdaArn: startFaceSearch.functionArn,
            MonitorLambdaArn: checkFaceSearch.functionArn,
        });

        createCustomResource(this, 'faceSearchOperationImage', {
            Name: "faceSearchImage",
            OutputName: "FaceSearchOperationImage",
            Description: "Face search image operator",
            Async: false,
            Configuration: { MediaType: "Image", Enabled: false, CollectionId: "" },
            StartLambdaArn: startFaceSearch.functionArn,
        });

        createCustomResource(this, 'labelDetectionOperation', {
            Name: "labelDetection",
            OutputName: "LabelDetection",
            Description: "Label detection operator",
            Async: true,
            Configuration: { MediaType: "Video", Enabled: true },
            StartLambdaArn: startLabelDetection.functionArn,
            MonitorLambdaArn: checkLabelDetection.functionArn,
        });

        createCustomResource(this, 'technicalCueDetectionOperation', {
            Name: "technicalCueDetection",
            OutputName: "TechnicalCueDetection",
            Description: "technicalCueDetection operator",
            Async: true,
            Configuration: { MediaType: "Video", Enabled: true },
            StartLambdaArn: startTechnicalCueDetection.functionArn,
            MonitorLambdaArn: checkTechnicalCueDetection.functionArn,
        });

        createCustomResource(this, 'shotDetectionOperation', {
            Name: "shotDetection",
            OutputName: "shotDetection",
            Description: "shotDetection operator",
            Async: true,
            Configuration: { MediaType: "Video", Enabled: true },
            StartLambdaArn: startShotDetection.functionArn,
            MonitorLambdaArn: checkShotDetection.functionArn,
        });

        createCustomResource(this, 'textDetectionOperation', {
            Name: "textDetection",
            OutputName: "TextDetection",
            Description: "Text detection operator",
            Async: true,
            Configuration: { MediaType: "Video", Enabled: true },
            StartLambdaArn: startTextDetection.functionArn,
            MonitorLambdaArn: checkTextDetection.functionArn,
        });

        createCustomResource(this, 'textDetectionOperationImage', {
            Name: "textDetectionImage",
            OutputName: "TextDetectionOperationImage",
            Description: "Text Detection image operator",
            Async: false,
            Configuration: { MediaType: "Image", Enabled: true },
            StartLambdaArn: startTextDetection.functionArn,
        });

        createCustomResource(this, 'labelDetectionOperationImage', {
            Name: "labelDetectionImage",
            OutputName: "LabelDetectionOperationImage",
            Description: "CelebRecognition image operator",
            Async: false,
            Configuration: { MediaType: "Image", Enabled: true },
            StartLambdaArn: startLabelDetection.functionArn,
        });

        createCustomResource(this, 'personTrackingOperation', {
            Name: "personTracking",
            OutputName: "PersonTracking",
            Description: "Person tracking",
            Async: true,
            Configuration: { MediaType: "Video", Enabled: false },
            StartLambdaArn: startPersonTracking.functionArn,
            MonitorLambdaArn: checkPersonTracking.functionArn,
        });

        createCustomResource(this, 'WaitOperation', {
            Name: "Wait",
            Description: "Wait operator - wait until /workflow/execution/continue API is called",
            Async: true,
            Configuration: { MediaType: "MetadataOnly", Enabled: false },
            StartLambdaArn: startWaitOperationLambda.valueAsString,
            MonitorLambdaArn: checkWaitOperationLambda.valueAsString,
        });


        //
        // Tags
        //

        [
            snsRekognitionTopic,
            genericDataLookupLambdaRole,
            mediainfoLambdaRole,
            mediaConvertS3Role,
            mediaConvertLambdaRole,
            transcribeRole,
            captionsRole,
            translateRole,
            pollyRole,
            comprehendS3Role,
            comprehendRole,
            rekognitionSNSRole,
            rekognitionLambdaRole,
        ].forEach(util.addMediaInsightsTag);

        //
        // Nag Rules
        //

        const roles = [
            genericDataLookupLambdaRole,
            mediainfoLambdaRole,
            mediaConvertLambdaRole,
            transcribeRole,
            captionsRole,
            translateRole,
            pollyRole,
            comprehendS3Role,
            comprehendRole,
        ];

        [
            mediaConvertS3Role,
            rekognitionLambdaRole,
            ...roles,
        ].map(role => role.node.defaultChild as iam.CfnRole).forEach(role => role.cfnOptions.metadata = {
            Comment: "This role contains two policies that provide GetObject permission for DataplaneBucketName. This duplication is necessary in order to avoid a syntax error when the user-specified ExternalBucketArn parameter is empty.",
        });


        // cfn_nag / cdk_nag
        [
            rekognitionSNSRole,
            rekognitionLambdaRole,
        ].forEach(role => util.setNagSuppressRules(role, {
            id: 'AwsSolutions-IAM5',
            id2: 'W11',
            reason: "the policy actions used in this role require * resource"
        }));


        // cfn_nag / cdk_nag
        roles.forEach(role => util.setNagSuppressRules(role, {
            id: 'AwsSolutions-IAM5',
            id2: 'W11',
            reason: "The X-Ray policy uses actions that must be applied to all resources. See https://docs.aws.amazon.com/xray/latest/devguide/security_iam_id-based-policy-examples.html#xray-permissions-resources",
        }));

        // cdk_nag
        [
            genericDataLookupLambdaRole,
            mediainfoLambdaRole,
        ].forEach(role => util.setNagSuppressRules(role, {
            id: 'AwsSolutions-IAM4',
            reason: "Managed policies required for IAM role.",
        }));

        util.setNagSuppressRules(Mediainfo, {
            id: 'AwsSolutions-L1',
            reason: "The version of pymediainfo does not support latest runtime version",
        });

        [
            mediaConvertS3Role,
            translateS3Role,
        ].forEach(role => util.setNagSuppressRules(role, {
            id: 'AwsSolutions-IAM5',
            reason: "Scoped down to S3 Bucket",
        }));

    }

    getLogicalId(element: CfnElement): string {
        return util.cleanUpLogicalId(super.getLogicalId(element));
    }
}
