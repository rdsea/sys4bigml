import sys
import json
import argparse
sys.path.append("../")
from qoa4ml_lib.qoa4ml.handlers import Mess_Handler


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Message Handler")
    parser.add_argument('--qoaInfo',help='qoa information file', default="./qoa_config.json")
    parser.add_argument('--prometheus',help='prometheus port', default=9098)
    args = parser.parse_args()
    with open(args.qoaInfo, "r") as f:
        qoa_info = json.load(f)
        print(qoa_info)
    OPA_object = Mess_Handler(qoa_info,prom=True)
    print("============================ OPA is running - Waiting for client ============================")
    OPA_object.start()