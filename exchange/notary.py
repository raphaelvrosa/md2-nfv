import logging
logger = logging.getLogger(__name__)

from exchange.common.mailing import Message
from exchange.common.content import Content


class Record(Content):
    def __init__(self, domain, tenant, service, contract, log, domains=None):
        Content.__init__(self)
        self.domain = domain
        self.tenant = tenant
        self.service = service
        self.contract = contract
        self.log = log
        self.domains = domains
        self.contract_id = None
        self.contract_info = {}
        self.ack = False

    def get_request(self, domain, call):
        request = {
            'call': call,
            'domain': domain,
            'data': {
                'type': 'request',
                'tenant': self.tenant,
                'service': self.service,
                'contract': self.contract,
                'log': self.log,
                'info': self.contract_info,
            }
        }
        return request

    def get_reply(self, call):
        reply = {
            'call': call,
            'data': {
                'type': 'reply',
                'domain': self.domain,
                'tenant': self.tenant,
                'service': self.service,
                'contract_id': self.contract_id,
                'ack': self.ack,
            }
        }
        return reply


class Bookeeper:
    def __init__(self, id, dapp):
        self.id = id
        self.dapp = dapp
        self.records = {}

    def init_record(self, data):
        tenant = data.get('tenant', None)
        service = data.get('service', None)
        contract = data.get('contract', None)
        log = data.get('log', None)
        domains = data.get('domains', None)

        if all([tenant, service, contract, log]):
            new_record = Record(self.id, tenant, service, contract, log, domains)
            self.records[(tenant, service, contract)] = new_record
            logger.info("init_record Ok - %s", new_record.items())
            return new_record

        logger.info("init_record Fail - missing element %s, %s, %s, %s",
                    tenant, service, contract, log)
        return None

    def get_record(self, data):
        tenant = data.get('tenant', None)
        service = data.get('service', None)
        contract = data.get('contract', None)
        if all([tenant, service, contract]):
            record = self.records[(tenant, service, contract)]
            return record
        return None

    def delete_record(self, data):
        tenant = data.get('tenant')
        service = data.get('service')
        contract = data.get('contract')
        if all([tenant, service, contract]):
            if (tenant, service, contract) in self.records:
                del self.records[(tenant, service, contract)]
                return True
        return False

    def init_contract(self, record, contract_info=None):
        if contract_info:
            contract_id = self.dapp.join(**contract_info)
            if contract_id:
                contract_info = self.dapp.get_info(contract_id)
                record.set('contract_id', contract_id)
                record.set('contract_info', contract_info)
                logger.info("Join_contract ok - id %s", contract_id)
                return True
        else:
            name = record.get('contract')
            contract_id = self.dapp.instantiate(name)
            if contract_id:
                contract_info = self.dapp.get_info(contract_id)
                record.set('contract_id', contract_id)
                record.set('contract_info', contract_info)
                logger.info("Init_contract ok - id %s", contract_id)
                return True

        logger.info("Could not init/join contract")
        return False

    def finish_contract(self, record):
        contract_id = record.get('contract_id')
        tx_receipt = self.dapp.transact(contract_id, 'kill', {})
        logger.info("finish_contract tx_receipt %s", tx_receipt)
        self.dapp.leave(contract_id)
        self.delete_record(record)
        return True

    def leave_contract(self, record):
        contract_id = record.get('contract_id')
        self.dapp.leave(contract_id)
        self.delete_record(record)
        logger.info("leave_contract %s", contract_id)
        return True

    def config_create(self, data):
        logger.info("config_create")
        records = []
        record = self.init_record(data)
        if record:
            if self.init_contract(record):
                domains = record.get('domains')
                for domain in domains:
                    domain_id = domain.get('id')
                    if domain_id != self.id:
                        record_request = record.get_request(domain_id, 'create')
                        records.append(record_request)
        return records

    def config_delete(self, data):
        logger.info("config_delete")
        records = []
        record = self.get_record(data)
        if record:
            domains = record.get('domains')
            for domain in domains:
                domain_id = domain.get('id')
                if domain_id != self.id:
                    record_request = record.get_request(domain_id, 'delete')
                    records.append(record_request)
        return records

    def request_create(self, data):
        logger.info("request_create")
        record_reply = {}
        record = self.init_record(data)
        if record:
            contract_info = data.get('info')
            if self.init_contract(record, contract_info=contract_info):
                record.set('ack', True)
                record_reply = record.get_reply('create')
        return record_reply

    def request_delete(self, data):
        logger.info("request_delete")
        record_reply = {}
        record = self.get_record(data)
        if record:
            if self.leave_contract(record):
                record.set('ack', False)
                record_reply = record.get_reply('delete')
        return record_reply

    def reply_create(self, data, acks):
        logger.info("reply_create")
        contract_reply_ack = {}

        acks_ok = {}
        contract_acks = {}
        for ack in acks:
            domain = ack.get('domain')
            contract_acks[domain] = ack
            ack_ok = ack.get('ack')
            acks_ok[domain] = ack_ok

        contract_ack = all(acks_ok.values())

        if contract_ack:
            record = self.get_record(data)
            record.set('ack', True)
            domain_id = record.get('domain')
            acks_ok[domain_id] = True

        contract_reply_ack['status'] = contract_ack
        contract_reply_ack.update(acks_ok)

        return contract_reply_ack

    def reply_delete(self, data, acks):
        logger.info("reply_delete")
        contract_reply_ack = {}

        acks_ok = {}
        contract_acks = {}
        for ack in acks:
            domain = ack.get('domain')
            contract_acks[domain] = ack
            ack_ok = ack.get('ack')
            acks_ok[domain] = ack_ok

        contract_ack = not any(acks_ok.values())
        contract_reply_ack['status'] = contract_ack
        contract_reply_ack.update(acks_ok)

        if contract_ack:
            record = self.get_record(data)
            if record:
                self.finish_contract(record)

        logger.info('domain contracts ack %s', acks_ok)
        return contract_reply_ack

    def config(self, call, data):
        records = []
        if call == 'create':
            records = self.config_create(data)
        # elif call == 'update':
        #     services = self.config_update(data)
        elif call == 'delete':
            records = self.config_delete(data)
        return records

    def request(self, call, data):
        records_reply = {}
        if call == 'create':
            records_reply = self.request_create(data)
        # elif call == 'update':
        #     records_reply = self.request_update(data)
        elif call == 'delete':
            records_reply = self.request_delete(data)
        return records_reply

    def reply(self, call, data, acks):
        records_reply_ack = {}
        if call == 'create':
            records_reply_ack = self.reply_create(data, acks)
        # elif call == 'update':
        #     records_reply = self.request_update(data)
        elif call == 'delete':
            records_reply_ack = self.reply_delete(data, acks)
        return records_reply_ack


class Notary:
    def __init__(self, id, configs, dapp, peering):
        self.id = id
        self.configs = configs
        self.peering = peering
        self.dapp = dapp
        self.bookeeper = Bookeeper(self.id, self.dapp)

    def handle(self, msg_type, msg, acks):
        output = []
        if msg_type == 'event':
            output = self.event(msg)
        if msg_type == 'config':
            output = self.config(msg)
        if msg_type == 'request':
            output = self.request(msg)
        if msg_type == 'reply':
            if acks:
                output = self.reply(msg, acks=acks)
        return output

    def event(self, msg):
        pass

    def config(self, msg):
        outputs = []
        data = msg.get('data')
        call = msg.get('call')
        prefix = self.id

        records = self.bookeeper.config(call, data)

        for record in records:
            domain_id = record.get('domain')
            domain_call = record.get('call')
            service_data = record.get('data')

            domain_address = self.peering.get_address(domain_id)

            logger.info('contract config')
            logger.info('creating request message')
            logger.info('to_address %s, call %s, prefix %s', domain_address, call, prefix)
            logger.info('data %s', service_data)

            msg = Message(to_address=domain_address,
                          event='contract',
                          call=domain_call,
                          prefix=prefix,
                          data=service_data)
            output = (domain_id, msg)
            outputs.append(output)
        return outputs

    def request(self, msg):
        outputs = []
        data = msg.get('data')
        call = msg.get('call')
        domain_id = msg.get('prefix')
        message_id = msg.get_id()
        prefix = self.id

        service_reply = self.bookeeper.request(call, data)

        data_reply = service_reply.get('data')

        domain_address = self.peering.get_address(domain_id)
        msg = Message(id=message_id,
                      to_address=domain_address,
                      event='contract',
                      call=call,
                      prefix=prefix,
                      data=data_reply,
                      reply=True)
        output = (domain_id, msg)
        outputs.append(output)
        return outputs

    def reply(self, msg, acks):
        logger.info('reply %s', msg.items())
        logger.info('reply acks %s', acks)
        outputs = []

        data = msg.get('data')
        call = msg.get('call')

        acks_data = []
        for ack in acks:
            ack_data = ack.get('data')
            acks_data.append(ack_data)

        service_ack = self.bookeeper.reply(call, data, acks_data)

        message_id = msg.get_id()
        domain_id = msg.get('prefix')
        to_address = msg.get('params').get('call-back')
        prefix = self.id

        msg = Message(id=message_id,
                      to_address=to_address,
                      event='contract',
                      call=call,
                      prefix=prefix,
                      data=service_ack,
                      reply=True)

        output = (domain_id, msg)
        outputs.append(output)
        return outputs