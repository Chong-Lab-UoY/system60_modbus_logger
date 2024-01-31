"""
Main entry point for system60_modbus_logger
"""
import argparse
import datetime
import itertools
import logging
import os
import struct
import time

from pymodbus import ModbusException
from pymodbus.client import ModbusTcpClient
from pymodbus.pdu import ModbusResponse


RACK_IP_ADDRESSES = [f"192.168.1.{x}" for x in range(160, 170)]
RACK_IDS = list(map(chr, range(ord("A"), ord("I") + 1)))

RACK_TO_IP_ADDRESS = dict(zip(RACK_IDS, RACK_IP_ADDRESSES))
IP_ADDRESS_TO_RACK = dict(zip(RACK_IP_ADDRESSES, RACK_IDS))


def sensor_rack(rack_id: str) -> str:
    """ """
    if (rack_id not in RACK_TO_IP_ADDRESS) and (rack_id != "all"):
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
    except ValueError as _:
        error_message = (
            f"{number} is not an integer - please choose a positive "
            "integer or -1 for indefinite requests"
        )
        raise argparse.ArgumentTypeError(error_message)

    if converted_number < -1:
        error_message = (
            f"{converted_number} is not greater than or equal to zero - "
            "please choose a positive integer or -1 for indefinite requests"
        )
        raise argparse.ArgumentTypeError(error_message)
    return converted_number


def potential_output_file(path: str) -> str:
    """ """
    absolute_path = os.path.abspath(path)

    if os.path.exists(absolute_path):
        if os.path.isfile(absolute_path) and os.access(absolute_path, os.W_OK):
            return absolute_path

        error_message = (
            f"{absolute_path} is a path to a non-writable file or a "
            "non-file - please choose a different path for the log file"
        )

        raise argparse.ArgumentTypeError(error_message)

    if os.access(os.path.dirname(absolute_path), os.W_OK):
        return absolute_path

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

    for REQUEST_ID in itertools.count(start=0):
        if REQUEST_ID == COMMAND_LINE_ARGUMENTS.number_of_requests:
            break

        CLIENT: ModbusTcpClient = ModbusTcpClient(
            RACK_IP_ADDRESSES[COMMAND_LINE_ARGUMENTS.rack_to_log], port=502
        )

        try:
            CLIENT.connect()
        except ConnectionError as EXCEPTION:
            logging.error(
                " Connecting to rack %s on %s failed",
                COMMAND_LINE_ARGUMENTS.rack_to_log,
                RACK_IP_ADDRESSES[COMMAND_LINE_ARGUMENTS.rack_to_log],
            )
            continue

        TIMESTAMP: int = int(
            datetime.datetime.timestamp(
                datetime.datetime.now(datetime.timezone.utc)
            )
        )

        try:
            RESPONSE: ModbusResponse = CLIENT.read_input_registers(0, 48)
        except ModbusException as EXCEPTION:
            logging.error(" Exception in pymodbus %s", EXCEPTION)
            continue

        if RESPONSE.isError():
            logging.error(
                " Request for input registers 0-47 from rack %s returned an error",
                COMMAND_LINE_ARGUMENTS.rack_to_log,
            )

        logging.info(
            " Input registers 0 - 47 are [ %s ]",
            ", ".join(map(str, RESPONSE.registers)),
        )

        VALUES.insert(0, TIMESTAMP)

        logging.info(
            "%s",
            ",".join(map(str, VALUES)),
        )

        time.sleep(1)
