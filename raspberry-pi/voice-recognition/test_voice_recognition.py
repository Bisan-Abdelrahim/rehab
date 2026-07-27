import serial
import time

PORT = "/dev/serial0"
BAUD = 9600

CLEAR_RECOGNIZER = bytes([0xAA, 0x02, 0x31, 0x0A])
LOAD_RECORD_0 = bytes([0xAA, 0x03, 0x30, 0x00, 0x0A])


def read_available(voice, wait_seconds=0.5):
    time.sleep(wait_seconds)
    data = bytearray()

    while voice.in_waiting:
        data.extend(voice.read(voice.in_waiting))
        time.sleep(0.05)

    return bytes(data)


def print_packet(label, data):
    if data:
        print(f"{label} HEX:", data.hex(" "))
    else:
        print(f"{label}: No response")


with serial.Serial(PORT, BAUD, timeout=0.1) as voice:
    voice.reset_input_buffer()

    # Remove any previously loaded commands
    print("Clearing recognizer...")
    voice.write(CLEAR_RECOGNIZER)
    voice.flush()

    clear_response = read_available(voice)
    print_packet("CLEAR", clear_response)

    # Load trained record 0
    print("\nLoading trained record 0...")
    voice.write(LOAD_RECORD_0)
    voice.flush()

    load_response = read_available(voice)
    print_packet("LOAD", load_response)

    if bytes([0x00, 0xFE]) in load_response:
        print("Record 0 is not trained.")
        raise SystemExit

    if bytes([0x00, 0x00]) not in load_response:
        print("Record 0 was not loaded successfully.")
        raise SystemExit

    print("\nRecognizer is active ✅")
    print("Say the EXACT word used during training.")
    print("Watch the module LEDs while speaking.")
    print("Press Ctrl+C to stop.\n")

    buffer = bytearray()

    try:
        while True:
            byte = voice.read(1)

            if not byte:
                continue

            buffer.extend(byte)

            # Remove anything before frame header AA
            while buffer and buffer[0] != 0xAA:
                buffer.pop(0)

            if len(buffer) < 2:
                continue

            frame_length = buffer[1]
            total_length = frame_length + 2

            if len(buffer) < total_length:
                continue

            frame = bytes(buffer[:total_length])
            del buffer[:total_length]

            print("RECEIVED:", frame.hex(" "))

            if len(frame) >= 8 and frame[2] == 0x0D:
                group_mode = frame[4]
                record_number = frame[5]
                recognizer_index = frame[6]

                print("\n==============================")
                print("VOICE RECOGNIZED ✅")
                print("Command: OPEN")
                print("Record:", record_number)
                print("Recognizer index:", recognizer_index)
                print("==============================\n")

    except KeyboardInterrupt:
        print("\nRecognition stopped.")
