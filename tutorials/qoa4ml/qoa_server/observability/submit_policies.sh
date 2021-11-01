#!/bin/bash

curl --location --request PUT '195.148.22.62:8181/v1/policies/bts' -H 'Content-Type: text/plain' --data-binary @bts.rego
