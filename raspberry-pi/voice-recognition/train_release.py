import serial
import time

PORT = "/dev/serial0"
BAUD = 9600

# Train record 1
TRAIN_RECORD_1 = bytes([0xAA, 0x03, 0x20, 0x01, 0x0A])


def readable_text(data: bytes) -> str:
    return "".join(
        chr(byte) if 32 <= byte <= 126 else " "
        for byte in data
    ).strip()


with serial.Serial(PORT, BAUD, timeout=0.2) as voice:
    voice.reset_input_buffer()

    print("Training record 1 as: RELEASE")
    print("Be ready to say RELEASE twice.")
    print("Say it immediately after each prompt.")
    print("Press Ctrl+C to stop.\n")

    voice.write(TRAIN_RECORD_1)
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
                print("Record 1 = RELEASE")
                break

            if "speak now" in text.lower():
                print("\n>>> SAY RELEASE NOW <<<")

            if "speak again" in text.lower():
                print("\n>>> SAY RELEASE AGAIN NOW <<<")

            if "can't matched" in lower_text or "cann't matched" in lower_text:
                print("\nThe two recordings did not match. Try again.")

            if "too noisy" in lower_text:
                print("\nToo noisy. Keep the microphone still.")

        else:
            print("\nTraining timed out. Run the script again.")

    except KeyboardInterrupt:
        print("\nTraining stopped.")
