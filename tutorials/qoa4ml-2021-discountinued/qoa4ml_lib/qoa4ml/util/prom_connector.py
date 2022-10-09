import prometheus_client as pr
_INF = float("inf")

class Prom_Handler(object):
    def __init__(self,info):
        self.info = info["metric"]
        self.port = info["port"]
        self.metrices = {}
        for key in self.info:
            self.metrices[key] = {}
            if self.info[key]["Type"] == "Gauge":
                self.metrices[key]["metric"] = pr.Gauge(self.info[key]["Prom_name"], self.info[key]["Description"])
            if self.info[key]["Type"] == "Counter":
                self.metrices[key]["metric"] = pr.Counter(self.info[key]["Prom_name"], self.info[key]["Description"])
            if self.info[key]["Type"] == "Summary":
                self.metrices[key]["metric"] = pr.Summary(self.info[key]["Prom_name"], self.info[key]["Description"])
            if self.info[key]["Type"] == "Histogram":
                self.metrices[key]["metric"] = pr.Histogram(self.info[key]["Prom_name"], self.info[key]["Description"],buckets=(tuple(self.info[key]["Buckets"])))
            self.metrices[key]["violation"] = pr.Counter(self.info[key]["Prom_name"]+"_violation", self.info[key]["Description"]+" (violation)")
        pr.start_http_server(int(info["port"]))

    def inc(self, key, num=1):
        if (self.info[key]["Type"] in ["Gauge", "Counter"]):
            self.metrices[key]["metric"].inc(num)
    def dec(self, key, num=1):
        if (self.info[key]["Type"] == "Gauge"):
            self.metrices[key]["metric"].dec(num)
    def set(self, key, num=1):
        if (self.info[key]["Type"] == "Gauge"):
            self.metrices[key]["metric"].set(num)
        elif (self.info[key]["Type"] == "Counter"):
            self.metrices[key]["metric"].inc(num)
        elif (self.info[key]["Type"] in ["Histogram","Summary"]):
            self.metrices[key]["metric"].observe(num)
    def observe(self, key, val):
        if (self.info[key]["Type"] in ["Summary", "Histogram"]):
            self.metrices[key]["metric"].observe(val)
    def inc_violation(self, key, num=1):
        self.metrices[key]["violation"].inc(num)

    def update_violation_count(self):
        for key in self.metrices:
            pr.generate_latest(self.metrices[key]["violation"])