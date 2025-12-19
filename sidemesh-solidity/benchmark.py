import requests
import json
import time
import asyncio
import websockets
import random
import string
from typing import Dict, Any, Optional
from datetime import datetime

MACHINE_IP = "http://192.168.88.219"

PRIMARY_NETWORK_BASE_URL = "http://localhost:5000/api/v1"
NETWORK_BASE_URL = "http://localhost:5003/api/v1"
PRIMARY_NETWORK_WS_URL = "ws://localhost:5000/ws"
NETWORK_WS_URL = "ws://localhost:5003/ws"
NAMESPACE = "default"

SIMPLE_STORAGE_CONTRACT_ADDRESS = "0x8838fee34f4110d374235853b0cafe1877205dd5"

# Global variables to track active WebSocket connections and transaction results
primary_ws_connection = None
network_ws_connection = None
transaction_events: Dict[str, Dict[str, Any]] = {}
benchmark_start_time = None
transaction_completion_event = None
current_tx_id = None
current_args = None


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


def generate_random_args() -> bytes:
    """Generate random bytes args"""
    return bytes([random.randint(0, 255) for _ in range(2)])


def generate_random_tx_id() -> str:
    """Generate random transaction ID"""
    return "tx-" + ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))


async def handle_ws_event(event_data: Dict[str, Any], connection_name: str) -> None:
    """
    Handle incoming WebSocket events and match with transactions

    Args:
        event_data: Event data received from WebSocket
        connection_name: Name of the connection (Primary/Network)
    """
    global transaction_events

    event_type = event_data.get("type")
    print(event_data)
    if event_type == "blockchain_event_received":
        blockchain_event = event_data.get("blockchainEvent", {})
        output_key = blockchain_event.get("output", {}).get("key")
        output_value = blockchain_event.get("output", {}).get("value")
        event_name = blockchain_event.get("name")

        # Match the event with any pending transaction using key (txId) and value (args)
        for tx_id, tx_info in transaction_events.items():
            if (tx_info.get("status") == "pending" and
                output_key == tx_id and
                output_value == tx_info["args_hex"] and
                    event_name == "Changed"):

                completion_time = time.time()
                elapsed = completion_time - \
                    tx_info.get("start_time", benchmark_start_time)

                transaction_events[tx_id]["status"] = "completed"
                transaction_events[tx_id]["end_time"] = completion_time
                transaction_events[tx_id]["elapsed_time"] = elapsed
                transaction_events[tx_id]["event_data"] = blockchain_event

                print(
                    f"\n✅ [{connection_name}] Transaction {tx_id} completed!")
                print(f"   Key (TxId): {output_key}")
                print(f"   Value (Args): {output_value}")
                print(f"   Elapsed Time: {elapsed:.4f}s")
                break
    else:
        print(f"\n📥 [{connection_name}] Event received (type: {event_type})")


async def ws_listen_and_send(ws_url: str, connection_name: str, send_events: Optional[list] = None) -> None:
    """
    Connect to WebSocket, send multiple events, and listen for responses

    Args:
        ws_url: WebSocket URL to connect to
        connection_name: Name of the connection (for logging)
        send_events: List of events to send back-to-back
    """
    global primary_ws_connection, network_ws_connection

    try:
        async with websockets.connect(ws_url) as websocket:
            # Store connection reference
            if connection_name == "Primary":
                primary_ws_connection = websocket
            else:
                network_ws_connection = websocket

            print(f"\n✅ [{connection_name}] WebSocket connected to {ws_url}")

            # Send events back-to-back if provided
            if send_events:
                print(
                    f"\n📤 [{connection_name}] Sending {len(send_events)} events...")
                for idx, event in enumerate(send_events, 1):
                    message = json.dumps(event)
                    await websocket.send(message)
                    print(
                        f"📤 [{connection_name}] Event {idx}/{len(send_events)} Sent:\n{json.dumps(event, indent=2)}")
                    # Small delay between messages if needed
                    # await asyncio.sleep(0.1)

            # Keep connection open and listen for events
            print(f"\n🔊 [{connection_name}] Listening for events...")
            try:
                async for message in websocket:
                    try:
                        event = json.loads(message)
                        await handle_ws_event(event, connection_name)
                    except json.JSONDecodeError:
                        print(
                            f"⚠️  [{connection_name}] Received non-JSON message: {message}")

            except asyncio.CancelledError:
                print(f"\n🛑 [{connection_name}] WebSocket listener stopped")

    except Exception as e:
        print(f"❌ [{connection_name}] WebSocket Error: {e}")
        raise
    finally:
        if connection_name == "Primary":
            primary_ws_connection = None
        else:
            network_ws_connection = None


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

        log_response(response)
        response.raise_for_status()
        return response

    except requests.exceptions.RequestException as e:
        print(f"\n❌ Error: {e}")
        raise


def doCross(tx_id: str, args: bytes) -> None:
    """
    Endpoint: POST /namespaces/{namespace}/apis/cross-chain/invoke/doCross
    Send two args as hex strings: first is tx_id, second is random arg
    """

    print(f"\n📤 Sending doCross - TxId: {tx_id}, Args: {args.hex()}")

    # Convert tx_id and args to hex representation
    tx_id_hex = '0x' + tx_id.encode('utf-8').hex()
    args_hex = '0x' + args.hex()

    print(f"   TxId (hex): {tx_id_hex}")
    print(f"   Args (hex): {args_hex}")

    payload = {
        "input": {
            "args": [tx_id_hex, args_hex],  # Two hex arguments
            "invocationId": "iv-1",
            "networkId": "20",
            "primaryNetworkId": "10",
            "txId": tx_id
        }
    }

    response = api_call(
        PRIMARY_NETWORK_BASE_URL, "POST", f"/namespaces/{NAMESPACE}/apis/cross-chain/invoke/doCross", payload)
    data = response.json()
    return data


async def run_transaction(tx_id: str, args: bytes) -> None:
    """
    Run a single transaction and track it

    Args:
        tx_id: Transaction ID
        args: Random bytes arguments
    """
    # Record transaction start
    args_hex = '0x' + args.hex()
    tx_id_hex = '0x' + tx_id.encode('utf-8').hex()
    transaction_events[tx_id_hex] = {
        "status": "pending",
        "args": args,
        "args_hex": args_hex,
        "start_time": time.time(),
        "end_time": None,
        "elapsed_time": None,
        "event_data": None
    }

    try:
        doCross(tx_id, args)
        print(f"✅ doCross API call successful for {tx_id}")
    except Exception as e:
        print(f"❌ Error in doCross for {tx_id}: {e}")
        transaction_events[tx_id]["status"] = "failed"


async def run_benchmark(num_transactions: int):
    """
    Run benchmark with specified number of transactions in parallel

    Args:
        num_transactions: Number of transactions to run
    """
    global benchmark_start_time, transaction_events

    transaction_events = {}
    benchmark_start_time = time.time()

    print(f"\n\n{'='*80}")
    print(
        f"🚀 Starting Benchmark with {num_transactions} transactions (Parallel)")
    print(f"{'='*80}")
    print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Create tasks for all transactions
    tasks = []
    for i in range(num_transactions):
        tx_id = generate_random_tx_id()
        args = generate_random_args()
        task = asyncio.create_task(run_transaction(tx_id, args))
        tasks.append(task)
        # Small delay between API calls
        await asyncio.sleep(0.1)

    # Wait for all API calls to complete
    await asyncio.gather(*tasks)

    # Wait for all transactions to complete (with timeout)
    print(f"\n⏳ Waiting for all transactions to complete (timeout: 120s)...")
    start_wait = time.time()
    timeout = 3000

    while True:
        pending = [tx for tx in transaction_events.values()
                   if tx["status"] == "pending"]

        if not pending:
            break

        elapsed_wait = time.time() - start_wait
        if elapsed_wait > timeout:
            print(
                f"⚠️  Timeout reached. {len(pending)} transactions still pending.")
            break

        await asyncio.sleep(1)

    benchmark_end_time = time.time()
    total_time = benchmark_end_time - benchmark_start_time

    # Print results
    print(f"\n\n{'='*80}")
    print(f"📊 Benchmark Results - {num_transactions} Transactions (Parallel)")
    print(f"{'='*80}")
    print(f"Total Time: {total_time:.4f}s")
    print(f"End Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    completed = [tx for tx in transaction_events.values()
                 if tx["status"] == "completed"]
    failed = [tx for tx in transaction_events.values() if tx["status"]
              == "failed"]
    pending = [tx for tx in transaction_events.values() if tx["status"]
               == "pending"]

    print(f"\nCompleted: {len(completed)}/{num_transactions}")
    print(f"Failed: {len(failed)}/{num_transactions}")
    print(f"Pending: {len(pending)}/{num_transactions}")

    if completed:
        times = [tx["elapsed_time"] for tx in completed]
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)

        print(f"\n⏱️  Transaction Times:")
        print(f"  Average: {avg_time:.4f}s")
        print(f"  Min: {min_time:.4f}s")
        print(f"  Max: {max_time:.4f}s")
        print(f"  Throughput: {len(completed) / total_time:.2f} tx/s")

    # Print individual transaction details
    print(f"\n📋 Individual Transactions:")
    for tx_id, tx_info in sorted(transaction_events.items()):
        status = tx_info["status"]
        elapsed = tx_info.get("elapsed_time")
        if elapsed:
            print(
                f"  {tx_id}: {status} ({elapsed:.4f}s) - Args: {tx_info['args']}")
        else:
            print(f"  {tx_id}: {status} - Args: {tx_info['args']}")

    print(f"\n{'='*80}\n")


async def main():
    """Main execution with dual WebSocket listeners"""

    # Create events to send to Primary Network
    primary_events = [
        # {
        #     "type": "start",
        #     "name": "Changed",
        #     "namespace": "default",
        #     "autoack": True
        # }
    ]

    # Create events to send to Network
    network_events = [
        {
            "type": "start",
            "name": "Changed",
            "namespace": "default",
            "autoack": True
        }
    ]

    print("\n" + "="*80)
    print("🚀 Starting WebSocket connections...")
    print("="*80)

    # Start both WebSocket listeners in background
    primary_ws_task = asyncio.create_task(
        ws_listen_and_send(PRIMARY_NETWORK_WS_URL, "Primary", primary_events)
    )
    network_ws_task = asyncio.create_task(
        ws_listen_and_send(NETWORK_WS_URL, "Network", network_events)
    )

    # Give WebSockets time to connect
    await asyncio.sleep(2)

    # Run benchmark with 10 transactions first
    await run_benchmark(50)

    # Cleanup
    print("🛑 Shutting down...")
    primary_ws_task.cancel()
    network_ws_task.cancel()
    try:
        await asyncio.gather(primary_ws_task, network_ws_task)
    except asyncio.CancelledError:
        pass


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Application closed")
