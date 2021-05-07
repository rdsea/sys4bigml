'''
TODO: not runnable, just template
Maybe we replace HTTP.server with other rest frameworks
'''
import http.server
import time
import json
from prometheus_client import start_http_server
from prometheus_client import Summary

'''
define  metrics which will be captured through the instrumentation of client library.
see https://github.com/prometheus/client_python
'''
SERVICETIME = Summary('MLServiceTime', 'Service Time')


'''
Template to be filled
'''
class MyHandler(http.server.BaseHTTPRequestHandler):
    @SERVICETIME.time()
    def do_GET(self):
        '''
        Set starting time
        '''
        start = time.time()

        '''
        Load model and do serving
        TODO: to be elaborated
        '''

        self.send_response(200)
        self.end_headers()
        message={"message":"here is the result"}
        self.wfile.write(json.dumps(message).encode())
        '''
        can try with other metrics
        '''
        SERVICETIME.observe(time.time() - start)


if __name__ == "__main__":
    '''
    FIXME: port and other info via configuration parameters
    '''
    '''
    prometheus endpoint
    '''
    start_http_server(8000)
    '''
    ML service
    '''
    server = http.server.HTTPServer(('localhost', 8001), MyHandler)
    server.serve_forever()
