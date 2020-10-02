# Client Library
For monitoring the metrics of your program, for instance, a python program, you can client api provided by prometheus to log all the metrics. Then you should export the information to an endpoint such as a http port (8000) or a web application port (5000), etc. You can follow the instruction below to practice monitor your python program using prometheus.

## Install Prometheus
Go to the download page and download the corresponding prometheus for your system. 

```console
user@test:~$ wget https://github.com/prometheus/prometheus/releases/download/v2.16.0-rc.0/prometheus-2.16.0-rc.0.linux-amd64.tar.gz

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

## Select the language and corresponding client library. Forexample: Python
After configuring prometheus and run it. You can start to run your python program:

```console
user@test:~$ python sample2.py

```

Prometheus will collect all the metrics of your program. Then you now can go to prometheus http://yourhost:9090, and search for the collected metrics, for example, the "hello_world_created". You should see now the value created by your program in prometheus. The sample3.py is an extension of sample2.py, where we add a machine learning pipeline to the code instead of printing only the hello world text. This is an example that let you know how to monitor your code using prometheus. 

In order to run the code, you do the same as the aboved command:

```console
user@test:~$ python sample3.py

```

Now, you can go to the local address http://localhost:8001 to see the accuracy of the pipeline. Check in the prometheus, you will see the performance of your pipeline. 


      
