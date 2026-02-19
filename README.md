# modbus_client

A simple Modbus TCP read/write tool for networked slave devices.
Designed for controls engineers and developers who need quick, reliable
access to Modbus registers without writing custom scripts.

---

## Installation

```bash
pip install .
```

This installs the `modbus` command-line tool and the `modbus_client` Python library.

**Requires Python 3.10+**

---

## Command-Line Usage

### Get help

```bash
modbus --help
modbus read --help
modbus write --help
```

### Reading registers

```bash
# Read 1 holding register at address 100
modbus read holding --host 192.168.1.50 --address 100

# Read 4 holding registers starting at address 200
modbus read holding --host 192.168.1.50 --address 200 --count 4

# Read a single input register (sensor/measurement value)
modbus read input --host 192.168.1.50 --address 10

# Read 8 coils starting at address 0
modbus read coil --host 192.168.1.50 --address 0 --count 8

# Read discrete inputs (digital input states)
modbus read discrete --host 192.168.1.50 --address 0 --count 4

# Use a non-standard port and specific unit ID
modbus read holding --host 192.168.1.50 --port 1502 --unit-id 3 --address 100
```

**Example output:**
```
Holding Registers read from 192.168.1.50:502 (Unit ID: 1)
Address      Value        Hex
------------------------------------
100          1500         0x5dc
101          200          0xc8
102          300          0x12c
```

### Writing registers

```bash
# Write 1500 to holding register address 100
modbus write holding --host 192.168.1.50 --address 100 --values 1500

# Write multiple values to consecutive registers (addresses 100, 101, 102)
modbus write holding --host 192.168.1.50 --address 100 --values 1500 200 300

# Turn ON coil at address 5
modbus write coil --host 192.168.1.50 --address 5 --values 1

# Turn OFF coil at address 5
modbus write coil --host 192.168.1.50 --address 5 --values 0

# Write ON/OFF/ON to coils at addresses 0, 1, 2
modbus write coil --host 192.168.1.50 --address 0 --values 1 0 1
```

**Example output:**
```
Holding Registers written to 192.168.1.50:502 (Unit ID: 1)
Address      Value Written
----------------------------
100          1500  (0x5dc)
```

---

## Register Address Note

Addresses are **0-based** by default. If your device documentation uses:

- **1-based addressing** (e.g., address listed as 101): subtract 1 → use `100`
- **Modbus PDU notation** (e.g., 40101 for holding registers): subtract 40001 → use `100`

---

## Python API Usage

You can also use `modbus_client` directly in Python scripts:

```python
from modbus_client import ModbusClient

mc = ModbusClient(host="192.168.1.50", port=502, unit_id=1)

# Read holding registers
values = mc.read_holding_registers(address=100, count=4)
print(values)  # [1500, 200, 300, 0]

# Write a single holding register
mc.write_holding_register(address=100, value=1500)

# Write multiple holding registers
mc.write_holding_registers(address=100, values=[1500, 200, 300])

# Read coils
coils = mc.read_coils(address=0, count=4)
print(coils)  # [True, False, True, False]

# Write a coil
mc.write_coil(address=5, value=True)
```

---

## Register Types Reference

| Type | FC | Access | Bit Width | Typical Use |
|---|---|---|---|---|
| Holding Register | 03/06/16 | R/W | 16-bit | Setpoints, config, status |
| Input Register | 04 | R only | 16-bit | Measurements, sensor data |
| Coil | 01/05/15 | R/W | 1-bit | Output states, relay control |
| Discrete Input | 02 | R only | 1-bit | Digital inputs, limit switches |

---

## Error Handling

The tool will print a clear `ERROR:` message and exit with a non-zero status if:

- The device cannot be reached (wrong IP, device offline, firewall)
- The device rejects the request (wrong address, wrong unit ID, unsupported function)
- A value is out of range (e.g., writing 70000 to a 16-bit register)
