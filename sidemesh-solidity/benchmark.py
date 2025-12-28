import requests
import json
import time
import asyncio
import websockets
import random
import string
import threading
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
network_ws_connection = None
transaction_events: Dict[str, Dict[str, Any]] = {}
# Thread-safe lock for transaction_events
transaction_events_lock = threading.Lock()
benchmark_start_time = None
transaction_completion_event = None
current_tx_id = None
current_args = None
events_received_count = 0
events_received_count_lock = threading.Lock()  # Thread-safe lock for counter
last_event_time = time.time()
last_event_time_lock = threading.Lock()  # Thread-safe lock for last_event_time
ws_thread = None  # Reference to WebSocket listener thread
ws_thread_stop_event = threading.Event()  # Event to signal thread to stop


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
    Thread-safe version that can be called from a separate thread

    Args:
        event_data: Event data received from WebSocket
        connection_name: Name of the connection (Primary/Network)
    """
    global transaction_events, events_received_count, last_event_time

    event_type = event_data.get("type")

    # Thread-safe counter increment and timestamp update
    with events_received_count_lock:
        events_received_count += 1
    with last_event_time_lock:
        last_event_time = time.time()  # Update last_event_time when event arrives

    print(
        f"\n📥 [{connection_name}] Event #{events_received_count} received (type: {event_type})")

    if event_type == "blockchain_event_received":
        blockchain_event = event_data.get("blockchainEvent", {})
        output_key = blockchain_event.get("output", {}).get("key")
        output_value = blockchain_event.get("output", {}).get("value")
        event_name = blockchain_event.get("name")

        print(
            f"   Event Details - Key: {output_key}, Value: {output_value}, Name: {event_name}")

        # Thread-safe matching with transaction_events
        matched = False
        with transaction_events_lock:
            # Try exact match first
            if output_key in transaction_events:
                tx_info = transaction_events[output_key]
                if (tx_info.get("status") == "pending" and
                    output_value == tx_info["args_hex"] and
                        event_name == "Changed"):

                    completion_time = time.time()
                    elapsed = completion_time - \
                        tx_info.get("start_time", benchmark_start_time)

                    transaction_events[output_key]["status"] = "completed"
                    transaction_events[output_key]["end_time"] = completion_time
                    transaction_events[output_key]["elapsed_time"] = elapsed
                    transaction_events[output_key]["event_data"] = blockchain_event

                    print(
                        f"\n✅ [{connection_name}] Transaction {output_key} completed!")
                    print(f"   Key (TxId): {output_key}")
                    print(f"   Value (Args): {output_value}")
                    print(f"   Elapsed Time: {elapsed:.4f}s")
                    matched = True

            # If exact match failed, try iterating through all transactions (fallback)
            if not matched:
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
                        matched = True
                        break

            if not matched:
                # Get a snapshot for debugging (still within lock)
                all_tx_keys = list(transaction_events.keys())
                pending_tx = [tx_id for tx_id, tx_info in transaction_events.items()
                              if tx_info.get('status') == 'pending']

        # Print debugging info outside the lock to avoid blocking
        if not matched:
            print(f"   ⚠️  Event received but no matching pending transaction found")
            print(f"   Looking for Key: {output_key}, Value: {output_value}")
            print(f"   All registered transactions: {all_tx_keys}")
            print(f"   Pending transactions: {pending_tx}")

            # Try to match with any transaction (even completed/failed) for debugging
            with transaction_events_lock:
                for tx_id, tx_info in transaction_events.items():
                    if output_key == tx_id:
                        print(
                            f"   🔍 Found matching tx_id but status is: {tx_info.get('status')}")
                    if output_value == tx_info.get("args_hex"):
                        print(
                            f"   🔍 Found matching args_hex in tx: {tx_id} (status: {tx_info.get('status')})")

                # Try case-insensitive and format variations
                output_key_lower = output_key.lower() if output_key else None
                for tx_id, tx_info in transaction_events.items():
                    tx_id_lower = tx_id.lower() if tx_id else None
                    if output_key_lower and tx_id_lower and output_key_lower == tx_id_lower:
                        print(
                            f"   🔍 Case-insensitive match found: {tx_id} (status: {tx_info.get('status')})")
    else:
        print(f"   Event Type: {event_type}")


async def ws_listen_and_send(ws_url: str, connection_name: str, send_events: Optional[list] = None) -> None:
    """
    Connect to WebSocket, send multiple events, and listen for responses

    Args:
        ws_url: WebSocket URL to connect to
        connection_name: Name of the connection (for logging)
        send_events: List of events to send back-to-back
    """
    global network_ws_connection

    try:
        print(f"\n🔌 [{connection_name}] Attempting to connect to {ws_url}...")
        async with websockets.connect(ws_url, ping_interval=20, ping_timeout=10) as websocket:
            # Store connection reference
            network_ws_connection = websocket

            print(f"\n✅ [{connection_name}] WebSocket connected to {ws_url}")
            print(f"   Connection state: {websocket.state}")

            # Send events back-to-back if provided
            if send_events:
                print(
                    f"\n📤 [{connection_name}] Sending {len(send_events)} events...")
                for idx, event in enumerate(send_events, 1):
                    message = json.dumps(event)
                    await websocket.send(message)
                    print(
                        f"📤 [{connection_name}] Event {idx}/{len(send_events)} Sent:\n{json.dumps(event, indent=2)}")
                    await asyncio.sleep(0.1)  # Small delay between messages

            # Keep connection open and listen for events
            print(f"\n🔊 [{connection_name}] Listening for events...")
            message_count = 0
            try:
                while True:
                    try:
                        # Use timeout to periodically check connection and yield to event loop
                        message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                        message_count += 1
                        print(
                            f"\n📨 [{connection_name}] Raw message #{message_count} received (length: {len(message)} bytes)")

                        try:
                            event = json.loads(message)
                            print(f"   Parsed JSON successfully")
                            await handle_ws_event(event, connection_name)
                        except json.JSONDecodeError as e:
                            print(
                                f"⚠️  [{connection_name}] Received non-JSON message: {message[:200]}...")
                            print(f"   JSON decode error: {e}")
                        except Exception as e:
                            print(
                                f"⚠️  [{connection_name}] Error handling event: {e}")
                            import traceback
                            traceback.print_exc()

                    except asyncio.TimeoutError:
                        # Timeout is normal - just yield to event loop and continue
                        # This allows other tasks to run and keeps the connection alive
                        # Print heartbeat every 30 seconds to confirm listener is alive
                        if message_count == 0 and int(time.time()) % 30 == 0:
                            print(
                                f"💓 [{connection_name}] WebSocket listener alive, waiting for messages... (no messages received yet)")
                        await asyncio.sleep(0.1)
                        continue
                    except asyncio.CancelledError:
                        # Task was cancelled - break out of loop
                        print(
                            f"\n🛑 [{connection_name}] WebSocket listener cancelled")
                        raise  # Re-raise to be caught by outer handler
                    except websockets.exceptions.ConnectionClosed as e:
                        print(
                            f"\n⚠️  [{connection_name}] WebSocket connection closed: {e}")
                        break
                    except Exception as e:
                        print(
                            f"\n❌ [{connection_name}] Unexpected error receiving message: {e}")
                        import traceback
                        traceback.print_exc()
                        # Continue listening unless it's a fatal error
                        await asyncio.sleep(0.1)
                        continue

            except asyncio.CancelledError:
                print(
                    f"\n🛑 [{connection_name}] WebSocket listener task cancelled")
                raise  # Re-raise to allow proper cleanup
            except websockets.exceptions.ConnectionClosed as e:
                print(
                    f"\n⚠️  [{connection_name}] WebSocket connection closed: {e}")
            except Exception as e:
                print(f"\n❌ [{connection_name}] Error in message loop: {e}")
                import traceback
                traceback.print_exc()

    except websockets.exceptions.InvalidURI as e:
        print(f"❌ [{connection_name}] Invalid WebSocket URI: {e}")
        raise
    except websockets.exceptions.ConnectionClosed as e:
        print(f"❌ [{connection_name}] Connection closed during setup: {e}")
        raise
    except Exception as e:
        print(f"❌ [{connection_name}] WebSocket Error: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        network_ws_connection = None
        print(f"🔌 [{connection_name}] WebSocket connection closed and cleaned up")


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

        if response.status_code >= 400:
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
    Thread-safe version

    Args:
        tx_id: Transaction ID
        args: Random bytes arguments
    """
    # Record transaction start BEFORE making the API call
    # This ensures the transaction is registered before events can arrive
    args_hex = '0x' + args.hex()
    tx_id_hex = '0x' + tx_id.encode('utf-8').hex()

    # Thread-safe registration
    with transaction_events_lock:
        transaction_events[tx_id_hex] = {
            "status": "pending",
            "args": args,
            "args_hex": args_hex,
            "start_time": time.time(),
            "end_time": None,
            "elapsed_time": None,
            "event_data": None
        }

    print(f"📝 Registered transaction {tx_id_hex} with args {args_hex}")

    # Small yield to ensure registration is complete
    await asyncio.sleep(0.001)

    try:
        # Run the blocking API call in a thread pool to avoid blocking the event loop
        # This allows WebSocket events to be processed while waiting for the HTTP response
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, doCross, tx_id, args)
        print(f"✅ doCross API call successful for {tx_id}")
        # Yield to event loop to allow WebSocket events to be processed
        await asyncio.sleep(0)
    except Exception as e:
        print(f"⚠️  Error in doCross for {tx_id}: {e}")
        with transaction_events_lock:
            if tx_id_hex in transaction_events:
                transaction_events[tx_id_hex]["status"] = "failed"


async def run_benchmark(num_transactions: int):
    """
    Run benchmark until we get num_transactions completed transactions.
    Sends 20% more transactions to account for event drop rate.

    Args:
        num_transactions: Target number of completed transactions needed
    """
    global benchmark_start_time, transaction_events, events_received_count, last_event_time, ws_thread

    # Thread-safe initialization
    with transaction_events_lock:
        transaction_events.clear()
    with events_received_count_lock:
        events_received_count = 0
    with last_event_time_lock:
        last_event_time = time.time()
    benchmark_start_time = time.time()

    # Calculate transactions to send (20% more to account for drop rate)
    transactions_to_send = int(num_transactions * 1.25)

    print(f"\n\n{'='*80}")
    print(
        f"🚀 Starting Benchmark")
    print(f"  Target Completed: {num_transactions} transactions")
    print(
        f"  Sending: {transactions_to_send} transactions (20% extra for drop rate)")
    print(f"{'='*80}")
    print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Create tasks for all transactions
    tasks = []
    sent_count = 0
    pending_timeout = 10  # seconds
    event_silence_timeout = 180  # If no events for 180s, consider connection stalled

    while sent_count < transactions_to_send:
        tx_id = generate_random_tx_id()
        args = generate_random_args()
        task = asyncio.create_task(run_transaction(tx_id, args))
        tasks.append(task)
        sent_count += 1

        print(f"📤 Sent transaction {sent_count}/{transactions_to_send}")

        # Small delay between API calls
        await asyncio.sleep(0.1)

    # Wait for all API calls to complete
    await asyncio.gather(*tasks)

    # Monitor pending transactions and mark as failed if they exceed timeout
    print(f"\n⏳ Waiting for transactions to complete...")
    print(f"   Registered {len(transaction_events)} transactions")
    start_wait = time.time()
    overall_timeout = 6000  # 10 minutes total timeout
    check_interval = 1
    last_status_print = 0

    while True:
        # Thread-safe access to transaction_events
        with transaction_events_lock:
            completed = [tx for tx in transaction_events.values()
                         if tx["status"] == "completed"]
            pending = [tx for tx in transaction_events.values()
                       if tx["status"] == "pending"]

        # Check if we've reached target completed transactions
        if len(completed) >= num_transactions:
            print(
                f"\n✅ Reached target! {len(completed)} transactions completed (target was {num_transactions}).")
            break

        elapsed_overall = time.time() - start_wait

        # Check for event silence (no new events arriving) - thread-safe
        current_time = time.time()
        with last_event_time_lock:
            time_since_last_event = current_time - last_event_time

        if time_since_last_event > event_silence_timeout and pending:
            print(
                f"\n⚠️  No events received for {event_silence_timeout}s. {len(pending)} transactions still pending.")
            print(f"   Events received so far: {events_received_count}")
            print(f"   Expected: {num_transactions}, Got: {len(completed)}")
            print(
                f"   Marking {len(pending)} pending transactions as timeout...")

            # Mark all remaining pending as timeout (thread-safe)
            with transaction_events_lock:
                for tx_id, tx_info in list(transaction_events.items()):
                    if tx_info["status"] == "pending":
                        tx_info["status"] = "timeout"
                        tx_info["end_time"] = current_time
                        tx_info["elapsed_time"] = current_time - \
                            tx_info.get("start_time", benchmark_start_time)
            break

        if elapsed_overall > overall_timeout:
            print(
                f"⚠️  Overall timeout reached. {len(completed)} completed, {len(pending)} still pending.")
            # Mark all remaining pending as timeout (thread-safe)
            with transaction_events_lock:
                for tx_id, tx_info in list(transaction_events.items()):
                    if tx_info["status"] == "pending":
                        tx_info["status"] = "timeout"
                        tx_info["end_time"] = current_time
                        tx_info["elapsed_time"] = current_time - \
                            tx_info.get("start_time", benchmark_start_time)
            break

        # Check for transactions that have been pending for too long (thread-safe)
        timeout_count = 0
        with transaction_events_lock:
            for tx_id, tx_info in list(transaction_events.items()):
                if tx_info["status"] == "pending":
                    elapsed_since_start = current_time - \
                        tx_info.get("start_time", benchmark_start_time)

                    if elapsed_since_start > pending_timeout:
                        timeout_count += 1
                        tx_info["status"] = "timeout"
                        tx_info["end_time"] = current_time
                        tx_info["elapsed_time"] = elapsed_since_start

        # Only print timeout message once per batch to avoid spam
        if timeout_count > 0:
            print(
                f"⏱️  {timeout_count} transaction(s) exceeded {pending_timeout}s timeout. Marking as timeout...")
            # Print diagnostic info
            with events_received_count_lock:
                events_count = events_received_count
            with last_event_time_lock:
                time_since_last = current_time - last_event_time
            print(
                f"   📊 Status: {len(completed)} completed, {len(pending)} pending, {events_count} events received")
            print(f"   ⏰ Last event received: {time_since_last:.1f}s ago")
            if ws_thread and not ws_thread.is_alive():
                print(f"   ⚠️  WARNING: WebSocket thread is not running!")

        # Print periodic status updates every 10 seconds
        if int(elapsed_overall) != last_status_print and int(elapsed_overall) % 10 == 0:
            last_status_print = int(elapsed_overall)
            with events_received_count_lock:
                events_count = events_received_count
            with last_event_time_lock:
                time_since_last = current_time - last_event_time
            print(f"\n📊 Progress Update (after {elapsed_overall:.0f}s):")
            print(f"   Completed: {len(completed)}/{num_transactions}")
            print(f"   Pending: {len(pending)}")
            print(f"   Events Received: {events_count}")
            print(f"   Last Event: {time_since_last:.1f}s ago")
            if ws_thread:
                print(f"   WebSocket Thread Alive: {ws_thread.is_alive()}")
                if not ws_thread.is_alive():
                    print(
                        f"   ⚠️  WARNING: WebSocket thread died! Events will not be received.")
            # Show sample of pending transactions
            if pending:
                print(
                    f"   Sample pending transactions: {[tx_id[:20] + '...' if len(tx_id) > 20 else tx_id for tx_id in list(transaction_events.keys())[:3] if transaction_events[tx_id].get('status') == 'pending']}")

        await asyncio.sleep(check_interval)

    benchmark_end_time = time.time()
    total_time = benchmark_end_time - benchmark_start_time

    # Print results
    print(f"\n\n{'='*80}")
    print(
        f"📊 Benchmark Results - Target: {num_transactions} Completed Transactions")
    print(f"{'='*80}")
    print(f"Total Time: {total_time:.4f}s")
    print(f"End Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Thread-safe access for final summary
    with transaction_events_lock:
        completed = [tx for tx in transaction_events.values()
                     if tx["status"] == "completed"]
        failed = [tx for tx in transaction_events.values() if tx["status"]
                  == "failed"]
        timeout = [tx for tx in transaction_events.values() if tx["status"]
                   == "timeout"]
        pending = [tx for tx in transaction_events.values() if tx["status"]
                   == "pending"]

    with events_received_count_lock:
        events_count = events_received_count

    print(f"\n📊 Summary:")
    print(f"  Target Completed: {num_transactions} ✅")
    print(f"  Actually Completed: {len(completed)}/{num_transactions}")
    print(f"  Failed: {len(failed)}")
    print(f"  Timeout: {len(timeout)}")
    print(f"  Pending: {len(pending)}")
    print(f"  Total Sent: {sent_count}")
    print(f"  Events Received: {events_count}")
    if sent_count > 0:
        print(
            f"  Event Loss Rate: {((sent_count - len(completed)) / sent_count * 100):.2f}%")

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

    # Print individual transaction details (only completed ones) - thread-safe
    print(f"\n📋 Completed Transactions:")
    with transaction_events_lock:
        for tx_id, tx_info in sorted(transaction_events.items()):
            if tx_info["status"] == "completed":
                elapsed = tx_info.get("elapsed_time")
                print(
                    f"  {tx_id}: {elapsed:.4f}s - Args: {tx_info['args'].hex()}")

    print(f"\n{'='*80}\n")


def ws_listener_thread(ws_url: str, connection_name: str, send_events: Optional[list] = None):
    """
    Run WebSocket listener in a separate thread with its own event loop.
    This ensures the WebSocket listener is completely isolated from API calls.

    Args:
        ws_url: WebSocket URL to connect to
        connection_name: Name of the connection
        send_events: List of events to send
    """
    # Create a new event loop for this thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        print(f"\n🧵 [{connection_name}] WebSocket listener thread started")
        # Run the WebSocket listener in this thread's event loop
        loop.run_until_complete(ws_listen_and_send(
            ws_url, connection_name, send_events))
    except Exception as e:
        print(f"❌ [{connection_name}] Error in WebSocket thread: {e}")
        import traceback
        traceback.print_exc()
    finally:
        loop.close()
        print(f"🧵 [{connection_name}] WebSocket listener thread ended")


async def main():
    """Main execution with Network WebSocket listener in separate thread"""

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
    print("🚀 Starting WebSocket connection in separate thread...")
    print("="*80)

    # Start WebSocket listener in a separate thread (completely isolated)
    global ws_thread
    ws_thread = threading.Thread(
        target=ws_listener_thread,
        args=(NETWORK_WS_URL, "Network", network_events),
        daemon=True,  # Thread will exit when main program exits
        name="WebSocketListener"
    )
    ws_thread.start()
    print("✅ WebSocket listener thread started")

    # Give WebSocket time to connect and verify connection
    print("\n⏳ Waiting for WebSocket to connect...")
    for i in range(30):  # Wait up to 3 seconds
        await asyncio.sleep(0.1)
        if network_ws_connection is not None:
            print("✅ WebSocket connection verified!")
            break
    else:
        print("⚠️  Warning: WebSocket connection not established after 3 seconds")
        print("   Continuing anyway, but events may not be received...")

    # Run benchmark - API calls won't block WebSocket listener since it's in a separate thread
    await run_benchmark(2500)

    # Cleanup - signal thread to stop
    print("🛑 Shutting down...")
    ws_thread_stop_event.set()

    # Wait for thread to finish (with timeout)
    if ws_thread.is_alive():
        print("⏳ Waiting for WebSocket thread to finish...")
        ws_thread.join(timeout=5.0)
        if ws_thread.is_alive():
            print("⚠️  WebSocket thread did not finish in time")
        else:
            print("✅ WebSocket thread finished cleanly")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Application closed")
