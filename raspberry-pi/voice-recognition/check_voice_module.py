import serial
import time

PORT = "/dev/serial0"
BAUD_RATE = 9600

# VR3 frame:
# AA 02 01 0A = Check system settings
CHECK_SYSTEM_COMMAND = bytes([0xAA, 0x02, 0x01, 0x0A])

try:
    with serial.Serial(PORT, BAUD_RATE, timeout=2) as voice:
        print(f"Opened {PORT} at {BAUD_RATE} baud")

        # Remove any old bytes waiting in the buffer.
        voice.reset_input_buffer()

        print("Sending check-system command...")
        voice.write(CHECK_SYSTEM_COMMAND)
        voice.flush()

        time.sleep(0.5)
        response = voice.read(64)

        if response:
            print("Module replied ✅")
            print("HEX:", response.hex(" "))
            print("RAW:", response)
        else:
            print("No response received ❌")
            print("Check TX/RX direction, power, converter wiring, and common GND.")

except serial.SerialException as error:
    print("Serial error:", error)
