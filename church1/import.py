#!/usr/bin/python3

"""
This donation import script is quite specific to our use case and
is unlikely to be directly usable for anyone else.

Requires a fundmap.csv to convert the F1 funds to PCO funds.
Columns:
Fund - value from the donation Fund column
SubFund - value from the donation SubFund column (can be empty)
PCOFund - name of the fund to use in PCO
Label - optional label to put on the donation

Uses a batchmap.csv to map donations to PCO sources.
Columns:
Contains - if this string is in the batch name, use the following values
Source - PCO source to use for this donation
Label - optional label to put on the donation
Group - value to add to the batch group name
"""

import csv
from datetime import datetime
import re
import time
from api import doGet, doPost
from support import getPeople

moneyMatch = re.compile(r'-?\$(\d+,)?\d+\.\d+')
moneyStrip = re.compile(r'[$,]')
number = re.compile(r'\d+')

newBatch = {"data": {"type": "Batch", "attributes": {"description": ""}}}
def createBatch(groupID, name):
  newBatch["data"]["attributes"]["description"] = name
  res = doPost(f"https://api.planningcenteronline.com/giving/v2/batch_groups/{groupID}/batches", newBatch)
  return res["data"]["id"]

newDonation = {
  "data": {
    "type": "Donation",
    "attributes": {
      "payment_method": "none",
      "payment_check_number": None,
      "received_at": "1970-01-01"
    },
    "relationships": {
      "person": {
        "data": { "type": "Person", "id": "0" }
      },
      "payment_source": {
        "data": { "type": "PaymentSource", "id": "0" }
      },
      "labels": {
        "data": [
          { "type": "Label", "id": "0" }
        ]
      }
    }
  },
  "included": [
    {
      "type": "Designation",
      "attributes": { "amount_cents": 0 },
      "relationships": {
        "fund": {
          "data": { "type": "Fund", "id": "123" }
        }
      }
    }
  ]
}
ndAttrib = newDonation["data"]["attributes"]
ndPerson = newDonation["data"]["relationships"]["person"]["data"]
ndSource = newDonation["data"]["relationships"]["payment_source"]["data"]
ndLabels = newDonation["data"]["relationships"]["labels"]
ndAmount = newDonation["included"][0]["attributes"]
ndFund = newDonation["included"][0]["relationships"]["fund"]["data"]

def createDonation(batch, cid, amount, rdate, method, num, source, fund, lblList):
  ndPerson["id"] = cid
  ndSource["id"] = source
  ndAmount["amount_cents"] = amount
  ndAttrib["received_at"] = rdate
  ndAttrib["payment_method"] = method
  ndAttrib["payment_check_number"] = num
  ndFund["id"] = fund
  ndLabels["data"] = [{"type": "Label", "id": labels[label]} for label in lblList]
  res = doPost(f"https://api.planningcenteronline.com/giving/v2/batches/{batch}/donations", newDonation)
  return res["data"]["id"]


"""
{'data': {'type': 'Batch', 'id': '1', 'attributes': {'committed_at': None, 'created_at': '2019-02-23T21:27:49Z', 'description': 'test', 'total_cents': 0, 'total_currency': 'CAD', 'updated_at': '2019-02-23T21:27:49Z'}, 'links': {'batch_group': None, 'commit': 'https://api.planningcenteronline.com/giving/v2/batches/1/commit', 'donations': 'https://api.planningcenteronline.com/giving/v2/batches/1/donations', 'owner': 'https://api.planningcenteronline.com/giving/v2/people/3146023', 'self': 'https://api.planningcenteronline.com/giving/v2/batches/1'}}, 'included': [], 'meta': {'can_include': ['owner'], 'parent': {'id': '26653', 'type': 'Organization'}}}
"""

print("fetch labels")
labels = {}
data = doGet('https://api.planningcenteronline.com/giving/v2/labels')
for label in data['data']:
  labels[label['attributes']['slug']] = label['id']
#print(repr(labels))

print("fetch funds")
funds = {}
data = doGet('https://api.planningcenteronline.com/giving/v2/funds')
for fund in data['data']:
  funds[fund['attributes']['name']] = fund['id']
#print(repr(funds))

print("fetch sources")
sources = {}
data = doGet('https://api.planningcenteronline.com/giving/v2/payment_sources')
for source in data['data']:
  sources[source['attributes']['name']] = source['id']
#print(repr(sources))

fundMap = {}
with open("fundmap.csv", "r") as csvfile:
  fcsv = csv.DictReader(csvfile)
  for row in fcsv:
    fund = row["Fund"]
    if row["SubFund"] != "":
      fund = row["SubFund"]
    fundMap[fund] = (row["PCOFund"], row["Label"])

batchMap = {}
with open("batchmap.csv", "r") as csvfile:
  bcsv = csv.DictReader(csvfile)
  for row in bcsv:
    batchMap[row['Contains']] = (row['Source'], row['Label'], row['Group'])

people, iMap = getPeople()

print("fetch groups")
groups = {}
url = "https://api.planningcenteronline.com/giving/v2/batch_groups?per_page=100"
while True:
  data = doGet(url)
  for group in data['data']:
    groups[group["attributes"]["description"]] = group["id"]
  if "next" in data['links']:
    url = data['links']['next']
  else:
    break

print("fetch batches\r", end="", flush=True)
doneBatches = set()
url = "https://api.planningcenteronline.com/giving/v2/batches?per_page=100"
count = 0
while True:
  data = doGet(url)
  total = int(data["meta"]["total_count"])
  count += int(data["meta"]["count"])
  print(f"fetch batches {count}/{total}\r", end="", flush=True)
  for batch in data['data']:
    doneBatches.add(batch["attributes"]["description"])
  if "next" in data['links']:
    url = data['links']['next']
  else:
    break
print()

indiv = {}
house = {}
with open("people.csv", "r") as csvfile:
  pcsv = csv.DictReader(csvfile)
  for row in pcsv:
    iid = row['Individual_ID']
    hid = row['Household_Id']
    pos = row['Household_Position']
    if iid in indiv:
      if indiv[iid] != hid:
        print(f"individual {iid} has household id {hid} != {indiv[iid]}")
        continue
    indiv[iid] = hid
    if not hid in house:
      house[hid] = []
    if not (iid, pos) in house[hid]:
      house[hid].append((iid, pos))

print("processing")
batches = {}
methods = {"Cash": ("cash", "Offering"), "Check": ("check", "Offering"), "Credit Card": ("card", "Debit/Credit"), "ACH": ("cash", "Offering")}
notfound = set()
upeople = {}
noBatch = 0
with open("donations.csv", "r") as csvfile:
  dcsv = csv.DictReader(csvfile)
  for row in dcsv:
    cid = row['Contributor_ID']
    if cid == "":
      continue
    if cid in iMap:
      cid = iMap[cid]
    else:
      if cid in house:
        for iid, pos in house[cid]:
          if pos == "Head":
            if not iid in iMap:
              notfound.add(cid)
              continue
            cid = iid
            cid = iMap[iid]
            break
        else:
          print(f"{cid} {row['Contributor_Type']} {house[cid]!r} household contributor found")
      else:
        #print("{} non-existant contributor found".format(cid))
        notfound.add(cid)
        if not cid in upeople:
          upeople[cid] = row['Contributor_Name']
    dSource = None
    method = row['Type']
    if method in methods:
      method, dSource = methods[method]
    elif method == "Non-Cash":
      continue
    else:
      print(f'unknown payment method: {method}')
      continue
    amount = row['Amount']
    if moneyMatch.fullmatch(amount) is None:
      print(f"invalid amount: {amount}")
      continue
    amount = moneyStrip.sub('', amount)
    amount = round(float(amount) * 100)
    #if amount <= 0:
    #  continue
    fund = row['SubFund']
    if fund == "":
      fund = row['Fund']
    if fund in fundMap:
      fund = fundMap[fund]
    else:
      print(f"unknown fund: {fund}")
      continue
    lblList = []
    fundID = funds[fund[0]]
    if fund[1] != "":
      lblList.append(fund[1])
    if row['Pledge_Drive1'] != "":
      lblList.append("v17-pledge")
    rdate = datetime.strptime(row['Received_Date'], "%m/%d/%Y")
    batchName = row['Batch_Name']
    if batchName == "":
      if row['Type'] == "Cash" or row['Type'] == "Check":
        bType = "Cash and Cheque"
      else:
        bType = "Online and Card"
      batchName = rdate.strftime(f"%Y-%m {bType}")
      dSource = "Sunergo Import"
      batchGroup = rdate.strftime("%Y-%B")
      if batchName not in batches:
        batches[batchName] = (batchGroup, [])
    else:
      for key, (source, label, group) in batchMap.items():
        if batchName.find(key) >= 0:
          dSource = source
          if label != "":
            lblList.append(label)
          batchGroup = group
          break
        else:
          batchGroup = "Sundays"
      if batchName not in batches:
        batchGroup = rdate.strftime(f"%Y-%B {batchGroup}")
        batches[batchName] = (batchGroup, [])
    batch = batches[batchName][1]
    if dSource not in sources:
      print(row)
      raise Exception(f"unknown source: {dSource}")
    dSource = sources[dSource]
    checkNum = row['Reference']
    if number.match(checkNum) is None:
      checkNum = None
    donation = [cid, amount, rdate.strftime("%Y-%m-%d"), method, checkNum, dSource, fundID, lblList]
    batch.append(donation)
if notfound:
  print(f"not found: {list(notfound)}")
for k, v in upeople.items():
  if k in indiv:
    hid = indiv[k]
  else:
    hid = "unknown"
  print(f"{v} {k} {hid}")


bGroups = list(set([v[0] for k, v in batches.items()]))
bGroups.sort()
for i, bGroup in enumerate(bGroups):
  print(f"{i+1}/{len(bGroups)} Using batch group '{bGroup}'")
  gid = groups[bGroup]
  blist = [k for k, v in batches.items() if v[0] == bGroup]
  blist.sort()
  for j, bName in enumerate(blist):
    if bName in doneBatches:
      continue
    print(f"{j+1}/{len(blist)} Creating batch {bName}")
    batch = batches[bName][1]
    bid = createBatch(gid, bName)
    for i, donation in enumerate(batch):
      if donation[1] <= 0:
        #print(f"\ndonation amount: ${donation[1]/100}")
        continue
      print(f"{i+1}/{len(batch)}\r", end="", flush=True)
      createDonation(bid, *donation)
    print()

