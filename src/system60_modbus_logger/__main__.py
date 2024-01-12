"""
Main entry point for system60_modbus_logger
"""
import logging
import typing

from pymodbus import ModbusException
from pymodbus.client import ModbusTcpClient
from pymodbus.pdu import ModbusResponse

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    CLIENT: ModbusTcpClient = ModbusTcpClient("127.0.0.1", port=8080)
    CLIENT.connect()

    try:
        RESPONSE: ModbusResponse = CLIENT.read_coils(0)
    except ModbusException as EXCEPTION:
        logging.error(" Exception in pymodbus %s", EXCEPTION)
        raise EXCEPTION

    if RESPONSE.isError():
        logging.error(" Request for coil 1 value returned an error")
        raise ModbusException("Request for coil 1 value returned an error")

    logging.info(" Coil 1 value is %i", RESPONSE.bits[0])

    CLIENT.close()
