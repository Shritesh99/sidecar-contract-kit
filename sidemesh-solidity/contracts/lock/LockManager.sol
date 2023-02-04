// SPDX-License-Identifier: GPL-3.0
pragma solidity >=0.7.0 <0.9.0;

import "../resource/Register.sol";

contract LockManager{

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
    
    struct Lock{
        string txId;
        bool isLocked;
        bool isValid;
        uint timestamp;
    }

    mapping(bytes32 => Lock) locks;

    Register register;

    constructor(address _register){
        register = Register(_register);
    }

    function putLock(string memory txId) external{
        bytes32 hash = keccak256(abi.encodePacked(txId));
        require(!locks[hash].isLocked, ERROR_LOCK_EXIST);
        
        locks[hash] = Lock(txId, true, true, block.timestamp);
    }

    function checkLock(string memory txId) external view returns(bool, uint){
        bytes32 hash = keccak256(abi.encodePacked(txId));
        require(locks[hash].isValid, ERROR_LOCK_NOT_VALID);
        
        return (locks[hash].isLocked, locks[hash].timestamp);
    }

    function releaseLock(string memory txId) external{
        bytes32 hash = keccak256(abi.encodePacked(txId));

        require(locks[hash].isValid, ERROR_LOCK_NOT_VALID);
        require(locks[hash].isLocked, ERROR_LOCK_NOT_EXIST);

        locks[hash].isLocked = false;
    }
}