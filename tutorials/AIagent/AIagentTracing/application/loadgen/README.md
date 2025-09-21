# Client for testing the application

## Running the client

```bash
locust -f load_test.py --host http://localhost:5010 --headless --user 10 --spawn-rate 1 --run-time 1m
```

## Using docker

```bash
docker run --network host rdsea/object_detection_client:latest --host http://localhost:5010 --user 10 --spawn-rate 1
```
