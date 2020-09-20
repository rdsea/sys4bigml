import predictionio
import argparse
import random
import time

def import_events(client, file):
  f = open(file, 'r')
  count = 0
  print("Sending data...")
  for line in f:
    time.sleep(2)
    data = line.rstrip('\r\n').split(",")
    index = (float(data[0]))
    station_id = data[2]
    datapoint_id = data[3]
    alarm_id = data[4]
    event_time = (float(data[5]))
    value = data[6]
    threadhold = data[7]
    active_status = data[8]

    client.create_event(
      event="$set",
      entity_type="alarm_event",
      entity_id="1",
      properties= {
        "index" : float(index),
        "station_id" : int(station_id),
        "datapoint_id" : int(datapoint_id),
        "alarm_id" : int(alarm_id),
        "event_time" : float(event_time),
        "value" : float(value),
        "threadhold" : float(threadhold),
        "active_status" : bool(active_status)
      }
    )
    print("Sent data: {}".format(count))
    count += 1
  f.close()


if __name__ == '__main__':
  parser = argparse.ArgumentParser(
    description="Import sample data for recommendation engine")
  parser.add_argument('--access_key', default='ayA5BT7mhFLsAokkIEu5TBvVHhPnK_CDhAjXTXMmDoWf8YmYk4gPUmzm31Ix9rBY')
  parser.add_argument('--url', default="http://localhost:7070")
  parser.add_argument('--file', default="./data/1160629000_121_308_train.csv")

  args = parser.parse_args()
  print(args)

  client = predictionio.EventClient(
    access_key=args.access_key,
    url=args.url,
    threads=5,
    qsize=500)
  import_events(client, args.file)