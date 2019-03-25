#!/usr/bin/python3

import pickle
from pathlib import Path
from api import doGet, doPost

F1PID = "245145"  # field ID for the Fellowship 1 personal ID
F1HID = "245146"  # field ID for the Fellowship 1 household ID

pLoaded = False
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
  global pLoaded, people, iMap
  if pLoaded:
    return (people, iMap)
  if Path('people.pkl').is_file():
    print("read pickled people")
    with open('people.pkl', 'rb') as pkl:
      people = pickle.load(pkl)
      iMap = pickle.load(pkl)
    pLoaded = True
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
    print(f"{count}/{total} people\r", end="", flush=True)
    for person in data["data"]:
      attr = person["attributes"]
      people[person["id"]] = [attr["name"], None, None, attr["first_name"], attr["last_name"]]
    for field in data["included"]:
      if field["type"] != "FieldDatum":
        continue
      rel = field["relationships"]
      if rel["field_definition"]["data"]["id"] == F1PID:
        iid = rel["customizable"]["data"]["id"]
        people[iid][1] = field["attributes"]["value"]
      elif rel["field_definition"]["data"]["id"] == F1HID:
        iid = rel["customizable"]["data"]["id"]
        people[iid][2] = field["attributes"]["value"]

  print(f"total: {len(people)}/{count}/{total}")

  iMap = {}
  for pcid, [name, iid, hid, fn, ln] in people.items():
    iMap[iid] = pcid
  print("write pickled people")
  with open('people.pkl', 'wb') as pkl:
    pickle.dump(people, pkl)
    pickle.dump(iMap, pkl)
  pLoaded = True
  return (people, iMap)


hLoaded = False
households = {}

"""
Returns a dictionary mapping the PCO household ID to a list of the members' person IDs
The data is pickled to "households.pkl" and loaded from there if it exists
To refresh the data, delete the "households.pkl" file.
"""
def getHouseholds():
  global hLoaded, households
  if hLoaded:
    return households
  if Path('households.pkl').is_file():
    print("read pickled households")
    with open('households.pkl', 'rb') as pkl:
      households = pickle.load(pkl)
    hLoaded = True
    return households
  print("fetch households")
  chunk = 0
  total = 1000
  while chunk < total:
    data = doGet(f'https://api.planningcenteronline.com/people/v2/households?include=people&per_page=100&offset={chunk}')
    houseList = []
    total = int(data["meta"]["total_count"])
    chunk += int(data["meta"]["count"])
    for house in data["data"]:
      hid = house["id"]
      print(f"{chunk}/{total} households\r", end="", flush=True)
      members = []
      for person in house["relationships"]["people"]["data"]:
        members.append(person["id"])
      households[hid] = members
  print("write pickled households")
  with open('households.pkl', 'wb') as pkl:
    pickle.dump(households, pkl)
  hLoaded = True
  return households

