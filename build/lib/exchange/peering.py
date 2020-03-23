import logging
logger = logging.getLogger(__name__)


from exchange.common.mailing import Message
from exchange.common.content import Content


class Contact(Content):
    def __init__(self, id, address, key, enode):
        Content.__init__(self)
        self.id = id
        self.address = address
        self.key = key
        self.enode = enode

    def info(self):
        info = {
            'id': self.id,
            'address': self.address,
            'key': self.key,
            'enode': self.enode,
        }
        return info


class Contacts:
    def __init__(self):
        self.contacts = {}

    def add(self, data):
        contact = Contact(**data)
        id = contact.get('id')
        self.contacts[id] = contact
        return id

    def rem(self, id):
        if id in self.contacts:
            del self.contacts[id]
            return True
        return False

    def get(self, id):
        if id in self.contacts:
            return self.contacts[id]
        return None


class Peering:
    def __init__(self, configs, dapp):
        self.configs = configs
        self.dapp = dapp
        self.contacts = Contacts()

        id = self.configs.get('nso').get('id')
        address = self.configs.get('nso').get('address')
        key = self.dapp.get_id(),
        enode = self.dapp.get_enode()
        self.contact = Contact(id, address, key, enode)

    def get_address(self, domain_id):
        address = None
        if domain_id == self.contact.get('id'):
            address = self.contact.get('address')
        else:
            contact = self.contacts.get(domain_id)
            if contact:
                address = contact.get('address')
        return address

    def handle(self, msg_type, msg, acks):
        output = []
        if msg_type == 'config':
            output = self.config(msg)
        if msg_type == 'request':
            output = self.request(msg)
        if msg_type == 'reply':
            if acks:
                output = self.reply(msg, acks=acks)
        return output

    def config(self, msg):
        outputs = []
        data = msg.get('data')
        domains = data.get('domains', None)
        if domains:
            for domain in domains:
                domain_id = domain.get('id')
                domain_address = domain.get('address')
                info_data = self.contact.info()
                msg_data = {
                    'type': 'request',
                    'from': info_data,
                }
                prefix = self.contact.get('id')
                msg = Message(to_address=domain_address,
                              event='peer',
                              call='create',
                              prefix=prefix,
                              data=msg_data)
                output = (domain_id, msg)
                outputs.append(output)
        return outputs

    def register_peer(self, data):
        id = self.contacts.add(data)
        contact = self.contacts.get(id)
        enode = contact.get('enode')
        self.dapp.peer(id, enode)

    def request(self, msg):
        outputs = []
        data = msg.get('data')
        domain_id = msg.get('prefix')
        message_id = msg.get_id()

        data_from_domain = data.get('from')
        domain_address = data_from_domain.get('address')
        self.register_peer(data_from_domain)

        info_data = self.contact.info()
        msg_data = {
            'type': 'reply',
            'from': info_data,
        }
        prefix = self.contact.get('id')
        msg = Message(id=message_id,
                      to_address=domain_address,
                      event='peer',
                      call='create',
                      prefix=prefix,
                      data=msg_data,
                      reply=True)
        output = (domain_id, msg)
        outputs.append(output)
        return outputs

    def reply(self, msg, acks):
        logger.info('reply %s', msg.items())
        logger.info('reply acks %s', acks)
        outputs = []

        for ack in acks:
            data = ack.get('data')
            data_from_domain = data.get('from')
            self.register_peer(data_from_domain)

        message_id = msg.get_id()
        domain_id = msg.get('prefix')
        to_address = msg.get('params').get('call-back')
        prefix = self.contact.get('id')
        msg = Message(id=message_id,
                      to_address=to_address,
                      event='peer',
                      call='create',
                      prefix=prefix,
                      data='OK',
                      reply=True)
        output = (domain_id, msg)
        outputs.append(output)
        return outputs

