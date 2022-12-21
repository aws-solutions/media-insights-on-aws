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

import { Template } from 'aws-cdk-lib/assertions';
import { App } from 'aws-cdk-lib';
import { MediaInsightsStack } from '../lib/media-insights-stack';
import 'jest-cdk-snapshot';

const regexHashedFileName = /[A-Fa-f0-9]{64}(\.[a-z]{3,4})$/;
const replaceHashedName = "[HASH REMOVED]$1";

expect.addSnapshotSerializer({
    test: (val) => typeof val === 'string' && regexHashedFileName.test(val),
    serialize: (val) => val.replace(regexHashedFileName, replaceHashedName),
});

test('Snapshot media-insights root stack test', () => {
    const app = new App();
    // WHEN
    const stack = new MediaInsightsStack(
        app,
        'MiTestStack'
    );
    const template = Template.fromStack(stack);

    // THEN
    expect(template).toMatchSnapshot();
});
