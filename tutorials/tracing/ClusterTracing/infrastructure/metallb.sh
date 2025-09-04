#!/usr/bin/env bash

set -euo pipefail
IFS=$'\n\t'

# Optional overrides: export START and END before running to choose a different last-octet range
START=${START:-2}
END=${END:-250}

# sanity checks
re='^[0-9]+$'
if ! [[ $START =~ $re && $END =~ $re ]]; then
  echo "ERROR: START and END must be integers (1-254). Got START=$START END=$END" >&2
  exit 2
fi
if ((START < 1 || START > 254 || END < 1 || END > 254 || START > END)); then
  echo "ERROR: invalid range: ${START}-${END}" >&2
  exit 2
fi

# Ensure minikube is running and get its IP
if ! minikube status >/dev/null 2>&1; then
  echo "ERROR: minikube does not appear to be running. Start minikube first." >&2
  exit 3
fi

minikube_ip="$(minikube ip 2>/dev/null || true)"
if [ -z "$minikube_ip" ]; then
  echo "ERROR: 'minikube ip' returned empty. Is minikube running?" >&2
  exit 4
fi

prefix="${minikube_ip%.*}"
address_range="${prefix}.${START}-${prefix}.${END}"

echo $prefix
echo $address_range

echo "Using minikube IP: $minikube_ip -> address pool: $address_range"

# enable addons (idempotent)
echo "Enabling ingress and metallb addons..."
minikube addons enable ingress
minikube addons enable metallb

# wait for metallb-system namespace to exist (timeout)
echo "Waiting for metallb-system to appear..."
for i in $(seq 1 30); do
  if kubectl get ns metallb-system >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

if ! kubectl get ns metallb-system >/dev/null 2>&1; then
  echo "WARNING: metallb-system namespace not found after waiting." >&2
fi

# create the ConfigMap (this will create or update)
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: ConfigMap
metadata:
  namespace: metallb-system
  name: config
data:
  config: |
    address-pools:
    - name: default
      protocol: layer2
      addresses:
      - ${address_range}
EOF

echo "Applied MetalLB address-pool: ${address_range}"
# echo "Verify with: kubectl -n metallb-system get configmap config -o yaml"
# echo "Then check MetalLB pods: kubectl -n metallb-system get pods"
