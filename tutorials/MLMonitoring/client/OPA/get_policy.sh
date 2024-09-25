#!/bin/bash

curl --location --request POST 'opa:8181/v0/data/sys4bigml/contract' -H 'Content-Type: application/json' 
curl --location --request GET 'opa:8181/v1/policies/sys4bigml/violation' -H 'Content-Type: application/json' 