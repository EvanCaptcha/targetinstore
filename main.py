import requests, threading
from flask import Flask, render_template, request
from discord_webhook import DiscordWebhook, DiscordEmbed
app = Flask(__name__)

webhookurl = 'https://discord.com/api/webhooks/712487108299718666/g1z8UsfR6K-bqGPtrOtVDnD0FBoV51o7nksgJ70JimL1knSICrpGWBbKlJXwIxkkKfag'
def sendHook(content):
    webhook = DiscordWebhook(url=webhookurl)
    embed = DiscordEmbed(title='Target Instore Monitor',description= content + '\nSizeer by jxn',color=int('009000'))
    webhook.add_embed(embed)
    webhook.execute()

@app.route("/")
def home():
    return render_template("index.html")

def monitor(zip, storeNum, PID, name):
    headers = {
        'authority': 'api.target.com',
        'cache-control': 'max-age=0',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.87 Safari/537.36',
        'sec-fetch-user': '?1',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
        'sec-fetch-site': 'none',
        'sec-fetch-mode': 'navigate',
        'accept-encoding': 'gzip, deflate, br',
        'accept-language': 'en-US,en;q=0.9',
    }

    params = (
        ('key', 'eb2551e4accc14f38cc42d32fbc2b2ea'),
        ('nearby', f'{zip}'),
        ('limit', '20'),
        ('requested_quantity', '1'),
        ('radius', f'{storeNum}'),
        ('fulfillment_test_mode', 'grocery_opu_team_member_test'),
    )


    json = requests.get(f'https://api.target.com/fulfillment_aggregator/v1/fiats/{PID}', headers=headers, params=params).json()
    quantities = []
    for locations in json['products'][0]['locations']:
        quantities.append(locations['location_available_to_promise_quantity'])
    sumStock = sum(quantities)
    if sumStock > 0:
        inStock = True
        sendHook(f"Monitor started on product {PID}.\nCurrent Status: In Stock")
        for locations in json['products'][0]['locations']:
            if locations['location_available_to_promise_quantity'] > 0:
                storeAddy = locations['store_address']
                storeName = locations['store_name']
                sendHook(f"Stock detected!\nProduct name: {name}.\nProduct TCIN: {PID}. \nQuantity Available: {locations['location_available_to_promise_quantity']}.\nStore name: {storeName}\n Store Address: {storeAddy}")
    else:
        inStock = False
        sendHook(f"Monitor started on {PID} in zip {zip}.\nCurrent status: OOS")

    while not inStock:
        try:
            json = requests.get(f'https://api.target.com/fulfillment_aggregator/v1/fiats/{PID}', headers=headers,params=params).json()
            quantities = []
            for locations in json['products'][0]['locations']:
                quantities.append(locations['location_available_to_promise_quantity'])
            sumStock = sum(quantities)
            if sumStock > 0:
                for locations in json['products'][0]['locations']:
                    if locations['location_available_to_promise_quantity'] > 0:
                        storeAddy = locations['store_address']
                        storeName = locations['store_name']
                        sendHook(f"Stock detected!\nProduct name: {name}\nProduct TCIN: {PID} \nQuantity Available: {locations['location_available_to_promise_quantity']}.\nStore name: {storeName}\nStore Address: {storeAddy}")
                print("Restock detected.")
                inStock = True
            else:
                print(f"No restock detected on {PID} in zip {zip} using a {storeNum} radius.")
        except:
            pass

    while inStock:
        try:
            json = requests.get(f'https://api.target.com/fulfillment_aggregator/v1/fiats/{PID}', headers=headers,params=params).json()
            quantities = []
            for locations in json['products'][0]['locations']:
                quantities.append(locations['location_available_to_promise_quantity'])
            sumStock = sum(quantities)
            if sumStock > 1:
                print("Product still in stock..")

            else:
                print(f"{PID} now OOS in {zip} using a {storeNum} radius.")
        except:
            pass




    # NB. Original query string below. It seems impossible to parse and
    # reproduce query strings 100% accurately so the one below is given
    # in case the reproduced version is not "correct".
    # response = requests.get('https://api.target.com/fulfillment_aggregator/v1/fiats/52052007?key=eb2551e4accc14f38cc42d32fbc2b2ea&nearby=10514&limit=20&requested_quantity=1&radius=50&fulfillment_test_mode=grocery_opu_team_member_test', headers=headers, cookies=cookies)
@app.route("/monitor", methods=["POST", "GET"])
def spam():
    if request.method == "POST":
        zip = request.form["zip"]
        radius = request.form["radius"]
        pid = request.form['PID']
        pName = request.form['name']
        # create threads
        jobs = []
        for i in range(0, 1):
            jobs.append(threading.Thread(target=monitor(name=f'{pName}', zip=f'{zip}', storeNum=f'{radius}', PID=f'{pid}')))

        # start  threads
        for j in jobs:
            j.start()

        # ensure all threads have been finished
        for j in jobs:
            j.join()
        return "Success"
    elif request.method == 'GET':
        return "Wrong method."
if __name__ == "__main__":
    app.run(host='0.0.0.0', port='80')
