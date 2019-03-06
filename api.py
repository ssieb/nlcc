#!/usr/bin/python3

import requests

# put your appid and secret as the first two lines in a file called api.key

f = open("api.key", "r")
appid = f.readline().strip()
secret = f.readline().strip()
authInfo = (appid, secret)

def doGet(url, debug=False):
  r = requests.get(url, auth=authInfo)
  res = r.json()
  if r.status_code != 200:
    print(repr(res))
    raise Exception(f"GET status code was {r.status_code}")
  if debug:
    print(f"GET status code was {r.status_code}")
    print(repr(res))
  return res

jsonHeader = {"Content-Type": "application/vnd.api+json"}
def doPost(url, data, debug=False):
  r = requests.post(url, json=data, headers=jsonHeader, auth=authInfo)
  res = r.json()
  if r.status_code != 201:
    print(repr(data))
    print(repr(res))
    raise Exception(f"POST status code was {r.status_code}")
  if debug:
    print(f"POST status code was {r.status_code}")
    print(repr(res))
  if not "data" in res:
    raise Exception(f"Error from server: {res!r}")
  return res

def doPatch(url, data, debug=False):
  r = requests.patch(url, json=data, headers=jsonHeader, auth=authInfo)
  res = r.json()
  if r.status_code != 200 and r.status_code != 202 and r.status_code != 204:
    print(repr(data))
    print(repr(res))
    raise Exception(f"PATCH status code was {r.status_code}")
  if debug:
    print(f"PATCH status code was {r.status_code}")
    print(repr(res))
  if not "data" in res:
    raise Exception(f"Error from server: {res!r}")
  return res

def doDelete(url, debug=False):
  r = requests.delete(url, auth=authInfo)
  if len(r.text):
    res = r.json()
  else:
    res = None
  if r.status_code != 200 and r.status_code != 202 and r.status_code != 204:
    print(repr(data))
    print(repr(res))
    raise Exception(f"DELETE status code was {r.status_code}")
  if debug:
    print(f"DELETE status code was {r.status_code}")
    if res is not None:
      print(repr(res))
  if res is not None and not "data" in res:
    raise Exception(f"Error from server: {res!r}")
  return res

