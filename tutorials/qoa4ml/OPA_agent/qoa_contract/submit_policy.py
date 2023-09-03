from urllib import response
from opa_client.opa import OpaClient
import json


client = OpaClient() 
client.update_opa_policy_fromfile("./object_detection.rego", endpoint="object_detection")
contract = json.load(open("./contract.json"))
client.update_or_create_opa_data(contract, "object_detection/contract")

report = json.load(open("./report.json"))

check_data = {"client_info":{"id": "aaltosea2", "roles": "inf_provider"}}
qoa_response = client.check_policy_rule(input_data=report, package_path="qoa4ml.object_detection", rule_name="violation")
print(qoa_response)
