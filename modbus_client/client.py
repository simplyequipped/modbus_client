"""
Core ModbusClient class for reading and writing Modbus registers over TCP.

Each method opens a fresh connection, performs the transaction, then closes it.

Holding and input registers are returned as signed 16-bit integers (-32768 to 32767)
by default, matching devices that use two's complement encoding. Pass signed=False
to get raw unsigned values (0 to 65535) if your device needs that instead.

Coil values are returned/accepted as booleans (True/False or 1/0).
"""

from pymodbus.client import ModbusTcpClient
from pymodbus.exceptions import ModbusException

from .exceptions import ModbusConnectionError, ModbusResponseError


class ModbusClient:
    """
    A simple Modbus TCP client.

    Each read/write method opens a connection, performs the transaction,
    and closes the connection before returning.

    Args:
        host (str): IP address or hostname of the Modbus slave device.
        port (int): TCP port number. Default is 502.
        unit_id (int): Slave unit ID (also called device address). Default is 1.
        timeout (float): Seconds to wait for a connection or response. Default is 3.
    """

    def __init__(self, host: str, port: int = 502, unit_id: int = 1, timeout: float = 3.0):
        self.host = host
        self.port = port
        self.unit_id = unit_id
        self.timeout = timeout

    def _connect(self) -> ModbusTcpClient:
        """Open a TCP connection and return the client. Raises on failure."""
        client = ModbusTcpClient(self.host, port=self.port, timeout=self.timeout)
        if not client.connect():
            raise ModbusConnectionError(
                f"Could not connect to Modbus device at {self.host}:{self.port}"
            )
        return client

    @staticmethod
    def _to_signed(value: int) -> int:
        """Convert a 16-bit unsigned integer to signed (-32768 to 32767) via two's complement."""
        return value if value < 32768 else value - 65536

    @staticmethod
    def _to_unsigned(value: int) -> int:
        """Convert a signed integer to 16-bit unsigned via two's complement. e.g. -1 -> 65535"""
        return value & 0xFFFF

    # -------------------------------------------------------------------------
    # READ METHODS
    # -------------------------------------------------------------------------

    def read_holding_registers(self, address: int, count: int = 1, signed: bool = True) -> list[int]:
        """
        Read one or more holding registers (Function Code 03).

        Args:
            address (int): Starting register address (0-based).
            count (int): Number of consecutive registers to read. Default is 1.
            signed (bool): If True (default), return signed 16-bit integers (-32768 to 32767).
                           If False, return raw unsigned values (0 to 65535).

        Returns:
            list[int]: List of integer values.

        Raises:
            ModbusConnectionError: If the device cannot be reached.
            ModbusResponseError: If the device returns an error response.
        """
        client = self._connect()
        try:
            result = client.read_holding_registers(address, count=count, slave=self.unit_id)
            if result.isError():
                raise ModbusResponseError(
                    f"Device returned an error reading holding registers at address {address}: {result}"
                )
            values = list(result.registers)
            if signed:
                values = [self._to_signed(v) for v in values]
            return values
        except ModbusException as e:
            raise ModbusResponseError(f"Modbus exception reading holding registers: {e}") from e
        finally:
            client.close()

    def read_input_registers(self, address: int, count: int = 1, signed: bool = True) -> list[int]:
        """
        Read one or more input registers (Function Code 04).

        Args:
            address (int): Starting register address (0-based).
            count (int): Number of consecutive registers to read. Default is 1.
            signed (bool): If True (default), return signed 16-bit integers (-32768 to 32767).
                           If False, return raw unsigned values (0 to 65535).

        Returns:
            list[int]: List of integer values.
        """
        client = self._connect()
        try:
            result = client.read_input_registers(address, count=count, slave=self.unit_id)
            if result.isError():
                raise ModbusResponseError(
                    f"Device returned an error reading input registers at address {address}: {result}"
                )
            values = list(result.registers)
            if signed:
                values = [self._to_signed(v) for v in values]
            return values
        except ModbusException as e:
            raise ModbusResponseError(f"Modbus exception reading input registers: {e}") from e
        finally:
            client.close()

    def read_coils(self, address: int, count: int = 1) -> list[bool]:
        """Read one or more coils (Function Code 01)."""
        client = self._connect()
        try:
            result = client.read_coils(address, count=count, slave=self.unit_id)
            if result.isError():
                raise ModbusResponseError(
                    f"Device returned an error reading coils at address {address}: {result}"
                )
            return list(result.bits[:count])
        except ModbusException as e:
            raise ModbusResponseError(f"Modbus exception reading coils: {e}") from e
        finally:
            client.close()

    def read_discrete_inputs(self, address: int, count: int = 1) -> list[bool]:
        """Read one or more discrete inputs (Function Code 02)."""
        client = self._connect()
        try:
            result = client.read_discrete_inputs(address, count=count, slave=self.unit_id)
            if result.isError():
                raise ModbusResponseError(
                    f"Device returned an error reading discrete inputs at address {address}: {result}"
                )
            return list(result.bits[:count])
        except ModbusException as e:
            raise ModbusResponseError(f"Modbus exception reading discrete inputs: {e}") from e
        finally:
            client.close()

    # -------------------------------------------------------------------------
    # WRITE METHODS
    # -------------------------------------------------------------------------

    def write_holding_register(self, address: int, value: int, signed: bool = True) -> None:
        """
        Write a single holding register (Function Code 06).

        Args:
            address (int): Register address (0-based).
            value (int): Value to write. If signed=True (default): -32768 to 32767.
                         If signed=False: 0 to 65535.
            signed (bool): If True (default), accept and encode signed values as two's complement.
        """
        if signed:
            if not (-32768 <= value <= 32767):
                raise ValueError(f"Value {value} out of range. Signed 16-bit must be -32768 to 32767.")
            raw = self._to_unsigned(value)
        else:
            if not (0 <= value <= 65535):
                raise ValueError(f"Value {value} out of range. Unsigned 16-bit must be 0 to 65535.")
            raw = value

        client = self._connect()
        try:
            result = client.write_register(address, raw, slave=self.unit_id)
            if result.isError():
                raise ModbusResponseError(
                    f"Device returned an error writing register at address {address}: {result}"
                )
        except ModbusException as e:
            raise ModbusResponseError(f"Modbus exception writing holding register: {e}") from e
        finally:
            client.close()

    def write_holding_registers(self, address: int, values: list[int], signed: bool = True) -> None:
        """
        Write multiple consecutive holding registers (Function Code 16).

        Args:
            address (int): Starting register address (0-based).
            values (list[int]): Values to write. If signed=True (default): each -32768 to 32767.
            signed (bool): If True (default), accept and encode signed values as two's complement.
        """
        if not values:
            raise ValueError("Values list must not be empty.")

        raw_values = []
        for i, v in enumerate(values):
            if signed:
                if not (-32768 <= v <= 32767):
                    raise ValueError(f"Value at index {i} ({v}) out of range. Must be -32768 to 32767.")
                raw_values.append(self._to_unsigned(v))
            else:
                if not (0 <= v <= 65535):
                    raise ValueError(f"Value at index {i} ({v}) out of range. Must be 0 to 65535.")
                raw_values.append(v)

        client = self._connect()
        try:
            result = client.write_registers(address, raw_values, slave=self.unit_id)
            if result.isError():
                raise ModbusResponseError(
                    f"Device returned an error writing registers at address {address}: {result}"
                )
        except ModbusException as e:
            raise ModbusResponseError(f"Modbus exception writing holding registers: {e}") from e
        finally:
            client.close()

    def write_coil(self, address: int, value: bool) -> None:
        """Write a single coil (Function Code 05)."""
        client = self._connect()
        try:
            result = client.write_coil(address, bool(value), slave=self.unit_id)
            if result.isError():
                raise ModbusResponseError(
                    f"Device returned an error writing coil at address {address}: {result}"
                )
        except ModbusException as e:
            raise ModbusResponseError(f"Modbus exception writing coil: {e}") from e
        finally:
            client.close()

    def write_coils(self, address: int, values: list[bool]) -> None:
        """Write multiple consecutive coils (Function Code 15)."""
        if not values:
            raise ValueError("Values list must not be empty.")
        client = self._connect()
        try:
            result = client.write_coils(address, [bool(v) for v in values], slave=self.unit_id)
            if result.isError():
                raise ModbusResponseError(
                    f"Device returned an error writing coils at address {address}: {result}"
                )
        except ModbusException as e:
            raise ModbusResponseError(f"Modbus exception writing coils: {e}") from e
        finally:
            client.close()
