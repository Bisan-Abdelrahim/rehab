import asyncio
import json
import time

import serial
import websockets


SERIAL_PORT = "/dev/serial0"
BAUD_RATE = 9600

WEBSOCKET_HOST = "0.0.0.0"
WEBSOCKET_PORT = 8765

CLEAR_RECOGNIZER = bytes([
    0xAA,
    0x02,
    0x31,
    0x0A,
])

# Loaded voice records:
# 0 = OPEN version 1
# 1 = RELEASE version 1
# 2 = OPEN version 2
# 3 = RELEASE version 2
LOAD_RECORDS = bytes([
    0xAA,
    0x06,
    0x30,
    0x00,
    0x01,
    0x02,
    0x03,
    0x0A,
])

RECORD_COMMANDS = {
    0: "open",
    1: "release",
    2: "open",
    3: "release",
}

connected_clients = set()


def read_module_response(
    voice: serial.Serial,
    wait_seconds: float = 0.6,
) -> bytes:
    time.sleep(wait_seconds)
    response = bytearray()

    while voice.in_waiting:
        response.extend(
            voice.read(voice.in_waiting)
        )
        time.sleep(0.05)

    return bytes(response)


def read_serial_frame(
    voice: serial.Serial,
    buffer: bytearray,
) -> bytes | None:
    new_data = voice.read(
        voice.in_waiting or 1
    )

    if new_data:
        buffer.extend(new_data)

    while buffer and buffer[0] != 0xAA:
        buffer.pop(0)

    if len(buffer) < 2:
        return None

    total_size = buffer[1] + 2

    if len(buffer) < total_size:
        return None

    frame = bytes(buffer[:total_size])
    del buffer[:total_size]

    return frame


async def send_to_all_clients(
    message: dict,
) -> None:
    if not connected_clients:
        print("No website is currently connected.")
        return

    encoded_message = json.dumps(message)

    disconnected_clients = []

    for client in connected_clients:
        try:
            await client.send(encoded_message)
        except Exception:
            disconnected_clients.append(client)

    for client in disconnected_clients:
        connected_clients.discard(client)


async def websocket_handler(
    websocket,
    path=None,
) -> None:
    connected_clients.add(websocket)

    print(
        "Website connected. "
        f"Active clients: {len(connected_clients)}"
    )

    await websocket.send(
        json.dumps({
            "type": "connection",
            "source": "raspberry-pi",
            "status": "connected",
        })
    )

    try:
        async for message in websocket:
            print("Website message:", message)

    except websockets.ConnectionClosed:
        pass

    finally:
        connected_clients.discard(websocket)

        print(
            "Website disconnected. "
            f"Active clients: {len(connected_clients)}"
        )


async def monitor_voice_module() -> None:
    try:
        with serial.Serial(
            SERIAL_PORT,
            BAUD_RATE,
            timeout=0.1,
        ) as voice:
            voice.reset_input_buffer()

            print("Clearing voice recognizer...")

            voice.write(CLEAR_RECOGNIZER)
            voice.flush()

            clear_response = read_module_response(
                voice
            )

            print(
                "CLEAR:",
                clear_response.hex(" ")
                if clear_response
                else "No response",
            )

            print(
                "Loading OPEN and RELEASE records..."
            )

            voice.write(LOAD_RECORDS)
            voice.flush()

            load_response = read_module_response(
                voice
            )

            print(
                "LOAD:",
                load_response.hex(" ")
                if load_response
                else "No response",
            )

            if not load_response:
                raise RuntimeError(
                    "Voice module did not respond."
                )

            print("\nVoice recognition is active.")
            print("OPEN    → website open position")
            print("RELEASE → website release position")
            print()

            buffer = bytearray()

            while True:
                frame = await asyncio.to_thread(
                    read_serial_frame,
                    voice,
                    buffer,
                )

                if frame is None:
                    await asyncio.sleep(0.01)
                    continue

                print(
                    "RECEIVED:",
                    frame.hex(" "),
                )

                if (
                    len(frame) >= 8
                    and frame[2] == 0x0D
                ):
                    record_number = frame[5]

                    command = RECORD_COMMANDS.get(
                        record_number
                    )

                    if command is None:
                        print(
                            "Unknown record:",
                            record_number,
                        )
                        continue

                    message = {
                        "type": "voice-command",
                        "source": "voice",
                        "command": command,
                        "recognizedText": command.upper(),
                        "record": record_number,
                        "timestamp": time.strftime(
                            "%Y-%m-%dT%H:%M:%S"
                        ),
                    }

                    print(
                        f"Recognized: {command.upper()} "
                        f"(record {record_number})"
                    )

                    await send_to_all_clients(
                        message
                    )

    except serial.SerialException as error:
        print(
            "Serial communication error:",
            error,
        )

    except Exception as error:
        print(
            "Voice monitor error:",
            error,
        )


async def main() -> None:
    print(
        "Starting WebSocket server at "
        f"ws://{WEBSOCKET_HOST}:"
        f"{WEBSOCKET_PORT}"
    )

    async with websockets.serve(
        websocket_handler,
        WEBSOCKET_HOST,
        WEBSOCKET_PORT,
    ):
        await monitor_voice_module()


if __name__ == "__main__":
    try:
        asyncio.run(main())

    except KeyboardInterrupt:
        print("\nServer stopped.")
