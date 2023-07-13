// SPDX-License-Identifier: Apache-2.0
pragma solidity >=0.7.0 <0.9.0;

// Declares a new contract
contract SimpleStorage {
    // Storage. Persists in between transactions
    bytes x;

    // Allows the unsigned integer stored to be changed
    function set(bytes memory newValue) public returns(bytes memory){
        x = newValue;
        emit Changed(msg.sender, newValue);
        return x;
    }

    // Returns the currently stored unsigned integer
    function get() public view returns (bytes memory) {
        return x;
    }

    event Changed(address indexed from, bytes value);
}