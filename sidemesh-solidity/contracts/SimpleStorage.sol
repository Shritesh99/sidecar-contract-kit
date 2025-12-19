// SPDX-License-Identifier: Apache-2.0
pragma solidity >=0.7.0 <0.9.0;

// Declares a new contract
contract SimpleStorage {
    // Storage. Persists in between transactions
    mapping(bytes => bytes) public map;

    // Allows the unsigned integer stored to be changed
    function set(bytes memory key, bytes memory value)public{
        map[key] = value;
        emit Changed(msg.sender, key, value);
    }

    // Returns the currently stored unsigned integer
    function get(bytes memory key) public view returns (bytes memory) {
        return map[key];
    }

    event Changed(address indexed from, bytes key, bytes value);
}