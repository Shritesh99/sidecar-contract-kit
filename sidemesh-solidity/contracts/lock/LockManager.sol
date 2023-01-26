// SPDX-License-Identifier: GPL-3.0
pragma solidity >=0.7.0 <0.9.0;

import "../lib/Utils.sol";
import "../lib/Constants.sol";
import "../resource/Register.sol";

contract LockManager{
    
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
        bytes32 hash = Utils.hash(abi.encodePacked(txId));
        require(!locks[hash].isLocked, Constants.ERROR_LOCK_EXIST);
        
        locks[hash] = Lock(txId, true, true, block.timestamp);
    }

    function checkLock(string memory txId) external view returns(bool, uint){
        bytes32 hash = Utils.hash(abi.encodePacked(txId));
        require(locks[hash].isValid, Constants.ERROR_LOCK_NOT_VALID);
        
        return (locks[hash].isLocked, locks[hash].timestamp);
    }

    function releaseLock(string memory txId) external{
        bytes32 hash = Utils.hash(abi.encodePacked(txId));

        require(locks[hash].isValid, Constants.ERROR_LOCK_NOT_VALID);
        require(locks[hash].isLocked, Constants.ERROR_LOCK_NOT_EXIST);

        locks[hash].isLocked = false;
    }
}