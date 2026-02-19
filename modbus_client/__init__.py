"""
modbus_client - A simple Modbus TCP read/write package for networked slave devices.
"""

from .client import ModbusClient
from .exceptions import ModbusClientError, ModbusConnectionError, ModbusResponseError

__version__ = "1.0.0"
__all__ = ["ModbusClient", "ModbusClientError", "ModbusConnectionError", "ModbusResponseError"]
