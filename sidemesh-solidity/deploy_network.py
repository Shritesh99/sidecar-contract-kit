"""
Hyperledger FireFly - Ethereum Smart Contract API Sequential Execution Script

This script demonstrates all API calls from the Hyperledger FireFly tutorial
for working with custom Ethereum smart contracts, executed in sequential order.

Prerequisites:
- FireFly stack running locally with at least 2 members
- Ethereum blockchain created by FireFly CLI
- Python 3.7+
- requests library: pip install requests
"""

import requests
import json
import time
from typing import Dict, Any, Optional

# Configuration
BASE_URL = "http://localhost:5003/api/v1"
NAMESPACE = "default"


def log_request(method: str, url: str, data: Optional[Dict] = None) -> None:
    """Log API request details"""
    print(f"\n{'='*80}")
    print(f"📤 {method} Request")
    print(f"URL: {url}")
    if data:
        print(f"Body:\n{json.dumps(data, indent=2)}")


def log_response(response: requests.Response) -> None:
    """Log API response details"""
    print(f"\n📥 Response ({response.status_code})")
    try:
        print(f"Body:\n{json.dumps(response.json(), indent=2)}")
    except:
        print(f"Body:\n{response.text}")


def api_call(
    method: str,
    endpoint: str,
    data: Optional[Dict] = None,
    params: Optional[Dict] = None,
) -> requests.Response:
    """
    Make an API call and handle errors

    Args:
        method: HTTP method (GET, POST, DELETE)
        endpoint: API endpoint path
        data: Request body
        params: Query parameters

    Returns:
        Response object
    """
    url = f"{BASE_URL}{endpoint}"
    headers = {"Content-Type": "application/json"}

    # log_request(method, url, data)

    try:
        if method == "GET":
            response = requests.get(url, headers=headers, params=params)
        elif method == "POST":
            response = requests.post(
                url, json=data, headers=headers, params=params)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")

        # log_response(response)
        response.raise_for_status()
        return response

    except requests.exceptions.RequestException as e:
        print(f"\n❌ Error: {e}")
        raise

# ============================================================================
# REQUEST 0: Operation
# ============================================================================


def get_operation(id):
    """
    Endpoint: POST /namespaces/{namespace}/operations/id
    """

    print("\n\n" + "="*80)
    print(f"REQUEST 0: Get Operation {id}")
    print("="*80)

    response = api_call(
        "GET", f"/namespaces/{NAMESPACE}/operations/{id}", params={"fetchstatus": "true"})
    data = response.json()

    return data


def get_interface(name: str, version: str) -> Optional[Dict]:
    """
    Checks if an interface with the given name and version already exists.
    """
    try:
        response = api_call(
            "GET",
            f"/namespaces/{NAMESPACE}/contracts/interfaces/{name}/{version}"
        )
        data = response.json()
        if data and len(data) > 0:
            print(
                f"ℹ️  Found existing interface '{name}' (version {version}) with ID: {data['id']}")
            return data['id']
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            return None
        else:
            raise
    return None


def get_api(name: str) -> Optional[Dict]:
    """
    Checks if an api with the given name
    """
    try:
        response = api_call(
            "GET",
            f"/namespaces/{NAMESPACE}/apis/{name}"
        )
        data = response.json()
        if data and len(data) > 0:
            print(f"ℹ️  Found existing api '{name}': {data['id']}")
            return data['id']
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            return None
        else:
            raise
    return None

# ============================================================================
# REQUEST 1: Deploy Smart Contract
# ============================================================================


def deploy_contract(name, contract_bytecode, contract_abi, inputs):
    """
    Endpoint: POST /namespaces/{namespace}/contracts/deploy
    """

    print("\n\n" + "="*80)
    print(f"REQUEST 1: Deploy {name} Smart Contract")
    print("="*80)

    payload = {
        "contract": contract_bytecode,
        "definition": contract_abi,
        "input": inputs,
    }

    response = api_call(
        "POST", f"/namespaces/{NAMESPACE}/contracts/deploy", payload, params={"confirm": "true"})
    data = response.json()

    operation_id = data.get("id")
    operation = get_operation(operation_id)

    contract_address = operation.get("detailedStatus", {}).get(
        "receipt", {}).get("extraInfo", {}).get("contractAddress")

    print(f"\n✅ Contract {name} deployed at address: {contract_address}")
    return contract_address


# ============================================================================
# REQUEST 2: Generate Interface from ABI
# ============================================================================
def generate_interface(name, version, contract_abi):
    """
    Generate FireFly Interface from Ethereum ABI

    Endpoint: POST /namespaces/{namespace}/contracts/interfaces/generate
    """

    print("\n\n" + "="*80)
    print("REQUEST 2: Generate FireFly Interface from ABI")
    print("="*80)

    payload = {"name": name, "version": version,
               "input": {"abi": contract_abi}}

    response = api_call(
        "POST",
        f"/namespaces/{NAMESPACE}/contracts/interfaces/generate",
        payload,
        params={"confirm": "true"},
    )

    data = response.json()
    print(f"\n✅ Interface generated successfully")

    return data

# ============================================================================
# REQUEST 3: Broadcast Contract Interface
# ============================================================================


def broadcast_interface(payload):
    """
    Broadcast contract interface to the network

    Endpoint: POST /namespaces/{namespace}/contracts/interfaces
    """

    print("\n\n" + "="*80)
    print("REQUEST 3: Broadcast Contract Interface")
    print("="*80)

    response = api_call(
        "POST",
        f"/namespaces/{NAMESPACE}/contracts/interfaces",
        payload,
        params={"confirm": "true", "publish": "true"},
    )
    data = response.json()
    print(f"\n✅ Interface broadcasted with ID: {data.get('id')}")

    return data.get("id")


# ============================================================================
# REQUEST 4: Create HTTP API for Contract
# ============================================================================
def create_api(name, interface_id: str, contract_address: str):
    """
    Create an HTTP API wrapper for the smart contract

    Endpoint: POST /namespaces/{namespace}/apis?publish=true
    """

    print("\n\n" + "="*80)
    print("REQUEST 4: Create HTTP API for Contract")
    print("="*80)

    payload = {
        "name": name,
        "interface": {"id": interface_id},
        "location": {"address": contract_address},
    }

    response = api_call(
        "POST",
        f"/namespaces/{NAMESPACE}/apis",
        payload,
        params={"confirm": "true", "publish": "true"},
    )
    data = response.json()
    print(f"\n✅ API created with ID: {data.get('id')}")

    return data.get("id")

# ============================================================================
# REQUEST 8: Create Blockchain Event Listener
# ============================================================================


def create_listener(interface_id: str, contract_address: str, event, topic):
    """
    Create a blockchain event listener for the Changed event

    Endpoint: POST /namespaces/{namespace}/contracts/listeners
    """
    print("\n\n" + "="*80)
    print("REQUEST 8: Create Blockchain Event Listener")
    print("="*80)

    payload = {
        "interface": {"id": interface_id},
        "location": {"address": contract_address},
        "eventPath": event,
        "options": {"firstEvent": "newest"},
        "topic": topic,
    }

    response = api_call(
        "POST",
        f"/namespaces/{NAMESPACE}/contracts/listeners",
        payload,
    )
    data = response.json()
    print(data)
    print(f"\n✅ Event listener created with ID: {data.get('id')}")

    return data.get("id")

# ============================================================================
# REQUEST 10: Create Subscription for Events
# ============================================================================


def create_subscription(listener_id, name):
    """
    Create a subscription to receive events via WebSocket

    Endpoint: POST /namespaces/{namespace}/subscriptions
    """

    print("\n\n" + "="*80)
    print("REQUEST 10: Create Event Subscription (WebSocket)")
    print("="*80)

    payload = {
        "namespace": NAMESPACE,
        "name": name,
        "transport": "websockets",
        "filter": {
            "events": "blockchain_event_received",
            "blockchainevent": {"listener": listener_id},
        },
        "options": {"firstEvent": "newest"},
    }

    response = api_call(
        "POST",
        f"/namespaces/{NAMESPACE}/subscriptions",
        payload,
    )
    data = response.json()
    print(f"\n✅ Event subscription created with ID: {data.get('id')}")
    return data.get("id")


# ============================================================================
# Main Execution Flow
# ============================================================================
def main():
    """Execute all API calls in sequential order"""

    print("\n")
    print("╔" + "="*78 + "╗")
    print("║" + " "*78 + "║")
    print("║" + "  Hyperledger FireFly - Primary Network Deployment".center(78) + "║")
    print("║" + " "*78 + "║")
    print("╚" + "="*78 + "╝")

    with open("./build/contracts/Register.json", "r") as register_json, open("./build/contracts/LockManager.json", "r") as lock_manager_json, open("./build/contracts/NetworkTransactionManager.json", "r") as network_tx_manager_json, open("./build/contracts/CrossNetwork.json", "r") as cross_network_json, open("./build/contracts/SimpleStorage.json", "r") as simple_storage_json:
        register = json.load(register_json)
        lock_manager = json.load(lock_manager_json)
        network_tx_manager = json.load(network_tx_manager_json)
        cross_network = json.load(cross_network_json)
        simple_storage = json.load(simple_storage_json)

        try:
            register_name = "Register"
            lock_manager_name = "LockManager"
            network_tx_manager_name = "PrimaryTransactionManager"
            cross_network_name = "cross-network"  # Important: must be lowercase
            simple_storage_name = "SimpleStorage"

            register_RegisterEventTopic = "RegisterEventTopic"
            register_InvocationRegisteredEvent = "InvocationRegisteredEvent"
            register_NetworkRegisteredEvent = "NetworkRegisteredEvent"

            cross_network_CrossNetworkEventTopic = "CrossNetworkEventTopic"
            cross_network_ConfirmNetworkTransactionEvent = "ConfirmNetworkTransaction"
            cross_network_NetworkTxStatusEvent = "NetworkTxStatus"

            simple_storage_SimpleStorageEventTopic = "SimpleStorageEventTopic"
            simple_storage_ChangedEvent = "Changed"

            register_version = "v1.0.0"
            network_tx_manager_version = "v1.0.0"
            cross_network_version = "v1.0.0"
            simple_storage_version = "v1.0.0"

            # Deploy contracts
            register_contract_address = deploy_contract(
                register_name, register["bytecode"], register["abi"], [])
            if not register_contract_address:
                return

            lock_manager_contract_address = deploy_contract(
                lock_manager_name, lock_manager["bytecode"], lock_manager["abi"], [register_contract_address])

            if not lock_manager_contract_address:
                return

            network_tx_manager_contract_address = deploy_contract(network_tx_manager_name, network_tx_manager["bytecode"], network_tx_manager["abi"], [
                                                                  register_contract_address, lock_manager_contract_address])

            if not network_tx_manager_contract_address:
                return

            cross_network_contract_address = deploy_contract(cross_network_name, cross_network["bytecode"], cross_network["abi"], [
                                                             register_contract_address, network_tx_manager_contract_address])

            if not cross_network_contract_address:
                return

            simple_storage_contract_address = deploy_contract(
                simple_storage_name, simple_storage["bytecode"], simple_storage["abi"], [])
            if not simple_storage_contract_address:
                return

            # Register interface and API
            register_interface_payload = generate_interface(
                register_name, register_version, register["abi"])

            register_interface_id = get_interface(
                register_name, register_version)
            if not register_interface_id:
                register_interface_id = broadcast_interface(
                    register_interface_payload)

            register_api_id = get_api(register_name)
            if not register_api_id and register_interface_id and register_contract_address:
                register_api_id = create_api(
                    register_name, register_interface_id, register_contract_address)

            #  Network tx manager interface
            network_tx_manager_interface_payload = generate_interface(
                network_tx_manager_name, network_tx_manager_version, network_tx_manager["abi"])

            network_tx_manager_interface_id = get_interface(
                network_tx_manager_name, network_tx_manager_version)
            if not network_tx_manager_interface_id:
                network_tx_manager_interface_id = broadcast_interface(
                    network_tx_manager_interface_payload)

            # Cross network interface and API
            cross_network_interface_payload = generate_interface(
                cross_network_name, cross_network_version, cross_network["abi"])

            cross_network_interface_id = get_interface(
                cross_network_name, cross_network_version)
            if not cross_network_interface_id:
                cross_network_interface_id = broadcast_interface(
                    cross_network_interface_payload)

            cross_network_api_id = get_api(cross_network_name)
            if not cross_network_api_id and cross_network_interface_id and cross_network_contract_address:
                cross_network_api_id = create_api(
                    cross_network_name, cross_network_interface_id, cross_network_contract_address)

            # Single storage interface and API
            simple_storage_interface_payload = generate_interface(
                simple_storage_name, simple_storage_version, simple_storage["abi"])
            simple_storage_interface_id = get_interface(
                simple_storage_name, simple_storage_version)
            if not simple_storage_interface_id:
                simple_storage_interface_id = broadcast_interface(
                    simple_storage_interface_payload)

            # Register events
            register_InvocationRegisteredEvent_id = create_listener(
                register_interface_id, register_contract_address, register_InvocationRegisteredEvent, register_RegisterEventTopic)
            register_NetworkRegisteredEvent_id = create_listener(
                register_interface_id, register_contract_address, register_NetworkRegisteredEvent, register_RegisterEventTopic)

            subscription_InvocationRegisteredEvent_id = create_subscription(
                register_InvocationRegisteredEvent_id, register_InvocationRegisteredEvent)
            subscription_NetworkRegisteredEvent_id = create_subscription(
                register_NetworkRegisteredEvent_id, register_NetworkRegisteredEvent)

            # Network tx events
            cross_network_ConfirmNetworkTransactionEvent_id = create_listener(
                network_tx_manager_interface_id, network_tx_manager_contract_address, cross_network_ConfirmNetworkTransactionEvent, cross_network_CrossNetworkEventTopic)
            cross_network_NetworkTxStatusEvent_id = create_listener(
                network_tx_manager_interface_id, network_tx_manager_contract_address, cross_network_NetworkTxStatusEvent, cross_network_CrossNetworkEventTopic)

            subscription_ConfirmNetworkTransactionEvent_id = create_subscription(
                cross_network_ConfirmNetworkTransactionEvent_id, cross_network_ConfirmNetworkTransactionEvent)
            subscription_NetworkTxStatusEvent_id = create_subscription(
                cross_network_NetworkTxStatusEvent_id, cross_network_NetworkTxStatusEvent)

            # Simple storage events
            simple_storage_ChangedEvent_id = create_listener(
                simple_storage_interface_id, simple_storage_contract_address, simple_storage_ChangedEvent, simple_storage_SimpleStorageEventTopic)
            subscription_ChangedEvent_id = create_subscription(
                simple_storage_ChangedEvent_id, simple_storage_ChangedEvent)

            # Summary
            print("\n\n" + "="*80)
            print("✅ ALL API REQUESTS EXECUTED SUCCESSFULLY!")
            print("="*80)
            print(f"\nSummary:")
            print(
                f"  • Register Contract Address: {register_contract_address}")
            print(f"  • Register Interface ID: {register_interface_id}")
            print(f"  • Register API ID: {register_api_id}")
            print(
                f"  • CrossNetwork Contract Address: {cross_network_contract_address}")
            print(
                f"  • CrossNetwork Interface ID: {cross_network_interface_id}")
            print(f"  • CrossNetwork API ID: {cross_network_api_id}")
            print(
                f"  • Simple Storage Contract address: {simple_storage_contract_address}")
            print(
                f"  • Register InvocationRegisteredEvent Subscription ID: {subscription_InvocationRegisteredEvent_id}")
            print(
                f"  • Register NetworkRegisteredEvent Subscription ID: {subscription_NetworkRegisteredEvent_id}")
            print(
                f"  • Cross Network ConfirmNetworkTransactionEvent Subscription ID: {subscription_ConfirmNetworkTransactionEvent_id}")
            print(
                f"  • Cross Network NetworkTxStatusEvent Subscription ID: {subscription_NetworkTxStatusEvent_id}")
            print(
                f"  • Simple Storage Changed Event Subscription ID: {subscription_ChangedEvent_id}")
            # print("\n" + "="*80)

        except Exception as e:
            print(f"\n❌ Execution failed: {e}")
            raise


if __name__ == "__main__":
    main()
