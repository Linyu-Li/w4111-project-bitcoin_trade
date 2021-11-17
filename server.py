"""
Columbia's COMS W4111.001 Introduction to Databases
Example Webserver
To run locally:
    python3 server.py
Go to http://localhost:8111 in your browser.
A debugger such as "pdb" may be helpful for debugging.
Read about it online.
"""
import os
import random
import time

import requests
# accessible as a variable in index.html:
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response
import json
from decimal import *

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)

#
# The following is a dummy URI that does not connect to a valid database. You will need to modify it to connect to your Part 2 database in order to use the data.
#
# XXX: The URI should be in the format of: 
#
#     postgresql://USER:PASSWORD@34.74.246.148/proj1part2
#
# For example, if you had username gravano and password foobar, then the following line would be:
#
#     DATABASEURI = "postgresql://gravano:foobar@34.74.246.148/proj1part2"
#
DATABASEURI = "postgresql://zw2723:7071@34.74.246.148/proj1part2"

#
# This line creates a database engine that knows how to connect to the URI above.
#
engine = create_engine(DATABASEURI)

#
# Example of running queries in your database
# Note that this will probably not work if you already have a table named 'test' in your database, containing meaningful data. This is only an example showing you how to run queries in your database using SQLAlchemy.
#
'''
engine.execute("""CREATE TABLE IF NOT EXISTS test (
  id serial,
  name text
);""")
engine.execute("""INSERT INTO test(name) VALUES ('grace hopper'), ('alan turing'), ('ada lovelace');""")
'''


@app.before_request
def before_request():
    """
  This function is run at the beginning of every web request 
  (every time you enter an address in the web browser).
  We use it to setup a database connection that can be used throughout the request.

  The variable g is globally accessible.
  """
    try:
        g.conn = engine.connect()
    except:
        print("uh oh, problem connecting to database")
        import traceback;
        traceback.print_exc()
        g.conn = None


@app.teardown_request
def teardown_request(exception):
    """
  At the end of the web request, this makes sure to close the database connection.
  If you don't, the database could run out of memory!
  """
    try:
        g.conn.close()
    except Exception as e:
        pass


#
# @app.route is a decorator around index() that means:
#   run index() whenever the user tries to access the "/" path using a GET request
#
# If you wanted the user to go to, for example, localhost:8111/foobar/ with POST or GET then you could use:
#
#       @app.route("/foobar/", methods=["POST", "GET"])
#
# PROTIP: (the trailing / in the path is important)
# 
# see for routing: https://flask.palletsprojects.com/en/2.0.x/quickstart/?highlight=routing
# see for decorators: http://simeonfranklin.com/blog/2012/jul/1/python-decorators-in-12-steps/
#

@app.route('/exchange/classic')
def exchange_classic():
  cursor = g.conn.execute("SELECT * FROM exchange")
  exchange_info = []
  for result in cursor:
    exchange_info.append(result['exchange_name'].strip())
  cursor.close()

  exchange_api_rsp = requests.get('https://www.binance.com/api/v3/ticker/24hr')

  # Query the coin data in current database
  coin_id_list = []
  cursor = g.conn.execute("SELECT coin_id FROM coin")
  for result in cursor:
      coin_id_list.append(result['coin_id'])
  cursor.close()

  # Only update the data in coin as api's data if the api's data is included in the database
  context = dict()
  context['exchange_name'] = exchange_info
  trade_info = []
  count = 0
  for rsp in exchange_api_rsp.json():
    trade_tuple = dict()
    trade_tuple['coinId'] = rsp['symbol']
    if trade_tuple['coinId'] not in coin_id_list:
        continue
    trade_tuple['price'] = rsp['lastPrice']
    trade_tuple['change'] = rsp['priceChange']
    trade_tuple['volume'] = rsp['volume']
    cursor = g.conn.execute("UPDATE coin SET price = {0}, trading_volume = {1} WHERE coin_id = '{2}'".format(
        (rsp['lastPrice']), (rsp['volume']), rsp['symbol']))
    cursor.close()
    trade_info.append(trade_tuple)
    count += 1
    if count == 20:
      break

  items = []
  for name in exchange_info:
    item = dict()
    item['name'] = name
    item['trade'] = random.sample(trade_info, 5)
    items.append(item)
  context['items'] = items
  return render_template("/exchange/classic.html", **context)
  

@app.route('/exchange/margin')
def exchange_margin():
  cursor = g.conn.execute("SELECT * FROM exchange")
  exchange_info = []
  for result in cursor:
    exchange_info.append(result['exchange_name'].strip())
  cursor.close()

  exchange_api_rsp = requests.get('https://www.binance.com/fapi/v1/ticker/24hr')

  # Query the contract data in current database
  contract_id_list = []
  cursor = g.conn.execute("SELECT contract_id FROM contract")
  for result in cursor:
      contract_id_list.append(result['contract_id'])
  cursor.close()

  # Only update the data in contract as api's data if the api's data is included in the database
  context = dict()
  context['exchange_name'] = exchange_info
  trade_info = []
  count = 0
  for rsp in exchange_api_rsp.json():
    trade_tuple = dict()
    trade_tuple['contractId'] = rsp['symbol']
    if trade_tuple['contractId'] not in contract_id_list:
        continue
    trade_tuple['price'] = rsp['lastPrice']
    trade_tuple['change'] = rsp['priceChange']
    trade_tuple['volume'] = rsp['volume']
    cursor = g.conn.execute("UPDATE contract SET price = {0}, trading_volume = {1} WHERE contract_id = '{2}'".format(float(rsp['lastPrice']), float(rsp['volume']), rsp['symbol']))
    cursor.close()
    trade_info.append(trade_tuple)
    count += 1
    if count == 20:
      break

  items = []
  for name in exchange_info:
    item = dict()
    item['name'] = name
    item['trade'] = random.sample(trade_info, 5)
    items.append(item)
  context['items'] = items
  return render_template("/exchange/margin.html", **context)



@app.route('/user/<uid>/wallet', methods=['GET'])
def query_wallet(uid):
    cursor1 = g.conn.execute("SELECT * FROM contain_coin WHERE uid = (%s)", uid)
    containCoins = []
    for result in cursor1:
        containCoin = dict()
        containCoin['coinId'] = result['coin_id']
        containCoin['amount'] = result['amount']
        containCoins.append(containCoin)
    cursor1.close()

    cursor2 = g.conn.execute("SELECT * FROM contain_contract C, trade_contract T " +
                             "WHERE C.uid = (%s) AND C.contract_id = T.contract_id AND C.uid = T.uid", uid)
    containContracts = []
    for result in cursor2:
        containContract = dict()
        containContract['amount'] = result['amount']
        containContract['liquidationPrice'] = result['liquidation_price']
        containContract['contractId'] = result['contract_id']
        containContracts.append(containContract)
    cursor2.close()

    cursor3 = g.conn.execute("SELECT * FROM trade_coin WHERE uid = (%s)", uid)
    tradeCoinHistorys = []
    for result in cursor3:
        tradeCoinHistory = dict()
        tradeCoinHistory['trackID'] = result['trade_coin_track_id']
        tradeCoinHistory['coinID'] = result['coin_id']
        tradeCoinHistory['price'] = result['price']
        tradeCoinHistory['amount'] = result['amount']
        tradeCoinHistory['dealTime'] = result['deal_date']
        tradeCoinHistorys.append(tradeCoinHistory)
    cursor3.close()

    cursor4 = g.conn.execute("SELECT * FROM trade_contract WHERE uid = (%s)", uid)
    tradeMarginHistorys = []
    for result in cursor4:
        tradeMarginHistory = dict()
        tradeMarginHistory['trackID'] = result['trade_contract_track_id']
        tradeMarginHistory['marginID'] = result['contract_id']
        tradeMarginHistory['price'] = result['price']
        tradeMarginHistory['amount'] = result['amount']
        tradeMarginHistory['dealTime'] = result['deal_date']
        tradeMarginHistorys.append(tradeMarginHistory)
    cursor4.close()

    context = dict()
    context['containCoin'] = containCoins
    context['containContract'] = containContracts
    context['tradeCoinHistory'] = tradeCoinHistorys
    context['tradeMarginHistory'] = tradeMarginHistorys
    context['uid'] = uid
    return render_template("/user/wallet.html", **context)



@app.route('/user/<uid>/miner', methods=['GET'])
def query_miner(uid):
    cursor1 = g.conn.execute("SELECT * FROM own_miner O, dev_belg D " +
                            "WHERE O.uid = (%s) AND O.mid = D.mid", uid)
    devices = []
    for result in cursor1:
        device = dict()
        device['status'] = result['status']
        device['deviceID'] = result['did']
        device['computingPower'] = result['computing_power']
        device['deviceName'] = result['device_name']
        device['IP'] = result['ip']
        device['status'] = result['status']
        devices.append(device)
    cursor1.close()

    cursor2 = g.conn.execute("SELECT * FROM own_miner O, dig D " +
                             "WHERE O.uid = (%s) AND O.mid = D.mid", uid)
    digHistorys = []
    for result in cursor2:
        digHistory = dict()
        digHistory['trackID'] = result['dig_track_id']
        digHistory['coinID'] = result['coin_id']
        digHistory['pid'] = result['pid']
        digHistory['did'] = result['did']
        digHistory['since'] = result['since']
        digHistorys.append(digHistory)
    cursor2.close()

    context = dict()
    context['device'] = devices
    context['digHistory'] = digHistorys
    context['uid'] = uid

    return render_template("/user/miner.html", **context)


@app.route('/pool')
def pool_center():
  cursor = g.conn.execute("SELECT * FROM pool")
  pool_info = []
  for result in cursor:
    pool = dict()
    pool['pid'] = result['pid']
    pool['hashrate'] = result['hashrate']
    pool['taxFee'] = result['tax_fee']
    pool_info.append(pool)
  cursor.close()
  context = dict()
  context['poolInfo'] = pool_info

  cursor = g.conn.execute("SELECT * FROM dev_belg")
  dev_info = []
  for result in cursor:
    if (result['status']) is False:
        continue
    dev = dict()
    dev['did'] = result['did']
    dev['deviceName'] = result['device_name']
    dev_info.append(dev)
  cursor.close()
  context["deviceInfo"] = dev_info

  cursor = g.conn.execute("SELECT coin_id FROM coin")
  coin_list = []
  for result in cursor:
    coin_list.append(result['coin_id'])
  cursor.close()
  context["coinName"] = coin_list

  return render_template("/pool.html", **context)


@app.route('/trade/coin/<coin_id>', methods=['POST'])
def trade_coin(coin_id):
    # TODO: frontend maybe need to return the eid data
    coin_record = request.form.to_dict()
    method = coin_record.get('method')
    amount = int(coin_record.get('“amount”'))
    uid = coin_record.get('“uid”')
    deal_date = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    price = 0
    current_coin_amount = 0
    wid = ''

    # query the price
    cursor = g.conn.execute("SELECT * FROM coin WHERE coin_id = (%s)", coin_id)
    for result in cursor:
        price = result['price']
    cursor.close()

    # query the current contract amount
    cursor = g.conn.execute(
        "SELECT * FROM contain_coin WHERE uid = '{0}' AND coin_id = '{1}'".format(uid, coin_id))
    for result in cursor:
        current_coin_amount = result['amount']
    cursor.close()

    # query wid
    cursor = g.conn.execute("SELECT * FROM own_user WHERE uid = '{0}'".format(uid))
    for result in cursor:
        wid = result['wid']
    cursor.close()

    # TODO: No eid
    if method == 'buy':
        cursor1 = g.conn.execute(
            "INSERT INTO trade_coin (coin_id, uid, price, amount, deal_date) VALUES ('{0}', '{1}', {2}, {3}, TIMESTAMP '{4}')".format(
                coin_id, uid, price, amount, deal_date))
        cursor2 = g.conn.execute(
            "INSERT INTO contain_coin (uid, coin_id, wid, amount) VALUES ('{0}', '{1}', '{2}', {3}) on conflict (uid, coin_id, wid) DO UPDATE SET amount = {4};".format(
                uid, coin_id, wid, current_coin_amount + amount, current_coin_amount + amount))
        cursor1.close()
        cursor2.close()
    else:
        cursor1 = g.conn.execute(
            "INSERT INTO sell_coin (coin_id, uid, deal_date, price) VALUES ('{0}', '{1}', TIMESTAMP '{2}', {3})".format(
                coin_id, uid, deal_date, price))
        cursor2 = g.conn.execute(
            "INSERT INTO contain_coin (uid, coin_id, wid, amount) VALUES ('{0}', '{1}', '{2}', {3}) on conflict (uid, coin_id, wid) DO UPDATE SET amount = {4};".format(
                uid, coin_id, wid, current_coin_amount - amount, current_coin_amount - amount))
        cursor1.close()
        cursor2.close()

    return redirect('/user/{0}/wallet'.format(uid))


@app.route('/trade/margin/<contract_id>', methods=['POST'])
def trade_margin(contract_id):
    # TODO: frontend maybe need to return the eid data
    margin_record = request.form.to_dict()
    method = margin_record.get('method')
    amount = int(margin_record.get('“amount”'))
    uid = margin_record.get('“uid”')
    deal_date = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    price = 0
    current_contract_amount = 0

    # query the price
    cursor = g.conn.execute("SELECT * FROM contract WHERE contract_id = (%s)", contract_id)
    for result in cursor:
        price = result['price']
    cursor.close()

    # query the current contract amount
    cursor = g.conn.execute("SELECT * FROM contain_contract WHERE uid = '{0}' AND contract_id = '{1}'".format(uid, contract_id))
    for result in cursor:
        current_contract_amount = result['amount']
    cursor.close()

    # TODO: No eid
    if method == 'buy':
        random_liquidation_price = round(random.uniform(0, price), 2)
        cursor1 = g.conn.execute("INSERT INTO trade_contract (contract_id, uid, price, amount, liquidation_price, deal_date) VALUES ('{0}', '{1}', {2}, {3}, {4}, TIMESTAMP '{5}')".format(contract_id, uid, price, amount, random_liquidation_price, deal_date))
        cursor2 = g.conn.execute("INSERT INTO contain_contract (uid, contract_id, amount, liquidation_price) VALUES ('{0}', '{1}', {2}, {3}) on conflict (uid, contract_id) DO UPDATE SET amount = {4};".format(uid, contract_id, current_contract_amount+amount, random_liquidation_price, current_contract_amount+amount))
        cursor1.close()
        cursor2.close()
    else:
        cursor1 = g.conn.execute("INSERT INTO sell_contract (contract_id, uid, deal_time, price) VALUES ('{0}', '{1}', TIMESTAMP '{2}', {3})".format(contract_id, uid, deal_date, price))
        cursor2 = g.conn.execute(
            "INSERT INTO contain_contract (uid, contract_id, amount) VALUES ('{0}', '{1}', {2}) on conflict (uid, contract_id) DO UPDATE SET amount = {3};".format(uid, contract_id, current_contract_amount - amount, current_contract_amount - amount))
        cursor1.close()
        cursor2.close()

    return redirect('/user/{0}/wallet'.format(uid))


@app.route('/dig/<pid>', methods=['POST'])
def dig(pid):
    dig_record = request.form.to_dict()
    did = dig_record.get('did')
    coin_id = dig_record.get('coin_id')
    deal_date = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    mid = ''
    uid = ''

    # query mid
    cursor1 = g.conn.execute("SELECT * FROM dev_belg WHERE did = '{0}'".format(did))
    for result in cursor1:
        mid = result['mid']
    cursor1.close()

    # query uid
    cursor2 = g.conn.execute("SELECT * FROM own_miner WHERE mid = '{0}'".format(mid))
    for result in cursor2:
        uid = result['uid']
    cursor2.close()

    # insert rows in dig table
    cursor3 = g.conn.execute("INSERT INTO dig (pid, coin_id, mid, since, did) VALUES ('{0}', '{1}', '{2}', TIMESTAMP '{3}', '{4}')".format(pid, coin_id, mid, deal_date, did))
    cursor3.close()

    # set device status
    cursor4 = g.conn.execute("UPDATE dev_belg SET status = {0} WHERE did = '{1}'".format(False, did))
    cursor4.close()

    return redirect('/user/{0}/miner'.format(uid))


if __name__ == "__main__":
    import click


    @click.command()
    @click.option('--debug', is_flag=True)
    @click.option('--threaded', is_flag=True)
    @click.argument('HOST', default='0.0.0.0')
    @click.argument('PORT', default=8111, type=int)
    def run(debug, threaded, host, port):
        """
    This function handles command line parameters.
    Run the server using:

        python3 server.py

    Show the help text using:

        python3 server.py --help

    """

        HOST, PORT = host, port
        print("running on %s:%d" % (HOST, PORT))
        app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)

    run()
