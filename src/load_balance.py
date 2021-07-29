"""Implments LoadBalancer class """
import logging
import os
import sys

from src.error import BalancerError
from src.conf import SERVER_COST, TTASK_MIN, TTASK_MAX, UMAX_MIN, UMAX_MAX, OVERWRITE_DEST_FILE


logger = logging.getLogger(__name__)


class LoadBalancer():
    """Reads clients loads per tick from a file and simulate the load distributes accros multiple
       servers"""
    # pylint: disable=too-many-instance-attributes
    def __init__(self, file_in, file_out=None):
        self.file_in = None
        self.file_out = None
        self.ttask = 0
        self.umax = 0
        self.servers_in_use = {}
        self.tick_count = 0
        self.tick_servers_count = 0
        self.server_id_count = 0
        self._open_read(file_in)
        self._open_write(file_out)

    def _open_read(self, file_name):
        """Checks if the input file is OK, open it and set it to self.file_in"""
        if not os.path.isfile(file_name):
            raise BalancerError(f"Input file {file_name} not found.")
        if not os.access(file_name, os.R_OK):
            raise BalancerError(f"Access denied to file {file_name}.")
        self.file_in = open(file_name, "rt")

    def _open_write(self, file_name):
        """Checks if the output file is OK, open it in write mode and set it to self.file_out"""
        if file_name is None:
            self.file_out = sys.stdout
            return

        if not (file_dir := os.path.dirname(file_name)):
            file_dir = "./"
        else:
            if not os.path.isdir(file_dir):
                raise BalancerError("Path '{file_dir}' is not a valid directory.")
        if not os.access(file_dir, os.W_OK):
            raise BalancerError("Access denied to write to direcoty '{file_dir}'.")
        if os.path.isfile(file_name):
            if not OVERWRITE_DEST_FILE:
                raise BalancerError("Destination file already exists and can't be overwriten. "
                                    "You can change default behavior in conf file. "
                                    "Look for OVERWRITE_DEST_FILE.")
        if not os.access(file_name, os.W_OK):
            raise BalancerError("Access denied to write to file '{file_dir}'.")
        self.file_out = open(file_name, "wt")

    def _clean_up(self):
        logger.info("Closing all files...")
        self.file_in.close()
        self.file_out.close()

    def _test_init_limit(self, limit, value, min_value, max_value):
        if not isinstance(value, int):
            raise BalancerError("Value must be an integer.")
        if value < min_value:
            raise BalancerError(f"{limit} must be greater then or equal to '{min_value}'.")
        if value > max_value:
            raise BalancerError(f"{limit} must be lesser then or equal to '{max_value}'.")
        setattr(self, limit, value)

    def _launch_server(self, number_tasks):
        if number_tasks > self.umax:
            raise BalancerError(
                f"Invalid number of tasks. Each server suports at most {self.umax} tasks.")
        self.server_id_count += 1
        server_name = f"S-{self.server_id_count}"
        logger.info("Launching server %s", server_name)
        new_server = {"tasks_count": 0, "tasks": {}}
        self.servers_in_use[server_name] = new_server
        for _new_task in range(number_tasks):
            self._add_task_server(server_name=server_name)

    def _add_task_server(self, server_name):
        if server_name not in self.servers_in_use:
            raise BalancerError("Server {server_name} not found among running servers.")
        if len(self.servers_in_use[server_name]["tasks"]) == self.umax:
            raise BalancerError("Server {server_name} can't start new task. Limit 'umax' reached.")
        self.servers_in_use[server_name]["tasks_count"] += 1
        task_name = f"T-{self.servers_in_use[server_name]['tasks_count']}"
        logger.info("Adding task %s to server %s", task_name, server_name)
        self.servers_in_use[server_name]["tasks"][task_name] = self.ttask

    def _find_server_for_task(self):
        servers_available = {}
        for srv_name, srv in self.servers_in_use.items():
            ticks_left = self.umax - len(srv["tasks"])
            if ticks_left > 0:
                servers_available[ticks_left] = srv_name
        if servers_available:
            return sorted(servers_available.items())[0][1]
        return None

    def _add_new_clients(self, new_clients):
        """Add new clients"""
        new_full_servers = new_clients // self.umax
        rest_new_clients = new_clients % self.umax
        for _i in range(new_full_servers):
            self._launch_server(number_tasks=self.umax)
        for _i in range(rest_new_clients):
            if server := self._find_server_for_task():
                self._add_task_server(server)
                rest_new_clients -= 1
            else:
                self._launch_server(number_tasks=rest_new_clients)
                break

    def _remove_server(self, server_name):
        """"Removes a given server if it has no tasks running."""
        if server_name not in self.servers_in_use:
            raise BalancerError(f"Server {server_name} not found.")
        if len(self.servers_in_use[server_name]["tasks"]) > 0:
            raise BalancerError(f"Server {server_name} still has tasks running. Can't remove it!")
        logger.info("Remove server: %s", server_name)
        del self.servers_in_use[server_name]

    def _remove_task_server(self, task_name, server_name):
        """Removes a given task from a given server."""
        if server_name not in self.servers_in_use:
            raise BalancerError(f"Server {server_name} not found.")
        if task_name not in self.servers_in_use[server_name]["tasks"]:
            raise BalancerError(f"Task {task_name} not found in server {server_name}.")
        logger.info("Removing task %s from server %s", task_name, server_name)
        del self.servers_in_use[server_name]["tasks"][task_name]

    def _run_tick(self):
        """Simulates a tick run.

           Generates a list of running servers this cicle.
           Updates the counters of running servers per tick (tick_servers_count) for use
           to calculate the cost of the simulation.
           Decrements the ticks left from each task running on each server. If the task is
           complete (0 ticks left to run) removes it. If the server has no tasks runiing
           removes it too.
           Returns a comma separated string with tasks per server in this cicle."""
        running_tasks_servers = [str(len(x["tasks"])) for x in self.servers_in_use.values()]
        self.tick_servers_count += len(running_tasks_servers)
        for server_name, server in list(self.servers_in_use.items()):
            for task in list(server["tasks"].keys()):
                server["tasks"][task] -= 1
                if server["tasks"][task] == 0:
                    self._remove_task_server(task, server_name)
            if len(server["tasks"]) == 0:
                self._remove_server(server_name)
        return ", ".join(running_tasks_servers)

    def _get_next_tick_clients(self):
        """Reads the next number in the file provided by the user."""
        try:
            return int(self.file_in.readline().strip())
        except ValueError:
            return None

    def _print_result(self, msg):
        """Prints the msg to the file opened at self.file_out"""
        self.file_out.write(f"{msg}\n")

    def _init_limits(self):
        """Init ttask and umax"""
        self._test_init_limit("ttask", self._get_next_tick_clients(), TTASK_MIN, TTASK_MAX)
        self._test_init_limit("umax", self._get_next_tick_clients(), UMAX_MIN, UMAX_MAX)

    def _run_cicle(self, new_clients):
        """Runs a tick cicle

           If there are new clients add them to available or new servers.
           Run a tick for each server/task.
           If this run make any work writes server load to out_file and returns True
           If no work is done (no new clients and no tasks/servers running) returns False"""
        self.tick_count += 1
        logger.info("Tick: %s New clients: %s", self.tick_count, new_clients)
        if new_clients:
            self._add_new_clients(new_clients)
        tick_run_result = self._run_tick()
        if tick_run_result:
            self._print_result(tick_run_result)
            return True
        return False

    def load_balance(self):
        """Simulates a load_balencer with the implemented logic.

           Read configuration (umax and ttask) and # of new clients from a file provided by the
           user. Prints total cost when no more clients in the file and no more servers runing.
           Writes the total cost to outfile and closes all files before exit."""
        self._init_limits()
        pending_tasks = False
        while (new_clients := self._get_next_tick_clients()) or pending_tasks:
            pending_tasks = self._run_cicle(new_clients)
        self._print_result(self.tick_servers_count * SERVER_COST)
        self._clean_up()
