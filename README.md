# w4111-project

## PostgreSQL Information
The PostgreSQL we use is: 

username: zw2723 

password: 7071

## Deployment

For local test, run:
```sh
python3 server.py
```

This site is built using [Flask](https://flask.palletsprojects.com/en/2.0.x/) and [Bootstrap](https://getbootstrap.com/)

## URL of Application
- exchange center: 
    - http://34.73.27.72:8111/exchange/classic
    - http://34.73.27.72:8111/exchange/margin
- user center:
    - http://34.73.27.72:8111/user/{{uid}}/wallet
    - http://34.73.27.72:8111/user/{{uid}}/miner
- pool center:
    - http://34.73.27.72:8111/pool

## Implementation
- A user control center page, including his wallet information and miner information. 
- Users are able to monitor their balances and mining situation from the user center
- The system has exchange page, listing all kinds of crypto currencies and contract for trading, users can interact with exchange to buy and sell coins and contracts
- We also implemented a blockchain pool summaries page like btc.com, providing information to miners. This page relies one the pool table and has an asynchronous task to keep refresh the page with the real-time API provided by pools’ website

## Page Example
### Exchange Center
Exchange center is the place we can trade coins and margins, this part involves several operations. We use the real-time API provided by exchanges like Binance to get the updated price of coins and margins, and exhibit them to users. This data is also used to update our own database. In the exchange center, users can trade in different products, the RESTful API will send the coin/margin id and amount provided by user in the front-end interaction to back-end. Then our service will first do the constraint check of the database then update the trade information to current wallet status and record this trade into trade history.

### Pool Center
Pool Center is another interesting part of our system. We get the status of many popular pools from BTC.com website. Users can view these informations from front-end and choose a pool to dig coins. From the backend, we send the currently free machines and coin types that is available to dig to the users. Then user can make a choice and start dig. Then the RESTful API will send the user's choice to backend and the system will update the status of the machine and add record to the dig history. Users will also able to stop the machine in their miner user center.

