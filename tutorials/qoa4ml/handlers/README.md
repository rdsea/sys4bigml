# QoA4ML Handler
* a qoa4ml handler is a component that takes observed data, which is in qoa4ml reports, and sends the qoa4ml reports to observability service
* a qoa4ml handler can also take observed data in other formats, transforms the data to qoa4ml report and sends to observability
* a qoa4ml handler can take data from files, broker or rest api (different connectors)

currently qoa4ml handlers are hard code in the ML service example. This should be moved into the core qoa4ml library to make sure that we can use different handlers for different tests. One example of handlers is the mqtt/rabbitmq one that Tri has in the BTS example.
