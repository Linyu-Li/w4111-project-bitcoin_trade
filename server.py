
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
from click.core import Context
import requests
  # accessible as a variable in index.html:
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response

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
engine.execute("""CREATE TABLE IF NOT EXISTS test (
  id serial,
  name text
);""")
engine.execute("""INSERT INTO test(name) VALUES ('grace hopper'), ('alan turing'), ('ada lovelace');""")


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
    import traceback; traceback.print_exc()
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
  cursor = g.conn.execute("SELECT * FROM Exchange")
  exchange_info = []
  for result in cursor:
    exchange_info.append(result['exchange_name'])
  cursor.close()

  exchange_api_rsp = requests.get('https://www.binance.com/api/v3/ticker/24hr')

  context = dict()
  context['exchange_name'] = exchange_info
  trade_info = []
  count = 0
  for rsp in exchange_api_rsp.json():
    trade_tuple = dict()
    trade_tuple['coinId'] = rsp['symbol']
    trade_tuple['price'] = rsp['lastPrice']
    trade_tuple['change'] = rsp['priceChange']
    trade_tuple['volume'] = rsp['volume']
    trade_info.append(trade_tuple)
    count+=1
    if count==20:
      break
  items = []
  for name in exchange_info:
    item = dict()
    item['name'] = name
    item['trade'] = trade_info
    items.append(item)
  context['items'] = items
  return render_template("/exchange/classic.html", **context)
  

@app.route('/exchange/margin')
def exchange_margin():
  cursor = g.conn.execute("SELECT * FROM Exchange")
  exchange_info = []
  for result in cursor:
    exchange_info.append(result['exchange_name'])
  cursor.close()

  exchange_api_rsp = requests.get('https://www.binance.com/fapi/v1/ticker/24hr')

  context = dict()
  context['exchange_name'] = exchange_info
  trade_info = []
  count = 0
  for rsp in exchange_api_rsp.json():
    trade_tuple = dict()
    trade_tuple['contractId'] = rsp['symbol']
    trade_tuple['price'] = rsp['lastPrice']
    trade_tuple['change'] = rsp['priceChange']
    trade_tuple['volume'] = rsp['volume']
    trade_info.append(trade_tuple)
    count+=1
    if count==20:
      break
  items = []
  for name in exchange_info:
    item = dict()
    item['name'] = name
    item['trade'] = trade_info
    items.append(item)
  context['items'] = items
  return render_template("/exchange/margin.html", **context)

""" TO BE DEVELOPED FOR LINYU
@app.route('/user/<uid>/wallet')
def user_center(uid):
  return render_template("/user/wallet.html", **context)


@app.route('/user/<uid>/miner')
def user_center(uid):
  return render_template("/user/miner.html", **context)


@app.route('/pool')
def user_center(uid):
  return render_template("/pool.html", **context)


"""


@app.route('/')
def index():
  """
  request is a special object that Flask provides to access web request information:

  request.method:   "GET" or "POST"
  request.form:     if the browser submitted a form, this contains the data in the form
  request.args:     dictionary of URL arguments, e.g., {a:1, b:2} for http://localhost?a=1&b=2

  See its API: https://flask.palletsprojects.com/en/2.0.x/api/?highlight=incoming%20request%20data

  """

  # DEBUG: this is debugging code to see what request looks like
  print(request.args)


  #
  # example of a database query
  #
  cursor = g.conn.execute("SELECT name FROM test")
  names = []
  for result in cursor:
    names.append(result['name'])  # can also be accessed using result[0]
  cursor.close()

  #
  # Flask uses Jinja templates, which is an extension to HTML where you can
  # pass data to a template and dynamically generate HTML based on the data
  # (you can think of it as simple PHP)
  # documentation: https://realpython.com/primer-on-jinja-templating/
  #
  # You can see an example template in templates/index.html
  #

  context = dict(data = names)


  #
  # render_template looks in the templates/ folder for files.
  # for example, the below file reads template/index.html
  #
  return render_template("index.html", **context)

#
# This is an example of a different path.  You can see it at:
# 
#     localhost:8111/another
#
# Notice that the function name is another() rather than index()
# The functions for each app.route need to have different names
#
@app.route('/another')
def another():
  return render_template("another.html")


# Example of adding new data to the database
@app.route('/add', methods=['POST'])
def add():
  name = request.form['name']
  g.conn.execute('INSERT INTO test(name) VALUES (%s)', name)
  return redirect('/')


@app.route('/login')
def login():
    abort(401)
    this_is_never_executed()


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
