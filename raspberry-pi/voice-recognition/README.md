# Raspberry Pi Voice Recognition

This folder contains the Raspberry Pi scripts used with the Elechouse Voice Recognition Module V3.

## Hardware Connection

- Voice Recognition Module V3
- Raspberry Pi 4
- 5V to 3.3V bidirectional logic level converter
- UART communication through `/dev/serial0`

## Scripts

- `check_voice_module.py`  
  Checks UART communication with the voice recognition module.

- `train_voice_command.py`  
  Trains a voice command and stores it in record 0.

- `test_voice_recognition.py`  
  Loads record 0 and waits for a recognized voice command.

## Tested Command

- Record 0: `OPEN`

## Current Status

The module was successfully connected, trained, and tested with the Raspberry Pi.
