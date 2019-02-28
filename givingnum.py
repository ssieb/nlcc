#!/usr/bin/python3

from api import doGet, doPatch

# the giving number was imported as a custom field
# this script puts that number into the giving app

GIVINGID = "251471"  # field ID for the giving number

count = 0
chunk = 0
total = 1000
while chunk < total:
  data = doGet(f'https://api.planningcenteronline.com/people/v2/people?include=field_data&per_page=100&offset={count}')
  total = int(data["meta"]["total_count"])
  chunk += int(data["meta"]["count"])
  people = {}
  for person in data["data"]:
    people[person["id"]] = None
  for field in data["included"]:
    if field["type"] != "FieldDatum":
      continue
    rel = field["relationships"]
    if rel["field_definition"]["data"]["id"] == GIVINGID:
      iid = rel["customizable"]["data"]["id"]
      gnum = int(field["attributes"]["value"])
      people[iid] = gnum
  for pid, gnum in people.items():
    count += 1
    if gnum is None:
      continue
    print(f"{count}/{chunk}/{total} people\r", end="", flush=True)
    data = {"data": {"type": "Person", "id": pid, "attributes": {"donor_number": gnum}}}
    doPatch(f'https://api.planningcenteronline.com/giving/v2/people/{pid}', data)

print()

