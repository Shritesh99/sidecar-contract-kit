// SPDX-License-Identifier: GPL-3.0
pragma solidity >=0.7.0 <0.9.0;

import "./CommonChain.sol";
import "./transaction/NetworkTransactionManager.sol";

contract CrossNetwork is CommonChain {

    NetworkTransactionManager networkTransactionManager;
    constructor(address _register, address _networkTransactionManager) CommonChain(_register){
        networkTransactionManager = NetworkTransactionManager(_networkTransactionManager);
    }

    function doNetwork(
        string memory txId,
        string memory primaryNetworkId,
        string memory networkId,
        string memory invocationId,
        bytes memory args) 
            public{
                networkTransactionManager.startNetworkTransaction(txId, primaryNetworkId, networkId, invocationId, args);
                networkTransactionManager.prepareNetworkTransaction(txId);
    }
    function confirmDoNetwork(string memory txId) public{
        networkTransactionManager.confirmNetworkTransaction(txId);
    }
    function changeStatus(string memory txId, uint _status)public{
        networkTransactionManager.changeStatus(txId, _status);
    }
}