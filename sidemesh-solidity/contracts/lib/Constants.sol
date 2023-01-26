// SPDX-License-Identifier: GPL-3.0
pragma solidity >=0.7.0 <0.9.0;

library Constants{
    string constant ERROR_REG_ID_NOT_FOUND = "[Register] Cant able find id";
    string constant ERROR_REG_ID_FOUND = "[Register] ID already exist, please send a different one";
    string constant ERROR_INO_ID_NOT_FOUND = "[Invocation] Cant able find id";
    string constant ERROR_INO_ID_FOUND = "[Invocation] ID already exist, please send a different one";
    string constant ERROR_LOCK_NOT_VALID = "Lock is not valid";
    string constant ERROR_LOCK_EXIST = "Lock already exist at timestamp: ";
    string constant ERROR_LOCK_NOT_EXIST = "Lock not exist";
    string constant ERROR_TX_EXIST = "Tx already exist";
    string constant ERROR_TX_NOT_EXIST = "Tx not exist";
    string constant ERROR_INVALID_STATUS = "Invalid status";
}