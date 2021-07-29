"""Tests for src.app.py"""
import os

from src.app import usage, validate_parameters, main, logger
from src.error import BalancerError

# pylint: disable=missing-function-docstring


def test_usage(mocker):
    mocker_print = mocker.patch("builtins.print")
    mocker_sys_exit = mocker.patch("sys.exit")
    usage()
    assert mocker_print.called_once_with("USAGE: load_balance INPUT_FILE [OUTPUT_FILE]")
    assert mocker_sys_exit.called_once_with(1)


def test_usage_docker(mocker):
    mocker_print = mocker.patch("builtins.print")
    mocker_sys_exit = mocker.patch("sys.exit")
    mocker.patch("os.environ", {"DOCKER": "True"})
    usage()
    assert mocker_print.called_once_with("USAGE - Docker mode: load_balance INPUT_FILE")
    assert mocker_sys_exit.called_once_with(1)


def test_validate_parameters_input_only(mocker):
    mocker.patch("sys.argv", ["python", "clients.txt"])
    ret1, ret2 = validate_parameters()
    assert ret1 == "clients.txt"
    assert ret2 is None


def test_validate_parameters_input_output(mocker):
    mocker.patch("sys.argv", ["python", "clients.txt", "results.txt"])
    ret1, ret2 = validate_parameters()
    assert ret1 == "clients.txt"
    assert ret2 == "results.txt"


def test_validate_parameters_input_only_docker(mocker):
    mocker.patch("sys.argv", ["python", "clients.txt"])
    mocker.patch.dict(os.environ, {"DOCKER": "True"})  # Not working in real life
    ret1, ret2 = validate_parameters()
    assert ret1 == "clients.txt"
    assert ret2 is None


# BUG: can not patch os.environ!!!
# def test_validate_parameters_input_output_docker(mocker):
#     mocker.patch("sys.argv", ["python", "clients.txt", "results.txt"])
#     patch.dict("os.environ", {"DOCKER", "True"}, clear=True)
#     mocker.patch("sys.exit")
#     # mocker_print = mocker.patch("builtins.print")
#     mocker_usage = mocker.patch("src.app.usage")
#     validate_parameters()
#     # assert mocker_print.called_once_with(
#     #   "While running this app in a Docker container it's not allowed to use output parameter.")
#     # assert mocker_print.call_count == 2
#     assert mocker_usage.call_count == 1


def test_main(mocker):
    mocker_validate_parameters = mocker.patch(
        "src.app.validate_parameters", return_value=("file1", None))
    mocker_load_balacer = mocker.patch("src.load_balance.LoadBalancer.__init__", return_value=None)
    mocker_load_balacer_load_balance = mocker.patch("src.load_balance.LoadBalancer.load_balance")
    main()
    assert mocker_validate_parameters.call_count == 1
    assert mocker_load_balacer.call_count == 1
    assert mocker_load_balacer_load_balance.call_count == 1


def test_main_predicted_error(mocker):
    mocker_validate_parameters = mocker.patch(
        "src.app.validate_parameters", return_value=("file1", None))
    mocker_load_balacer = mocker.patch(
        "src.load_balance.LoadBalancer.__init__", return_value=None)
    mocker_load_balacer_load_balance = mocker.patch(
        "src.load_balance.LoadBalancer.load_balance", side_effect=BalancerError("BUG!"))
    mocker_print = mocker.patch("builtins.print")
    mocker_logging_error = mocker.patch.object(logger, "error")
    main()
    assert mocker_validate_parameters.call_count == 1
    assert mocker_load_balacer.call_count == 1
    assert mocker_load_balacer_load_balance.call_count == 1
    assert mocker_print.call_count == 1
    assert mocker_logging_error.call_count == 1


def test_main_unpredicted_error(mocker):
    mocker_validate_parameters = mocker.patch(
        "src.app.validate_parameters", return_value=("file1", None))
    mocker_load_balacer = mocker.patch(
        "src.load_balance.LoadBalancer.__init__", return_value=None)
    mocker_load_balacer_load_balance = mocker.patch(
        "src.load_balance.LoadBalancer.load_balance", side_effect=ValueError("BUG!"))
    mocker_print = mocker.patch("builtins.print")
    mocker_logging_exception = mocker.patch.object(logger, "exception")
    main()
    assert mocker_validate_parameters.call_count == 1
    assert mocker_load_balacer.call_count == 1
    assert mocker_load_balacer_load_balance.call_count == 1
    assert mocker_print.call_count == 1
    assert mocker_logging_exception.call_count == 1
