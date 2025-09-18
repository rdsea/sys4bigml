#!/bin/sh
exec locust -f load_test.py --headless "$@"
