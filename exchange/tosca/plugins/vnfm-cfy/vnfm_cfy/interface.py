import requests

# import logging
# logger = logging.getLogger()


class WebClient():
    headers = {'Content-Type': 'application/json'}
    def __init__(self):
        self.logger = None

    def set_logger(self, logger):
        self.logger = logger

    def send_msg(self, _type, url, message, **kwargs):
        response = None
        try:
            if _type == 'post':
                response = requests.post(url, headers=WebClient.headers,
                                         data=message, **kwargs)
            elif _type == 'put':
                response = requests.put(url, headers=WebClient.headers,
                                        data=message, **kwargs)
            elif _type == 'get':
                response = requests.get(url, headers=WebClient.headers,
                                        data=message, **kwargs)
            else:
                response = requests.delete(url, headers=WebClient.headers,
                                           data=message, **kwargs)
        except requests.RequestException as exception:
            self.logger.info('Requests fail - exception %s', exception)
            response = None
        finally:
            reply = self.__process_msg_response(response)
            self.logger.info('Requests - response %s', response)
            if reply:
                return reply.text
            return reply

    def __process_msg_response(self, response):
        try:
            response.raise_for_status()
        except Exception as exception:
            self.logger.info("Response exception %s", exception)
            response = None
        finally:
            return response


if __name__ == '__main__':
    pass