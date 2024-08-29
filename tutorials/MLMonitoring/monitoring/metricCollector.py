import curses
import threading
import json
import requests
import argparse
import logging
from qoa4ml.collector.amqp_collector import AmqpCollector
from qoa4ml.config.configs import AMQPCollectorConfig
from qoa4ml.utils import qoa_utils as utils

# Set logging level to WARNING to suppress INFO messages
logging.basicConfig(format="%(asctime)s:%(levelname)s -- %(message)s", level=logging.WARNING)

violation_count = 0
error_request_count = 0
violation_messages = []

def display_summary(stdscr):
    global violation_count, error_request_count, violation_messages

    # Initialize colors
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLUE)  
    curses.init_pair(2, curses.COLOR_RED, -1)  
    curses.init_pair(3, curses.COLOR_GREEN, -1) 

    # Clear the screen
    stdscr.clear()

    # Get screen dimensions
    height, width = stdscr.getmaxyx()

    # Prepare data for the table
    table_data = [
        ["Number of Violations", violation_count],
        ["Number of Error Requests", error_request_count],
    ]

    # Display the table with borders
    for i, row in enumerate(table_data):
        text = f"{row[0]}: {row[1]}"
        start_x = (width - len(text)) // 2
        color_pair = curses.color_pair(2 if row[0] == "Number of Violations" else 3)
        stdscr.addstr(i + 1, start_x, text, color_pair)

    # Draw a border around the table
    stdscr.attron(curses.color_pair(1))
    stdscr.border()
    stdscr.attroff(curses.color_pair(1))

    # Create a new window for the latest violation message
    msg_win_height = height - len(table_data) - 4
    msg_win_width = width - 4
    msg_win = curses.newwin(msg_win_height, msg_win_width, len(table_data) + 3, 2)
    msg_win.attron(curses.color_pair(1))
    msg_win.border()
    msg_win.attroff(curses.color_pair(1))

    # Display the latest violation message
    if violation_messages:
        msg_win.clear()
        msg_win.attron(curses.color_pair(1))
        msg_win.border()
        msg_win.attroff(curses.color_pair(1))
        for i, message in enumerate(violation_messages):
            row = i + 1
            if row < msg_win_height - 1:
                msg_win.addstr(row, 1, message)

    # Refresh the main window
    stdscr.refresh()
    msg_win.refresh()


class OPA_Reporter(object):
    def __init__(self, config: dict):
        self.config = config

    def message_processing(self, ch, method, properties, body):
        global violation_count, error_request_count, violation_messages

        mess = json.loads(str(body.decode('utf-8')))
        instance_id = mess["metadata"]["client_config"]["id"]
        stage_id = mess["metadata"]["client_config"]["stage_id"]
        response_time = mess["service"][stage_id]["metrics"]["response_time"][instance_id]["records"][0]["responseTime"]
        # logging.info(f"Stage: {stage_id} - Response time: {response_time}")
        
        # Construct the input data for the OPA policy
        input_data = {
            "input": {
                "stage_id":  stage_id,
                "response_time": response_time
            }
        }

        # Send a POST request to the OPA server with the input data
        response = requests.post(self.config["end_point"], headers={'Content-Type': 'application/json'}, data=json.dumps(input_data))
        # logging.info(f"Status Code: {response.status_code}")
        response_body = response.json()
        # logging.info(f"Response Body: {response_body}")

        # Update error counters based on the response
        if response.status_code != 200:
            error_request_count += 1

        # Update the violation count and messages
        result = response_body.get('result', [])
        if result and result[0].get('violation', False):
            violation_count += 1
            violation_messages = result[0].get('messages', []) + violation_messages 

def main(stdscr):
    # Parse arguments from the command line
    parser = argparse.ArgumentParser(description="QoA4ML collector")
    parser.add_argument("--conf", type=str, default="./collector.yaml", help="AMQP configuration file")
    args = parser.parse_args()

    # Load the configuration file
    conf = utils.load_config(args.conf)
    opa_conf = conf["opa"]

    # Create an OPA reporter object
    opa_reporter = OPA_Reporter(opa_conf)

    # Create an AMQP collector object
    ampq_conf = AMQPCollectorConfig(**conf["collector"])
    collector = AmqpCollector(configuration=ampq_conf, host_object=opa_reporter)
    
    # Start collecting in a separate thread
    collector_thread = threading.Thread(target=collector.start_collecting)
    collector_thread.start()

    # Main loop to update the display
    while True:
        display_summary(stdscr)
        stdscr.refresh()
        stdscr.timeout(1000)  # Refresh every second
        key = stdscr.getch()
        if key == ord('q'):  # Press 'q' to quit
            break

if __name__ == "__main__":
    curses.wrapper(main)