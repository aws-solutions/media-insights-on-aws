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

import { Construct, IConstruct } from 'constructs';
import {
    Aws,
    CfnCondition,
    CfnMapping,
    CfnResource,
    Fn,
    IResource,
    Stack,
    Tags,
} from 'aws-cdk-lib';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as lambda from 'aws-cdk-lib/aws-lambda';

/**
 * Used with setNagSuppressRules to represent a cfn_nag rule.
 */
export interface NagSuppressRule {
    readonly id: string;
    readonly reason: string;
}

/**
 * Creates a metadata property on resource to suppress cfn_nag rules.
 * Note: This overwrites the metadata with a new object.
 */
export function setNagSuppressRules(resource: IResource | CfnResource, ...rules: NagSuppressRule[]): void {
    // We need the underlying CfnResource so get it if we have a IResource.
    const cfn: CfnResource = resource instanceof CfnResource ? resource : resource.node.defaultChild as CfnResource;
    // Add metadata representing the rules to suppress.
    cfn.cfnOptions.metadata = Object.assign({
        cfn_nag: {
            rules_to_suppress: rules,
        },
    }, cfn.cfnOptions.metadata);
}

/**
 * Set a condition on any resource.
 */
export function setCondition(resource: IResource | Stack, condition: CfnCondition): void {
    (resource.node.defaultChild as CfnResource).cfnOptions.condition = condition;
}

/**
 * Initialization props for the `SourceCodeHelper`.
 */
export interface SourceCodeMapProps {
    readonly GlobalS3Bucket?: string;
    readonly TemplateKeyPrefix?: string;
    readonly FrameworkVersion?: string;
}

/**
 * Helper utility for creating the "SourceCode" mapping used in each stack.
 */
export class SourceCodeHelper {
    private readonly sourceCodeMap: CfnMapping;
    private readonly regionalBucket: s3.IBucket;

    constructor(scope: Construct, map?: SourceCodeMapProps) {
        this.sourceCodeMap = new CfnMapping(scope, 'SourceCode', {
            mapping: {
                General: {
                    RegionalS3Bucket: "%%REGIONAL_BUCKET_NAME%%",
                    CodeKeyPrefix: "aws-media-insights-engine/%%VERSION%%",
                    ...map,
                }
            }
        });

        this.regionalBucket = s3.Bucket.fromBucketName(this.sourceCodeMap.stack,
                            'RegionalS3Bucket', this.getRegionalS3BucketName());
    }

    /**
     * @returns A reference to a value in the map based on the key.
     */
    findInMap(key: string): string {
        return this.sourceCodeMap.findInMap("General", key);
    }

    /**
     * @returns The RegionalS3Bucket name.
     */
    getRegionalS3BucketName(): string {
        return Fn.join('-', [ this.findInMap("RegionalS3Bucket"), Aws.REGION ]);
    }

    /**
     * @returns The CodeKeyPrefix value.
     */
    getSourceCodeKey(name: string): string {
        return Fn.join('/', [ this.findInMap("CodeKeyPrefix"), name ]);
    }

    /**
     * @returns a `lambda.Code` construct representing a source code archive
     * in the regional S3 bucket located under the code key prefix.
     */
    codeFromRegionalBucket(name: string): lambda.Code {
        return lambda.Code.fromBucket(
            this.regionalBucket,
            this.getSourceCodeKey(name),
        );
    }
}

/**
 * Tag the construct with the media insights environment tag.
 */
export function addMediaInsightsTag(scope: IConstruct): void {
    Tags.of(scope).add('environment', 'mie');
}

/**
 * Cleans up the logical ID by removing excessive customizations made by CDK.
 */
export function cleanUpLogicalId(logicalId: string): string {
    return logicalId
        .replace('referencetomediainsights', '')
        .replace('mediainsightsAnalyticsA', 'a')
        .replace(/NestedStack.*NestedStackResource/, '')
        .replace(/^(CustomResource|TestLambda)/, '')
        .replace(/[A-F0-9]{8}([A-Z][a-z][a-z])?$/, (_, m1) => (m1 || '').replace(/^Ref$/, ''));
}
