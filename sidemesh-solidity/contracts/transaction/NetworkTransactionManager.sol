// SPDX-License-Identifier: GPL-3.0
pragma solidity >=0.7.0 <0.9.0;

import "../resource/Register.sol";
import "../lock/LockManager.sol";

contract NetworkTransactionManager {

    string constant public ERROR_REG_ID_NOT_FOUND = "[Register] Cant able find id";
    string constant public ERROR_REG_ID_FOUND = "[Register] ID already exist, please send a different one";
    string constant public ERROR_INO_ID_NOT_FOUND = "[Invocation] Cant able find id";
    string constant public ERROR_INO_ID_FOUND = "[Invocation] ID already exist, please send a different one";
    string constant public ERROR_LOCK_NOT_VALID = "Lock is not valid";
    string constant public ERROR_LOCK_EXIST = "Lock already exist at timestamp: ";
    string constant public ERROR_LOCK_NOT_EXIST = "Lock not exist";
    string constant public ERROR_TX_EXIST = "Tx already exist";
    string constant public ERROR_TX_NOT_EXIST = "Tx not exist";
    string constant public ERROR_INVALID_STATUS = "Invalid status";

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
        bool success,
        bytes data,
        string primaryNetworkUrl
    );

    event NetworkTxStatus(
        string txId,
        NetworkTransactionStatusType status,
        string primaryNetworkUrl
    );

    mapping(bytes32 => Transaction) transactions;
    
    Register register;
    LockManager lockManager;

    constructor(address _register, address _lockManager){
        register = Register(_register);
        lockManager = LockManager(_lockManager);
    }

    modifier checkInvocationID(string memory networkID, string memory id){
        require(register.checkInvocationIDExist(networkID, id), ERROR_INO_ID_NOT_FOUND);
        _;
    }

    modifier checkTx(string memory txId, bool ifExist, string memory errMsg){
        require((ifExist) ? checkTxExist(txId): !checkTxExist(txId), errMsg);
        _;
    }

    function checkTxExist(string memory txId) public view returns(bool){
        bytes32 hash = keccak256(bytes(txId));
        return transactions[hash].isValid;
    }

    function changeStatus(string memory txId, uint _status) public checkTx(txId, true, ERROR_TX_NOT_EXIST){
        bytes32 hash = keccak256(abi.encodePacked(txId));
        
        transactions[hash].status = NetworkTransactionStatusType(_status);

        (, , string memory url) = register.resolveNetwork(transactions[hash].primaryNetworkId);
        emit NetworkTxStatus(txId, NetworkTransactionStatusType(_status), url);
    }

    function startNetworkTransaction(
        string memory txId,
        string memory primaryNetworkId,
        string memory networkId,
        string memory invocationId,
        bytes memory args)
        external checkInvocationID(networkId, invocationId) checkTx(txId, false, ERROR_TX_EXIST) {            
            bytes32 hash = keccak256(abi.encodePacked(txId));
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
        external checkTx(txId, true, ERROR_TX_NOT_EXIST){
            bytes32 hash = keccak256(abi.encodePacked(txId));
            require(transactions[hash].status == NetworkTransactionStatusType.NETWORK_TRANSACTION_STARTED, ERROR_INVALID_STATUS);

            lockManager.putLock(txId);
            changeStatus(txId, 3);
    }

    function confirmNetworkTransaction(string memory txId)
        external checkTx(txId, true, ERROR_TX_NOT_EXIST){
            bytes32 hash = keccak256(abi.encodePacked(txId));
            require(transactions[hash].status == NetworkTransactionStatusType.PRIMARY_TRANSACTION_COMMITTED, ERROR_INVALID_STATUS);

            (, address contractAddress, string memory functionSignature, bytes memory args) = register.resolveInvocation(transactions[hash].networkId, transactions[hash].invocationId);
            
            (bool success, bytes memory data) = contractAddress.call(abi.encodeWithSignature(functionSignature, args));
            (, , string memory url) = register.resolveNetwork(transactions[hash].primaryNetworkId);

            emit ConfirmNetworkTransaction(txId, success, data, url);
            
            lockManager.releaseLock(txId);
            changeStatus(txId, 5);
    }
}