#!/bin/bash

curl --location --request PUT '195.148.22.62:8181/v1/data/bts/contract' -H 'Content-Type: application/json' -d @contract.json
