#!/usr/bin/python3

# Find people that have multiple households and delete their individual household

from api import doGet, doDelete
from support import getPeople, getHouseholds

people, iMap = getPeople()
households = getHouseholds()

pMap = {}
for hid, members in households.items():
  for iid in members:
    if iid not in pMap:
      pMap[iid] = []
    pMap[iid].append(hid)
count = 0
toRemove = set()
for iid, houses in pMap.items():
  if len(houses) > 1:
    count += 1
    s = f"{people[iid]['name']} has {len(houses)} households:"
    for hid in houses:
      num = len(households[hid])
      if num == 1:
        toRemove.add(hid)
      s += f" {hid}({num})"
    print(s)
print(f"{count} multiples, removing {len(toRemove)}")
total = len(toRemove)
for i, hid in enumerate(toRemove):
  print(f"Deleting {i+1}/{total} - {hid}               \r", end="", flush=True)
  doDelete(f"https://api.planningcenteronline.com/people/v2/households/{hid}")
print()

