import requests
import json
from typing import Dict, Optional

MACHINE_IP = "http://192.168.88.219"

PRIMARY_NETWORK_BASE_URL = "http://localhost:5000/api/v1"
NETWORK_BASE_URL = "http://localhost:5003/api/v1"
PRIMARY_NETWORK_WS_URL = "ws://localhost:5000/ws"
NETWORK_WS_URL = "ws://localhost:5003/ws"
NAMESPACE = "default"

SIMPLE_STORAGE_CONTRACT_ADDRESS = "0x8838fee34f4110d374235853b0cafe1877205dd5"


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
    base_url: str,
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
    url = f"{base_url}{endpoint}"
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
# REQUEST 1: Register Network
# ============================================================================
def register_network(base_url, id, name, url):
    """
    Endpoint: POST /namespaces/{namespace}/apis/Register/invoke/registerNetwork
    """

    print("\n\n" + "="*80)
    print(f"REQUEST 1: Register Network on Primary Network")
    print("="*80)

    payload = {
        "input": {
            "id": id,
            "name": name,
            "url": url
        }
    }

    response = api_call(
        base_url, "POST", f"/namespaces/{NAMESPACE}/apis/Register/invoke/registerNetwork", payload)
    data = response.json()
    print(f"\n✅ Network registration successful")

    return data

# ============================================================================
# REQUEST 2: Register Invocation
# ============================================================================


def register_invocation(base_url, contractAddress, invocationId, networkId):
    """
    Endpoint: POST /namespaces/{namespace}/apis/Register/invoke/registerInvocation
    """

    print("\n\n" + "="*80)
    print(f"REQUEST 1: Register Invocation")
    print("="*80)

    payload = {
        "input": {
            "contractAddress": contractAddress,
            "functionSignature": "set(bytes,bytes)",
            "id": invocationId,
            "networkId": networkId
        }
    }

    response = api_call(
        base_url, "POST", f"/namespaces/{NAMESPACE}/apis/Register/invoke/registerInvocation", payload)
    data = response.json()
    print(f"\n✅ Invocation registration successful")

    return data


def main():
    """Main execution"""

    # Register network via API

    register_network(PRIMARY_NETWORK_BASE_URL, "10",
                     "besu", f"{MACHINE_IP}:5000")
    register_network(PRIMARY_NETWORK_BASE_URL, "20",
                     "dev", f"{MACHINE_IP}:5003")
    register_network(NETWORK_BASE_URL, "10", "besu",
                     f"{MACHINE_IP}:5000")
    register_network(NETWORK_BASE_URL, "20", "dev",
                     f"{MACHINE_IP}:5003")

    register_invocation(PRIMARY_NETWORK_BASE_URL,
                        SIMPLE_STORAGE_CONTRACT_ADDRESS, "iv-1", "20")
    register_invocation(
        NETWORK_BASE_URL, SIMPLE_STORAGE_CONTRACT_ADDRESS,  "iv-1", "20")


if __name__ == "__main__":
    main()
