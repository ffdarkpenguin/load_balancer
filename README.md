
# Project Load Balancer Simulation

This project simulates a load balancer test to calculte the cost of running services on multiple
configuration. It's main goal is to find the lowest possible cost of running a given load of service
by twiking it's configuration while testing various scenarios.

It reads data from a text file containing one interger number per line. The first two numbers
are used for configuration. All others number are treated as new clients that requested a service
and so they need to be allocated to a given server. New servers must be launched if all running server
reached they maximun capacity.

The first configuration number is `ttask` which tells the app how many ticks are used per client request.
The second configuraiton number is `umax` which tells the maximum number of tasks (or clients requests)
a given server can handle. If no servers are running or all running servers are using all availables slots
new servers must be launched to accomodate the new tasks.

## Requirements

This project was implemented using Python 3.9. Some features used requires at least Python 3.8.

## Usage:

First install the requirements creating a virtual environment and stalling the packages in `requirements.txt` file:

    virtualenv -p python3.9 .venv
    source .venv/bin/activate
    pip install -r requirements.txt

Run the tests with pytest:

    pytest

Run the app using the sintaxe: `python src/app <INPUT_FILE> [OUTPUT_FILE]`

    python src/app clients.txt

`INPUT_FILE` is a required parameter and should point to a text file with one integer per line.

`OUTPUT_FILE` is an optional parameter to where the result should be sent. If no output file is provided the result is sent to `sys.stdout`

The app generates a log file with details of each run: server launched or removed, tasks assigned to a server and removed from a server. Also any predicted error will be logged to this file. Unpredicted errors are printed to `stdout` with the exception back track sent to the log file.

## Config file:

A configuration file was create in python format. The possible configurable values are:

    SERVER_COST = 1.0               # Server cost per tick
    TTASK_MIN = 1                   # Minimun value for ttask
    TTASK_MAX = 10                  # Maximun value for ttask
    UMAX_MIN = 1                    # Minimun value for umax
    UMAX_MAX = 10                   # Maximun value for umax
    OVERWRITE_DEST_FILE = True      # Defines if the out_file (if informed) can be orverwriten if it exists

## Containers:

If you don't have `Python 3.8+` in you system but have docker installed you can run the application and tests using docker. At this point you can not set an output file if you running the app using container. The results are going to be printed to `stdout` and you should redirect the result to a file if necessary.

To build an image for later use run:

    docker image build -t load_balancer .

The steps below assumes you built an image with the command above.

You can run the app with the default sample `clients.txt` include in this source code just typing:

    docker container run --rm load_balancer

If you need capture the output to a file use redirection:

    docker container run --rm load_balancer > results.txt

To run the app with another file that exists in the container image (the file was present in the project directory when the image was built):


    docker container run --rm load_balancer <INPUT_FILE>


To pass an input file not in the image to the container at run time use volumes:

    docker container run --rm -v /FULL/PATH/TO/MY/INPUT/FILE.TXT:/app/clients.txt load_balancer

This will "replace" the file /app/clients.txt with your new file. As the file `app/clients.txt` is the default parameter for the app you dont need to inform it.

To run the tests:

    docker container run --rm -it --entrypoint pytest load_balancer
