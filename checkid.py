#!/usr/bin/python3

import csv
from support import getPeople, getHouseholds

# check that all the Fellowship 1 IDs are matched to a person

contrib = {}

with open("donations.csv", "r") as csvfile:
  dcsv = csv.DictReader(csvfile)
  for row in dcsv:
    cid = row['Contributor_ID']
    if cid == "":
      continue
    if cid in contrib:
      continue
    contrib[cid] = row['Contributor_Name']

people, iMap = getPeople()
households = getHouseholds()
unknown = set()
seen = set()

with open("people-all.csv", "r") as csvfile:
  pcsv = csv.DictReader(csvfile)
  for row in pcsv:
    #print(row)
    iid = row['Individual_ID']
    hid = row['Household_Id']
    pos = row['Household_Position']
    fn = row['First_Name']
    ln = row['Last_Name']
    if iid in iMap:
      continue
    if iid in seen:
      continue
    seen.add(iid)
    dups = 0
    if iid in contrib:
      print(f"{contrib[iid]} is {iid} / {hid}")
      continue
    for pid, info in people.items():
      if info[3] == fn and info[4] == ln:
        dups += 1
    s = f"ID {iid} ({fn} {ln}) ({dups}) is with:"
    for pid, info in people.items():
      if info[2] == hid:
        s += f" {info[0]}({info[1]})"
    print(s)


