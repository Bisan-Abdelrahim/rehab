import serial
import time

PORT = "/dev/serial0"
BAUD = 9600

CLEAR_RECOGNIZER = bytes([0xAA, 0x02, 0x31, 0x0A])

# Load record 0 and record 2
LOAD_RECORDS = bytes([
    0xAA,
    0x04,
    0x30,
    0x00,
    0x02,
    0x0A
])

OPEN_RECORDS = {0, 2}


def read_response(voice, wait_seconds=0.5):
    time.sleep(wait_seconds)
    data = bytearray()

    while voice.in_waiting:
        data.extend(voice.read(voice.in_waiting))
        time.sleep(0.05)

    return bytes(data)


with serial.Serial(PORT, BAUD, timeout=0.1) as voice:
    voice.reset_input_buffer()

    print("Clearing recognizer...")
    voice.write(CLEAR_RECOGNIZER)
    voice.flush()

    clear_response = read_response(voice)
    print(
        "CLEAR HEX:",
        clear_response.hex(" ") if clear_response else "No response"
    )

    print("\nLoading OPEN records 0 and 2...")
    voice.write(LOAD_RECORDS)
    voice.flush()

    load_response = read_response(voice)
    print(
        "LOAD HEX:",
        load_response.hex(" ") if load_response else "No response"
    )

    print("\nRecognition is active ✅")
    print("Record 0 = OPEN version 1")
    print("Record 2 = OPEN version 2")
    print("Say OPEN in a natural way.")
    print("Press Ctrl+C to stop.\n")

    buffer = bytearray()

    try:
        while True:
            new_byte = voice.read(1)

            if not new_byte:
                continue

            buffer.extend(new_byte)

            while buffer and buffer[0] != 0xAA:
                buffer.pop(0)

            if len(buffer) < 2:
                continue

            total_size = buffer[1] + 2

            if len(buffer) < total_size:
                continue

            frame = bytes(buffer[:total_size])
            del buffer[:total_size]

            print("RECEIVED:", frame.hex(" "))

            if len(frame) >= 8 and frame[2] == 0x0D:
                record_number = frame[5]

                if record_number in OPEN_RECORDS:
                    print(
                        f"Recognized command: OPEN ✅ "
                        f"(matched record {record_number})\n"
                    )
                else:
                    print(f"Unknown record: {record_number}\n")

    except KeyboardInterrupt:
        print("\nRecognition stopped.")
