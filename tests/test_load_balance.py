"""Tests LoadBalancer class"""
import subprocess

from pytest import fixture, raises
from mock import mock_open

from src.error import BalancerError
from src.load_balance import LoadBalancer

INPUT_FILE = "tests/input_test.txt"
OUTPUT_FILE = "tests/out_text.txt"
ACCESS_DENIED_IN_FILE = "tests/access_denied_file.txt"
ACCESS_DENIED_DIR = "tests/access_denied_dir"
ACCESS_DENIED_OUT_FILE = f"{ACCESS_DENIED_DIR}/out.txt"

# pylint: disable=protected-access
# pylint: disable=redefined-outer-name
# pylint: disable=missing-function-docstring
# pylint: disable=invalid-name


def clean_up():
    """Remove temporary files and directory created by any test function"""
    cmd = ["rm", "-rf", ACCESS_DENIED_IN_FILE, ACCESS_DENIED_DIR]
    subprocess.run(cmd, check=True)


@fixture
def lb():
    """Fixture to instanciate an object"""
    return LoadBalancer(INPUT_FILE, OUTPUT_FILE)


@fixture
def umax_lb():
    """Fixture to instanciate an object"""
    lb = LoadBalancer(INPUT_FILE, OUTPUT_FILE)
    lb._test_init_limit('ttask', 4, 1, 10)
    lb._test_init_limit('umax', 2, 1, 10)
    return lb


@fixture
def access_denied_file():
    """Fixture to create a file with no read permission"""
    clean_up()
    subprocess.run(f"touch {ACCESS_DENIED_IN_FILE} && chmod 000 {ACCESS_DENIED_IN_FILE}",
                   shell=True, check=True)
    yield ACCESS_DENIED_IN_FILE
    clean_up()


@fixture
def access_denied_dir():
    """Fixture to create a directory with no write permission"""
    clean_up()
    subprocess.run(f"mkdir {ACCESS_DENIED_DIR} && chmod 440 {ACCESS_DENIED_DIR}",
                   shell=True, check=True)
    yield ACCESS_DENIED_DIR
    clean_up()


def test_instance():
    lb = LoadBalancer(INPUT_FILE, OUTPUT_FILE)
    assert lb.file_in.name == INPUT_FILE
    assert lb.file_out.name == OUTPUT_FILE
    assert lb.ttask == 0
    assert lb.umax == 0
    assert bool(lb.servers_in_use) is False
    assert lb.tick_count == 0
    assert lb.tick_servers_count == 0
    assert lb.server_id_count == 0


def test_open_input_file(lb):
    lb._open_read(INPUT_FILE)
    assert lb.file_in.name == INPUT_FILE


def test_open_input_file_dont_exist(lb):
    with raises(BalancerError) as e:
        lb._open_read("tests/dont_exist.txt")
    assert "not found" in str(e)


def test_open_input_file_permission_denied(lb, access_denied_file):
    with raises(BalancerError) as e:
        lb._open_read(access_denied_file)
    assert "Access denied" in str(e)


def test_open_write_file(lb):
    lb._open_write(OUTPUT_FILE)
    assert lb.file_out.name == OUTPUT_FILE


def test_open_existing_write_file_overwrite(lb):
    lb._open_write(OUTPUT_FILE)
    assert lb.file_out.name == OUTPUT_FILE
    lb._open_write(OUTPUT_FILE)
    assert lb.file_out.name == OUTPUT_FILE


def test_open_existing_write_file_no_overwrite(lb, mocker):
    mocker.patch('src.load_balance.OVERWRITE_DEST_FILE', False)
    with raises(BalancerError) as e:
        lb._open_write(OUTPUT_FILE)
        lb._open_write(OUTPUT_FILE)
    assert "can't be overwriten" in str(e)


def test_open_existing_write_file_access_denied_dir(lb, access_denied_dir):
    with raises(BalancerError) as e:
        lb._open_write(f"{access_denied_dir}/out.txt")
    assert "Access denied to write to" in str(e)


def test_open_existing_write_file_path_dont_exist(lb):
    with raises(BalancerError) as e:
        lb._open_write("dont_exist/out.txt")
    assert "not a valid directory" in str(e)


def text_clean_up(lb):
    assert lb.file_in.closed is False
    assert lb.file_out.closed is False
    lb._clean_up()
    assert lb.file_in.closed is True
    assert lb.file_out.closed is True


def test_test_init_limit(lb):
    assert lb.ttask == 0
    lb._test_init_limit('ttask', 10, 1, 10)
    assert lb.ttask == 10


def test_test_init_limit_using_str(lb):
    assert lb.ttask == 0
    with raises(BalancerError) as e:
        lb._test_init_limit('ttask', '10', 1, 10)
    assert "must be an integer" in str(e)


def test_test_init_limit_using_float(lb):
    assert lb.ttask == 0
    with raises(BalancerError) as e:
        lb._test_init_limit('ttask', 5.1, 1, 10)
    assert "must be an integer" in str(e)


def test_test_init_limit_less_then_min(lb):
    assert lb.ttask == 0
    with raises(BalancerError) as e:
        lb._test_init_limit('ttask', 0, 1, 10)
    assert "must be greater then" in str(e)


def test_test_init_limit_greater_then_max(lb):
    assert lb.ttask == 0
    with raises(BalancerError) as e:
        lb._test_init_limit('ttask', 11, 1, 10)
    assert "must be lesser then" in str(e)


def test_launch_server(umax_lb, mocker):
    mocked_add_task_server = mocker.patch.object(umax_lb, "_add_task_server")
    assert umax_lb.server_id_count == 0
    assert len(umax_lb.servers_in_use) == 0
    assert umax_lb.umax == 2
    umax_lb._launch_server(1)
    assert umax_lb.server_id_count == 1
    assert len(umax_lb.servers_in_use) == 1
    assert "S-1" in umax_lb.servers_in_use
    assert mocked_add_task_server.call_count == 1


def test_launch_server_more_tasks(umax_lb, mocker):
    mocked_add_task_server = mocker.patch.object(umax_lb, "_add_task_server")
    assert umax_lb.server_id_count == 0
    assert len(umax_lb.servers_in_use) == 0
    assert umax_lb.umax == 2
    umax_lb._launch_server(2)
    assert umax_lb.server_id_count == 1
    assert len(umax_lb.servers_in_use) == 1
    assert "S-1" in umax_lb.servers_in_use
    assert mocked_add_task_server.call_count == 2


def test_launch_server_too_much_tasks(umax_lb):
    assert umax_lb.server_id_count == 0
    assert len(umax_lb.servers_in_use) == 0
    assert umax_lb.umax == 2
    with raises(BalancerError) as e:
        umax_lb._launch_server(3)
    assert "Invalid number of tasks" in str(e)


def test_add_task_server(umax_lb):
    umax_lb._launch_server(1)
    server_name = "S-1"
    assert server_name in umax_lb.servers_in_use
    assert len(umax_lb.servers_in_use[server_name]["tasks"]) == 1
    umax_lb._add_task_server(server_name)
    assert len(umax_lb.servers_in_use[server_name]["tasks"]) == 2


def test_add_task_server_invalid_server_name(umax_lb):
    assert len(umax_lb.servers_in_use) == 0
    with raises(BalancerError) as e:
        umax_lb._add_task_server("do_not_exist")
    assert "not found" in str(e)


def test_add_task_server_server_limit_reached(umax_lb):
    umax_lb._launch_server(2)
    server_name = "S-1"
    assert server_name in umax_lb.servers_in_use
    assert len(umax_lb.servers_in_use[server_name]["tasks"]) == 2
    with raises(BalancerError) as e:
        umax_lb._add_task_server(server_name)
    assert "can't start new task" in str(e)


def test_find_server_for_task(umax_lb):
    umax_lb._launch_server(1)
    assert umax_lb._find_server_for_task() == 'S-1'


def test_find_server_for_task_no_server_available(umax_lb):
    umax_lb._launch_server(2)
    assert umax_lb._find_server_for_task() is None


def test_add_new_clients_max_tasks(umax_lb, mocker):
    mocker_launch_server = mocker.patch.object(umax_lb, '_launch_server')
    mocker_find_server_for_task = mocker.patch.object(umax_lb, '_find_server_for_task')
    mocker_add_task_server = mocker.patch.object(umax_lb, '_add_task_server')
    umax_lb._add_new_clients(2)
    assert mocker_launch_server.called_once()
    assert mocker_find_server_for_task.call_count == 0
    assert mocker_add_task_server.call_count == 0


def test_add_new_clients_min_tasks_twice(umax_lb, mocker):
    mocker_launch_server = mocker.patch.object(umax_lb, '_launch_server')
    mocker_find_server_for_task = mocker.patch.object(umax_lb, '_find_server_for_task')
    mocker_add_task_server = mocker.patch.object(umax_lb, '_add_task_server')
    umax_lb._add_new_clients(1)
    assert mocker_launch_server.called_once_with(1)
    assert mocker_find_server_for_task.called_once()
    umax_lb._add_new_clients(1)
    assert mocker_add_task_server.called_once()
    assert mocker_find_server_for_task.call_count == 2


def test_remove_server(umax_lb):
    umax_lb._launch_server(1)
    server_name = "S-1"
    del umax_lb.servers_in_use[server_name]["tasks"]["T-1"]
    assert len(umax_lb.servers_in_use) == 1
    umax_lb._remove_server(server_name)
    assert len(umax_lb.servers_in_use) == 0


def test_remove_server_running_tasks(umax_lb):
    umax_lb._launch_server(1)
    with raises(BalancerError) as e:
        umax_lb._remove_server("S-1")
    assert "still has tasks running" in str(e)


def test_remove_server_unknown(umax_lb):
    with raises(BalancerError) as e:
        umax_lb._remove_server("S-1")
    assert "not found" in str(e)


def test_remove_task_server(umax_lb):
    umax_lb._launch_server(2)
    server_name = "S-1"
    assert len(umax_lb.servers_in_use[server_name]["tasks"]) == 2
    umax_lb._remove_task_server("T-1", server_name)
    assert len(umax_lb.servers_in_use[server_name]["tasks"]) == 1


def test_remove_task_server_invalid_server_name(umax_lb):
    umax_lb._launch_server(2)
    assert len(umax_lb.servers_in_use["S-1"]["tasks"]) == 2
    fake_server_name = "S-2"
    with raises(BalancerError) as e:
        umax_lb._remove_task_server("T-1", fake_server_name)
    assert f"Server {fake_server_name} not found" in str(e)


def test_remove_task_server_invalid_task_name(umax_lb):
    umax_lb._launch_server(2)
    server_name = "S-1"
    assert len(umax_lb.servers_in_use[server_name]["tasks"]) == 2
    fake_task_name = "S-2"
    with raises(BalancerError) as e:
        umax_lb._remove_task_server(fake_task_name, server_name)
    assert f"Task {fake_task_name} not found in server" in str(e)


def test_run_tick(umax_lb):
    umax_lb._add_new_clients(4)
    assert umax_lb.tick_servers_count == 0
    assert len(umax_lb.servers_in_use) == 2
    server1_name = "S-1"
    assert len(umax_lb.servers_in_use[server1_name]["tasks"]) == 2
    assert umax_lb.servers_in_use[server1_name]["tasks"]["T-1"] == umax_lb.ttask
    assert umax_lb.servers_in_use[server1_name]["tasks"]["T-2"] == umax_lb.ttask
    ret = umax_lb._run_tick()
    assert ret == "2, 2"
    assert umax_lb.tick_servers_count == 2
    assert len(umax_lb.servers_in_use) == 2
    assert len(umax_lb.servers_in_use[server1_name]["tasks"]) == 2
    assert umax_lb.servers_in_use[server1_name]["tasks"]["T-1"] == umax_lb.ttask - 1
    assert umax_lb.servers_in_use[server1_name]["tasks"]["T-2"] == umax_lb.ttask - 1


def test_run_tick_remove_task_server(umax_lb, mocker):
    spy_remove_task_server = mocker.spy(umax_lb, "_remove_task_server")
    spy_remove_server = mocker.spy(umax_lb, "_remove_server")
    umax_lb._add_new_clients(2)
    assert umax_lb.tick_servers_count == 0
    assert len(umax_lb.servers_in_use) == 1
    print(umax_lb.servers_in_use)
    for _i in range(umax_lb.ttask):
        umax_lb._run_tick()
    print(umax_lb.servers_in_use)
    assert spy_remove_task_server.call_count == 2
    assert spy_remove_server.call_count == 1


def test_get_next_tick_clients(mocker):
    mocked_f = mock_open(read_data="1")
    mocker_readline = mocker.patch("builtins.open", mocked_f)
    lb = LoadBalancer(INPUT_FILE, None)
    assert lb._get_next_tick_clients() == 1
    assert mocker_readline.call_count == 1


def test_get_next_tick_clients_EOF(mocker):
    mocked_f = mock_open(read_data="")
    mocker_readline = mocker.patch("builtins.open", mocked_f)
    lb = LoadBalancer(INPUT_FILE, None)
    assert lb._get_next_tick_clients() is None
    assert mocker_readline.call_count == 1


def test_print_result(lb, mocker):
    mocker_print_result = mocker.patch("builtins.print")
    lb._print_result("test")
    assert mocker_print_result.called_once_with("test")


def test_init_limits(lb, mocker):
    mocker_test_init_limit = mocker.patch.object(lb, "_test_init_limit")
    mocker_get_next_tick_clients = mocker.patch.object(lb, "_get_next_tick_clients", return_value=2)
    lb._init_limits()
    assert mocker_get_next_tick_clients.call_count == 2
    assert mocker_test_init_limit.call_count == 2


def test_run_cicle_with_tasks(lb, mocker):
    mocker_add_new_clients = mocker.patch.object(lb, "_add_new_clients")
    mocker_run_tick = mocker.patch.object(lb, "_run_tick", return_value="anything")
    mocker_print_result = mocker.patch.object(lb, "_print_result")
    ret = lb._run_cicle(1)
    assert mocker_add_new_clients.run_once_with(1)
    assert mocker_run_tick.run_once()
    assert mocker_print_result.run_once_with("something")
    assert ret is True


def test_run_cicle_no_tasks(lb, mocker):
    mocker_add_new_clients = mocker.patch.object(lb, "_add_new_clients")
    mocker_run_tick = mocker.patch.object(lb, "_run_tick", return_value="")
    mocker_print_result = mocker.patch.object(lb, "_print_result")
    ret = lb._run_cicle(None)
    assert mocker_add_new_clients.call_count == 0
    assert mocker_run_tick.run_once()
    assert mocker_print_result.call_count == 0
    assert ret is False


def test_load_balance(lb, mocker):
    mocker_init_limits = mocker.patch.object(lb, "_init_limits")
    mocker_get_next_tick_clients = mocker.patch.object(
        lb, "_get_next_tick_clients", side_effect=[1, None, None])
    mocker_run_cicle = mocker.patch.object(lb, "_run_cicle", side_effect=[True, False])
    mocker_print_result = mocker.patch.object(lb, "_print_result")
    mocker_clean_up = mocker.patch.object(lb, "_clean_up")
    lb.load_balance()
    assert mocker_init_limits.call_count == 1
    assert mocker_get_next_tick_clients.call_count == 3
    assert mocker_run_cicle.call_count == 2
    assert mocker_print_result.called_once_with(0)
    assert mocker_clean_up.call_count == 1
