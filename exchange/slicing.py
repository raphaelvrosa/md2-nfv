import logging
logger = logging.getLogger(__name__)


from exchange.common.mailing import Message
from exchange.common.content import Content

from exchange.tosca.engine import Catalog, Deployments



class Service(Content):
    def __init__(self, id=None, domain=None,
                 tenant=None, params=None):
        Content.__init__(self)
        self.id = id
        self.domain = domain
        self.tenant = tenant
        self.params = params
        self.deployment = None
        self.active = False
        self.update = False

    def get_request(self, call):
        request = {
            'call': call,
            'domain': self.domain,
            'data': {
                'type': 'request',
                'domain': self.domain,
                'service': self.id,
                'tenant': self.tenant,
                'deployment': self.deployment,
                'params': self.params,
            }
        }
        return request

    def get_reply(self, call):
        reply = {
            'call': call,
            'data': {
                'type': 'reply',
                'domain': self.domain,
                'service': self.id,
                'deployment': self.deployment,
                'ack': self.active,
                'update': self.update,
            }
        }
        return reply

    def update_params(self, params):
        self.params.update(params)


class Services:
    def __init__(self, id, configs):
        self.id = id
        self.mdo_service_ids = 700
        self.services = {}
        self.mdo_services = {}
        self.mdo_service_map = {}
        self.params = {}
        self.input_params(configs)
        self.catalog = Catalog()
        self.deployments = Deployments()

    def config_create(self, service_data):
        logger.info("config_create")
        tenant = service_data.get('tenant')
        service_id = service_data.get('service')
        domain_services = service_data.get('domains')
        service_requests = []
        if self.catalog.has(service_id):
            # service_deployment_id = self.catalog.subscribe_service(tenant, service_id)
            mdo_service_deployment_id = self.mdo_service_ids
            self.mdo_service_ids += 1

            logger.info('creating mdo_service_deployment_id %s', mdo_service_deployment_id)
            logger.info('tenant %s, service_id %s', tenant, service_id)

            created_mdo_services = []
            for domain_service in domain_services:
                logger.info('creating service %s', domain_service)
                domain_id = domain_service.get('id')
                params = domain_service.get('params')
                mdo_service = Service(id=service_id, domain=domain_id,
                                      tenant=tenant, params=params)

                created_mdo_services.append(mdo_service)
                service_request = mdo_service.get_request('create')
                service_requests.append(service_request)

            self.mdo_services[mdo_service_deployment_id] = created_mdo_services
            self.mdo_service_map[(tenant, service_id)] = mdo_service_deployment_id
        return service_requests

    def config_update(self, service_data):
        logger.info("config_update")
        tenant = service_data.get('tenant')
        service_id = service_data.get('service')
        domain_services = service_data.get('domains')
        updated_services = []

        if self.catalog.has(service_id):
            mdo_service_deployment_id = self.mdo_service_map[(tenant, service_id)]
            services = self.mdo_services[mdo_service_deployment_id]

            logger.info('updating mdo_service_deployment_id %s', mdo_service_deployment_id)
            logger.info('tenant %s, service_id %s', tenant, service_id)

            service_updates = {}
            for domain_service in domain_services:
                domain = domain_service.get('id')
                service_updates[domain] = domain_service

            created_service_domains = []
            for service in services:
                domain = service.get('domain')
                created_service_domains.append(domain)
                if domain in service_updates:
                    # logger.info('updating domain %s', domain)
                    service_update = service_updates[domain]
                    if service_update.get('call') == 'update':
                        logger.info('updating domain %s', domain)
                        service_params = service_update.get('params')
                        logger.info('updating params %s', service_params)
                        service.update_params(service_params)
                        service_request = service.get_request('update')
                        updated_services.append(service_request)
                    if service_update.get('call') == 'delete':
                        logger.info('deleting domain %s', domain)
                        service_request = service.get_request('delete')
                        updated_services.append(service_request)

            created_domains = {}
            for domain_id in service_updates:
                if domain_id not in created_service_domains:
                    service_update = service_updates[domain_id]
                    if service_update.get('call') == 'create':
                        logger.info('creating domain %s', domain_id)
                        params = service_update.get('params')
                        new_mdo_service = Service(id=service_id, domain=domain_id,
                                                    tenant=tenant, params=params)
                        created_domains[domain_id] = new_mdo_service
                        service_request = new_mdo_service.get_request('create')
                        updated_services.append(service_request)

            for domain in created_domains.values():
                services.append(domain)
                domain_id = domain.get('domain')
                logger.info('added mdo_services domain %s', domain_id)

            self.mdo_services[mdo_service_deployment_id] = services
            logger.info('mdo_services len %s', len(self.mdo_services[mdo_service_deployment_id]))

        return updated_services

    def config_delete(self, service_data):
        logger.info("config_delete")
        tenant = service_data.get('tenant')
        service_id = service_data.get('service')
        # domain_services = service_data.get('domains')
        deleted_services = []

        if self.catalog.has(service_id):
            mdo_service_deployment_id = self.mdo_service_map[(tenant, service_id)]
            services = self.mdo_services[mdo_service_deployment_id]

            logger.info('deleting mdo_service_deployment_id %s', mdo_service_deployment_id)
            logger.info('tenant %s, service_id %s', tenant, service_id)

            for service in services:
                service_request = service.get_request('delete')
                deleted_services.append(service_request)

        return deleted_services

    def request_create(self, service_data):
        logger.info("request_create")
        service_reply = {}

        domain_id = service_data.get('domain')
        service_id = service_data.get('service')
        tenant = service_data.get('tenant')
        params = service_data.get('params')

        if self.catalog.has(service_id):

            service_deployment_id = self.catalog.subscribe_service(tenant, service_id)
            mdo_service = Service(id=service_id, domain=domain_id,
                                  tenant=tenant, params=params)

            logger.info('create service_deployment_id %s', service_deployment_id)
            logger.info('tenant %s, service_id %s', tenant, service_id)

            self.services[service_deployment_id] = mdo_service

            service_instance = self.catalog.get_service(tenant, service_deployment_id)
            service_instance.set_domain_prefix(self.id)

            inputs = params
            inputs.update(self.params)
            deployment_params = {
                'inputs': inputs,
                'workflow': 'install',
            }
            deployment_reply = self.deployments.handle_service(tenant,
                                                               deployment_params,
                                                               service_instance)
            mdo_service.set('deployment', service_deployment_id)
            deployment_status = deployment_reply.get('status')

            if deployment_status == 'OK':
                mdo_service.set('active', True)
            if deployment_status == 'FAIL':
                mdo_service.set('active', False)

            service_reply = mdo_service.get_reply('create')
        return service_reply

    def request_update(self, service_data):
        logger.info("request_update")
        service_reply = {}

        service_id = service_data.get('service')
        tenant = service_data.get('tenant')
        params = service_data.get('params')
        service_deployment_id = service_data.get('deployment')

        if self.catalog.has(service_id):
            if service_deployment_id in self.services:
                mdo_service = self.services[service_deployment_id]

                service_instance = self.catalog.get_service(tenant, service_deployment_id)
                logger.info('update service_deployment_id %s', service_deployment_id)
                logger.info('tenant %s, service_id %s', tenant, service_id)

                mdo_service.update_params(params)
                inputs = mdo_service.get('params')
                inputs.update(self.params)
                deployment_params = {
                    'inputs': inputs,
                    'workflow': 'update',
                }
                deployment_reply = self.deployments.handle_service(tenant,
                                                                   deployment_params,
                                                                   service_instance)
                deployment_status = deployment_reply.get('status')
                if deployment_status == 'OK':
                    mdo_service.set('update', True)
                if deployment_status == 'FAIL':
                    mdo_service.set('update', False)

                service_reply = mdo_service.get_reply('update')
        return service_reply

    def request_delete(self, service_data):
        logger.info("request_delete")
        service_reply = {}

        service_id = service_data.get('service')
        tenant = service_data.get('tenant')
        params = service_data.get('params')
        service_deployment_id = service_data.get('deployment')

        if self.catalog.has(service_id):
            if service_deployment_id in self.services:
                mdo_service = self.services[service_deployment_id]

                service_instance = self.catalog.get_service(tenant, service_deployment_id)
                service_instance.set_domain_prefix(self.id)

                logger.info('delete service_deployment_id %s', service_deployment_id)
                logger.info('tenant %s, service_id %s', tenant, service_id)

                mdo_service.update_params(params)
                inputs = mdo_service.get('params')
                inputs.update(self.params)
                deployment_params = {
                    'inputs': inputs,
                    'workflow': 'uninstall',
                }
                deployment_reply = self.deployments.handle_service(tenant,
                                                                   deployment_params,
                                                                   service_instance)
                deployment_status = deployment_reply.get('status')
                if deployment_status == 'OK':
                    mdo_service.set('active', False)
                    del self.services[service_deployment_id]
                    ack_unsub = self.catalog.unsubscribe_service(tenant, service_deployment_id)
                    logger.info('service_deployment_id %s from tenant %s ack_unsub: %s',
                                service_deployment_id, tenant, ack_unsub)
                if deployment_status == 'FAIL':
                    mdo_service.set('active', True)

                service_reply = mdo_service.get_reply('delete')
        return service_reply

    def reply_create(self, service_data, acks):
        logger.info("reply_create")
        msg_type = service_data.get('type')
        service_reply_ack = {}

        if msg_type == 'config':
            tenant = service_data.get('tenant')
            service_id = service_data.get('service')

            mdo_service_deployment_id = self.mdo_service_map[(tenant, service_id)]
            services = self.mdo_services[mdo_service_deployment_id]

            logger.info('reply_create mdo_service_deployment_id %s', mdo_service_deployment_id)
            logger.info('tenant %s, service_id %s', tenant, service_id)

            service_acks = {}
            for ack in acks:
                domain = ack.get('domain')
                service_acks[domain] = ack

            acks_ok = []
            info = {}
            for service in services:
                domain = service.get('domain')
                ack_info = service_acks[domain]
                ack_ok = ack_info.get('ack')
                acks_ok.append(ack_ok)
                info[domain] = ack_ok
                service.set('active', ack_ok)
                service.set('deployment', ack_info.get('deployment'))

            service_ack = all(acks_ok)
            service_reply_ack['status'] = service_ack
            service_reply_ack.update(info)
        return service_reply_ack

    def reply_update(self, service_data, acks):
        logger.info("reply_update")
        msg_type = service_data.get('type')
        tenant = service_data.get('tenant')
        service_id = service_data.get('service')
        domain_services = service_data.get('domains')
        service_reply_ack = {}

        if msg_type == 'config':
            mdo_service_deployment_id = self.mdo_service_map[(tenant, service_id)]
            services = self.mdo_services[mdo_service_deployment_id]

            logger.info('reply_update mdo_service_deployment_id %s', mdo_service_deployment_id)
            logger.info('tenant %s, service_id %s', tenant, service_id)

            service_acks = {}
            for ack in acks:
                domain = ack.get('domain')
                service_acks[domain] = ack

            service_updates = {}
            for domain_service in domain_services:
                domain = domain_service.get('id')
                service_updates[domain] = domain_service

            services_to_remove = []
            acks_ok = []
            info = {}
            for service in services:
                domain = service.get('domain')
                logger.info('checking updates on domain %s', domain)
                if domain in service_updates and domain in service_acks:
                    service_update = service_updates[domain]
                    domain_service_ack = service_acks[domain]
                    service_call = service_update.get('call')
                    logger.info('domain %s, service_call %s', domain, service_call)
                    logger.info('domain_service_ack %s', domain_service_ack)
                    if service_call == 'create':
                        ack_ok = domain_service_ack.get('ack')
                        service.set('deployment', domain_service_ack.get('deployment'))
                        acks_ok.append(ack_ok)
                        info[domain] = ack_ok
                        service.set('active', ack_ok)
                    if service_call == 'update':
                        ack_ok = domain_service_ack.get('update')
                        acks_ok.append(ack_ok)
                        info[domain] = ack_ok
                        service.set('update', ack_ok)
                    if service_call == 'delete':
                        ack_ok = domain_service_ack.get('ack')
                        if not ack_ok:
                            services_to_remove.append(domain)
                        acks_ok.append(ack_ok)
                        info[domain] = ack_ok
                        service.set('active', ack_ok)
            logger.info('acks_ok %s', acks_ok)
            logger.info('info %s', info)

            maintain_services = []
            for service_domain in services:
                domain_id = service_domain.get('domain')
                if domain_id not in services_to_remove:
                    maintain_services.append(service_domain)

            self.mdo_services[mdo_service_deployment_id] = maintain_services

            service_ack = all(acks_ok)
            service_reply_ack['status'] = service_ack
            service_reply_ack.update(info)
        return service_reply_ack

    def reply_delete(self, service_data, acks):
        logger.info("reply_delete")
        msg_type = service_data.get('type')
        service_reply_ack = {}

        if msg_type == 'config':
            tenant = service_data.get('tenant')
            service_id = service_data.get('service')

            mdo_service_deployment_id = self.mdo_service_map[(tenant, service_id)]
            services = self.mdo_services[mdo_service_deployment_id]

            logger.info('reply_delete mdo_service_deployment_id %s', mdo_service_deployment_id)
            logger.info('tenant %s, service_id %s', tenant, service_id)

            service_acks = {}
            for ack in acks:
                domain = ack.get('domain')
                service_acks[domain] = ack

            acks_ok = []
            info = {}
            for service in services:
                domain = service.get('domain')
                if domain in service_acks:
                    ack_info = service_acks[domain]
                    logger.info('domain %s, ack_info %s', domain, ack_info)
                    ack_ok = ack_info.get('active')
                    acks_ok.append(ack_ok)
                    info[domain] = ack_ok
                    service.set('active', ack_ok)

            logger.info('acks_ok %s', acks_ok)
            logger.info('info %s', info)

            service_ack = all(acks_ok)
            service_reply_ack['status'] = service_ack
            service_reply_ack.update(info)
            if service_ack:
                del self.mdo_services[mdo_service_deployment_id]
        return service_reply_ack

    def input_params(self, configs):
        sdn_configs = configs.get('sdn')
        _id = sdn_configs.get('id')
        _address = sdn_configs.get('address')
        if _id and _address:
            self.params = {
                'switch_id': _id,
                'switch_url': _address,
            }

    def config(self, call, data):
        services = []
        if call == 'create':
            services = self.config_create(data)
        elif call == 'update':
            services = self.config_update(data)
        elif call == 'delete':
            services = self.config_delete(data)
        return services

    def request(self, call, data):
        service_reply = {}
        if call == 'create':
            service_reply = self.request_create(data)
        elif call == 'update':
            service_reply = self.request_update(data)
        elif call == 'delete':
            service_reply = self.request_delete(data)
        return service_reply

    def reply(self, call, data, acks):
        service_reply_ack = {}
        if call == 'create':
            service_reply_ack = self.reply_create(data, acks)
        elif call == 'update':
            service_reply_ack = self.reply_update(data, acks)
        elif call == 'delete':
            service_reply_ack = self.reply_delete(data, acks)
        return service_reply_ack


class Slicing:
    def __init__(self, id, configs, dapp, peering):
        self.id = id
        self.configs = configs
        self.dapp = dapp
        self.peering = peering
        self.services = Services(self.id, self.configs)

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
        call = msg.get('call')
        prefix = self.id

        services = self.services.config(call, data)

        for service in services:
            domain_id = service.get('domain')
            domain_call = service.get('call')
            service_data = service.get('data')

            domain_address = self.peering.get_address(domain_id)

            logger.info('service config')
            logger.info('creating request message')
            logger.info('to_address %s, call %s, prefix %s', domain_address, call, prefix)
            logger.info('data %s', service_data)

            msg = Message(to_address=domain_address,
                          event='service',
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

        service_reply = self.services.request(call, data)

        data_reply = service_reply.get('data')

        domain_address = self.peering.get_address(domain_id)
        msg = Message(id=message_id,
                      to_address=domain_address,
                      event='service',
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

        service_ack = self.services.reply(call, data, acks_data)

        message_id = msg.get_id()
        domain_id = msg.get('prefix')
        to_address = msg.get('params').get('call-back')
        prefix = self.id

        msg = Message(id=message_id,
                      to_address=to_address,
                      event='service',
                      call=call,
                      prefix=prefix,
                      data=service_ack,
                      reply=True)

        output = (domain_id, msg)
        outputs.append(output)
        return outputs


