"""Main application: launches loadbalancer app"""
import logging
from os import environ
import sys

from src.error import BalancerError
from src.load_balance import LoadBalancer

logging.basicConfig(
    level=logging.DEBUG,
    filename="balancer.log",
    format="%(asctime)s - %(levelname)s - %(name)s:%(lineno)d - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

logger = logging.getLogger(__name__)


def usage():
    "Prints how to use this program and exits with error."
    if "DOCKER" in environ and environ["DOCKER"] == "True":
        print("USAGE - Docker mode: load_balance INPUT_FILE")
    else:
        print("USAGE: load_balance INPUT_FILE [OUTPUT_FILE]")
    sys.exit(1)


def validate_parameters():
    """Validates the paramters used to call the app"""
    param_count = len(sys.argv)
    if param_count < 2 or param_count > 3:
        usage()
    if param_count == 3:
        if "DOCKER" in environ and environ["DOCKER"] == "True":
            print("While running this app in a Docker container it's not allowed to use output "
                  "parameter.")
            usage()
        out_file = sys.argv[2]
    else:
        out_file = None

    in_file = sys.argv[1]
    return in_file, out_file


def main():
    """Main app function. Starts the app"""
    in_file, out_file = validate_parameters()
    # pylint: disable=broad-except
    # pylint: disable=invalid-name
    try:
        lb = LoadBalancer(in_file, out_file)
        lb.load_balance()
    except BalancerError as e:
        logger.error(e)
        print(e)
    except Exception:
        logger.exception("System failure - unpredicted error")
        print("Internal failure, please check the logs for more detail.")


if __name__ == "__main__":
    main()
