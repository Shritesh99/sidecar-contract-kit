// SPDX-License-Identifier: GPL-3.0
pragma solidity >=0.7.0 <0.9.0;

import "../resource/Register.sol";
import "../lock/LockManager.sol";

contract PrimaryTransactionManager {

    string constant public CALLBACK = "_callback(string,bytes)";

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
    string constant public ERROR_CALLBACK_FAILED = "Callback execution failed";

    enum PrimaryTransactionStatusType{
        PRIMARY_TRANSACTION_STARTED, // 0
        PRIMARY_TRANSACTION_PREPARED, // 1
        PRIMARY_TRANSACTION_COMMITTED, // 2
        PRIMARY_TRANSACTION_FINISHED // 3
    }

    struct Transaction{
        string primaryNetworkId;
        string networkId;
        string invocationId;
        string txId;
        // string txProof;
        PrimaryTransactionStatusType status;
        bool isValid;
        address callerContract;
    }

    event PreparePrimaryTransaction(
        string txId,
        string primaryNetworkId,
        string networkId,
        string url,
        string invocationId,
        bytes args
    );

    event PrimaryTxStatus(
        string txId,
        PrimaryTransactionStatusType status,
        string networkUrl
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

    function changeStatus(string memory txId, uint _status) 
        public checkTx(txId, true, ERROR_TX_NOT_EXIST){
            bytes32 hash = keccak256(abi.encodePacked(txId));
            require(_status == 0 || _status-1 == uint(transactions[hash].status), ERROR_INVALID_STATUS);
            transactions[hash].status = PrimaryTransactionStatusType(_status);

            (, , string memory networkUrl) = register.resolveNetwork(transactions[hash].networkId);
            emit PrimaryTxStatus(txId, PrimaryTransactionStatusType(_status), networkUrl);
    }

    function startPrimaryTransaction(string memory txId, string memory primaryNetworkId)
        external checkTx(txId, false, ERROR_TX_EXIST){
            bytes32 hash = keccak256(abi.encodePacked(txId));
            
            Transaction storage tsx = transactions[hash];
            tsx.primaryNetworkId = primaryNetworkId;
            tsx.txId = txId;
            tsx.isValid = true;
            tsx.status = PrimaryTransactionStatusType.PRIMARY_TRANSACTION_STARTED;
    }
    
    function registerNetworkTransaction(
        string memory txId,
        string memory networkId,
        string memory invocationId,
        bytes memory args,
        address callerContract)
        external checkInvocationID(networkId, invocationId) checkTx(txId, true, ERROR_TX_NOT_EXIST){
            bytes32 hash = keccak256(abi.encodePacked(txId));
            
            register.addArgs(networkId, invocationId, args);

            transactions[hash].networkId = networkId;
            transactions[hash].invocationId = invocationId;
            transactions[hash].callerContract = callerContract;
    }

    function preparePrimaryTransaction(string memory txId)
        external checkTx(txId, true, ERROR_TX_NOT_EXIST){
        bytes32 hash = keccak256(abi.encodePacked(txId));
            lockManager.putLock(txId);
            
            (string memory networkId, , string memory url) = register.resolveNetwork(transactions[hash].networkId);
            
            (string memory invocatonId, , , bytes memory args) = register.resolveInvocation(transactions[hash].networkId, transactions[hash].invocationId);
            changeStatus(txId, 1);
            emit PreparePrimaryTransaction(txId, transactions[hash].primaryNetworkId, networkId, url, invocatonId, args);
    }

    function confirmPrimaryTransaction(string memory txId)
        external checkTx(txId, true, ERROR_TX_NOT_EXIST){
            bytes32 hash = keccak256(abi.encodePacked(txId));
            require(transactions[hash].status == PrimaryTransactionStatusType.PRIMARY_TRANSACTION_PREPARED, ERROR_INVALID_STATUS);

            lockManager.releaseLock(txId);
            changeStatus(txId, 2);
    }
    function finishPrimaryTransaction(string memory txId, bytes memory data)external checkTx(txId, true, ERROR_TX_NOT_EXIST) {
        bytes32 hash = keccak256(abi.encodePacked(txId));

        (bool success, ) = transactions[hash].callerContract.call(abi.encodeWithSignature(CALLBACK, txId, data));
        require(success, ERROR_CALLBACK_FAILED);
        changeStatus(txId, 3);
    }
}