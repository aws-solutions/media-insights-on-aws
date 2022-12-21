from unittest.mock import MagicMock
import requests, json, unittest

class Context():
    log_stream_name = ''

    def __init__(self, log_stream_name = 'testLogStreamName'):
        self.log_stream_name = log_stream_name

class TestCfnResponse(unittest.TestCase):
    @classmethod
    def setUp(self):
        # mocks
        self.requests = requests.put
        requests.put = MagicMock(return_value = { 'reason': 'test_reason' })

    @classmethod
    def tearDown(self):
        requests.put = self.requests


    def test_send_success(self):
        # imports
        from lib import cfnresponse

        # test parameters
        event_param = {
            'ResponseURL': 'testResponseURL',
            'StackId': 'testStackId',
            'RequestId': 'testRequestId',
            'LogicalResourceId': 'testLogicalResourceId'
        }
        context_param = Context()
        response_status_param = 'testResponseStatus'
        response_data_param = 'testResponseData'
        physical_resource_id_param = 'testPhysicalResourceId'
        no_echo_param = 'testNoEchoParam'

        #expected responses
        expected_response_body = json.dumps({
            'Status': response_status_param,
            'Reason': 'See the details in CloudWatch Log Stream: ' + context_param.log_stream_name,
            'PhysicalResourceId': physical_resource_id_param,
            'StackId': event_param['StackId'],
            'RequestId': event_param['RequestId'],
            'LogicalResourceId': event_param['LogicalResourceId'],
            'NoEcho': no_echo_param,
            'Data': response_data_param
        })

        cfnresponse.send(
            event_param,
            context_param,
            response_status_param,
            response_data_param,
            physical_resource_id_param,
            no_echo_param
        )

        # assertions
        assert requests.put.call_count == 1
        assert requests.put.call_args[0][0] == event_param['ResponseURL']
        assert requests.put.call_args[1]['data'] == expected_response_body
        assert requests.put.call_args[1]['headers'] == {
            'content-type': '',
            'content-length': str(len(expected_response_body))
        }
