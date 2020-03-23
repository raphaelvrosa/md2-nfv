import logging

import gevent
from gevent.queue import Queue

logger = logging.getLogger(__name__)

from exchange.eth.dapp import ExchangeDapp

from exchange.peering import Peering
from exchange.slicing import Slicing
from exchange.notary import Notary
from exchange.common.entity import Component


class Exchange(Component):
    def __init__(self, configs, events_queue, output_queue):
        Component.__init__(self)
        self.id = configs.get('nso').get('id')
        self.address = configs.get('nso').get('address')
        self.dapp = ExchangeDapp(configs.get('dapp'), events_queue)
        self.events_queue = events_queue
        self.output_queue = output_queue
        self.msgs_per_service = {}
        self.peering = Peering(configs, self.dapp)
        self.slicing = Slicing(self.id, configs, self.dapp, self.peering)
        self.notary = Notary(self.id, configs, self.dapp, self.peering)
        logger.info('Exchange Started')

    def get_jobs(self):
        jobs = []
        jobs.append(gevent.spawn(self._events))
        return jobs

    def _events(self):
        while True:
            try:
                msg = self.events_queue.get(block=False)
                event = msg.get("event")
            except gevent.queue.Empty:
                gevent.sleep(0.05)
                # continue
            else:
                handled_outputs = self.receive(msg)
                outputs = self.dispatch(msg, handled_outputs)
                if outputs:
                    logger.info("Output of event %s queued", event)
                    self.output_queue.put(outputs)

    def handle(self, msg, acks):
        event = msg.get('event')
        output = []
        logger.info("Handle event received: %s", event)

        if event == 'peer':
            output = self.peer(msg, acks)
        if event == 'notify':
            output = self.notify(msg, acks)
        if event == 'contract':
            output = self.contract(msg, acks)
        if event == 'service':
            output = self.service(msg, acks)
        if event == 'reply':
            output = self.reply(msg, acks)
        return output

    def get_msg_type(self, msg, acks):
        have_acks = acks is not None
        if have_acks:
            ack = acks[0]
            data = ack.get('data')
            msg_type = data.get('type')

            for ack in acks:
                data = ack.get('data')
                msg_type = data.get('type')
                logger.info('acks msg_type %s', msg_type)
                logger.info('acks data %s', data)

        else:
            data = msg.get('data')
            msg_type = data.get('type')
        logger.info('acks {0} - msg_type {1}'.format(have_acks, msg_type))
        return msg_type

    def peer(self, msg, acks):
        logger.info('######### peer #########')
        output = []
        msg_type = self.get_msg_type(msg, acks)
        if msg_type in ['config', 'request', 'reply']:
            output = self.peering.handle(msg_type, msg, acks)
        else:
            logger.info("unknown peer msg type %s", msg_type)
        return output

    def service(self, msg, acks):
        logger.info('######### service #########')
        output = []
        msg_type = self.get_msg_type(msg, acks)
        if msg_type in ['config', 'request', 'reply']:
            output = self.slicing.handle(msg_type, msg, acks)
        else:
            logger.info("unknown service msg type %s", msg_type)
        return output

    def notify(self, data, acks):
        pass

    def contract(self, msg, acks):
        logger.info('######### contract #########')
        output = []
        msg_type = self.get_msg_type(msg, acks)
        if msg_type in ['event', 'config', 'request', 'reply']:
            output = self.notary.handle(msg_type, msg, acks)
        else:
            logger.info("unknown servoce msg type %s", msg_type)
        return output

    def reply(self, data, acks):
        pass
