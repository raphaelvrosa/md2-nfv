import time

import logging
from web3 import Web3, HTTPProvider, TestRPCProvider
from web3.contract import ConciseContract

from web3.providers.eth_tester import EthereumTesterProvider
from eth_tester import EthereumTester

from solc import compile_source

from exchange.eth.wait import Wait

from exchange.eth.dapp import DApp, ExchangeDapp

contract_source = '''
pragma solidity ^0.4.18;

contract LifecycleNotary {

    enum State { Created, Updated, Inactive }

    address public customer; // service customer
    uint id; // service identifier
    State public state; // current service state

    function greet() public constant returns (address) {
        return customer;
    }

    struct Domain {
        string name;
        bool isValue;
    }

    struct Workflow {
        string name; // name of workflow
        string domain; // domain who triggered workflow
        bool ack;  // if true, workflow applied successfully
        bool updates;   // check if workflow was caused by updates in params
    }

    mapping(address => Domain) public domains;
    mapping(address => Workflow[]) public domainsWorkflows;


    modifier onlyCustomer() { if(msg.sender == customer) _; }
    modifier inState(State _state) {
        require(state == _state);
        _;
    }


    // Events
    event WorkflowCall(address from, string call, bool ack);
    // event WorkflowCall(address from, Workflow work);
    event DomainRegistry(address from, string name);


    function LifecycleNotary() public {
        customer = msg.sender;
    }

    function onlyDomain(address domain) public view returns (bool exist) {
        if (domains[domain].isValue) {
            return true;
        } else {
            return false;
        }
    }

    function registerDomain(address domain, string name) public onlyCustomer returns (bool ok) {

        Domain storage d = domains[domain];
        d.name = name;
        d.isValue = true;

        DomainRegistry(domain, name);

        return true;

    }

    function callWorkflow(string name, bool ack, bool updates) public returns (bool ok) {
        if (onlyDomain(msg.sender)) {

            var domainName = domains[msg.sender].name;
            var work = Workflow({
                name: name,
                domain: domainName,
                ack: ack,
                updates: updates });

            domainsWorkflows[msg.sender].push(work);

            WorkflowCall(msg.sender, domainName, ack);
            // WorkflowCall(msg.sender, work);
            return true;
        } else {
            return false;
        }
    }

    function kill() public onlyCustomer {
        selfdestruct(msg.sender);  // kills this contract and sends remaining funds back to customer
    }
}
'''





def simple_test():
    contract_source_code = '''
    pragma solidity ^0.4.18;

    contract C {
        event Test(uint indexed x);
        function test()  {
            Test(2);
        }
    }
    '''

    compiled_sol = compile_source(contract_source_code)  # Compiled source code
    contract_interface = compiled_sol['<stdin>:C']
    print(contract_interface['abi'])

    print("======================= ETH-TESTRPC =======================")
    web3 = Web3(TestRPCProvider())
    accounts = web3.eth.accounts
    contract = web3.eth.contract(abi=contract_interface['abi'], bytecode=contract_interface['bin'])
    tx_hash = contract.deploy(transaction={'from': accounts[0], 'gas': 410000})
    tx_receipt = web3.eth.getTransactionReceipt(tx_hash)
    contract_address = tx_receipt['contractAddress']
    contract_instance = web3.eth.contract(address=contract_address, abi=contract_interface['abi'])

    transfer_filter = contract_instance.eventFilter('Test')
    print(transfer_filter.get_all_entries())
    tx_hash = contract_instance.transact({'from': accounts[0]}).test()
    receipt = web3.eth.getTransactionReceipt(tx_hash)
    print('Tx receipt', receipt)
    print(transfer_filter.get_new_entries())


def raw_test(provider_address):
    compiled_sol = compile_source(contract_source)  # Compiled source code
    contract_interface = compiled_sol['<stdin>:LifecycleNotary']
    print(contract_interface['abi'])

    web3 = Web3(HTTPProvider(provider_address))
    wait = Wait(web3)

    accounts = web3.eth.accounts
    web3.personal.unlockAccount(accounts[0], '123', 300)
    contract = web3.eth.contract(abi=contract_interface['abi'], bytecode=contract_interface['bin'])
    tx_hash = contract.deploy(transaction={'from': accounts[0]})
    # tx_receipt = web3.eth.getTransactionReceipt(tx_hash)
    # contract_address = tx_receipt['contractAddress']
    contract_address = wait.for_contract_address(tx_hash)
    contract_instance = web3.eth.contract(address=contract_address, abi=contract_interface['abi'])

    transfer_filter = contract_instance.eventFilter('DomainRegistry')
    print(transfer_filter.get_all_entries())

    domain_addres = "0x017fe62cA912FD1dE45B09bD088AF44be0fDE99A"

    # tx_hash = contract_instance.transact({'from': accounts[0]}).registerDomain(domain_addres, "Algum")
    # # receipt = web3.eth.getTransactionReceipt(tx_hash)
    # receipt = wait.for_receipt(tx_hash)
    # print('Tx receipt', receipt)

    tx_hash = contract_instance.functions.registerDomain(domain_addres, "Algum").transact({'from': accounts[0]})
    receipt = wait.for_receipt(tx_hash)
    print('Tx receipt', receipt)

    print(transfer_filter.get_new_entries())


def simple_local_test():

    compiled_sol = compile_source(contract_source)  # Compiled source code
    contract_interface = compiled_sol['<stdin>:LifecycleNotary']
    print(contract_interface['abi'])

    print("======================= ETH-TESTRPC =======================")
    eth_tester = EthereumTester()
    web3 = Web3(EthereumTesterProvider(eth_tester))
    accounts = eth_tester.get_accounts()

    print(accounts)

    contract = web3.eth.contract(abi=contract_interface['abi'], bytecode=contract_interface['bin'])
    tx_hash = contract.deploy(transaction={'from': accounts[0]})
    tx_receipt = web3.eth.getTransactionReceipt(tx_hash)
    contract_address = tx_receipt['contractAddress']
    contract_instance = web3.eth.contract(address=contract_address, abi=contract_interface['abi'])

    transfer_filter = contract_instance.eventFilter('DomainRegistry')
    print(transfer_filter.get_all_entries())


    domain_addres = accounts[1]
    # domain_addres = Web3.toBytes(domain_addres)

    # tx_hash = contract_instance.transact({'from': accounts[0]}).registerDomain(domain=domain_addres, name="Algum")
    tx_hash = contract_instance.functions.registerDomain(domain=domain_addres, name="Algum").transact({'from': accounts[0]})

    receipt = web3.eth.getTransactionReceipt(tx_hash)
    print('Tx receipt', receipt)

    print(transfer_filter.get_new_entries())

    workflow_call = contract_instance.eventFilter('WorkflowCall')
    print(workflow_call.get_all_entries())

    # tx_hash = contract_instance.transact({'from': domain_addres}). \
    #     callWorkflow("install", True, False)

    tx_hash = contract_instance.functions.callWorkflow(name="install", ack=True, updates=False).transact({'from': accounts[1]})

    receipt = web3.eth.getTransactionReceipt(tx_hash)
    print('Tx receipt', receipt)

    print(workflow_call.get_new_entries())


def simple_remote_test(provider_address):
    compiled_sol = compile_source(contract_source)  # Compiled source code
    contract_interface = compiled_sol['<stdin>:LifecycleNotary']
    print(contract_interface['abi'])

    web3 = Web3(HTTPProvider(provider_address))
    wait = Wait(web3)

    accounts = web3.eth.accounts
    web3.personal.unlockAccount(accounts[0], '123', 300)
    contract = web3.eth.contract(abi=contract_interface['abi'], bytecode=contract_interface['bin'])
    tx_hash = contract.deploy(transaction={'from': accounts[0]})
    # tx_receipt = web3.eth.getTransactionReceipt(tx_hash)
    # contract_address = tx_receipt['contractAddress']
    contract_address = wait.for_contract_address(tx_hash)
    contract_instance = web3.eth.contract(address=contract_address, abi=contract_interface['abi'])

    transfer_filter = contract_instance.eventFilter('DomainRegistry')
    print(transfer_filter.get_all_entries())

    domain_addres = "0x017fe62cA912FD1dE45B09bD088AF44be0fDE99A"

    # tx_hash = contract_instance.transact({'from': accounts[0]}).registerDomain(domain_addres, "Algum")

    method = 'registerDomain'
    func_call = getattr(contract_instance.functions, method)
    tx_hash = func_call(**{'domain':domain_addres, 'name':"Algum"}).transact({'from': accounts[0]})
    # receipt = web3.eth.getTransactionReceipt(tx_hash)
    receipt = wait.for_receipt(tx_hash)
    print('Tx receipt', receipt)

    print(transfer_filter.get_new_entries())


def complex_test():
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
    enode2_key = dapp2.get_id()
    dapp1.peer('2', enode2)

    cid_app1 = dapp1.instantiate('LifecycleNotary')

    contract_info = dapp1.get_info(cid_app1)
    cid_app2 = dapp2.join(**contract_info)

    def transaction_callback(transaction_hash):
        print("New transaction_hash from Evt: {0}".format(transaction_hash))

    registerDomain_kwargs = {'domain':enode2_key, 'name':"Algum"}
    print(dapp2.watch(cid_app2, 'DomainRegistry', transaction_callback))

    print(dapp1.transact(cid_app1, 'registerDomain', registerDomain_kwargs))
    # print('onlyDomain', dapp1.transact(cid_app1, 'onlyDomain', {'domain':enode2_key} ))
    print('dapp2 DomainRegistry events', dapp2.watch_events(cid_app2, 'DomainRegistry'))

    print(dapp1.watch(cid_app1, 'WorkflowCall', transaction_callback))
    registerDomain_kwargs = {'name': 'install', 'ack': True, 'updates': False}
    print(dapp2.transact(cid_app2, 'callWorkflow', registerDomain_kwargs))
    print(dapp1.watch_events(cid_app1, 'WorkflowCall'))


def more_complex_test():
    from gevent import queue

    debug = False
    level = logging.DEBUG if debug else logging.INFO
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    handler.setLevel(level)
    logging.getLogger().addHandler(handler)
    logging.getLogger().setLevel(level)
    logger = logging.getLogger(__name__)

    q1 = queue.Queue()
    configs1 = {'method': 'rpc', 'address': 'http://127.0.0.1:8101'}
    dapp1 = ExchangeDapp(configs1, q1)

    q2 = queue.Queue()
    configs2 = {'method': 'rpc', 'address': 'http://127.0.0.1:8102'}
    dapp2 = ExchangeDapp(configs2, q2)

    enode2 = dapp2.get_enode()
    enode2_key = dapp2.get_id()
    dapp1.peer('2', enode2)

    cid_app1 = dapp1.instantiate('LifecycleNotary')

    contract_info = dapp1.get_info(cid_app1)
    cid_app2 = dapp2.join(**contract_info)

    registerDomain_kwargs = {'domain':enode2_key, 'name':"Algum"}

    print(dapp2.watch_contract(cid_app2, 'DomainRegistry'))
    print(dapp1.watch_contract(cid_app1, 'WorkflowCall'))

    print(dapp1.transact(cid_app1, 'registerDomain', registerDomain_kwargs))

    print('q2', q2.get(block=True, timeout=10))

    registerDomain_kwargs = {'name': 'install', 'ack': True, 'updates': False}
    print(dapp2.transact(cid_app2, 'callWorkflow', registerDomain_kwargs))

    print('q1', q1.get(block=True, timeout=10))

    print(dapp2.watch_contract(cid_app2, 'DomainRegistry', end=True))
    print(dapp1.watch_contract(cid_app1, 'WorkflowCall', end=True))


if __name__ == '__main__':
    # simple_remote_test('http://127.0.0.1:8101')
    # raw_test('http://127.0.0.1:8101')
    # simple_local_test()
    # complex_test()
    more_complex_test()
