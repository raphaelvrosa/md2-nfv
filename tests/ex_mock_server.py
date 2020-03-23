import gevent
import logging
from exchange.rest.server import WebServer

logger = logging.getLogger(__name__)


class MockServer(WebServer):
    def __init__(self, url, content_type='application/json'):
        self.logs(True)
        self.handlers = {
            'post':self._process_messages,
            'put': self._process_messages,
            'delete': self._process_messages,
            'get': self._process_messages,
        }
        WebServer.__init__(self, url, self.handlers, content_type)
        logger.info("Mock Server loaded")

    def _process_messages(self, msg):
        address, params, prefix, request, data = msg
        logger.debug('address %s, prefix %s, request %s', address, prefix, request)
        logger.debug('params %s', params)
        logger.debug('data %s', data)
        return True, 'Ack'

    def logs(self, debug):
        level = logging.DEBUG if debug else logging.INFO
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        handler.setLevel(level)
        logging.getLogger().addHandler(handler)
        logging.getLogger().setLevel(level)
        logger = logging.getLogger(__name__)


if __name__ == "__main__":
    url = 'http://127.0.0.1:9090'

    web1 = MockServer(url)
    web_server_thread = gevent.spawn(web1.init)
    jobs = [web_server_thread]
    gevent.joinall(jobs)
