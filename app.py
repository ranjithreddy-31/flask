import os
from flask import Flask, request, jsonify
from sqlalchemy.exc import IntegrityError
from sqlalchemy import text
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt
from passlib.hash import pbkdf2_sha256
from flask_migrate import Migrate
from db import db
from models import ItemModel, StoreModel, UserModel
from schemas import ItemSchema, ItemUpdateSchema, StoreSchema, UserSchema
from blocklist import BLOCKLIST

store_schema = StoreSchema()
item_schema = ItemSchema()
item_update_schema = ItemUpdateSchema()
user_schema = UserSchema()

def create_app():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///data.db")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["JWT_SECRET_KEY"] = "109272929932864583663146964337201166505"
    db.init_app(app)

    with app.app_context():
        db.create_all()

    @app.before_request
    def enforce_foreign_keys():
        if db.engine.dialect.name == "sqlite":
            db.session.execute(text("PRAGMA foreign_keys=ON"))

    return app

app = create_app()
jwt = JWTManager(app)
migrate = Migrate(app,db)

@jwt.token_in_blocklist_loader
def check_if_token_in_blocklist(jwt_header, jwt_payload):
    return jwt_payload["jti"] in BLOCKLIST

@jwt.revoked_token_loader
def revoked_token_callback(jwt_header, jwt_payload):
    return (
        jsonify(
            {"description": "The token has been revoked.", "error": "token_revoked"}
        ),
        401,
    )

@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return (
        jsonify({"message": "The token has expired.", "error": "token_expired"}),
        401,
    )

@jwt.invalid_token_loader
def invalid_token_callback(error):
    return (
        jsonify(
            {"message": "Signature verification failed.", "error": "invalid_token"}
        ),
        401,
    )

@jwt.unauthorized_loader
def missing_token_callback(error):
    return (
        jsonify(
            {
                "description": "Request does not contain an access token.",
                "error": "authorization_required",
            }
        ),
        401,
    )

@app.route("/", methods=["GET"])
@app.route("/home", methods=["GET"])
def home():
    return "This is my flask app!!"

@app.route("/store", methods=["POST"])
@jwt_required()
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
@jwt_required()
def get_all_stores():
    stores = StoreModel.query.all()
    return jsonify({"stores": [store_schema.dump(store) for store in stores]})

@app.route("/store/<int:store_id>", methods=["GET"])
@jwt_required()
def get_store(store_id):
    store = StoreModel.query.get_or_404(store_id)
    return jsonify(store_schema.dump(store))

@app.route("/store/<int:store_id>", methods=["PUT"])
@jwt_required()
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
@jwt_required()
def delete_store(store_id):
    store = StoreModel.query.get_or_404(store_id)
    db.session.delete(store)
    db.session.commit()
    return {"message": "Store Deleted!!"}

@app.route("/item", methods=["POST"])
@jwt_required()
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
@jwt_required()
def get_all_items():
    items = ItemModel.query.all()
    return jsonify({"items": [item_schema.dump(item) for item in items]})

@app.route("/item/<int:item_id>", methods=["GET"])
@jwt_required()
def get_item(item_id):
    item = ItemModel.query.get_or_404(item_id)
    return jsonify(item_schema.dump(item))

@app.route("/item/<int:item_id>", methods=["PUT"])
@jwt_required()
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
@jwt_required()
def delete_item(item_id):
    item = ItemModel.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    return {"message": "Item Deleted!!"}

@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    user_data = user_schema.load(data)
    if UserModel.query.filter(UserModel.username == user_data["username"]).first():
        return {"message": "User with given username already exists"}, 400
    user = UserModel(
        username=user_data["username"],
        password=pbkdf2_sha256.hash(user_data["password"])
    )
    db.session.add(user)
    try:
        db.session.commit()
        return {"message": "User created!!"}, 200
    except IntegrityError as e:
        db.session.rollback()
        return {"message": f"An error occurred while creating user: {str(e.orig)}"}, 400
    except Exception as e:
        db.session.rollback()
        return {"message": f"An error occurred while creating user: {str(e)}"}, 400

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    user_data = user_schema.load(data)
    user = UserModel.query.filter(UserModel.username == user_data["username"]).first()
    if user and pbkdf2_sha256.verify(user_data["password"], user.password):
        access_token = create_access_token(identity=user.id)
        return {"access_token": access_token}
    else:
        return {"message": "Invalid credentials"}, 400

@app.route("/logout", methods=["POST"])
@jwt_required()
def logout():
    jti = get_jwt()["jti"]
    BLOCKLIST.add(jti)
    return {"message":"successfully logged out!!"}, 200

@app.route("/user/<int:id>", methods=["GET"])
@jwt_required()
def get_user(id):
    user = UserModel.query.get_or_404(id)
    return jsonify(user_schema.dump(user))

@app.route("/user/<int:id>", methods=["DELETE"])
@jwt_required()
def delete_user(id):
    user = UserModel.query.get_or_404(id)
    db.session.delete(user)
    db.session.commit()
    return {"message": "User deleted!!"}, 200

if __name__ == "__main__":
    app.run(debug=True)
