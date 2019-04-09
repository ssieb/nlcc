#!/usr/bin/python3

from api import doGet, doPatch

# the Fellowship 1 ID was imported as a custom field
# this script puts that value in the remote_id attribute

F1PID = "245145" # field id for Fellowship 1 personal ID

update = {"data": {"type": "Person", "id": None, "attributes": {"remote_id": None}}}

count = 0
chunk = 0
total = 1000
while count < total:
  data = doGet(f'https://api.planningcenteronline.com/people/v2/people?include=field_data&per_page=100&offset={count}')
  total = int(data["meta"]["total_count"])
  chunk += int(data["meta"]["count"])
  people = {}
  for person in data["data"]:
    people[person["id"]] = person["attributes"]["remote_id"]
  for field in data["included"]:
    if field["type"] != "FieldDatum":
      continue
    rel = field["relationships"]
    if rel["field_definition"]["data"]["id"] == F1PID:
      iid = rel["customizable"]["data"]["id"]
      if people[iid] is None:
        people[iid] = int(field["attributes"]["value"])
      else:
        people[iid] = None
  for pid, f1id in people.items():
    count += 1
    if f1id is None:
      continue
    print(f"{count}/{chunk}/{total} people\r", end="", flush=True)
    update["data"]["id"] = pid
    update["data"]["attributes"]["remote_id"] = f1id
    doPatch(f'https://api.planningcenteronline.com/people/v2/people/{pid}', update)
print()

