// SPDX-License-Identifier: GPL-3.0
pragma solidity >=0.7.0 <0.9.0;

contract Register{
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

    struct Invocation{
        string id;
        address contractAddress;
        string functionSignature;
        bool isValid;
    }

    struct Network{
        string id;
        string name;
        string url;
        // uint chainid;
        bool isValid;
        mapping(bytes32 => Invocation) invocations;
    }

    event InvocationRegisteredEvent(
        string networkId,
        string id,
        address contractAddress,
        string functionSignature
    );

    event NetworkRegisteredEvent(
        string id,
        string name,
        string url
    );

    mapping(bytes32 => Network) registeredNetworks;

    modifier checkNetworkID(string memory id, bool ifExist, string memory errorMsg){
        require((ifExist) ? checkNetworkIDExist(id) : !checkNetworkIDExist(id), errorMsg);
        _;
    }
    function checkNetworkIDExist(string memory id)public view returns(bool){
        bytes32 hash = keccak256(bytes(id));
        return registeredNetworks[hash].isValid;
    }
    
    modifier checkInvocationID(string memory networkID, string memory id, bool ifExist, string memory errorMsg){
        require((ifExist) ? checkInvocationIDExist(networkID, id) : !checkInvocationIDExist(networkID, id), errorMsg);
        _;
    }

    function checkInvocationIDExist(string memory networkID, string memory id) 
        checkNetworkID(networkID, true, ERROR_REG_ID_NOT_FOUND) public view returns(bool){
            bytes32 networkHash = keccak256(bytes(networkID));
            bytes32 hash = keccak256(bytes(id));
            return registeredNetworks[networkHash].invocations[hash].isValid;
    }

    function registerNetwork(
        string memory id,
        string memory name,
        string memory url
        // uint chainid
        )
        checkNetworkID(id, false, ERROR_REG_ID_FOUND)
        external {
            bytes32 hash = keccak256(bytes(id));
            
            Network storage network = registeredNetworks[hash];
            network.id = id;
            network.name = name;
            network.url = url;
            // network.chainid = chainid;
            network.isValid = true;

            emit NetworkRegisteredEvent(
                network.id,
                network.name,
                network.url
                // network.chainid
            );
    }
    
    function resolveNetwork(string memory id)
        external view
        checkNetworkID(id, true, ERROR_REG_ID_NOT_FOUND)
        returns(string memory, string memory, string memory){
            bytes32 hash = keccak256(bytes(id));
            return (
                registeredNetworks[hash].id,
                registeredNetworks[hash].name,
                registeredNetworks[hash].url
                // registeredNetworks[hash].chainid
            );    
    }

    function registerInvocation(
        string memory networkId,
        string memory id,
        address contractAddress,
        string memory functionSignature
        ) external checkInvocationID(networkId, id, false, ERROR_INO_ID_FOUND){
            bytes32 hashNetworkID = keccak256(bytes(networkId));
            bytes32 hash = keccak256(bytes(id));

            Invocation storage invocation = registeredNetworks[hashNetworkID].invocations[hash];
            invocation.id = id;
            invocation.contractAddress = contractAddress;
            invocation.functionSignature = functionSignature;
            invocation.isValid = true;
            
            emit InvocationRegisteredEvent(
                networkId,
                registeredNetworks[hashNetworkID].invocations[hash].id,
                registeredNetworks[hashNetworkID].invocations[hash].contractAddress,
                registeredNetworks[hashNetworkID].invocations[hash].functionSignature
            );
    }

    function resolveInvocation(string memory networkId, string memory id)
        external view
        checkInvocationID(networkId, id, true, ERROR_INO_ID_NOT_FOUND)
        returns(string memory, address, string memory){
            bytes32 hashNetworkID = keccak256(bytes(networkId));
            bytes32 hash = keccak256(bytes(id));

            return (
                registeredNetworks[hashNetworkID].invocations[hash].id,
                registeredNetworks[hashNetworkID].invocations[hash].contractAddress,
                registeredNetworks[hashNetworkID].invocations[hash].functionSignature
            );    
    }
}