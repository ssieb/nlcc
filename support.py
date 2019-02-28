#!/usr/bin/python3

import pickle
from pathlib import Path
from api import doGet, doPost

loaded = False
people = {}
iMap = {}

"""
Set onlyActive to True to exclude inactive people
returns a tuple
1. a dictionary containing person info keyed by PCO id
2. a dictionary mapping Fellowship1 ID to PCO id
The data is pickled to "people.pkl" and loaded from there if it exists
To refresh the data, delete the "people.pkl" file.
"""
def getPeople(onlyActive=False):
  global loaded, people, iMap
  if loaded:
    return (people, iMap)
  if Path('people.pkl').is_file():
    print("read pickled people")
    with open('people.pkl', 'rb') as pkl:
      people = pickle.load(pkl)
      iMap = pickle.load(pkl)
    loaded = True
    return (people, iMap)
  print("fetch people")
  people = {}
  count = 0
  total = 1000
  while count < total:
    if onlyActive:
      url = f'https://api.planningcenteronline.com/people/v2/people?include=field_data&where[status]=active&per_page=100&offset={count}'
    else:
      url = f'https://api.planningcenteronline.com/people/v2/people?include=field_data&per_page=100&offset={count}'
    data = doGet(url)
    total = int(data["meta"]["total_count"])
    count += int(data["meta"]["count"])
    print(f"{count}/{total} people")
    for person in data["data"]:
      people[person["id"]] = [person["attributes"]["name"], None, None]
    for field in data["included"]:
      if field["type"] != "FieldDatum":
        continue
      rel = field["relationships"]
      if rel["field_definition"]["data"]["id"] == "245145":
        iid = rel["customizable"]["data"]["id"]
        people[iid][1] = field["attributes"]["value"]
      elif rel["field_definition"]["data"]["id"] == "245146":
        iid = rel["customizable"]["data"]["id"]
        people[iid][2] = field["attributes"]["value"]

  print(f"total: {len(people)}/{count}/{total}")

  iMap = {}
  for pcid, [name, iid, hid] in people.items():
    iMap[iid] = pcid
  print("write pickled people")
  with open('people.pkl', 'wb') as pkl:
    pickle.dump(people, pkl)
    pickle.dump(iMap, pkl)
  loaded = True
  return (people, iMap)

