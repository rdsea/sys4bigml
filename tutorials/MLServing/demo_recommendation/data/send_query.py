"""
Send sample query to prediction engine
"""

import predictionio
engine_client = predictionio.EngineClient(url="http://localhost:8000")
result = engine_client.send_query({"user": "1", "num": 4})
print(result)
print type(result)
