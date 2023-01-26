// SPDX-License-Identifier: GPL-3.0
pragma solidity >=0.7.0 <0.9.0;

import "../lib/Utils.sol";
import "../lib/Constants.sol";

import "../resource/Register.sol";
import "../lock/LockManager.sol";

contract PrimaryTransactionManager {

    enum PrimaryTransactionStatusType{
        PRIMARY_TRANSACTION_STARTED, // 0
        PRIMARY_TRANSACTION_PREPARED, // 1
        NETWORK_TRANSACTION_STARTED, // 2
        NETWORK_TRANSACTION_PREPARED, // 3
        PRIMARY_TRANSACTION_COMMITTED, // 4
        NETWORK_TRANSACTION_COMMITTED // 5
    }

    struct Transaction{
        string networkId;
        string invocationId;
        string txId;
        // string txProof;
        PrimaryTransactionStatusType status;
        bool isValid;
    }

    event PreparePrimaryTransaction(
        string txId,
        string networkId,
        string invocatonId,
        bytes args
    );

    event PrimaryTxStatus(
        string txId,
        PrimaryTransactionStatusType status
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

    function changeStatus(string memory txId, uint _status) 
        public checkTx(txId, true, Constants.ERROR_TX_NOT_EXIST){
            bytes32 hash = Utils.hash(abi.encodePacked(txId));
            
            transactions[hash].status = PrimaryTransactionStatusType(_status);
            emit PrimaryTxStatus(txId, PrimaryTransactionStatusType(_status));
    }

    function startPrimaryTransaction(string memory txId)
        external checkTx(txId, false, Constants.ERROR_TX_EXIST){
            bytes32 hash = Utils.hash(abi.encodePacked(txId));
            
            Transaction storage tsx = transactions[hash];
            tsx.txId = txId;
            tsx.isValid = true;
            tsx.status = PrimaryTransactionStatusType.PRIMARY_TRANSACTION_STARTED;
            
            changeStatus(txId, 0);
    }
    
    function registerNetworkTransaction(
        string memory txId,
        string memory networkId,
        string memory invocationId,
        bytes memory args)
        external checkInvocationID(networkId, invocationId) checkTx(txId, true, Constants.ERROR_TX_NOT_EXIST){
            bytes32 hash = Utils.hash(abi.encodePacked(txId));
            
            register.addArgs(networkId, invocationId, args);

            transactions[hash].networkId = networkId;
            transactions[hash].invocationId = invocationId;
    }

    function preparePrimaryTransaction(string memory txId)
        external checkTx(txId, true, Constants.ERROR_TX_NOT_EXIST){
        bytes32 hash = Utils.hash(abi.encodePacked(txId));
            require(transactions[hash].status == PrimaryTransactionStatusType.PRIMARY_TRANSACTION_STARTED, Constants.ERROR_INVALID_STATUS);

            lockManager.putLock(txId);
            
            (string memory networkId, , ) = register.resolveNetwork(transactions[hash].networkId);
            
            (string memory invocatonId, , , bytes memory args) = register.resolveInvocation(transactions[hash].networkId, transactions[hash].invocationId);
            
            emit PreparePrimaryTransaction(txId, networkId, invocatonId, args);
            
            changeStatus(txId, 1);
    }

    function confirmPrimaryTransaction(string memory txId)
        external checkTx(txId, true, Constants.ERROR_TX_NOT_EXIST){
            bytes32 hash = Utils.hash(abi.encodePacked(txId));
            require(transactions[hash].status == PrimaryTransactionStatusType.NETWORK_TRANSACTION_PREPARED, Constants.ERROR_INVALID_STATUS);

            lockManager.releaseLock(txId);
            changeStatus(txId, 4);
    }
}