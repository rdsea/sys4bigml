#!/bin/bash

curl --location --request POST 'localhost:8181/v0/data/sys4bigml/contract' -H 'Content-Type: application/json' 
curl --location --request GET 'localhost:8181/v1/policies/sys4bigml/violation' -H 'Content-Type: application/json' 