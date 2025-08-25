#!/usr/bin/env python3
"""
Debug script to test hardware access step by step
"""
import os
import sys

print("=== Hardware Detection Debug ===")
print(f"Python executable: {sys.executable}")
print(f"Current working directory: {os.getcwd()}")
print(f"BLINKA_MCP2221 environment variable: {os.environ.get('BLINKA_MCP2221', 'NOT SET')}")

# Set environment variable 
os.environ["BLINKA_MCP2221"] = "1"
print(f"Set BLINKA_MCP2221 to: {os.environ.get('BLINKA_MCP2221')}")

print("\n=== Step 1: Test basic imports ===")
try:
    import board
    print("✓ Successfully imported 'board'")
except ImportError as e:
    print(f"✗ Failed to import 'board': {e}")
    sys.exit(1)

try:
    import adafruit_vcnl4010
    print("✓ Successfully imported 'adafruit_vcnl4010'")
except ImportError as e:
    print(f"✗ Failed to import 'adafruit_vcnl4010': {e}")
    sys.exit(1)

print("\n=== Step 2: Test I2C initialization ===")
try:
    i2c = board.I2C()
    print("✓ Successfully created I2C object")
    print(f"I2C object: {i2c}")
except Exception as e:
    print(f"✗ Failed to create I2C object: {e}")
    print(f"Exception type: {type(e)}")
    sys.exit(1)

print("\n=== Step 3: Test sensor initialization ===")
try:
    sensor = adafruit_vcnl4010.VCNL4010(i2c)
    print("✓ Successfully created VCNL4010 sensor object")
    print(f"Sensor object: {sensor}")
except Exception as e:
    print(f"✗ Failed to create VCNL4010 sensor: {e}")
    print(f"Exception type: {type(e)}")
    sys.exit(1)

print("\n=== Step 4: Test sensor reading ===")
try:
    reading = sensor.proximity
    print(f"✓ Successfully read proximity value: {reading}")
except Exception as e:
    print(f"✗ Failed to read proximity: {e}")
    print(f"Exception type: {type(e)}")
    sys.exit(1)

print("\n=== All tests passed! Hardware is working correctly ===")
