import json
import logging

import gevent
from gevent.queue import Empty, Queue
from exchange.rest.server import WebServer
from exchange.rest.async_client import WebClient

from exchange.core import Exchange
from exchange.common.mailing import Message

logger = logging.getLogger(__name__)


class Web():
    def __init__(self, configs):
        self.configs = configs
        self.events_queue = Queue()
        self.in_q = Queue()
        self.out_q = Queue()
        url = configs.get('nso').get('address')
        self.exchange = Exchange(configs, self.events_queue, self.out_q)

        self.events = [
            'peer',
            'notify',
            'contract',
            'service',
        ]
        self.handlers = {
            'post': self.post_handler,
            'put': self.put_handler,
            'delete': self.delete_handler,
            'get': self.get_handler,
        }
        self.map_calls = {
            'create':'post',
            'delete':'delete',
            'update':'put'
        }
        self.client = WebClient()
        self.server = WebServer(url, self.handlers)
        logger.info("Web App Started")

    def send_msg(self, url, msg, type='post', params=None):
        kwargs = {}
        if params:
            kwargs = {'params': params}
        answer = self.client.send_msg(type, url, msg, **kwargs)
        return answer

    def get_jobs(self):
        _jobs = []
        _jobs.extend(self.exchange.get_jobs())
        _jobs.append(gevent.spawn(self.process_messages))
        _jobs.append(gevent.spawn(self.server.init))
        _jobs.append(gevent.spawn(self._outputs))
        return _jobs

    def handle(self, call, msg):
        address, params, prefix, event, data = msg
        params = self.process_params(params)
        message_id = params.get('message-id', None)
        reply = params.get('reply', 'False')

        if reply == 'False':
            reply = False
        elif reply == 'True':
            reply = True
        else:
            reply = False

        dict_data = self.in_dict(data)

        logger.info("Web message id {0} type {1} from {2}".format(message_id, event, address))
        logger.info("prefix {0} - call {1} - params {2}".format(prefix, call, params))
        logger.info("data {0}".format(dict_data))

        msg = Message(id=message_id, event=event, from_address=address, params=params,
                      prefix=prefix, call=call, data=dict_data, reply=reply)
        self.in_q.put(msg)

    def post_handler(self, msg):
        self.handle('create', msg)
        ack, ok = 'wait', 'Ack'
        return ack, ok

    def delete_handler(self, msg):
        self.handle('delete', msg)
        ack, ok = 'wait', 'Ack'
        return ack, ok

    def put_handler(self, msg):
        self.handle('update', msg)
        ack, ok = 'wait', 'Ack'
        return ack, ok

    def get_handler(self, msg):
        event_type = 'get'
        outputs = []
        if outputs:
            if type(outputs) is list:
                output = outputs.pop()
                url, params, data, wait_reply = output
                ack, ok = True, data
            else:
                ack, ok = True, outputs
            return ack, ok

    def process_messages(self):
        while True:
            try:
                msg = self.in_q.get(block=False)
                event = msg.get('event')
                if event in self.events:
                    self.events_queue.put(msg)
                else:
                    logger.info("Process_messages: No event {0} registered".format(event))

            except Empty:
                # logger.debug("Input queue exception %s", e)
                gevent.sleep(.1)
                continue

    def format_url(self, url, prefix, event):
        full_url = url
        if prefix is not None:
            full_url = full_url + '/' + prefix
        if event is not None:
            full_url = full_url + '/' + event
        # logger.info("format_url {0} prefix {1} event {2}".format(url, prefix, event))
        return full_url

    def format_output(self, output):
        url = output.get('to_address')
        prefix = output.get('prefix')
        event = output.get('event')
        call = output.get('call')
        params = output.get('params')
        data = output.get('data')
        params['message-id'] = output.get_id()
        params['reply'] = output.reply()

        full_url = self.format_url(url, prefix, event)
        json_data = self.in_json(data)
        method = self.map_calls[call]
        return method, full_url, params, json_data

    def send_output(self, output):
        method, url, params, data = self.format_output(output)
        logger.debug("Output method {0} sent to {1} - {2}".format(method, url, params))
        # logger.debug("Output data {0}".format(data))

        self.send_msg(url, data, type=method, params=params)
        # answer = self.send_msg(url, data, type=method, params=params)
        # if answer:
        #     logger.debug("Reply {0}".format(answer))

    def _outputs(self):
        while True:
            try:
                outputs = self.out_q.get(block=False)
            except Empty:
                gevent.sleep(0.1)
                # continue
            else:
                if type(outputs) is list:
                    for output in outputs:
                        self.send_output(output)
                else:
                    logger.info('unknown output type {0} - {1}'.format(type(outputs), outputs))

    def get(self, context_id, request):
        answer = ''
        ack = False
        if context_id:
            if request == 'services':
                pass
            elif request == 'flags':
                pass
            else:
                logger.info('error: unknown get request {0} - context-id {1}'.format(request, context_id))
        if answer:
            ack = True
        else:
            logger.info('error: could not get state status for unknown {0} - context-id {1}'.format(request, context_id))
        return ack, answer

    def process_params(self, params):
        _params = {}
        for _item, _value in params.items():
            if len(_value) > 1:
                _params[_item] = _value
            else:
                value = _value.pop()
                _params[_item] = value
        return _params

    def in_json(self, data):
        if type(data) is dict or type(data) is str:
            json_data = json.dumps(data)
            return json_data
        else:
            try:
                json.loads(data)
                return data
            except ValueError as error:
                print("invalid json data: %s" % error)
            return ''

    def in_dict(self, data):
        if type(data) is dict:
            return data
        else:
            try:
                dict_data = json.loads(data)
                return dict_data
            except ValueError as error:
                print("invalid json data: %s" % error)
            return {}



if __name__ == "__main__":
    pass
