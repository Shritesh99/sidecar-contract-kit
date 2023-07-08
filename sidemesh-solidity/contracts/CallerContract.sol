// SPDX-License-Identifier: Apache-2.0
pragma solidity >=0.7.0 <0.9.0;

import "./CrossChain.sol";
// Declares a new contract
contract CallerContract {
    
    event Result(
        string txId,
        bytes data
    );
    
    function call(
        address crossChainAddress,
        string memory txId,
        string memory primaryNetworkId,
        string memory networkId,
        string memory invocationId,
        bytes memory args)
        public {
            CrossChain crossChain = CrossChain(crossChainAddress);
            crossChain.doCross(txId, primaryNetworkId, networkId, invocationId, args);
    }
    function _callback(string memory txId, bytes memory data) public{
        emit Result(txId, data);
    }
}