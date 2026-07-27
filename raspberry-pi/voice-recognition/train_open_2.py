import serial
import time

PORT = "/dev/serial0"
BAUD = 9600

RECORD_NUMBER = 2
COMMAND_NAME = "OPEN"

TRAIN_COMMAND = bytes([
    0xAA,
    0x03,
    0x20,
    RECORD_NUMBER,
    0x0A
])


def extract_text(frame: bytes) -> str:
    return "".join(
        chr(byte) if 32 <= byte <= 126 else " "
        for byte in frame
    ).strip()


def read_frame(voice: serial.Serial, buffer: bytearray):
    while True:
        new_byte = voice.read(1)

        if new_byte:
            buffer.extend(new_byte)

        # Remove anything before the frame header.
        while buffer and buffer[0] != 0xAA:
            buffer.pop(0)

        if len(buffer) < 2:
            continue

        # In this module, total frame size = length byte + 2.
        total_size = buffer[1] + 2

        if len(buffer) < total_size:
            continue

        frame = bytes(buffer[:total_size])
        del buffer[:total_size]

        return frame


with serial.Serial(PORT, BAUD, timeout=0.1) as voice:
    voice.reset_input_buffer()

    print(f"Training record {RECORD_NUMBER} as another version of {COMMAND_NAME}")
    print("Keep the microphone still and stay ready to repeat immediately.")
    print("Press Ctrl+C to stop.\n")

    voice.write(TRAIN_COMMAND)
    voice.flush()

    buffer = bytearray()
    end_time = time.time() + 90

    try:
        while time.time() < end_time:
            frame = read_frame(voice, buffer)
            text = extract_text(frame)
            lower_text = text.lower()

            print("HEX :", frame.hex(" "))

            if text:
                print("TEXT:", text)

            if "speak now" in lower_text:
                print(f"\n>>> SAY {COMMAND_NAME} NOW <<<\n")

            elif "speak again" in lower_text:
                print(f"\n>>> REPEAT {COMMAND_NAME} IMMEDIATELY <<<\n")

            elif "success" in lower_text:
                print("\nTraining succeeded ✅")
                print(f"Record {RECORD_NUMBER} = {COMMAND_NAME}")
                break

            elif "matched" in lower_text:
                print("\nThe two recordings did not match.")
                print("Wait for the next Speak now prompt.\n")

            elif "too noisy" in lower_text:
                print("\nToo noisy.")
                print("Keep the microphone still and move to a quieter place.\n")

        else:
            print("\nTraining timed out. Run the script again.")

    except KeyboardInterrupt:
        print("\nTraining stopped.")
