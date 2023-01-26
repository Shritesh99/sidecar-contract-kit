// SPDX-License-Identifier: GPL-3.0
pragma solidity >=0.7.0 <0.9.0;

import "../lib/Utils.sol";
import "../lib/Constants.sol";

import "../resource/Register.sol";
import "../lock/LockManager.sol";

contract NetworkTransactionManager {

    enum NetworkTransactionStatusType{
        PRIMARY_TRANSACTION_STARTED, // 0
        PRIMARY_TRANSACTION_PREPARED, // 1
        NETWORK_TRANSACTION_STARTED, // 2
        NETWORK_TRANSACTION_PREPARED, // 3
        PRIMARY_TRANSACTION_COMMITTED, // 4
        NETWORK_TRANSACTION_COMMITTED // 5
    }

    struct Transaction{
        string primaryNetworkId;
        string txId;
        string networkId;
        string invocationId;
        // string txProof;
        NetworkTransactionStatusType status;
        bool isValid;
    }

    event ConfirmNetworkTransaction(
        string txId,
        bool success
    );

    event NetworkTxStatus(
        string txId,
        NetworkTransactionStatusType status
    );

    mapping(bytes32 => Transaction) transactions;
    
    Register register;
    LockManager lockManager;

    constructor(address _register, address _lockManager){
        register = Register(_register);
        lockManager = LockManager(_lockManager);
    }

    modifier checkInvocationID(string memory networkID, string memory id){
        require(register.checkInvocationIDExist(networkID, id), Constants.ERROR_INO_ID_NOT_FOUND);
        _;
    }

    modifier checkTx(string memory txId, bool ifExist, string memory errMsg){
        require((ifExist) ? checkTxExist(txId): !checkTxExist(txId), errMsg);
        _;
    }

    function checkTxExist(string memory txId) public view returns(bool){
        bytes32 hash = Utils.hash(bytes(txId));
        return transactions[hash].isValid;
    }

    function changeStatus(string memory txId, uint _status) public checkTx(txId, true, Constants.ERROR_TX_NOT_EXIST){
        bytes32 hash = Utils.hash(abi.encodePacked(txId));
        
        transactions[hash].status = NetworkTransactionStatusType(_status);
        emit NetworkTxStatus(txId, NetworkTransactionStatusType(_status));
    }

    function startNetworkTransaction(
        string memory txId,
        string memory primaryNetworkId,
        string memory networkId,
        string memory invocationId,
        bytes memory args)
        external checkInvocationID(networkId, invocationId) checkTx(txId, false, Constants.ERROR_TX_EXIST) {            
            bytes32 hash = Utils.hash(abi.encodePacked(txId));
            // require(transactions[hash].status == NetworkTransactionStatusType.PRIMARY_TRANSACTION_PREPARED, Constants.ERROR_INVALID_STATUS);

            register.addArgs(networkId, invocationId, args);

            Transaction storage tsx = transactions[hash];
            tsx.txId = txId;
            tsx.primaryNetworkId = primaryNetworkId;
            tsx.isValid = true;
            transactions[hash].networkId = networkId;
            transactions[hash].invocationId = invocationId;
            tsx.status = NetworkTransactionStatusType.NETWORK_TRANSACTION_STARTED;
            
            changeStatus(txId, 2);
    }

    function prepareNetworkTransaction(string memory txId) 
        external checkTx(txId, true, Constants.ERROR_TX_NOT_EXIST){
            bytes32 hash = Utils.hash(abi.encodePacked(txId));
            require(transactions[hash].status == NetworkTransactionStatusType.NETWORK_TRANSACTION_STARTED, Constants.ERROR_INVALID_STATUS);

            lockManager.putLock(txId);
            changeStatus(txId, 3);
    }

    function confirmNetworkTransaction(string memory txId)
        external checkTx(txId, true, Constants.ERROR_TX_NOT_EXIST){
            bytes32 hash = Utils.hash(abi.encodePacked(txId));
            require(transactions[hash].status == NetworkTransactionStatusType.NETWORK_TRANSACTION_PREPARED, Constants.ERROR_INVALID_STATUS);

            (, address contractAddress, string memory functionSignature, bytes memory args) = register.resolveInvocation(transactions[hash].networkId, transactions[hash].invocationId);
            
            (bool success,) = contractAddress.call(abi.encodeWithSignature(functionSignature, args));
            
            emit ConfirmNetworkTransaction(txId, success);
            
            lockManager.releaseLock(txId);
            changeStatus(txId, 5);
    }
}