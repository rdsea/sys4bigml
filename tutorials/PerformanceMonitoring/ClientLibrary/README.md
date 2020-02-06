# Client Library

## Install Prometheus
Go to the download page and download the corresponding prometheus for your system. 

```console
user@test:~$ wget https://github.com/prometheus/prometheus/releases/download/v2.16.0-rc.0/prometheus-2.16.0-rc.0.linux-amd64.tar.gz

```

## Select the language and corresponding client library. Forexample: Python

```console
user@test:~$ python sample2.py

```


## Configure prometheus to monitor the python program sample2.py

Extract the folder prometheus-version.targ.gz and go inside the folder. Then perform the modifications such as follows:
```properties

scrape_configs:
  - job_name: 'sample2'

    # Override the global default and scrape targets from this job every 5 seconds.
    scrape_interval: 5s

    static_configs:
    - targets: ['localhost:8000']

```  


You can also modify the scrape_interval to an arbitrary number upon your demand. Then you can run prometheus

```console
user@test:~$ ./prometheus

```

You now go to prometheus http://yourhost:9090, and search for "hello_world_created". You should see now the value created by your program in prometheus. 



      
