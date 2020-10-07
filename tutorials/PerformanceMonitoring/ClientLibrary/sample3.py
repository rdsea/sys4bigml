# Prometheus
import http.server
from prometheus_client import start_http_server
from prometheus_client import Summary

LATENCY = Summary('pipeline_perf_seconds', 'Time for a request the pipeline.')

class myFloat( float ):
    def __str__(self):
        return "%.12f"%self


class MyHandler(http.server.BaseHTTPRequestHandler):
    @LATENCY.time()
    def do_GET(self):
        # Set starting time
        start = time.time()

        # 1. Add dataset
        filename = 'pima-indians-diabetes.data.csv'
        names = ['preg', 'plas', 'pres', 'skin', 'test', 'mass', 'pedi', 'age', 'class']

        # 2. Processing data
        dataframe = read_csv(filename, names=names)
        array = dataframe.values
        X = array[:, 0:8]
        Y = array[:, 8]

        test_size = 0.33
        seed = 7

        # 3. Training the data
        X_train, X_test, Y_train, Y_test = train_test_split(X, Y, test_size=test_size, random_state=seed)

        model = LogisticRegression()
        model.fit(X_train, Y_train)

        # 4. Get the result
        result = model.score(X_test, Y_test)

        # print("Accuracy: %.3f%%" % (result * 100.0))
        x = myFloat(result * 100.0)
        message = str(x)

        # 5. Send the result to the web
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Pipeline Accuracy:\n")
        self.wfile.write(message.encode())

        # 6. Get the performance of the pipeline
        LATENCY.observe(time.time() - start)


if __name__ == "__main__":
    start_http_server(8000)
    server = http.server.HTTPServer(('localhost', 8001), MyHandler)
    server.serve_forever()

# rate(pipeline_perf_seconds_count[5m])