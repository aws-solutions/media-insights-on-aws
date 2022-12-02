import unittest
from unittest.mock import MagicMock
import json, datetime, urllib.request as request

class MockUrlResponse():
    def getcode(self):
        return 'testCode'

class TestMetrics(unittest.TestCase):
    @classmethod
    def setUp(self):
        self.request = request.Request
        self.urlopen = request.urlopen

        # mocks
        request.Request = MagicMock(return_value = 'testValue')
        request.urlopen = MagicMock(return_value = MockUrlResponse())

    @classmethod
    def tearDown(self) -> None:
        request.Request = self.request
        request.urlopen = self.urlopen
        return super().tearDownClass()

    def test_send_metrics(self): 
        from lib import metrics

        # test parameters
        config_param = {
            'SolutionId': 'testSolutionId',
            'UUID': 'testUUID'
        }
        timestamp_param = str(datetime.datetime.utcnow().isoformat())

        # expected values
        expected_data = json.dumps({
            'Solution': 'testSolutionId',
            'UUID': 'testUUID',
            'TimeStamp': timestamp_param,
            'Data': {}
        }).encode('utf8')

        metrics.send_metrics(config_param, timestamp_param)

        # assertions
        assert request.Request.call_count == 1
        assert request.Request.call_args[0][0] == 'https://metrics.awssolutionsbuilder.com/generic'
        assert request.Request.call_args[0][1] == expected_data
        assert request.Request.call_args[0][2] == {'content-type': 'application/json'}

        assert request.urlopen.call_count == 1
        assert request.urlopen.call_args[0][0] == 'testValue'
