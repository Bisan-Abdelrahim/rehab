import serial
import time

PORT = "/dev/serial0"
BAUD = 9600

CLEAR_RECOGNIZER = bytes([
    0xAA,
    0x02,
    0x31,
    0x0A
])

# Load records 0, 1, 2, and 3
LOAD_RECORDS = bytes([
    0xAA,
    0x06,
    0x30,
    0x00,
    0x01,
    0x02,
    0x03,
    0x0A
])

COMMANDS = {
    0: "OPEN",
    1: "RELEASE",
    2: "OPEN",
    3: "RELEASE",
}


def read_response(
    voice: serial.Serial,
    wait_seconds: float = 0.6
) -> bytes:
    time.sleep(wait_seconds)
    response = bytearray()

    while voice.in_waiting:
        response.extend(
            voice.read(voice.in_waiting)
        )
        time.sleep(0.05)

    return bytes(response)


def print_response(
    label: str,
    response: bytes
) -> None:
    if response:
        print(
            f"{label} HEX:",
            response.hex(" ")
        )
    else:
        print(f"{label}: No response")


def get_frame(
    voice: serial.Serial,
    buffer: bytearray
) -> bytes | None:
    new_data = voice.read(voice.in_waiting or 1)

    if new_data:
        buffer.extend(new_data)

    # Remove bytes before the AA header.
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


try:
    with serial.Serial(
        PORT,
        BAUD,
        timeout=0.1
    ) as voice:
        voice.reset_input_buffer()

        print("Clearing recognizer...")

        voice.write(CLEAR_RECOGNIZER)
        voice.flush()

        clear_response = read_response(voice)
        print_response(
            "CLEAR",
            clear_response
        )

        print(
            "\nLoading records 0, 1, 2, and 3..."
        )

        voice.write(LOAD_RECORDS)
        voice.flush()

        load_response = read_response(voice)
        print_response(
            "LOAD",
            load_response
        )

        if not load_response:
            print(
                "\nThe module did not respond."
            )
            print(
                "Restart the Raspberry Pi and "
                "run the script again."
            )
            raise SystemExit(1)

        print("\nRecognition is active ✅")
        print("Record 0 = OPEN version 1")
        print("Record 1 = RELEASE version 1")
        print("Record 2 = OPEN version 2")
        print("Record 3 = RELEASE version 2")
        print("\nSay OPEN or RELEASE.")
        print("Press Ctrl+C to stop.\n")

        buffer = bytearray()

        while True:
            frame = get_frame(
                voice,
                buffer
            )

            if frame is None:
                continue

            print(
                "RECEIVED:",
                frame.hex(" ")
            )

            # Recognition result frame
            if (
                len(frame) >= 8
                and frame[2] == 0x0D
            ):
                record_number = frame[5]
                recognizer_index = frame[6]

                command = COMMANDS.get(
                    record_number
                )

                if command is None:
                    print(
                        "Unknown record:",
                        record_number,
                        "\n"
                    )
                    continue

                print(
                    "\n"
                    "============================"
                )
                print(
                    f"Recognized command: "
                    f"{command} ✅"
                )
                print(
                    f"Matched record: "
                    f"{record_number}"
                )
                print(
                    f"Recognizer slot: "
                    f"{recognizer_index}"
                )
                print(
                    "============================"
                    "\n"
                )

except KeyboardInterrupt:
    print("\nRecognition stopped.")

except serial.SerialException as error:
    print(
        "\nSerial communication error:",
        error
    )
