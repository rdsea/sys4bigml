import json
import requests


class QoaConnector(object):
    def __init__(self, header, method):
        # TO DO:
        self.header = header
        self.method = method

    def send(self, url, qoa_report):
        response = requests.request(self.method, url, headers=self.header, data = qoa_report)
        # return the response with the corresponding ID
        return json.loads(response.text.encode('utf8'))["result"]