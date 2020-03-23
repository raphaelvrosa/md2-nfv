pragma solidity ^0.4.18;

contract LifecycleNotary {

    enum State { Created, Updated, Inactive }

    address public customer; // service customer
    uint id; // service identifier
    State public state; // current service state

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
            return true;
        } else {
            return false;
        }
    }

    function kill() public onlyCustomer {
        selfdestruct(msg.sender);  // kills this contract and sends remaining funds back to customer
    }
}
