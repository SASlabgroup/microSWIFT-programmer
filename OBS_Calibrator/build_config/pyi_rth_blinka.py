"""
Runtime hook for PyInstaller to set BLINKA_MCP2221 environment variable
This ensures the variable is set when the bundled app starts
"""
import os

# Set the BLINKA_MCP2221 environment variable for MCP2221 support
os.environ["BLINKA_MCP2221"] = "1"
print("Runtime hook: Set BLINKA_MCP2221=1")
