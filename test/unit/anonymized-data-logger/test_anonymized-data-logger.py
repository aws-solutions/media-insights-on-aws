# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import re, unittest, importlib
from unittest.mock import MagicMock

class Context():
    log_stream_name = ''

    def __init__(self, log_stream_name = 'testLogStreamName'):
        self.log_stream_name = log_stream_name

class TestAnonymizedDataLogger(unittest.TestCase):
    @classmethod
    def setUp(self):
        import lib.cfnresponse as cfn
        import lib.metrics as metrics
        self.cfn = cfn.send
        self.metrics = metrics.send_metrics

        # mocks
        cfn.send = MagicMock()
        metrics.send_metrics = MagicMock()

    @classmethod
    def tearDown(self):
        import lib.cfnresponse as cfn
        import lib.metrics as metrics
        cfn.send = self.cfn
        metrics.send_metrics = self.metrics
        return super().tearDownClass()

    def test_handler_create_with_uuid(self):
        # imports
        import lib.cfnresponse as cfn
        import lib.metrics as metrics
        anonymized_data_logger = importlib.import_module('anonymized-data-logger')

        # test parameters
        event_param = {
            'RequestType': 'Create',
            'ResourceProperties': {
                'Resource': 'UUID',
                'ServiceToken': 'testServiceToken',
                'SolutionId': 'testSolutionId',
                'UUID': 'testUUID'
            },
        }
        context_param = 'testContext'

        # expected values

        anonymized_data_logger.handler(
            event_param,
            context_param
        )
        assert metrics.send_metrics.call_count == 0
        assert cfn.send.call_count == 1
        assert cfn.send.call_args[0][0] == event_param
        assert cfn.send.call_args[0][1] == 'testContext'
        assert cfn.send.call_args[0][2] == 'SUCCESS'
        assert cfn.send.call_args[0][3]['UUID'] != None
        assert re.match(
            r'^[0-9a-fA-F]{8}\b-[0-9a-fA-F]{4}\b-[0-9a-fA-F]{4}\b-[0-9a-fA-F]{4}\b-[0-9a-fA-F]{12}$',
            cfn.send.call_args[0][3]['UUID']
        ) != None
        assert re.match(
            r'^[0-9a-fA-F]{8}\b-[0-9a-fA-F]{4}\b-[0-9a-fA-F]{4}\b-[0-9a-fA-F]{4}\b-[0-9a-fA-F]{12}$',
            cfn.send.call_args[0][4]
        ) != None

    def test_handler_create_with_anonymized_metrics(self):
        # imports
        import lib.cfnresponse as cfn
        import lib.metrics as metrics
        anonymized_data_logger = importlib.import_module('anonymized-data-logger')

        # test parameters
        event_param = {
            'RequestType': 'Create',
            'ResourceProperties': {
                'Resource': 'AnonymizedMetric',
                'ServiceToken': 'testServiceToken',
                'SolutionId': 'testSolutionId',
            },
        }
        context_param = 'testContext'

        # expected values
        anonymized_data_logger.handler(
            event_param,
            context_param
        )

        # assertions
        assert metrics.send_metrics.call_count == 1
        assert metrics.send_metrics.call_args[0][0] == {
            'SolutionId': event_param['ResourceProperties']['SolutionId'],
            'CFTemplate': (
                'Created'
            )
        }
        assert cfn.send.call_count == 1
        assert cfn.send.call_args[0][0] == event_param
        assert cfn.send.call_args[0][1] == 'testContext'
        assert cfn.send.call_args[0][2] == 'SUCCESS'
        assert cfn.send.call_args[0][3] == {}
        assert cfn.send.call_args[0][4] == 'Metrics Sent'

    def test_create_with_unsupported_resource(self):
        # imports
        import lib.cfnresponse as cfn
        import lib.metrics as metrics
        anonymized_data_logger = importlib.import_module('anonymized-data-logger')

        # test parameters
        event_param = {
            'RequestType': 'Create',
            'ResourceProperties': {
                'Resource': 'Unsupported',
                'ServiceToken': 'testServiceToken',
                'SolutionId': 'testSolutionId',
            },
        }
        context_param = Context()

        # expected values
        anonymized_data_logger.handler(
            event_param,
            context_param
        )

        # assertions
        assert metrics.send_metrics.call_count == 0

        assert cfn.send.call_count == 1
        assert cfn.send.call_args[0][0] == event_param
        assert cfn.send.call_args[0][1] == context_param
        assert cfn.send.call_args[0][2] == 'FAILED'
        assert cfn.send.call_args[0][3] == {}
        assert cfn.send.call_args[0][4] == context_param.log_stream_name

    def test_handler_update_with_uuid(self):
        # imports
        import lib.cfnresponse as cfn
        import lib.metrics as metrics
        anonymized_data_logger = importlib.import_module('anonymized-data-logger')

        # test parameters
        event_param = {
            'RequestType': 'Update',
            'ResourceProperties': {
                'Resource': 'UUID',
                'ServiceToken': 'testServiceToken',
                'SolutionId': 'testSolutionId',
                'UUID': 'testUUID'
            },
        }
        context_param = 'testContext'

        # expected values

        anonymized_data_logger.handler(
            event_param,
            context_param
        )
        assert metrics.send_metrics.call_count == 0
        assert cfn.send.call_count == 1
        assert cfn.send.call_args[0][0] == event_param
        assert cfn.send.call_args[0][1] == 'testContext'
        assert cfn.send.call_args[0][2] == 'SUCCESS'
        assert cfn.send.call_args[0][3]['UUID'] != None
        assert re.match(
            r'^[0-9a-fA-F]{8}\b-[0-9a-fA-F]{4}\b-[0-9a-fA-F]{4}\b-[0-9a-fA-F]{4}\b-[0-9a-fA-F]{12}$',
            cfn.send.call_args[0][3]['UUID']
        ) != None
        assert re.match(
            r'^[0-9a-fA-F]{8}\b-[0-9a-fA-F]{4}\b-[0-9a-fA-F]{4}\b-[0-9a-fA-F]{4}\b-[0-9a-fA-F]{12}$',
            cfn.send.call_args[0][4]
        ) != None

    def test_handler_update_with_anonymized_metrics(self):
        # imports
        import lib.cfnresponse as cfn
        import lib.metrics as metrics
        anonymized_data_logger = importlib.import_module('anonymized-data-logger')

        # test parameters
        event_param = {
            'RequestType': 'Update',
            'ResourceProperties': {
                'Resource': 'AnonymizedMetric',
                'ServiceToken': 'testServiceToken',
                'SolutionId': 'testSolutionId',
            },
        }
        context_param = 'testContext'

        # expected values
        anonymized_data_logger.handler(
            event_param,
            context_param
        )

        # assertions
        assert metrics.send_metrics.call_count == 1
        assert metrics.send_metrics.call_args[0][0] == {
            'SolutionId': event_param['ResourceProperties']['SolutionId'],
            'CFTemplate': (
                'Updated'
            )
        }
        assert cfn.send.call_count == 1
        assert cfn.send.call_args[0][0] == event_param
        assert cfn.send.call_args[0][1] == 'testContext'
        assert cfn.send.call_args[0][2] == 'SUCCESS'
        assert cfn.send.call_args[0][3] == {}
        assert cfn.send.call_args[0][4] == 'Metrics Sent'

    def test_handler_delete(self):
        # imports
        import lib.cfnresponse as cfn
        import lib.metrics as metrics
        anonymized_data_logger = importlib.import_module('anonymized-data-logger')

        # test parameters
        event_param = {
            'RequestType': 'Delete',
            'ResourceProperties': {
                'Resource': 'AnonymizedMetric',
                'ServiceToken': 'testServiceToken',
                'SolutionId': 'testSolutionId',
            },
        }
        context_param = 'testContext'

        # expected values
        anonymized_data_logger.handler(
            event_param,
            context_param
        )

        # assertions
        assert metrics.send_metrics.call_count == 0
        assert cfn.send.call_count == 1
        assert cfn.send.call_args[0][0] == event_param
        assert cfn.send.call_args[0][1] == 'testContext'
        assert cfn.send.call_args[0][2] == 'SUCCESS'
        assert cfn.send.call_args[0][3] == {}

    def test_handler_not_supported_request(self):
        # imports
        import lib.cfnresponse as cfn
        import lib.metrics as metrics
        anonymized_data_logger = importlib.import_module('anonymized-data-logger')

        # test parameters
        event_param = {
            'RequestType': 'Not_Supported',
            'ResourceProperties': {
                'Resource': 'AnonymizedMetric',
                'ServiceToken': 'testServiceToken',
                'SolutionId': 'testSolutionId',
            },
        }
        context_param = 'testContext'

        # expected values
        anonymized_data_logger.handler(
            event_param,
            context_param
        )

        # assertions
        assert metrics.send_metrics.call_count == 0
        assert cfn.send.call_count == 0

    def test_handler_error_handling(self):
        # imports
        import lib.cfnresponse as cfn
        import lib.metrics as metrics
        anonymized_data_logger = importlib.import_module('anonymized-data-logger')

        # test parameters
        event_param = {
            'ResourceProperties': {
                'Resource': 'AnonymizedMetric',
                'ServiceToken': 'testServiceToken',
                'SolutionId': 'testSolutionId',
            },
        }
        context_param = Context()

        # expected values
        anonymized_data_logger.handler(
            event_param,
            context_param
        )

        # assertions
        assert metrics.send_metrics.call_count == 0
        assert cfn.send.call_count == 1
        assert cfn.send.call_args[0][0] == event_param
        assert cfn.send.call_args[0][1] == context_param
        assert cfn.send.call_args[0][2] == 'FAILED'
        assert cfn.send.call_args[0][3] == {}
        assert cfn.send.call_args[0][4] == context_param.log_stream_name
