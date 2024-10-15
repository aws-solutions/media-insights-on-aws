#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import datetime
import json
import urllib.request

def send_metrics(config):
    metrics = {}
    # move Solution ID and UUID to the root JSON level
    metrics['Solution'] = config.pop("SolutionId", None)
    metrics['UUID'] = config.pop("UUID", None)
    metrics['TimeStamp'] = str(datetime.datetime.utcnow().isoformat())
    metrics['Data'] = config
    url = 'https://metrics.awssolutionsbuilder.com/generic'
    data = json.dumps(metrics).encode('utf8')
    headers = {'content-type': 'application/json'}
    req = urllib.request.Request(url, data,headers)
    response = urllib.request.urlopen(req) #nosec
    print('RESPONSE CODE:: {}'.format(response.getcode()))
    print('METRICS SENT:: {}'.format(data))
