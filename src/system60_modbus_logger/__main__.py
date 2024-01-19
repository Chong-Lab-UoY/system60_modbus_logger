"""
Main entry point for system60_modbus_logger
"""
import argparse
import logging
import os
import typing

from pymodbus import ModbusException
from pymodbus.client import ModbusTcpClient
from pymodbus.pdu import ModbusResponse

RACK_IP_ADDRESSES: dict[str, str] = {
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


def sensor_rack(rack_id: str) -> str:
    """ """
    if (rack_id not in RACK_IP_ADDRESSES.keys()) and (rack_id != "all"):
        error_message = (
            f"{rack_id} is an invalid rack ID - "
            "please choose a rack from A - J or 'all'"
        )
        raise argparse.ArgumentTypeError(error_message)

    return rack_id


def integer_gte_zero(number: str) -> int:
    """ """
    try:
        converted_number = int(number)
    except ValueError as exception:
        error_message = (
            f"{number} is not an integer - please choose a positive "
            "integer or 0 for indefinite requests"
        )
        raise argparse.ArgumentTypeError(error_message)

    if not converted_number >= 0:
        error_message = (
            f"{converted_number} is not greater than or equal to zero - "
            "please choose a positive integer or 0 for indefinite requests"
        )
        raise argparse.ArgumentTypeError(error_message)
    return converted_number


def potential_output_file(path: str) -> str:
    """ """
    absolute_path = os.path.abspath(path)

    if os.path.exists(absolute_path):
        if os.path.isfile(absolute_path) and os.access(absolute_path, os.W_OK):
            return absolute_path
        else:
            error_message = (
                f"{absolute_path} is a path to a non-writable file or a "
                "non-file - please choose a different path for the log file"
            )
            raise argparse.ArgumentTypeError(error_message)
    else:
        if os.access(os.path.dirname(absolute_path), os.W_OK):
            return absolute_path
        else:
            error_message = (
                f"The directory {os.path.dirname(absolute_path)} is not "
                "writeable or doesn't exist - please choose a different "
                "path for the log file"
            )
            raise argparse.ArgumentTypeError(error_message)


def parse_command_line() -> argparse.Namespace:
    description_text = ""
    epilog_text = ""

    parser = argparse.ArgumentParser(
        description=description_text,
        epilog=epilog_text,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "rack_to_log",
        type=sensor_rack,
        metavar="rack_to_log",
        help="The sensor rack from which to log data",
    )

    parser.add_argument(
        "number_of_requests",
        type=integer_gte_zero,
        metavar="number_of_requests",
        help="The number of data requests to make of the sensor rack(s)",
    )

    parser.add_argument(
        "log_file",
        type=potential_output_file,
        metavar="log_file",
        help="The file to which data request results will be logged",
    )

    return parser.parse_args()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    COMMAND_LINE_ARGUMENTS: argparse.Namespace = parse_command_line()

    CLIENT: ModbusTcpClient = ModbusTcpClient(RACK_IP_ADDRESSES["A"], port=502)
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
