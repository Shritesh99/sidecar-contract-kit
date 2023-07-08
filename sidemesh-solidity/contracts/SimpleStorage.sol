// SPDX-License-Identifier: Apache-2.0
pragma solidity >=0.7.0 <0.9.0;

// Declares a new contract
contract SimpleStorage {
    // Storage. Persists in between transactions
    uint256 x;

    // Allows the unsigned integer stored to be changed
    function set(uint256 newValue) public returns(uint256){
        x = newValue;
        emit Changed(msg.sender, newValue);
        return x;
    }

    // Returns the currently stored unsigned integer
    function get() public view returns (uint256) {
        return x;
    }

    event Changed(address indexed from, uint256 value);
}