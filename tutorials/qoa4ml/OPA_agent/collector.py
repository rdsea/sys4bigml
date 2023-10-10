from qoa4ml.collector.amqp_collector import Amqp_Collector
from qoa4ml import qoaUtils as utils

import json, copy
import pandas as pd
from os.path import exists as file_exists
from opa_client.opa import OpaClient
from prometheus_client import Gauge, start_http_server


default_schema = {'client_id': pd.Series(dtype='str'),
        'application_id': pd.Series(dtype='str'),
        'service': pd.Series(dtype='str'),
        'interval': pd.Series(dtype='int'),
        'node_name': pd.Series(dtype='str'),
        'runtime': pd.Series(dtype='float')}
print(type(default_schema))

df_process_schema = {'cpu-time-user': pd.Series(dtype='float'),
        'cpu-time-sys': pd.Series(dtype='float'),
        'cpu-time-io': pd.Series(dtype='float'),
        'memory-rss': pd.Series(dtype='float')}

df_app_schema = {'Timestamp': pd.Series(dtype='float'),
        'Responsetime': pd.Series(dtype='float')}

class Monitoring_collector(object):
    def __init__(self, process_schema=None, app_schema=None, f_report='./qoa_contract/report.json') -> None:
        if process_schema == None:
            process_schema = df_process_schema
        if app_schema == None:
            app_schema = df_app_schema
        default_schema.update(process_schema)
        self.process_df = pd.DataFrame(default_schema)
        print(self.process_df.info)
        self.opa_client = OpaClient()
        self.report = json.load(open(f_report))
        self.proc_cpu_time = {}
        self.proc_mem = {}
        self.prom_id = 0

    def message_processing(self, ch, method, props, body):
        mess = json.loads(str(body.decode("utf-8")))
        app_metric = None
        if 'quality' in mess:
            app_metric = mess.pop('quality')
            for key in app_metric:
                mess[key] = app_metric[key]
            report = self.report

            
            # This code is sending default report to OPA
            # TO DO:
            # Get quality metric from "mess" and send to OPA

 
            report['client_info']['id'] = mess['metadata']['client_id']
            qoa_response = self.opa_client.check_policy_rule(input_data=report, package_path="qoa4ml.object_detection", rule_name="violation")
            print(qoa_response)


        if 'proc_cpu_stats' in mess:
            process_metric = mess.pop('proc_cpu_stats')
            for key in process_metric:
                mess[key] = process_metric[key]
            client_id = mess['metadata']['client_id']
            stage_id = mess['metadata']['stage_id']
            instance_id = mess['metadata']['instance_name']
            
            if not (client_id in self.proc_cpu_time):
                self.proc_cpu_time[client_id] = {}
            if not (stage_id in self.proc_cpu_time[client_id]):
                self.proc_cpu_time[client_id][stage_id] = {}
            if not (instance_id in self.proc_cpu_time[client_id][stage_id]):
                self.proc_cpu_time[client_id][stage_id][instance_id] = Gauge('process_cpu_time_'+str(self.prom_id), "CPU-Time of process in user mod of "+str(instance_id))
                self.prom_id += 1
            cpu_key = list(process_metric.keys())[0]
            self.proc_cpu_time[client_id][stage_id][instance_id].set(process_metric[cpu_key]['user'])
            mess_df = pd.DataFrame(process_metric[cpu_key], index=[0]) 
            mess_df.to_csv('process_monitor.csv', mode='a', index=False, header= not file_exists('process_monitor.csv'))
        
        # Above code report 'cpu stats' to Prometheus
        # TO DO:
        # Report 'memory stats' to Prometheus 

        

start_http_server(8989)
connetor_conf = utils.load_config("./collector.yaml")
monitor_col = Monitoring_collector()
client = Amqp_Collector(connetor_conf['collector'],monitor_col)
client.start()



