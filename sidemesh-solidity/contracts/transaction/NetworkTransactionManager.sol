// SPDX-License-Identifier: GPL-3.0
pragma solidity >=0.7.0 <0.9.0;

import "../resource/Register.sol";
import "../lock/LockManager.sol";

contract NetworkTransactionManager {
    bytes constant NULL = "";
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
        NETWORK_TRANSACTION_STARTED, // 0
        NETWORK_TRANSACTION_PREPARED, // 1
        NETWORK_TRANSACTION_COMMITTED // 2
    }

    struct Transaction{
        string primaryNetworkId;
        string txId;
        string networkId;
        string invocationId;
        // string txProof;
        NetworkTransactionStatusType status;
        bool isValid;
        bytes[] args;
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
        require(_status == 0 || _status-1 == uint(transactions[hash].status), ERROR_INVALID_STATUS);
        transactions[hash].status = NetworkTransactionStatusType(_status);

        (, , string memory primaryNetworkUrl) = register.resolveNetwork(transactions[hash].primaryNetworkId);
        emit NetworkTxStatus(txId, NetworkTransactionStatusType(_status), primaryNetworkUrl);
    }

    function startNetworkTransaction(
        string memory txId,
        string memory primaryNetworkId,
        string memory networkId,
        string memory invocationId,
        bytes[] memory args)
        external checkInvocationID(networkId, invocationId) checkTx(txId, false, ERROR_TX_EXIST) {            
            bytes32 hash = keccak256(abi.encodePacked(txId));

            Transaction storage tsx = transactions[hash];
            tsx.txId = txId;
            tsx.primaryNetworkId = primaryNetworkId;
            tsx.isValid = true;
            transactions[hash].networkId = networkId;
            transactions[hash].invocationId = invocationId;
            transactions[hash].args = args;
            tsx.status = NetworkTransactionStatusType.NETWORK_TRANSACTION_STARTED;
            
            changeStatus(txId, 0);
    }

    function prepareNetworkTransaction(string memory txId) 
        external checkTx(txId, true, ERROR_TX_NOT_EXIST){
            lockManager.putLock(txId);
            changeStatus(txId, 1);
    }

    function paddedLength(uint256 len) public pure returns (uint256) {
        return ((len + 31) / 32) * 32;
    }

    function buildCalldata(bytes4 selector, bytes[] memory args) public pure returns (bytes memory) {
        uint256 baseOffset = args.length * 32;
        uint256[] memory offsets = new uint256[](args.length);
        uint256 currentOffset = baseOffset;
        
        for (uint i = 0; i < args.length; i++) {
            offsets[i] = currentOffset;
            // Each dynamic type needs: 32 bytes for length + padded data
            currentOffset += 32 + paddedLength(args[i].length);
        }
        
        // Build calldata: selector + offsets + encoded args
        bytes memory callData = abi.encodePacked(selector);
        
        // Append all offsets
        for (uint i = 0; i < offsets.length; i++) {
            callData = abi.encodePacked(callData, abi.encode(offsets[i]));
        }
        
        // Append all argument data with length prefix and padding
        for (uint i = 0; i < args.length; i++) {
            // Encode length (32 bytes) + data + padding
            callData = abi.encodePacked(callData, abi.encode(args[i].length));
            callData = abi.encodePacked(callData, args[i]);
            
            // Add padding to reach 32-byte boundary
            uint256 padding = paddedLength(args[i].length) - args[i].length;
            if (padding > 0) {
                bytes memory paddingBytes = new bytes(padding);
                callData = abi.encodePacked(callData, paddingBytes);
            }
        }
        
        return callData;
    }
    
    function confirmNetworkTransaction(string memory txId)
        external checkTx(txId, true, ERROR_TX_NOT_EXIST){
            bytes32 hash = keccak256(abi.encodePacked(txId));

            (, address contractAddress, string memory functionSignature) = register.resolveInvocation(transactions[hash].networkId, transactions[hash].invocationId);

            bytes4 selector = bytes4(keccak256(bytes(functionSignature)));
            bytes memory callData = buildCalldata(selector, transactions[hash].args);
            
            (bool success, bytes memory data) = contractAddress.call(callData);
            (, , string memory url) = register.resolveNetwork(transactions[hash].primaryNetworkId);
            
            lockManager.releaseLock(txId);
            changeStatus(txId, 2);

            emit ConfirmNetworkTransaction(txId, success, data, url);
    }
}