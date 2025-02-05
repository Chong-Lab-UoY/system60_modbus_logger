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

RACK_ID_TO_IP_ADDRESS = dict(zip(RACK_IDS, RACK_IP_ADDRESSES))
IP_ADDRESS_TO_RACK_ID = dict(zip(RACK_IP_ADDRESSES, RACK_IDS))


def sensor_rack(rack_id: str) -> str:
    """ """
    if (rack_id not in RACK_ID_TO_IP_ADDRESS) and (rack_id != "all"):
        error_message = (
            f"{rack_id} is an invalid rack ID - "
            "please choose a rack from A - J or 'all'"
        )
        raise argparse.ArgumentTypeError(error_message)

    return rack_id


def integer_gte_minus_one(number: str) -> int:
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
            f"{converted_number} is not a valid value - "
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
    """ """
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
        type=integer_gte_minus_one,
        metavar="number_of_requests",
        help="The number of data requests to make of the sensor rack(s)",
    )

    parser.add_argument(
        "logging_interval",
        type=integer_gte_minus_one,
        metavar="logging_interval",
        help="The interval, in seconds, between requests for data from a rack",
    )

    parser.add_argument(
        "log_file",
        type=potential_output_file,
        metavar="log_file",
        help="The file to which data request results will be logged",
    )

    return parser.parse_args()


def connect_to_rack(rack_id: str) -> ModbusTcpClient:
    """ """
    client: ModbusTcpClient = ModbusTcpClient(
        RACK_ID_TO_IP_ADDRESS[rack_id], port=502
    )

    if not client.connect():
        error_message: str = " Connecting to rack %s on %s failed"
        logging.error(error_message, rack_id, RACK_ID_TO_IP_ADDRESS[rack_id])
        raise ConnectionError(
            error_message % (rack_id, RACK_ID_TO_IP_ADDRESS[rack_id])
        )

    return client


def get_registers_from_rack(modbus_client: ModbusTcpClient) -> list:
    """ """
    rack_ip_address: str = modbus_client.comm_params.host
    rack_id: str = IP_ADDRESS_TO_RACK_ID[rack_ip_address]

    try:
        response: ModbusResponse = modbus_client.read_input_registers(0, 48)
    except ModbusException as exception:
        read_error_message: str = " Reading registers from rack %s on %s failed"
        logging.error(read_error_message, rack_id, rack_ip_address)
        raise ModbusException(
            read_error_message % (rack_id, rack_ip_address)
        ) from exception

    if response.isError():
        request_error_message: str = (
            " Request for input registers 0 - 47 from rack %s on %s"
            " returned an error"
        )
        logging.error(request_error_message, rack_id, rack_ip_address)
        raise ModbusException(
            request_error_message % (rack_id, rack_ip_address)
        )

    return response.registers


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    COMMAND_LINE_ARGUMENTS: argparse.Namespace = parse_command_line()

    RACKS_TO_LOG: list[str] = (
        list(RACK_ID_TO_IP_ADDRESS.keys())
        if (COMMAND_LINE_ARGUMENTS.rack_to_log == "all")
        else [
            COMMAND_LINE_ARGUMENTS.rack_to_log,
        ]
    )

    for REQUEST_ID in itertools.count(start=0):
        if REQUEST_ID == COMMAND_LINE_ARGUMENTS.number_of_requests:
            break

        for RACK_ID in RACKS_TO_LOG:
            try:
                CONNECTION: ModbusTcpClient = connect_to_rack(
                    COMMAND_LINE_ARGUMENTS.rack_to_log
                )
            except ConnectionError as EXCEPTION:
                continue

            TIMESTAMP: int = int(
                datetime.datetime.timestamp(
                    datetime.datetime.now(datetime.timezone.utc)
                )
            )

            try:
                REGISTERS: list = get_registers_from_rack(CONNECTION)
                CONNECTION.close()
            except ModbusException as EXCEPTION:
                CONNECTION.close()
                continue

            logging.info(
                " Input registers 0 - 47 are [ %s ]",
                ", ".join(map(str, REGISTERS)),
            )

            VALUES = [
                struct.unpack("f", struct.pack("HH", MSW, LSW))[0]
                for MSW, LSW in zip(REGISTERS[::2], REGISTERS[1::2])
            ]

            logging.info(
                " Values are [ %s ]",
                ", ".join(map(str, VALUES)),
            )

            VALUES.insert(0, TIMESTAMP)
            VALUES.insert(1, RACK_ID)

            logging.info(
                "%s",
                ",".join(map(str, VALUES)),
            )

            with open(
                COMMAND_LINE_ARGUMENTS.log_file, "a", encoding="utf-8"
            ) as LOG_FILE:
                LOG_FILE.write(",".join(map(str, VALUES)) + "\n")

            time.sleep(COMMAND_LINE_ARGUMENTS.logging_interval)
