pragma solidity ^0.4.18;

contract Greeter {
    string public greeting;

    event AckGreet(
        string aloha,
        address accountAddress
    );

    function Greeter() public {
        greeting = 'Hello';
    }

    function setGreeting(string _greeting) public {
        greeting = _greeting;

        AckGreet("greeting set by", msg.sender);
    }

    function greet() public constant returns (string) {
        return greeting;
    }
}