import logging
logger = logging.getLogger(__name__)

from exchange.common.mailing import Mailing

class Component():

    def __init__(self):
        self.mail = Mailing()

    def handle(self, msg, acks):
        raise NotImplementedError

    def receive(self, msg):
        logger.debug("receive")
        reply_acks = self.mail.input(msg)
        if reply_acks:
            logger.debug("Has reply_acks %s", reply_acks)
            (msg_entrypoint, msgs_reply) = self.mail.get_reply(msg)
            outputs = self.handle(msg_entrypoint, msgs_reply)
        elif self.mail.has_next(msg):
            logger.debug("has_next")
            outputs = self.mail.get_next_outputs(msg)
        else:
            outputs = self.handle(msg, None)
        return outputs

    def dispatch(self, msg, handled_outputs):
        logger.debug("dispatch")
        outputs = []
        if handled_outputs:
            outputs = self.mail.output(msg, handled_outputs)
        else:
            logger.info("outputs empty")
        return outputs

