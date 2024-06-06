import uuid
from flask import Flask, request
from db import stores, items

app = Flask(__name__)



@app.route("/", methods = ["GET"])
@app.route("/home", methods = ["GET"])
def home():
    return "This is my flask app!!"

@app.route("/store", methods = ["GET"])
def get_stores():
    return {"stores": list(stores.values())}

@app.route("/item", methods = ["GET"])
def get_items():
    return {"items": list(items.values())}

@app.route("/store", methods = ["POST"])
def create_stores():
    store_data = request.get_json()
    store_id = uuid.uuid4().hex
    new_store = {**store_data, "id": store_id}
    stores[store_id] = new_store
    return new_store, 201

@app.route("/item", methods = ["POST"])
def add_items():
    item_data = request.get_json()
    if item_data["store_id"] not in stores:
        return {"message": "store not found"}, 404
    item_id = uuid.uuid4().hex
    new_item = {**item_data, "id": item_id}
    items[item_id] = new_item
    return new_item, 201

@app.route("/store/<store_id>", methods = ["GET"])
def get_store(store_id):
    try:
        return stores[store_id]
    except:
        return {"message": "store not found"}, 404  
    
@app.route("/store/<store_id>", methods = ["PUT"])
def update_store(store_id):
    store_data = request.get_json()
    try:
        store = stores[store_id]
        store |= store_data
        return store_data, 200
    except:
        return {"message": "store not found"}, 404  
    
@app.route("/store/<store_id>", methods = ["DELETE"])
def delete_store(store_id):
    try:
        for item in list(items.keys()):
            print(item)
            if items[item]['store_id'] == store_id:
                del items[item]
        del stores[store_id]
        return {"message": "successfully deleted the store!!"}, 200 
    except:
        return {"message": "store not found"}, 404  

@app.route("/item/<string:item_id>", methods = ["GET"])
def get_store_items(item_id):
    try:
        return items[item_id], 200
    except:
        return {"message": "Item not found"}, 404  
    
@app.route("/item/<string:item_id>", methods = ["PUT"])
def update_store_items(item_id):
    item_data = request.get_json()
    try:
        item = items[item_id]
        item|=item_data
        return item, 200
    except:
        return {"message": "Item not found"}, 404  
    
@app.route("/item/<string:item_id>", methods = ["DELETE"])
def delete_store_items(item_id):
    try:
        del items[item_id]
        return {"message": "successfully deleted the item!!"}, 200
    except:
        return {"message": "Item not found"}, 404  


if __name__ == "__main__":
    app.run(debug=True)