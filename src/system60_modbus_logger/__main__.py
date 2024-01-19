"""
Main entry point for system60_modbus_logger
"""
import logging
import typing

from pymodbus import ModbusException
from pymodbus.client import ModbusTcpClient
from pymodbus.pdu import ModbusResponse

DEVICE_IP_ADDRESSES: dict[str, str] = {
    "A": "192.168.1.160",
    "B": "192.168.1.161",
    "C": "192.168.1.162",
    "D": "192.168.1.163",
    "E": "192.168.1.164",
    "F": "192.168.1.165",
    "G": "192.168.1.166",
    "H": "192.168.1.167",
    "I": "192.168.1.168",
    "J": "192.168.1.169",
}

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    CLIENT: ModbusTcpClient = ModbusTcpClient(
        DEVICE_IP_ADDRESSES["A"], port=502
    )
    CLIENT.connect()

    try:
        RESPONSE: ModbusResponse = CLIENT.read_input_registers(0, 48)
    except ModbusException as EXCEPTION:
        logging.error(" Exception in pymodbus %s", EXCEPTION)
        raise EXCEPTION

    if RESPONSE.isError():
        logging.error(" Request for input registers 0-47 returned an error")
        raise ModbusException(
            "Request for input register 0-47 returned an error"
        )

    logging.info(
        " Input registers 0 - 47 are [ %s ]",
        ", ".join(map(str, RESPONSE.registers)),
    )

    CLIENT.close()
