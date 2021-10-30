from flask import Flask, request
from LSTM_Prediction_Server import LSTM_Prediction_Server
import time, argparse, json

if __name__ == '__main__':
    # Parse the input args
    parser = argparse.ArgumentParser(description="Data processing")
    parser.add_argument('--conf', help='configuration file', default='./server.json')
    # parser.add_argument('--next_ip', help='next destination ip', required=False)
    # parser.add_argument('--next_port', help='next destination ip', required=False)
    args = parser.parse_args()
    config_data = json.load(open(args.conf))
    # if args.next_ip != None:
    #     config_data["sender"][0]["info"]["url"] = "tcp://" + args.next_ip + ":"+args.next_port
    task = LSTM_Prediction_Server(config_data)
    print("start the loop")
    task.start()
