# 03-cluster-kubernetes-tracing

## Study Goals
This tutorial demonstrates how to set up end-to-end tracing in a hybrid "edge-cloud" environment. You will learn to:
- Deploy an observability backend (OpenTelemetry Collector, Jaeger, Elasticsearch) to a Kubernetes cluster.
- Deploy application services to both a Kubernetes cluster ("cloud") and a local Docker container ("edge").
- Configure services to send traces to a central OpenTelemetry Collector.
- Visualize end-to-end traces that span across the Docker and Kubernetes environments.

## Prerequisites
- minikube
- kubectl
- Helm
- Docker

## Architecture
This tutorial implements a hybrid architecture:
- **Cloud Environment (Kubernetes):** The main application logic (`ensemble`, `efficientnetb0`, `mobilenetv2`) and the entire observability stack (Collector, Jaeger, Elasticsearch) run in a minikube cluster.
- **Edge Environment (Docker):** The `preprocessing` service runs as a container on your local machine, simulating an edge device.
- **Tracing Flow:** The `preprocessing` service on the edge sends traces to the OpenTelemetry Collector in the cluster via an Ingress. The services within the cluster also send their traces to the Collector. The Collector then exports these traces to Jaeger, which uses Elasticsearch for storage.

## Hands-on Steps

### Part 1: Cluster Setup
1. **Start Minikube:**
   ```bash
   minikube start --cpus=4 --memory=8g
   ```

2. **Install Traefik Ingress Controller:**
   ```bash
   helm repo add traefik https://traefik.github.io/charts
   helm repo update
   kubectl create namespace traefik
   helm install traefik traefik/traefik --namespace traefik
   ```

3. **Expose Cluster Services:**
   Enable external access to your cluster. The easiest way is to use `minikube tunnel`.
   ```bash
   minikube tunnel
   # OR
   ./infrastructure/metallb.sh
   ```
   Keep this command running in a separate terminal.

4. **Configure Hostnames:**
   Find the external IP address of the Traefik proxy service and add it to your `/etc/hosts` file.
   ```bash
   # Get the IP address
   kubectl get svc -n traefik traefik -o jsonpath='{.status.loadBalancer.ingress[0].ip}'

   # Add the following lines to your /etc/hosts file, replacing <IP_ADDRESS> with the output from the command above
   <IP_ADDRESS> jaeger.softsys.com
   <IP_ADDRESS> otel-collector.softsys.com
   ```

### Part 2: Deploying the Observability Backend
1. **Create Namespace:**
   ```bash
   kubectl create namespace observability
   ```

2. **Install Elasticsearch:**
   This will install Elasticsearch from the Elastic Helm charts, using the provided configuration.
   ```bash
   cd infrastructure
   helm repo add elastic https://helm.elastic.co
   helm install elasticsearch elastic/elasticsearch -n observability -f value_elasticsearch.yaml
   ```

3. **Create Jaeger Secrets:**
   Create secrets for Jaeger to securely connect to Elasticsearch.
   ```bash
   # Get the Elasticsearch CA certificate
   kubectl get secret elasticsearch-master-certs -n observability -o jsonpath="{.data['ca\.crt']}" | base64 --decode > ca.crt
   kubectl create secret generic jaeger-es-ca --from-file=ca.crt=./ca.crt -n observability
   # to get password
   kubectl get secret -n observability elasticsearch-master-credentials -o yaml
   # Create the secret with Elasticsearch credentials
   kubectl create secret generic jaeger-es-creds -n observability \
     --from-literal=ES_USERNAME=elastic \
     --from-literal=ES_PASSWORD='rVXiXmQvz9lCk2qZ'
   ```

4. **Deploy Collectors and Jaeger:**
   Deploy the OpenTelemetry Collector, Jaeger Collector, and Jaeger Query services.
   ```bash
   cd ../deployment
   kubectl apply -f .
   ```

### Part 3: Deploying the Application
1. **Deploy the "Cloud" Services:**
   Deploy the `ensemble` and inference services to your Kubernetes cluster.
   ```bash
   cd ../application/cluster
   kubectl apply -f .
   ```

2. **Deploy the "Edge" Service:**
   In a new terminal, start the `preprocessing` service using Docker Compose.
   ```bash
   cd ../edge
   docker compose up -d
   ```

### Part 4: Running a Test
1. **Generate a request:**
   From the `03-cluster-kubernetes-tracing` directory, run the client script to send a request to the edge service.
   ```bash
   # Make sure you have the necessary python packages installed (requests, etc.)
   python ../loadgen/client_processing.py --url http://localhost:5010/preprocessing
   ```

2. **Visualize the trace:**
   Open your browser and navigate to `http://jaeger.softsys.com`. You should see the Jaeger UI. Search for traces for the `preprocessing` service to see the full, end-to-end trace that includes spans from both the Docker container and the Kubernetes pods.

## Cleanup
1. **Stop the edge service:**
   ```bash
   cd application/edge
   docker compose down
   ```

2. **Delete Kubernetes resources:**
   ```bash
   kubectl delete -f application/cluster/
   kubectl delete -f deployment/
   helm delete elasticsearch -n observability
   kubectl delete namespace observability
   ```

3. **Stop Minikube:**
   ```bash
   minikube stop
   ```
