import os
from flask import Flask, request, jsonify
from sqlalchemy.exc import IntegrityError
from sqlalchemy import text
from db import db
from models import ItemModel, StoreModel
from flask_smorest import Api
from schemas import ItemSchema, ItemUpdateSchema, StoreSchema

store_schema = StoreSchema()
item_schema = ItemSchema()
item_update_schema = ItemUpdateSchema()

def create_app():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///data.db")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)

    with app.app_context():
        db.create_all()

    @app.before_request
    def enforce_foreign_keys():
        if db.engine.dialect.name == "sqlite":
            db.session.execute(text("PRAGMA foreign_keys=ON"))

    return app

app = create_app()

@app.route("/", methods=["GET"])
@app.route("/home", methods=["GET"])
def home():
    return "This is my flask app!!"

@app.route("/store", methods=["POST"])
def create_stores():
    data = request.get_json()
    store_data = store_schema.load(data)
    new_store = StoreModel(**store_data)
    try:
        db.session.add(new_store)
        db.session.commit()
        return jsonify(store_schema.dump(new_store)), 201
    except Exception as e:
        return {"message": f"An error occurred while saving to DB: {str(e)}"}, 400

@app.route("/store", methods=["GET"])
def get_all_stores():
    stores = StoreModel.query.all()
    return jsonify({"stores": [store_schema.dump(store) for store in stores]})

@app.route("/store/<int:store_id>", methods=["GET"])
def get_store(store_id):
    store = StoreModel.query.get_or_404(store_id)
    return jsonify(store_schema.dump(store))

@app.route("/store/<int:store_id>", methods=["PUT"])
def update_store(store_id):
    store_data = request.get_json()
    store = StoreModel.query.get(store_id)
    if store:
        store.name = store_data["name"]
    else:
        store_data["id"] = store_id
        store = StoreModel(**store_data)
    
    db.session.add(store)
    db.session.commit()

    return jsonify(store_schema.dump(store))

@app.route("/store/<int:store_id>", methods=["DELETE"])
def delete_store(store_id):
    store = StoreModel.query.get_or_404(store_id)
    db.session.delete(store)
    db.session.commit()
    return {"message": "Store Deleted!!"}

@app.route("/item", methods=["POST"])
def add_items():
    data = request.get_json()
    item_data = item_schema.load(data)
    new_item = ItemModel(**item_data)
    try:
        db.session.add(new_item)
        db.session.commit()
        return jsonify(item_schema.dump(new_item)), 201
    except IntegrityError as e:
        db.session.rollback()
        return {"message": f"An error occurred while saving to DB: {str(e.orig)}"}, 400
    except Exception as e:
        db.session.rollback()
        return {"message": f"An unexpected error occurred: {str(e)}"}, 400

@app.route("/item", methods=["GET"])
def get_all_items():
    items = ItemModel.query.all()
    return jsonify({"items": [item_schema.dump(item) for item in items]})

@app.route("/item/<int:item_id>", methods=["GET"])
def get_item(item_id):
    item = ItemModel.query.get_or_404(item_id)
    return jsonify(item_schema.dump(item))

@app.route("/item/<int:item_id>", methods=["PUT"])
def update_item(item_id):
    item_data = request.get_json()
    item = ItemModel.query.get(item_id)
    if item:
        item.name = item_data["name"]
        item.price = item_data["price"]
    else:
        item_data["id"] = item_id
        item = ItemModel(**item_data)

    db.session.add(item)
    db.session.commit()

    return jsonify(item_schema.dump(item))

@app.route("/item/<int:item_id>", methods=["DELETE"])
def delete_item(item_id):
    item = ItemModel.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    return {"message": "Item Deleted!!"}

if __name__ == "__main__":
    app.run(debug=True)
