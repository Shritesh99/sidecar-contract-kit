// SPDX-License-Identifier: GPL-3.0
pragma solidity >=0.7.0 <0.9.0;

import "./resource/Register.sol";

contract CommonChain{

    Register register;

    constructor(address _register){
        register = Register(_register);
    }

    function getChainId()public view returns(uint) {
        return block.chainid;
    }
    function registerPrimaryNetwork(
        string memory id,
        string memory name,
        string memory url) public {
            register.registerNetwork(id, name, url);
    }
    function registerNetwork(
        string memory networkId,
        string memory name,
        string memory url,
        string memory invocationId,
        address contractAddress,
        string memory functionSignature
            ) public{
                register.registerNetwork(networkId, name, url);
                register.registerInvocation(networkId, invocationId, contractAddress, functionSignature);
    }
}