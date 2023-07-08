// SPDX-License-Identifier: GPL-3.0
pragma solidity >=0.7.0 <0.9.0;

import "./CommonChain.sol";
import "./transaction/PrimaryTransactionManager.sol";

contract CrossChain is CommonChain{

    PrimaryTransactionManager primaryTransactionManager;
    address private callbackContract;

    constructor(address _register, address _primaryTransactionManager) CommonChain(_register) {
        primaryTransactionManager = PrimaryTransactionManager(_primaryTransactionManager);
    }

    function doCross(
        string memory txId,
        string memory primaryNetworkId,
        string memory networkId,
        string memory invocationId,
        bytes memory args)
            public{
                callbackContract = msg.sender;
                primaryTransactionManager.startPrimaryTransaction(txId, primaryNetworkId);
                primaryTransactionManager.registerNetworkTransaction(txId, networkId, invocationId, args, msg.sender);
                primaryTransactionManager.preparePrimaryTransaction(txId);
    }
    function confirmDoCross(string memory txId) public{
        primaryTransactionManager.confirmPrimaryTransaction(txId);
    }

    function finishPrimaryTransaction(string memory txId, bytes memory data)public{
        primaryTransactionManager.finishPrimaryTransaction(txId, data);
    }

    function changeStatus(string memory txId, uint _status)public{
        primaryTransactionManager.changeStatus(txId, _status);
    }
}