#!/bin/bash

docker run -p 8181:8181 openpolicyagent/opa -d run --server --log-level debug