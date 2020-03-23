import logging
import os
import json
import subprocess

from yaml import load, dump
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

logger = logging.getLogger(__name__)
filename = '/tmp/states'


from exchange.common.content import Content


class Deployment(Content):
    def __init__(self, **kwargs):
        Content.__init__(self)
        self._kwargs = kwargs
        self.id = None
        self.service_id = None
        self.blueprint = None
        self.state = None
        self.active = False
        self.inputs = None
        self._outputs = None
        self._path = None
        self._folder = 'blueprints'

    def params(self):
        # _params = {'deployment-id':self.id, 'state':self.state}
        _params = {'deployment-id': self.id}
        return _params

    def init(self):
        _items = ['id', 'service_id', 'blueprint', 'inputs', 'state']
        if all([True if _item in self._kwargs else False for _item in _items]):
            for _item, _value in self._kwargs.items():
                self.set(_item, _value)
            self.update_path()
            # logger.debug(self.to_json())
            return True
        return False

    def update_path(self):
        current_path = os.path.realpath(__file__)
        dirs = current_path.split('/')[:-1]
        current_path = '/'.join(dirs)
        self._path = os.path.join(current_path, self._folder)
        self.blueprint = self._path + self.blueprint

    def instantiate(self):
        ack = False
        out_msg = ''
        try:
            command = 'aria init -b ' + \
                      self.id + ' -p ' + self.blueprint
            if self.inputs:
                command = command + ' -i ' + '\'' + self.inputs + '\''

            logger.info('deployment init command %s', command)
            output = subprocess.check_output(command, stderr=subprocess.STDOUT, shell=True)
            # logger.info('deployment init output %s', output)

            if output:
                out_msg = output.decode('UTF-8')
            else:
                out_msg = 'FAIL'

            if 'Initiated' in out_msg:
                ack = True
                message =  "success: deployment {0} was initiated"
            else:
                message = "error: deployment {0} can not be initiated"
            logger.info(message.format(self.id))
        except subprocess.CalledProcessError as e:
            logger.debug(e)
            message = "error: server internal error for deployment {0}"
            logger.debug(message.format(self.id))
        finally:
            logger.info('deployment init output %s', out_msg)
            self.active = ack
            return ack

    def execute_workflow(self, workflow):
        command = 'aria execute -b ' + self.id + ' -w ' + workflow + \
                  ' --task-retries 0 --task-retry-interval 0'
        ack = False
        message = 'execute_workflow {0}'
        try:
            subprocess.check_output(command, stderr=subprocess.STDOUT, shell=True)
            message = "success: workflow {0} applied to deployment {1}"
            ack = True
        except subprocess.CalledProcessError as ex:
            logger.debug(ex)
            message = "error: in workflow {0} server internal error for deployment {1}"
        finally:
            logger.info(message.format(workflow, self.id))
            self.state = workflow
            return ack

    def outputs(self):
        command = 'aria outputs -b ' + self.id
        outputs = None
        message = 'outputs {0}'
        try:
            outputs = subprocess.check_output(command, stderr=subprocess.STDOUT, shell=True)
            message = "outputs: success of deployment {0} retrieve"
        except subprocess.CalledProcessError as ex:
            message = "outputs: error of outputs deployment {0} retrieve"
            outputs = None
        finally:
            logger.info(message.format(self.id))
            if outputs:
                try:
                    outputs = json.loads(outputs)
                except:
                    logger.debug("could not parse outputs from json")
                    outputs = None
            self._outputs = outputs
            return outputs

    def teardown(self):
        logger.info('deployment teardown - id %s', self.id)
        self.active = False
        return True

    def update_data(self, kwargs):
        for _item, _value in kwargs.items():
            if self.get(_item):
                self.set(_item, _value)
        self.update_path()


class Deployments:
    def __init__(self):
        self._ids = 10
        self._deployments = {}
        self._service_deployments = {}
        self._deployments_states = {}
        self._checked_deployments = []
        self._deployment_maps = {}

    def create_deployment(self, **deployment_data):
        _deployment_id = self._ids
        deployment_data['id'] = str(_deployment_id)
        self._ids += 1
        logger.info('create_deployment %s', deployment_data)
        _deployment = Deployment(**deployment_data)
        if _deployment.init():
            self._deployments[_deployment_id] = _deployment
            return _deployment_id
        else:
            logger.info('deployment NOT init - id %s', _deployment_id)
            return None

    def instantiate_deployment(self, deployment_id):
        if deployment_id in self._deployments:
            deployment = self._deployments[deployment_id]
            ack = deployment.instantiate()
            return ack
        return False

    def update_deployment(self, workflow, deployment_id):
        if deployment_id in self._deployments:
            deployment = self._deployments[deployment_id]
            if deployment.execute_workflow(workflow):
               output = deployment.outputs()
               return output
        return None

    def delete_deployment(self, deployment_id):
        if deployment_id in self._deployments:
            deployment = self._deployments[deployment_id]
            deployment.teardown()
            del self._deployments[deployment_id]
            return True
        return False

    def handle_service(self, context_id, params, service):
        logger.info('handle_service')
        outputs = {}
        workflow = params.get('workflow', None)
        service_id = service.get('instance')

        if workflow == 'install':
            outputs = self.instantiate_service(context_id, params, service)
        elif workflow == 'update':
            if service_id in self._service_deployments:
                outputs = self.upgrade_service(context_id, params, service)
        elif workflow == 'uninstall':
            if service_id in self._service_deployments:
                outputs = self.destroy_service(context_id, params, service)
        else:
            logger.info('No workflow defined for service_id %', service_id)

        out = {'status': outputs}
        return out

    def instantiate_service(self, context_id, params, service):
        logger.info('instantiate_service')

        service_id = service.get('instance')
        inputs = params.get('inputs',{})
        service.set_inputs(inputs)
        deployment_data = service.get_deployment_data()
        logger.debug('logging service state of context %s %s', context_id, service.get_status())

        deployment_id = self.create_deployment(**deployment_data)
        instantiated = self.instantiate_deployment(deployment_id)

        if deployment_id and instantiated:
            service.set('deployment', deployment_id)
            workflow = params.get('workflow', None)
            outputs = self.exec_deployment(service, workflow, deployment_id)
            self._service_deployments[service_id] = deployment_id
            output = self.check_deployment_outputs(outputs)
        else:
            logger.info('error: instantiate_service')
            self.delete_deployment(deployment_id)
            output = 'FAIL'
        return output

    def check_deployment_outputs(self, outputs):
        ack = outputs.get('ack', False)
        out = 'OK' if ack else 'FAIL'
        return out

    def upgrade_service(self, context_id, params, service):
        logger.info('upgrade_service')

        service_id = service.get('instance')
        updated_data = service.get_deployment_data()
        inputs = params.get('inputs', {})
        # workflow = params.get('workflow', None)
        workflow = 'install'

        inputs.update(updated_data.items())
        service.set_inputs(inputs)

        if service_id in self._service_deployments:
            outputs = {}
            deployment_id = self._service_deployments[service_id]
            if deployment_id in self._deployments:
                deployment = self._deployments[deployment_id]
                deployment.update_data(updated_data)
                if self.instantiate_deployment(deployment_id):
                    outputs = self.exec_deployment(service, workflow, deployment_id)
            output = self.check_deployment_outputs(outputs)
        else:
            logger.info('error: upgrade_service')
            output = 'FAIL'
        return output

    def destroy_service(self, context_id, params, service):
        logger.info('destroy_service')

        service_id = service.get('instance')
        deployment_id = self._service_deployments[service_id]
        updated_data = service.get_deployment_data()
        inputs = params.get('inputs', {})
        workflow = params.get('workflow', None)

        inputs.update(updated_data.items())
        service.set_inputs(inputs)

        outputs = {}
        if deployment_id in self._deployments:
            deployment = self._deployments[deployment_id]
            deployment.update_data(updated_data)
            if self.instantiate_deployment(deployment_id):
                outputs = self.exec_deployment(service, workflow, deployment_id)

        if self.delete_deployment(deployment_id=deployment_id):
            output = self.check_deployment_outputs(outputs)
            logger.info('success: service-id %s of context-id %s teardown', service_id, context_id)
        else:
            logger.info('error: service NOT teardown')
            output = 'FAIL'
        return output

    def deployment_params(self, deployment_id):
        params = {}
        if deployment_id in self._deployments:
            deployment = self._deployments[deployment_id]
            params = deployment.params()
        return params

    def exec_deployment(self, service, workflow, deployment_id):
        logger.debug('exec_deployment')
        outputs = {}
        if workflow in service.get('workflows'):
            outs = self.update_deployment(workflow, deployment_id)
            if outs:
                service.filter_outputs(outs)
                outputs = outs
                # _params = self.deployment_params(deployment_id)
                # for item,value in outs.items():
                #     _msg = {'data': value, 'params': _params}
                #     outputs.append(_msg)
        else:
            service_id = service.get('instance')
            logger.debug("error: workflow %s not present in service-id %s - deployment_id %s", workflow, service_id, deployment_id)
        return outputs


class Blueprint(Content):
    def __init__(self, **kwargs):
        Content.__init__(self)
        self._kwargs = kwargs
        self.id = None
        self.deployment = None
        self.instance = None
        self.name = None
        self.url = None
        self.description = None
        self.inputs = None
        self.workflows = []
        self._status = {
            'current': None,
            'last': None,
            'reply': None,
            'action': None,
        }
        self.current_state = {}
        self.current_state_inputs = ''
        self.states = {}
        self._persistent_outputs = {}
        self.inputs_filename = 'inputs.yaml'
        self._keys = ['id', 'name', 'inputs', 'description', 'workflows']

    def set_domain_prefix(self, prefix):
        self.inputs_filename =  prefix + 'inputs.yaml'

    def set_url(self, url):
        self.url = url

    def status(self, item):
        if item in self._status:
            return self._status[item]
        return None

    def set_status(self, item, value):
        if item in self._status:
            self._status[item] = value

    def get_status(self):
        return self._status

    def set_inputs(self, inputs):
        logger.info('set_inputs %s', inputs)
        self.current_state_inputs = None
        if type(inputs) is dict:
            _state_inputs = self.current_state.get('inputs')
            _filtered_inputs = {}
            for input_key in _state_inputs:
                if input_key in inputs:
                    _filtered_inputs[input_key] = inputs[input_key]
                if input_key in self._persistent_outputs:
                    _filtered_inputs[input_key] = self._persistent_outputs[input_key]

            if _filtered_inputs:
                self.inputs = _filtered_inputs
                current_path = os.path.realpath(__file__)
                dirs = current_path.split('/')[:-1]
                current_path = '/'.join(dirs)
                _path = os.path.join(current_path, 'inputs/')
                filename = _path + self.inputs_filename
                logger.info('set_inputs %s %s', filename, _filtered_inputs)
                with open(filename, 'w') as outfile:
                    dump(_filtered_inputs, outfile, Dumper=Dumper)
                # _inputs_list = map(lambda (k,v): str(k)+'='+str(v), _filtered_inputs.items())
                # _inputs_str = ';'.join(_inputs_list)
                # self.current_state_inputs = _inputs_str
                self.current_state_inputs = filename

    def get_current_state(self):
        return self.current_state

    def change_state(self, state, trigger):
        _id = state.get('id', None)
        _state = filter(lambda st: st['id']==_id, self.states.values())
        if len(_state) == 1:
            # _state = _state.pop()
            # if state == _state:
            self._status['action'] = trigger
            self._status['last'] = self.current_state.get('id')
            self.current_state = state
            self._status['current'] = self.current_state.get('id')
            return True
        return False

    def get_deployment_data(self):
        state = self.current_state
        inputs = self.current_state_inputs
        info = {'service_id': self.id,
                'blueprint': state['blueprint'],
                'inputs': inputs,
                'state': state['id']}
        return info

    def init(self):
        _items = ['id', 'name','description','workflows', 'states']
        if all([True if _item in self._kwargs else False for _item in _items]):
            for _item, _value in self._kwargs.items():
                setattr(self, _item, _value)
            self.init_state()
            return True
        return False

    def init_state(self):
        logger.debug('init_state')
        logger.debug(self.states)
        for _id,_value in self.states.items():
            if 'default' in _value:
                self.current_state = _value
                self.current_state['status'] = False
                self._status['current'] = self.current_state.get('id')

    def can_transit(self, input):
        transitions = self.current_state.get('transitions', None)
        if transitions and type(transitions) is list:
            chance = filter(lambda x: input == x['input'], transitions)
            if chance:
                return True
        return False

    def get_trigger(self, input):
        transitions = self.current_state.get('transitions', None)
        if transitions and type(transitions) is list:
            chance = filter(lambda x: input in x['input'], transitions)
            if chance:
                first_chance = chance.pop()
                trigger = first_chance.get('trigger', None)
                self._status['action'] = trigger
                return trigger
        return None

    def next_state(self, input):
        transitions = self.current_state.get('transitions', None)
        if transitions:
            change = filter(lambda x: input == x['input'], transitions)
            if change:
                change = change.pop()
                next_id = change['target']
                self._status['action'] = change.get('trigger', '')
                if next_id in self.states:
                    self._status['last'] = self.current_state.get('id')
                    next_state = self.states[next_id]
                    self.current_state = {}
                    self.current_state.update(next_state.items())
                    self._status['current'] = self.current_state.get('id')
                    return True
        return False

    def filter_outputs(self, outputs):
        outs = self.current_state.get('outputs',[])
        keys = filter(lambda x: x not in outs, outputs.keys())
        for out_key in keys:
            del outputs[out_key]
        for out in outputs.keys():
            if out in outs:
                out_props = outs[out]
                logger.info('filtering outputs persist %s %s', out, out_props.get('persist'))
                if out_props.get('persist'):
                    if out not in self._persistent_outputs:
                        self._persistent_outputs[out] = outputs[out]
                    else:
                        current_persist = self._persistent_outputs[out]
                        self._persistent_outputs[out] = current_persist + outputs[out]
                    del outputs[out]
                else:
                    pass

    def update_current_state_status(self, status):
        actual_status = self.current_state.get('status', None)
        if actual_status != status:
            self.current_state['status'] = status

    def current_state_status(self):
        actual_status = self.current_state.get('status', None)
        return actual_status


class Catalog:
    def __init__(self):
        self._ids = 9000
        self._services_path = 'sdn/'
        self._services = {}
        self._customers_services = {}
        self._service_deployments = {}
        self._customers = {}
        self._folder = 'etc/'
        self.register_services()

    def get_service_by(self, id_or_name, item):
        for _id, _service in self._services.items():
            if _service.get(item) == id_or_name:
                return _id
        return None

    def get_context_service_by(self, context_id, id_or_name, item):
        for _id, _service in self._customers_services[context_id].items():
            if _service.get(item) == id_or_name:
                return _id
        return None

    def has(self, service_id):
        if service_id in self._services:
            return True
        return False

    def get_service_deployment(self, context_id, service_id):
        if context_id in self._service_deployments:
            if service_id in self._service_deployments[context_id]:
                deployment_id = self._service_deployments[context_id][service_id]
                return deployment_id
        return None

    def unsubscribe_service(self, context_id, service_id):
        if context_id in self._customers:
            if service_id in self._customers[context_id]:
                self._customers[context_id].remove(service_id)
                del self._customers_services[context_id][service_id]
                return True
        return False

    def subscribe_service(self, context_id, service_id, deployment_id=None):
        logger.debug('subscribe_service')
        if context_id not in self._customers:
            self._customers[context_id] = []
            self._customers_services[context_id] = {}
            self._service_deployments[context_id] = {}
        if service_id not in self._customers[context_id]:
            self._customers[context_id].append(service_id)
            _service = self._services[service_id]
            _service_data = _service.items()
            if not deployment_id:
                _customer_service_id = str(self._ids)
            else:
                _customer_service_id = str(deployment_id)
            self._service_deployments[context_id][service_id] = _customer_service_id
            _customer_service = Blueprint(**_service_data)
            _customer_service.init()
            _customer_service.set('instance', _customer_service_id)
            self._customers_services[context_id][_customer_service_id] = _customer_service
            self._ids += 1
            logger.info("success: service-id %s enrolled by context-id %s - deployment-id %s", service_id, context_id, _customer_service_id)
            return _customer_service_id
        else:
            logger.info("error: service-id %s already enrolled by context-id %s", service_id, context_id)
            return None

    def get_service(self, context_id, service_id):
        logger.info('get_service service_id %s', service_id)
        service_id = str(service_id)
        if context_id in self._customers_services:
            if service_id in self._customers_services[context_id]:
                customer_service = self._customers_services[context_id][service_id]
                return customer_service
        return None

    def get_services(self):
        _services = []
        for _id, _service in self._services.items():
            _data = _service.items(filter_keys=True)
            _services.append(_data)
        return _services

    def load_service(self, service_data):
        if 'id' in service_data:
            _id = service_data['id']
            _service = Blueprint(**service_data)
            if _service.init():
                self._services[_id] = _service
                logger.info('service registered - id %s', _id)
            else:
                logger.info('service NOT registered - id %s', _id)

    def update_path(self):
        current_path = os.path.realpath(__file__)
        dirs = current_path.split('/')[:-1]
        current_path = '/'.join(dirs)
        _path = os.path.join(current_path, self._folder)
        self._services_path = _path
        print(self._services_path)

    def register_services(self):
        self.update_path()
        logger.debug('register_services path %s', self._services_path)
        _files = self.load_files(self._services_path, 'service_', full_path=True)
        logger.debug('_files path %s', _files)
        for file in _files:
            data_loaded = self.parse_file(file)
            self.load_service(data_loaded)

    def load_files(self, folder, file_begin_with, full_path=False):
        _files = []
        # current_path = os.getcwd()
        # real_path = os.path.join(current_path, folder)
        for root, dirs, files in os.walk(folder):
            for file in files:
                if file.startswith(file_begin_with):
                    p = os.path.join(root, file)
                    if full_path:
                        file_path = os.path.abspath(p)
                        _files.append(file_path)
                    else:
                        _files.append(file)
        return _files

    def parse_file(self, filename):
        data = {}
        with open(filename, 'r') as f:
            data = load(f, Loader=Loader)
        return data

    def get_services_description(self, context_id):
        descriptions = []
        if context_id in self._customers_services:
            for context_service_id,service in self._customers_services[context_id].items():
                service_desc = service.get('description')
                descriptions.append(service_desc)
        return descriptions

    def subscribe_context(self, context_id):
        sub_ids = []
        for _id, _service in self._services.items():
            sub_id = self.subscribe_service(context_id, _id)
            sub_ids.append(sub_id)
        return sub_ids


if __name__ == "__main__":

    ctlog = Catalog()
    # print ctlog.get_services()
    # print ctlog.subscribe_service('1', '1')
    # service = ctlog.get_service('1', '9000')
    #
    # print service.get_current_state()
    # print service.can_transit('ok')
    # print service.next_state('ok')
    # inputs = {'switch_id': '0000000000000001', 'switch_url':'http://127.0.0.1:8080'}
    # service.set_inputs(inputs)
    # print service.get_deployment_data()

    # dpl = {'id':'1', 'service_id':'1', 'blueprint':'/robotics/s0.yaml', 'state':'s0', 'inputs':""}
    # deploy = Deployment(**dpl)
    # print deploy.init()
    # print deploy.instantiate()
    # if deploy.execute_workflow('create'):
    #     outputs = deploy.outputs()
    #     if outputs:
    #         print outputs['out_01']