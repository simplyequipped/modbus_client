"""
Command-line interface for modbus_client.

Designed for controls engineers who may not be Python developers.
Run `modbus --help` or `modbus <command> --help` for usage details.
"""

import argparse
import sys

from .client import ModbusClient
from .exceptions import ModbusClientError


# =============================================================================
# HELP TEXT
# =============================================================================

MAIN_DESCRIPTION = """\
modbus - Read and write registers on a Modbus TCP slave device
==============================================================

This tool lets you communicate with any Modbus TCP device on your network,
such as a PLC, VFD, sensor, or controller.

REGISTER TYPES (--register-type, default: holding):
  holding    Holding registers (FC03/FC06/FC16): Read/write, 16-bit values.
             Most common type. Used for setpoints, configuration, status words.

  input      Input registers (FC04): Read-only, 16-bit values.
             Used for live measurements (temperature, current, etc.)

  coil       Coils (FC01/FC05/FC15): Read/write, single ON/OFF bit.
             Used for output states, relay control, enable flags.

  discrete   Discrete inputs (FC02): Read-only, single ON/OFF bit.
             Used for digital input states (limit switches, alarms, etc.)

SIGNED vs UNSIGNED:
  By default, register values are treated as signed 16-bit integers (-32768 to 32767).
  This matches most PLCs and controllers. Add --unsigned if your device uses
  unsigned values (0 to 65535) instead.

COMMANDS:
  read       Read one or more consecutive registers or coils.
  write      Write one or more consecutive registers or coils.

TYPICAL USAGE:
  modbus read  --host <IP> --address <ADDR> [--count N] [--register-type TYPE]
  modbus write --host <IP> --address <ADDR> --values <V1> [V2 ...] [--register-type TYPE]

OPTIONS (shared by all commands):
  --host            IP address or hostname of the device       [REQUIRED]
  --address         Register address to read/write             [REQUIRED]
  --register-type   holding, input, coil, or discrete          [default: holding]
  --unit-id         Slave device ID                            [default: 1]
  --port            TCP port number                            [default: 502]
  --timeout         Connection timeout in seconds              [default: 3.0]
  --unsigned        Treat values as unsigned (0-65535) rather than signed
  --verbose         Print detailed info about the transaction before sending
  --count           (read only) Number of registers to read    [default: 1]
  --values          (write only) One or more values to write   [REQUIRED for write]

EXAMPLES:
  # Read 1 holding register at address 100
  modbus read --host 192.168.1.50 --address 100

  # Read 4 holding registers starting at address 200
  modbus read --host 192.168.1.50 --address 200 --count 4

  # Read a single input register (sensor value)
  modbus read --host 192.168.1.50 --address 10 --register-type input

  # Write -500 to holding register address 100
  modbus write --host 192.168.1.50 --address 100 --values -500

  # Write multiple values to consecutive registers (addresses 100, 101, 102)
  modbus write --host 192.168.1.50 --address 100 --values 1500 -200 300

  # Write with verbose output to confirm what is sent
  modbus write --host 192.168.1.50 --address 100 --values -500 --verbose

  # Turn ON a coil at address 5
  modbus write --host 192.168.1.50 --address 5 --register-type coil --values 1

NOTE ON ADDRESSES:
  Register addresses are 0-based. If your documentation uses 40001-style notation,
  subtract 40001 (e.g., 40101 -> address 100). If 1-based, subtract 1.
"""

READ_DESCRIPTION = """\
Read one or more consecutive registers or coils from a Modbus TCP device.

The register type defaults to "holding". Use --register-type to change it.

TYPICAL USAGE:
  modbus read --host <IP> --address <ADDR> [OPTIONS]

OPTIONS:
  --host            IP address or hostname of the device       [REQUIRED]
  --address         Starting register address (0-based)        [REQUIRED]
  --register-type   holding, input, coil, or discrete          [default: holding]
  --count           Number of consecutive registers to read    [default: 1]
  --unit-id         Slave device ID                            [default: 1]
  --port            TCP port number                            [default: 502]
  --timeout         Connection timeout in seconds              [default: 3.0]
  --unsigned        Return raw unsigned values (0-65535) instead of signed
  --verbose         Print transaction details before reading

REGISTER TYPES:
  holding    Holding registers - read/write 16-bit values (FC03)  [DEFAULT]
  input      Input registers   - read-only 16-bit values (FC04)
  coil       Coils             - read/write ON/OFF bits (FC01)
  discrete   Discrete inputs   - read-only ON/OFF bits (FC02)

EXAMPLES:
  # Read 1 holding register at address 100
  modbus read --host 192.168.1.50 --address 100

  # Read 4 holding registers starting at address 200, on unit ID 3
  modbus read --host 192.168.1.50 --address 200 --count 4 --unit-id 3

  # Read a single input register
  modbus read --host 192.168.1.50 --address 10 --register-type input

  # Read 8 coils on a non-standard port
  modbus read --host 192.168.1.50 --port 1502 --address 0 --count 8 --register-type coil

  # Read and show raw unsigned values
  modbus read --host 192.168.1.50 --address 100 --unsigned
"""

WRITE_DESCRIPTION = """\
Write one or more consecutive registers or coils to a Modbus TCP device.

The register type defaults to "holding". Use --register-type to change it.
Input registers and discrete inputs are READ-ONLY and cannot be written.

TYPICAL USAGE:
  modbus write --host <IP> --address <ADDR> --values <V1> [V2 ...] [OPTIONS]

OPTIONS:
  --host            IP address or hostname of the device       [REQUIRED]
  --address         Starting register address (0-based)        [REQUIRED]
  --values          One or more values to write                [REQUIRED]
  --register-type   holding or coil                            [default: holding]
  --unit-id         Slave device ID                            [default: 1]
  --port            TCP port number                            [default: 502]
  --timeout         Connection timeout in seconds              [default: 3.0]
  --write-mode      multiple (FC16) or single (FC06)              [default: multiple]
  --unsigned        Treat values as unsigned (0-65535) instead of signed
  --verbose         Print transaction details before writing (useful for debugging)

VALUES:
  For holding registers: signed integers -32768 to 32767 (or 0-65535 with --unsigned).
  For coils: 1 (ON) or 0 (OFF).

EXAMPLES:
  # Write -500 to holding register address 100
  modbus write --host 192.168.1.50 --address 100 --values -500

  # Write three values to addresses 100, 101, 102
  modbus write --host 192.168.1.50 --address 100 --values 1500 -200 300

  # Debug a write by printing what will be sent to the device
  modbus write --host 192.168.1.50 --address 100 --values -500 --verbose

  # Write an unsigned value
  modbus write --host 192.168.1.50 --address 100 --values 50000 --unsigned

  # Turn ON the coil at address 5
  modbus write --host 192.168.1.50 --address 5 --register-type coil --values 1

  # Write ON/OFF/ON to coils at addresses 0, 1, 2
  modbus write --host 192.168.1.50 --address 0 --register-type coil --values 1 0 1
"""


# =============================================================================
# ARGUMENT PARSING
# =============================================================================

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="modbus",
        description=MAIN_DESCRIPTION,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", metavar="COMMAND")
    subparsers.required = False

    # --- Shared connection arguments -----------------------------------------
    connection_args = argparse.ArgumentParser(add_help=False)
    connection_args.add_argument(
        "--host", required=True,
        metavar="IP",
        help="IP address or hostname of the Modbus device"
    )
    connection_args.add_argument(
        "--port", type=int, default=502,
        metavar="PORT",
        help="TCP port number (default: 502)"
    )
    connection_args.add_argument(
        "--unit-id", type=int, default=1,
        metavar="ID",
        dest="unit_id",
        help="Slave unit ID / device address (default: 1)"
    )
    connection_args.add_argument(
        "--timeout", type=float, default=3.0,
        metavar="SECONDS",
        help="Connection timeout in seconds (default: 3.0)"
    )
    connection_args.add_argument(
        "--address", type=int, required=True,
        metavar="ADDR",
        help="Starting register/coil address (0-based)"
    )
    connection_args.add_argument(
        "--register-type",
        dest="register_type",
        default="holding",
        metavar="TYPE",
        help="Register type: holding, input, coil, or discrete (default: holding)"
    )
    connection_args.add_argument(
        "--unsigned", action="store_true",
        help="Use unsigned integers (0-65535) instead of signed (-32768 to 32767)"
    )
    connection_args.add_argument(
        "--verbose", action="store_true",
        help="Print detailed transaction info before sending (useful for debugging writes)"
    )

    # --- READ subcommand -----------------------------------------------------
    read_parser = subparsers.add_parser(
        "read",
        help="Read registers or coils from the device",
        description=READ_DESCRIPTION,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        parents=[connection_args],
    )
    read_parser.add_argument(
        "--count", type=int, default=1,
        metavar="N",
        help="Number of consecutive registers/coils to read (default: 1)"
    )

    # --- WRITE subcommand ----------------------------------------------------
    write_parser = subparsers.add_parser(
        "write",
        help="Write registers or coils to the device",
        description=WRITE_DESCRIPTION,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        parents=[connection_args],
    )
    write_parser.add_argument(
        "--values", nargs="+", required=True,
        metavar="VALUE",
        help="One or more values to write"
    )
    write_parser.add_argument(
        "--write-mode",
        dest="write_mode",
        choices=["multiple", "single"],
        default="multiple",
        metavar="MODE",
        help="Write function code: multiple (FC16, default) or single (FC06)"
    )

    return parser


# =============================================================================
# COMMAND HANDLERS
# =============================================================================

def handle_read(args) -> int:
    reg_type = args.register_type.lower()
    valid_types = ("holding", "input", "coil", "discrete")
    if reg_type not in valid_types:
        print(f"ERROR: Unknown register type '{reg_type}'. Must be one of: {', '.join(valid_types)}", file=sys.stderr)
        return 1

    signed = not args.unsigned
    address = args.address - 1  # subtract 1: user-facing addresses are 1-based, wire protocol is 0-based

    if args.verbose:
        fc_map = {"holding": "FC03", "input": "FC04", "coil": "FC01", "discrete": "FC02"}
        print(f"\n[VERBOSE] Read transaction details:")
        print(f"  Host:          {args.host}:{args.port}")
        print(f"  Unit ID:       {args.unit_id}")
        print(f"  Function code: {fc_map[reg_type]}")
        print(f"  Address (as entered): {args.address}")
        print(f"  Address (on wire):    {address} (0x{address:04X})")
        print(f"  Count:         {args.count}")
        if reg_type in ("holding", "input"):
            print(f"  Interpreting:  {'signed' if signed else 'unsigned'} 16-bit integers")
        print()

    mc = ModbusClient(host=args.host, port=args.port, unit_id=args.unit_id, timeout=args.timeout)

    try:
        if reg_type == "holding":
            results = mc.read_holding_registers(address, args.count, signed=signed)
            label = "Holding Register"
        elif reg_type == "input":
            results = mc.read_input_registers(address, args.count, signed=signed)
            label = "Input Register"
        elif reg_type == "coil":
            results = mc.read_coils(address, args.count)
            label = "Coil"
        elif reg_type == "discrete":
            results = mc.read_discrete_inputs(address, args.count)
            label = "Discrete Input"
    except ModbusClientError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    int_mode = "unsigned" if args.unsigned else "signed"
    print(f"\n{label}s read from {args.host}:{args.port} (Unit ID: {args.unit_id})")
    if reg_type in ("holding", "input"):
        print(f"Interpreting as: {int_mode} 16-bit integers (scaled value = raw / 10)")
        print(f"{'Address':<12} {'Raw Value':<14} {'Scaled (/10)':<16} {'Hex (raw)':<12}")
        print("-" * 56)
        for i, val in enumerate(results):
            addr = args.address + i  # display back in user-facing (1-based) addresses
            scaled = f"{val / 10:.1f}"
            print(f"{addr:<12} {val:<14} {scaled:<16} {hex(val & 0xFFFF):<12}")
    else:
        print(f"{'Address':<12} {'Value':<14}")
        print("-" * 26)
        for i, val in enumerate(results):
            addr = args.address + i  # display back in user-facing (1-based) addresses
            display_val = "ON (1)" if val else "OFF (0)"
            print(f"{addr:<12} {display_val:<14}")
    print()
    return 0


def handle_write(args) -> int:
    reg_type = args.register_type.lower()
    if reg_type in ("input", "discrete"):
        print(f"ERROR: '{reg_type}' registers are read-only and cannot be written.", file=sys.stderr)
        return 1
    if reg_type not in ("holding", "coil"):
        print(f"ERROR: Unknown register type '{reg_type}'. For writes, use: holding or coil", file=sys.stderr)
        return 1

    signed = not args.unsigned
    address = args.address - 1  # subtract 1: user-facing addresses are 1-based, wire protocol is 0-based
    raw_values = args.values

    # --- Parse and validate --------------------------------------------------
    try:
        if reg_type == "holding":
            parsed = [int(v) for v in raw_values]
            if signed:
                for i, v in enumerate(parsed):
                    if not (-32768 <= v <= 32767):
                        print(f"ERROR: Value {v} at position {i+1} out of range. Signed 16-bit: -32768 to 32767.", file=sys.stderr)
                        print(f"       (Add --unsigned if your device expects values 0 to 65535.)", file=sys.stderr)
                        return 1
            else:
                for i, v in enumerate(parsed):
                    if not (0 <= v <= 65535):
                        print(f"ERROR: Value {v} at position {i+1} out of range. Unsigned 16-bit: 0 to 65535.", file=sys.stderr)
                        return 1
        elif reg_type == "coil":
            parsed = []
            for i, v in enumerate(raw_values):
                if v not in ("0", "1"):
                    print(f"ERROR: Coil value '{v}' at position {i+1} invalid. Use 1 (ON) or 0 (OFF).", file=sys.stderr)
                    return 1
                parsed.append(bool(int(v)))
    except ValueError as e:
        print(f"ERROR: Invalid value — {e}", file=sys.stderr)
        return 1

    # --- Verbose output ------------------------------------------------------
    if args.verbose and reg_type == "holding":
        use_single = args.write_mode == "single"
        fc = "FC06 (Write Single Register)" if use_single else "FC16 (Write Multiple Registers)"
        print(f"\n[VERBOSE] Write transaction details:")
        print(f"  Host:          {args.host}:{args.port}")
        print(f"  Unit ID:       {args.unit_id}")
        print(f"  Function code: {fc}")
        print(f"  Address (as entered): {args.address}")
        print(f"  Address (on wire):    {address} (0x{address:04X})")
        print(f"  Encoding:      {'signed' if signed else 'unsigned'} 16-bit integers")
        print(f"  Values to write:")
        for i, v in enumerate(parsed):
            raw = v & 0xFFFF
            print(f"    Address {args.address + i}: {v:>7}  ->  wire value: {raw} (0x{raw:04X})")
        print()
    elif args.verbose and reg_type == "coil":
        use_single = args.write_mode == "single"
        fc = "FC05 (Write Single Coil)" if use_single else "FC15 (Write Multiple Coils)"
        print(f"\n[VERBOSE] Write transaction details:")
        print(f"  Host:          {args.host}:{args.port}")
        print(f"  Unit ID:       {args.unit_id}")
        print(f"  Function code: {fc}")
        print(f"  Address (as entered): {args.address}")
        print(f"  Address (on wire):    {address} (0x{address:04X})")
        print(f"  Values to write:")
        for i, v in enumerate(parsed):
            print(f"    Address {args.address + i}: {'ON (1)' if v else 'OFF (0)'}")
        print()

    # --- Execute write -------------------------------------------------------
    mc = ModbusClient(host=args.host, port=args.port, unit_id=args.unit_id, timeout=args.timeout)

    try:
        if reg_type == "holding":
            if args.write_mode == "single":
                if len(parsed) == 1:
                    mc.write_holding_register(address, parsed[0], signed=signed)
                else:
                    # single mode with multiple values: write registers one at a time
                    for i, v in enumerate(parsed):
                        mc.write_holding_register(address + i, v, signed=signed)
            else:
                mc.write_holding_registers(address, parsed, signed=signed)
            label = "Holding Register"
        elif reg_type == "coil":
            if args.write_mode == "single":
                for i, v in enumerate(parsed):
                    mc.write_coil(address + i, v)
            else:
                mc.write_coils(address, parsed)
            label = "Coil"
    except ModbusClientError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    # --- Confirmation --------------------------------------------------------
    int_mode = "unsigned" if args.unsigned else "signed"
    print(f"\n{label}s written successfully to {args.host}:{args.port} (Unit ID: {args.unit_id})")
    if reg_type == "holding":
        print(f"Encoding: {int_mode} 16-bit integers")
    print(f"{'Address':<12} {'Value Written':<16} {'Wire (hex)':<12}")
    print("-" * 42)
    for i, val in enumerate(parsed):
        addr = args.address + i  # display back in user-facing (1-based) addresses
        if isinstance(val, bool):
            display_val = "ON (1)" if val else "OFF (0)"
            print(f"{addr:<12} {display_val:<16}")
        else:
            print(f"{addr:<12} {val:<16} {hex(val & 0xFFFF):<12}")
    print()
    return 0


# =============================================================================
# ENTRY POINT
# =============================================================================

def main():
    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    if args.command == "read":
        sys.exit(handle_read(args))
    elif args.command == "write":
        sys.exit(handle_write(args))
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
