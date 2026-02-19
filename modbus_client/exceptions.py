"""
Custom exceptions for modbus_client.
"""


class ModbusClientError(Exception):
    """Base exception for all modbus_client errors."""
    pass


class ModbusConnectionError(ModbusClientError):
    """Raised when a connection to the slave device cannot be established."""
    pass


class ModbusResponseError(ModbusClientError):
    """Raised when the slave device returns an error or unexpected response."""
    pass
