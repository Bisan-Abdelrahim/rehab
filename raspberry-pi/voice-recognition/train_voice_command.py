import serial
import time

PORT = "/dev/serial0"
BAUD = 9600

# Train record 0.
TRAIN_RECORD_0 = bytes([0xAA, 0x03, 0x20, 0x00, 0x0A])

def readable_text(data: bytes) -> str:
    return "".join(
        chr(byte) if 32 <= byte <= 126 else " "
        for byte in data
    ).strip()

with serial.Serial(PORT, BAUD, timeout=0.2) as voice:
    voice.reset_input_buffer()

    print("Training record 0 as: OPEN")
    print("Wait for 'Speak now', then say OPEN.")
    print("When it says 'Speak again', repeat OPEN the same way.")
    print("Press Ctrl+C to stop.\n")

    voice.write(TRAIN_RECORD_0)
    voice.flush()

    end_time = time.time() + 60
    received = bytearray()

    try:
        while time.time() < end_time:
            data = voice.read(64)

            if not data:
                continue

            received.extend(data)

            print("HEX :", data.hex(" "))
            text = readable_text(data)

            if text:
                print("TEXT:", text)

            lower_text = readable_text(received).lower()

            if "success" in lower_text:
                print("\nTraining succeeded ✅")
                break

            if "again" in lower_text:
                print("\nRepeat the word OPEN now.")

        else:
            print("\nTraining timed out. Run the script again.")

    except KeyboardInterrupt:
        print("\nTraining stopped.")
