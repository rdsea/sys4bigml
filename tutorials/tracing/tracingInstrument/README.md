# Teaching-tracinginstrument


## Download tutorials from opentelemetry-python with auto-instrumetation

```bash
git clone -n --depth=3 --filter=tree:0 https://github.com/open-telemetry/opentelemetry-python
cd opentelemetry-python
git sparse-checkout set --no-cone docs/examples/auto-instrumentation
git checkout
```

## Requirement

To execute this auto-instrumetation, we need to create virtualenv and then dependencies.
```bash
# create virtualenv by yourself
mkdir auto-instrumetation
cd auto-instrumetation
python -m venv venv
source ./venv/bin/activate

# install requirements
pip install opentelemetry-distro
pip install flask requests

# then 
opentelemetry-bootstrap -a install
```

## Execute

### Server-manual

```bash
# 1st terminal
python server_manual.py

# 2nd terminal
python client.py YOLO # or any text you want 
```

### Server-automatic

```bash
# 1st terminal
opentelemetry-instrument --traces_exporter console --metrics_exporter none python server_automatic.py
# 2nd terminal
python client.py Hong3Nguyen # or any text you want 
```

### Server-programatic 

```bash
# 1st terminal
python server_programmatic.py
# 2nd terminal
python client.py Hong3Nguyen # or any text you want
```
