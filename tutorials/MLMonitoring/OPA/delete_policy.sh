#!/bin/bash

curl --location --request DELETE 'localhost:8181/v1/policies/sys4bigml/violation' -H 'Content-Type: application/json'
curl --location --request PUT 'localhost:8181/v1/data/sys4bigml/contract' -H 'Content-Type: application/json' -d @contract.json