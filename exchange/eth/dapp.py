import logging
import json
from os import path
import gevent
import functools
import random

from web3 import Web3, HTTPProvider, IPCProvider

from solc import compile_files

from exchange.eth.wait import Wait

logger = logging.getLogger(__name__)



class Content:
    def __init__(self):
        self._keys = []

    def get(self, param):
        if param in self._items():
            value = getattr(self, param, None)
            return value
        return None

    def set(self, param, value):
        if param in self._items():
            setattr(self, param, value)
            return True
        return False

    def _items(self, dic=False, filter_keys=False):
        if filter_keys:
            _keys = self._keys
        else:
            _keys = self.__dict__.keys()
        if dic:
            _items = dict([(i, self.__dict__[i]) for i in _keys if i[:1] != '_'])
        else:
            _items = [i for i in _keys if i[:1] != '_']
        return _items

    def default(self, o):
        return o.__dict__

    def to_json(self, _items=None, filter_keys=False):
        if _items and type(_items) == dict:
            pass
        else:
            _items = self.items(dic=True, filter_keys=filter_keys)
        return json.dumps(_items, default=self.default,
                          sort_keys=True, indent=4)

    def items(self, dic=True, filter_keys=False):
        return self._items(dic=dic, filter_keys=filter_keys)

    @classmethod
    def from_json(cls, msg):
        obj = cls()
        json_ = json.loads(msg)
        for (k, v) in json_.items():
            if k in obj._items():
                obj.set(k, v)
        return obj

    @classmethod
    def _parse(cls, msg, _map=None):
        obj = cls.from_json(msg)
        return obj

    def __iter__(self):
        for key,value in self.items(dic=True):
            yield (key, value)


class Contract(Content):
    dir_path = './contracts/'

    def __init__(self, id, name, compile=False):
        Content.__init__(self)
        self.id = id
        self.name = name
        self.path = None
        self.abi = None
        self.address = None
        self.active = False
        self.instance = None
        self.bytecode = None
        if compile:
            self.compile()

    def get_info(self):
        info = {
            'contract_name': self.name,
            'contract_abi': self.abi,
            'contract_address': self.address,
        }
        return info

    def filepath(self):
        filename = self.name + '.sol'
        filepath = path.normpath(path.join(
            path.dirname(__file__),
            self.dir_path, filename))
        self.path = filepath

    def compile(self):
        self.filepath()
        compiled_sol = compile_files([self.path])
        # logger.info('compiled_sol %s', compiled_sol)
        contract_interface = compiled_sol[self.path + ':' + self.name]
        self.abi = contract_interface['abi']
        self.bytecode = contract_interface['bin']
        logger.info("contract compiled %s", self.name)

    def transact(self, contract_instance, method, transaction, kwargs):
        logger.info("contract %s: transact %s with kwargs %s with transaction %s",
                    self.name, method, kwargs, transaction)
        logger.info("contract type %s instance %s",
                    type(contract_instance), contract_instance)
        logger.info("%s", dir(contract_instance))

        func_call = getattr(contract_instance.functions, method)
        return_transact = func_call(**kwargs).transact(transaction)
        return return_transact

    def call(self, method, kwargs):
        func_call = getattr(self.instance.functions, method)
        if func_call:
            return_call = func_call(**kwargs)
            logger.info("contract %s: calling %s - returns %s", self.name, method, return_call)
            return return_call


class Chain:
    def __init__(self):
        self.web3 = None
        self.provider = None

    def config_account(self, default_account):
        self.default_account = default_account

    def config_provider(self, provider_type, provider_address):
        if provider_type == 'ipc':
            self.provider = IPCProvider(provider_address)
        elif provider_type == 'rpc':
            self.provider = HTTPProvider(provider_address)
        else:
            logger.info("unknown provider type")

    def config(self, provider_type, provider_address):
        self.config_provider(provider_type, provider_address)
        if self.provider:
            self.web3 = Web3(self.provider)
        return self.web3


class Contracts:
    def __init__(self):
        self._ids = 100
        self.contracts = {}
        self.w3 = None
        self.wait = None
        self.default_account = None
        self.default_gas = 410000
        self.default_transaction = {'from': self.default_account, 'gas': self.default_gas}

    def set_default_gas(self, account):
        self.default_gas = account
        self.default_transaction = {'from': self.default_account, 'gas': self.default_gas}

    def set_default_account(self, account):
        self.default_account = account
        self.w3.personal.unlockAccount(self.default_account, '123', 300)
        self.default_transaction = {'from': self.default_account}

    def get_default_account(self):
        return self.default_account

    def set_w3(self, w3):
        self.w3 = w3
        self.wait = Wait(self.w3)
        self.set_default_account(self.w3.eth.accounts[0])

    def create(self, contract_name):
        contract = Contract(self._ids, contract_name, compile=True)
        self._ids += 1
        contract_instance = self.w3.eth.contract(abi=contract.get('abi'),
                                                 bytecode=contract.get('bytecode'))
        tx_hash = contract_instance.deploy(self.default_transaction)
        contract_address = self.wait.for_contract_address(tx_hash)
        logger.info("contract deployed addr %s", contract_address)
        contract.set('address', contract_address)
        logger.info("Created contract - address %s", contract_address)
        self.set_contract_instance(contract)
        return contract.get('id')

    def build(self, contract_name, contract_abi, contract_address):
        contract = Contract(self._ids, contract_name)
        self._ids += 1
        contract_instance = self.w3.eth.contract(address=contract_address,
                                                 abi=contract_abi)
        logger.info("Built contract - address %s", contract_address)
        contract.set('address', contract_address)
        contract.set('abi', contract_abi)
        contract.set('instance', contract_instance)
        contract.set('active', True)
        self.contracts[contract.get('id')] = contract
        return contract.get('id')

    def destroy(self, contract_id):
        if contract_id in self.contracts:
            del self.contracts[contract_id]
            return True
        return False

    def set_contract_instance(self, contract):
        contract_instance = self.w3.eth.contract(address=contract.get('address'),
                                                 abi=contract.get('abi'))
        if contract_instance:
            logger.info("contract instance created")
            contract.set('instance', contract_instance)
            contract.set('active', True)
            self.contracts[contract.get('id')] = contract

    def get(self, contract_id):
        contract = self.contracts.get(contract_id, None)
        return contract

    def get_balance(self):
        return self.w3.fromWei(self.w3.eth.getBalance(self.default_account), 'ether')

    def call(self, contract_id, func, kwargs):
        contract = self.contracts.get(contract_id)
        if contract:
            return_call = contract.call(func, kwargs)
            return return_call
        return None

    def transact(self, contract_id, func, kwargs):
        contract = self.contracts.get(contract_id)
        transaction = {'from': self.default_account}
        if contract:
            contract_instance = self.get_instance(contract)
            tx_hash = contract.transact(contract_instance, func, transaction, kwargs)
            # logger.info('contract transact hash %s', tx_hash)
            tx_receipt = self.wait.for_receipt(tx_hash)
            logger.info('contract transact receipt %s', tx_receipt)
            return tx_receipt
        return None

    def get_instance(self, contract):
        contract_instance = self.w3.eth.contract(address=contract.get("address"),
                                                 abi=contract.get("abi"))
        return contract_instance


class Events:
    def __init__(self):
        self.filters = {}

    def add_filter(self, contract_id, event_name, event_filter, eventlet):
        if contract_id not in self.filters:
            self.filters[contract_id] = {}
            self.filters[contract_id]['events'] = {}
        self.filters[contract_id]['events'][event_name] = (event_filter, eventlet)

    def get_filter(self, contract_id, event_name):
        if contract_id in self.filters:
            if event_name in self.filters[contract_id]['events']:
                (event_filter, eventlet) = self.filters[contract_id]['events'][event_name]
                return (event_filter, eventlet)
        return (None, None)

    def del_filter(self, contract_id, event_name):
        if contract_id in self.filters:
            if event_name in self.filters[contract_id]['events']:
                del self.filters[contract_id]['events'][event_name]

    def poll_until(self, poll_fn, success_fn, timeout, poll_interval_fn):
        with gevent.Timeout(timeout, False):
            while True:
                value = poll_fn()
                if value:
                    success_fn(value)
                gevent.sleep(poll_interval_fn())

    def watching_spawn(self, contract_filter, callback, poll_interval, timeout):
        return gevent.spawn(self.poll_until,
            poll_fn=functools.partial(contract_filter.get_new_entries),
            success_fn=callback,
            timeout=timeout,
            poll_interval_fn=lambda: poll_interval if poll_interval is not None else random.random()
        )

    def start_watch(self, contract, eventName, callback, poll_interval=10, timeout=300):
        instance = contract.get("instance")
        contract_filter = instance.eventFilter(eventName)
        logger.info("filter get_all_entries %s", contract_filter.get_all_entries())
        contract_id = contract.get("id")
        eventlet = self.watching_spawn(contract_filter, callback, poll_interval, timeout)
        eventlet.start()
        self.add_filter(contract_id, eventName, contract_filter, eventlet)
        logger.info("Start Watching contract %s - events %s - %s",
                    contract_id, eventName, eventlet.started)
        return eventlet.started

    def watch(self, contract, eventName):
        events = []
        contract_id = contract.get("id")
        (contract_filter, eventlet) = self.get_filter(contract_id, eventName)
        if contract_filter:
            events = contract_filter.get_new_entries()
            logger.info("filter %s get_new_entries %s", eventName, events)
        return events

    def stop_watch(self, contract, eventName):
        contract_id = contract.get("id")
        (contract_filter, eventlet) = self.get_filter(contract_id, eventName)
        if contract_filter:
            if eventlet.started:
                eventlet.kill()
                self.del_filter(contract_id, eventName)
                logger.info("Stop watching contract %s - events %s - %s",
                            contract_id, eventName, eventlet.dead)
                return True
        return False


class Peer(Content):
    def __init__(self, name, url):
        Content.__init__(self)
        self.name = name
        self.url = url
        self.active = False


class Peers:
    def __init__(self):
        self.peers = {}
        self.w3 = None

    def set_w3(self, w3):
        self.w3 = w3

    def get_node_info(self):
        return self.w3.admin.nodeInfo

    def add(self, name, url):
        peer = Peer(name, url)
        if self.w3.admin.addPeer(url):
            peer.set('active', True)
            self.peers[name] = peer
            logger.info("eth peer added - name %s", name)
        else:
            logger.info("eth could not add peer - name %s", name)

    def check(self, name):
        if name in self.peers:
            return True
        return False


class DApp:
    def __init__(self):
        self.id = None
        self.chain = Chain()
        self.contracts = Contracts()
        self.events = Events()
        self.peers = Peers()
        self.node_info = {}

    def get_id(self):
        return self.id

    def get_enode(self):
        enode = self.node_info.get('enode', None)
        return enode

    def config_chain(self, provider_type, provider_address):
        chain_web3 = self.chain.config(provider_type, provider_address)
        if chain_web3:
            self.config_contracts(chain_web3)
            self.config_peers(chain_web3)
        else:
            logger.info("could not instantiate web3 chain")

    def config_peers(self, chain_web3):
        self.peers.set_w3(chain_web3)
        self.node_info = self.peers.get_node_info()

    def config_contracts(self, chain_web3):
        self.contracts.set_w3(chain_web3)
        self.id = self.contracts.get_default_account()

    def peer(self, name, url):
        self.peers.add(name, url)

    def instantiate(self, contract_name):
        contract_id = self.contracts.create(contract_name)
        return contract_id

    def join(self, contract_name, contract_abi, contract_address):
        contract_id = self.contracts.build(contract_name, contract_abi, contract_address)
        return contract_id

    def leave(self, contract_id):
        ack = self.contracts.destroy(contract_id)
        return ack

    def call(self, contract_id, func, kwargs):
        return_call = self.contracts.call(contract_id, func, kwargs)
        return return_call

    def transact(self, contract_id, func, kwargs):
        return_call = self.contracts.transact(contract_id, func, kwargs)
        return return_call

    def get_info(self, contract_id):
        info = {}
        contract = self.contracts.get(contract_id)
        if contract:
            info = contract.get_info()
        return info

    def watch(self, contract_id, event_name, callback=None, end=False):
        contract = self.contracts.get(contract_id)
        if contract:
            if end:
                ack = self.events.stop_watch(contract, event_name)
                return ack
            else:
                if callback:
                    ack = self.events.start_watch(contract, event_name, callback)
                    return ack
                else:
                    logger.info("watch callback not provided for event %s", event_name)
        return False

    def watch_events(self, contract_id, event_name):
        contract = self.contracts.get(contract_id)
        if contract:
            events = self.events.watch(contract, event_name)
            return events
        return None

    def get_contract(self, contract_id):
        contract = self.contracts.get(contract_id)
        if contract:
            return contract
        return None


class ExchangeDapp(DApp):
    def __init__(self, configs, events_queue):
        DApp.__init__(self)
        self.method = configs.get('method')
        self.address = configs.get('address')
        self.events_queue = events_queue
        self.config_chain(self.method, self.address)

    def callback(self, transaction):
        event_type = 'contract'
        event_msg = {
            'data': {
                'type': 'event',
                'log': transaction,
            }
        }
        event = (event_type, event_msg)
        self.events_queue.put(event)

    def watch_contract(self, contract_id, event_name, end=False):
        ack = self.watch(contract_id, event_name, callback=self.callback, end=end)
        return ack



if __name__ == '__main__':
    import time

    debug = False
    level = logging.DEBUG if debug else logging.INFO
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    handler.setLevel(level)
    logging.getLogger().addHandler(handler)
    logging.getLogger().setLevel(level)
    logger = logging.getLogger(__name__)

    dapp1 = DApp()
    dapp1.config_chain('rpc', 'http://127.0.0.1:8101')

    dapp2 = DApp()
    dapp2.config_chain('rpc', 'http://127.0.0.1:8102')

    enode2 = dapp2.get_enode()
    dapp1.peer('2', enode2)

    cid_app1 = dapp1.instantiate('Greeter')
    print(dapp1.call(cid_app1, 'greet', [], {}))

    contract_info = dapp1.get_info(cid_app1)
    cid_app2 = dapp2.join(**contract_info)

    print(dapp2.call(cid_app2, 'greet', [], {}))
    print(dapp2.transact(cid_app2, 'setGreeting', 'HoHOHO', {}))

    def transaction_callback(transaction_hash):
        logger.info("New transaction_hash from Evt: {0}".format(transaction_hash))

    print(dapp2.watch(cid_app2, 'AckGreet', transaction_callback))

    print(dapp1.call(cid_app1, 'greet', [], {}))
    print(dapp1.transact(cid_app1, 'setGreeting', 'HaHAHA', {}))
    time.sleep(5)

    print(dapp2.watch(cid_app2, 'AckGreet', end=True))
    time.sleep(2)
