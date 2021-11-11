import requests

r = requests.get('https://www.binance.com/api/v3/ticker/24hr')
r.json()

for info in r.json():
    print (info['symbol'])

names = ['a', 'b']
context = dict(data = names)

print (context)