import logging
import json
import time
from exchange.rest.client import WebClient

logger = logging.getLogger(__name__)

import gevent


class OrchestratorTest(WebClient):
    def __init__(self, orch_id, nso_url, url):
        self._id = orch_id
        self._nso_url = nso_url
        self._callback_url = url
        self._msgs_id = 1
        self.logs(True)

    def logs(self, debug):
        level = logging.DEBUG if debug else logging.INFO
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        handler.setLevel(level)
        logging.getLogger().addHandler(handler)
        logging.getLogger().setLevel(level)
        logger = logging.getLogger(__name__)

    def send(self, url, msg, type='post', params=None):
        kwargs = {}
        if params:
            kwargs = {'params': params}
        answer = self.send_msg(type, url, msg, **kwargs)
        return answer

    def peer_request(self):
        logger.debug('peer_request')
        msg = {
            'type':'config',
            'domains': [
                {'id': 'B',
                 'address': 'http://127.0.0.1:8882'},
                {'id': 'C',
                 'address': 'http://127.0.0.1:8883'},
                {'id': 'D',
                 'address': 'http://127.0.0.1:8884'},
                {'id': 'E',
                 'address': 'http://127.0.0.1:8885'}
            ]
        }
        msg_json = json.dumps(msg)
        params = {'message-id': self._msgs_id, 'call-back': self._callback_url}
        suffix = '/' + self._id + '/peer'
        url = self._nso_url + suffix
        answer = self.send(url, msg_json, type='post', params=params)
        logger.debug('reply')
        logger.debug(answer)
        self._msgs_id += 1

    def config_service_go(self, service_id='1'):
        logger.debug('subscribe_service')
        msg = {
              'type': 'config',
              'tenant': 'X',
              'service': service_id,
              'domains': [
                  {
                    'id': 'A',
                    'params': {
                        'in_port': '1',
                        'out_port': '2',
                        'queue_max_rate': '50000000',
                        'action': 'push',
                        'tag': 4097
                    },
                  },
                  {
                    'id': 'B',
                    'params': {
                        'in_port': '1',
                        'out_port': '3',
                        'queue_max_rate': '50000000',
                        'action': 'match',
                        'tag': 4097
                    },
                  },
                  {
                      'id': 'C',
                      'params': {
                          'in_port': '1',
                          'out_port': '4',
                          'queue_max_rate': '50000000',
                          'action': 'pop',
                          'tag': 4097
                      },
                  },
              ]
        }

        msg_json = json.dumps(msg)
        params = {'message-id': self._msgs_id, 'call-back': self._callback_url}
        suffix = '/' + self._id + '/service'
        url = self._nso_url + suffix
        answer = self.send(url, msg_json, type='post', params=params)
        logger.debug('reply')
        logger.debug(answer)
        self._msgs_id += 1

    def config_service_back(self, service_id='1'):
        logger.debug('subscribe_service')
        msg = {
              'type': 'config',
              'tenant': 'Y',
              'service': service_id,
              'domains': [
                  {
                    'id': 'A',
                    'params': {
                        'in_port': '2',
                        'out_port': '1',
                        'queue_max_rate': '50000000',
                        'action': 'pop',
                        'tag': 4098
                    },
                  },
                  {
                    'id': 'B',
                    'params': {
                        'in_port': '3',
                        'out_port': '1',
                        'queue_max_rate': '50000000',
                        'action': 'match',
                        'tag': 4098
                    },
                  },
                  {
                      'id': 'C',
                      'params': {
                          'in_port': '4',
                          'out_port': '1',
                          'queue_max_rate': '50000000',
                          'action': 'push',
                          'tag': 4098
                      },
                  },
              ]
        }

        msg_json = json.dumps(msg)
        params = {'message-id': self._msgs_id, 'call-back': self._callback_url}
        suffix = '/' + self._id + '/service'
        url = self._nso_url + suffix
        answer = self.send(url, msg_json, type='post', params=params)
        logger.debug('reply')
        logger.debug(answer)
        self._msgs_id += 1

    def config_service_go_update_basic(self, service_id='1'):
        logger.debug('subscribe_service')
        msg = {
              'type': 'config',
              'tenant': 'X',
              'service': service_id,
              'domains': [
                  {
                    'id': 'A',
                    'call': 'update',
                    'params': {
                        'in_port': '1',
                        'out_port': '2',
                        'queue_max_rate': '30000000',
                        'action': 'push',
                        'tag': 4097
                    },
                  },
                  {
                    'id': 'B',
                    'call': 'update',
                    'params': {
                        'in_port': '1',
                        'out_port': '3',
                        'queue_max_rate': '30000000',
                        'action': 'match',
                        'tag': 4097
                    },
                  },
                  {
                      'id': 'C',
                      'call': 'update',
                      'params': {
                          'in_port': '1',
                          'out_port': '4',
                          'queue_max_rate': '30000000',
                          'action': 'pop',
                          'tag': 4097
                      },
                  },
              ]
        }

        msg_json = json.dumps(msg)
        params = {'message-id': self._msgs_id, 'call-back': self._callback_url}
        suffix = '/' + self._id + '/service'
        url = self._nso_url + suffix
        answer = self.send(url, msg_json, type='put', params=params)
        logger.debug('reply')
        logger.debug(answer)
        self._msgs_id += 1

    def config_service_go_update_complex(self, service_id='1'):
        logger.debug('subscribe_service')
        msg = {
              'type': 'config',
              'tenant': 'X',
              'service': service_id,
              'domains': [
                  {
                    'id': 'A',
                    'call': 'update',
                    'params': {
                        'in_port': '1',
                        'out_port': '2',
                        'queue_max_rate': '30000000',
                        'action': 'push',
                        'tag': 4097
                    },
                  },
                  {
                    'id': 'B',
                    'call': 'update',
                    'params': {
                        'in_port': '1',
                        'out_port': '2',
                        'queue_max_rate': '30000000',
                        'action': 'match',
                        'tag': 4097
                    },
                  },
                  {
                      'id': 'C',
                      'call': 'delete',
                      'params': {
                          'in_port': '1',
                          'out_port': '4',
                          'queue_max_rate': '30000000',
                          'action': 'match',
                          'tag': 4097
                      },
                  },
                  {
                      'id': 'D',
                      'call': 'create',
                      'params': {
                          'in_port': '2',
                          'out_port': '4',
                          'queue_max_rate': '30000000',
                          'action': 'match',
                          'tag': 4097
                      },
                  },
                  {
                      'id': 'E',
                      'call': 'create',
                      'params': {
                          'in_port': '1',
                          'out_port': '3',
                          'queue_max_rate': '30000000',
                          'action': 'pop',
                          'tag': 4097
                      },
                  },
              ]
        }

        msg_json = json.dumps(msg)
        params = {'message-id': self._msgs_id, 'call-back': self._callback_url}
        suffix = '/' + self._id + '/service'
        url = self._nso_url + suffix
        answer = self.send(url, msg_json, type='put', params=params)
        logger.debug('reply')
        logger.debug(answer)
        self._msgs_id += 1

    def config_service_back_update_complex_1(self, service_id='1'):
        logger.debug('subscribe_service')
        msg = {
              'type': 'config',
              'tenant': 'Y',
              'service': service_id,
              'domains': [
                  {
                      'id': 'A',
                      'call': 'delete',
                      'params': {
                          'in_port': '2',
                          'out_port': '1',
                          'queue_max_rate': '50000000',
                          'action': 'pop',
                          'tag': 4098
                      },
                  },
              ]
        }

        msg_json = json.dumps(msg)
        params = {'message-id': self._msgs_id, 'call-back': self._callback_url}
        suffix = '/' + self._id + '/service'
        url = self._nso_url + suffix
        answer = self.send(url, msg_json, type='put', params=params)
        logger.debug('reply')
        logger.debug(answer)
        self._msgs_id += 1

    def config_service_back_update_complex_2(self, service_id='1'):
        logger.debug('subscribe_service')
        msg = {
              'type': 'config',
              'tenant': 'Y',
              'service': service_id,
              'domains': [
                  {
                      'id': 'A',
                      'call': 'delete',
                      'params': {
                          'in_port': '2',
                          'out_port': '1',
                          'queue_max_rate': '50000000',
                          'action': 'pop',
                          'tag': 4098
                      },
                  },
                  {
                    'id': 'A',
                    'call': 'create',
                    'params': {
                        'in_port': '3',
                        'out_port': '1',
                        'queue_max_rate': '50000000',
                        'action': 'pop',
                        'tag': 4098
                    },
                  },
                  {
                    'id': 'B',
                    'call': 'delete',
                    'params': {
                        'in_port': '3',
                        'out_port': '1',
                        'queue_max_rate': '50000000',
                        'action': 'match',
                        'tag': 4098
                    },
                  },
                  {
                      'id': 'C',
                      'call': 'delete',
                      'params': {
                          'in_port': '4',
                          'out_port': '1',
                          'queue_max_rate': '50000000',
                          'action': 'push',
                          'tag': 4098
                      },
                  },
                  {
                      'id': 'D',
                      'call': 'create',
                      'params': {
                          'in_port': '4',
                          'out_port': '1',
                          'queue_max_rate': '50000000',
                          'action': 'match',
                          'tag': 4098
                      },
                  },
                  {
                      'id': 'E',
                      'call': 'create',
                      'params': {
                          'in_port': '3',
                          'out_port': '1',
                          'queue_max_rate': '50000000',
                          'action': 'push',
                          'tag': 4098
                      },
                  },
              ]
        }

        msg_json = json.dumps(msg)
        params = {'message-id': self._msgs_id, 'call-back': self._callback_url}
        suffix = '/' + self._id + '/service'
        url = self._nso_url + suffix
        answer = self.send(url, msg_json, type='put', params=params)
        logger.debug('reply')
        logger.debug(answer)
        self._msgs_id += 1

    def config_service_go_delete(self, service_id='1'):
        logger.debug('subscribe_service')
        msg = {
              'type': 'config',
              'tenant': 'X',
              'service': service_id,
              'domains': []
        }

        msg_json = json.dumps(msg)
        params = {'message-id': self._msgs_id, 'call-back': self._callback_url}
        suffix = '/' + self._id + '/service'
        url = self._nso_url + suffix
        answer = self.send(url, msg_json, type='del', params=params)
        logger.debug('reply')
        logger.debug(answer)
        self._msgs_id += 1

    def config_service_back_delete(self, service_id='1'):
        logger.debug('subscribe_service')
        msg = {
              'type': 'config',
              'tenant': 'Y',
              'service': service_id,
              'domains': []
        }

        msg_json = json.dumps(msg)
        params = {'message-id': self._msgs_id, 'call-back': self._callback_url}
        suffix = '/' + self._id + '/service'
        url = self._nso_url + suffix
        answer = self.send(url, msg_json, type='del', params=params)
        logger.debug('reply')
        logger.debug(answer)
        self._msgs_id += 1

    def config_create_contract(self, service_id='1'):
        logger.debug('config_create_contract')
        msg = {
              'type': 'config',
              'tenant': 'X',
              'service': service_id,
              'contract': 'LifecycleNotary',
              'log': {
                    'WorkflowCall': {
                    'on': 'service',
                    'calls': ['create', 'update', 'delete'],
                    'attribs': {
                        'call': 'workflow',
                        'ack': 'acks',
                        'update': 'updates',
                        }
                    }
               },
              'domains': [
                  {
                    'id': 'A',
                  },
                  {
                    'id': 'B',
                  },
                  {
                    'id': 'C',
                  },
                  {
                      'id': 'D',
                  },
                  {
                      'id': 'E',
                  },
              ]
        }
        msg_json = json.dumps(msg)
        params = {'message-id': self._msgs_id, 'call-back': self._callback_url}
        suffix = '/' + self._id + '/contract'
        url = self._nso_url + suffix
        answer = self.send(url, msg_json, type='post', params=params)
        logger.debug('reply')
        logger.debug(answer)
        self._msgs_id += 1

    def config_delete_contract(self, service_id='1'):
        logger.debug('config_delete_contract')
        msg = {
              'type': 'config',
              'tenant': 'X',
              'service': service_id,
              'contract': 'LifecycleNotary',
        }
        msg_json = json.dumps(msg)
        params = {'message-id': self._msgs_id, 'call-back': self._callback_url}
        suffix = '/' + self._id + '/contract'
        url = self._nso_url + suffix
        answer = self.send(url, msg_json, type='delete', params=params)
        logger.debug('reply')
        logger.debug(answer)
        self._msgs_id += 1

    def run_cycle_real(self):
        self.peer_request()
        # time.sleep(3)
        self.config_service_go(service_id='1')
        # time.sleep(15)
        self.config_service_back(service_id='1')
        self.config_service_go_update_complex(service_id='1')
        self.config_service_back_update_complex_1(service_id='1')
        self.config_service_back_update_complex_2(service_id='1')
        # time.sleep(15)
        self.config_service_go_delete(service_id='1')
        self.config_service_back_delete(service_id='1')

    def run_cycle_contract(self):
        self.peer_request()
        time.sleep(5)
        self.config_create_contract()
        time.sleep(20)
        self.config_delete_contract()


class Execution():

    def execute_local_configs(self):
        nso_url = 'http://127.0.0.1:8881'
        mock_server_url = 'http://127.0.0.1:9090'
        id = '100'

        mock = OrchestratorTest(id, nso_url, mock_server_url)
        t1 = gevent.spawn(mock.run_cycle_real)
        gevent.joinall([t1])

    def execute_local_contracts(self):
        nso_url = 'http://127.0.0.1:8881'
        mock_server_url = 'http://127.0.0.1:9090'
        id = '100'

        mock = OrchestratorTest(id, nso_url, mock_server_url)
        t1 = gevent.spawn(mock.run_cycle_contract)
        gevent.joinall([t1])


if __name__ == "__main__":
    run = Execution()
    # run.execute_local_configs()
    run.execute_local_contracts()
