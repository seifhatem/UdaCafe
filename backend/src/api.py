import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink, db
from .auth.auth import AuthError, requires_auth, allowedPermissions





app = Flask(__name__)
setup_db(app)
CORS(app)

'''
@TODO uncomment the following line to initialize the datbase
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
'''
db_drop_and_create_all()
#db.drop_all()
db.create_all()

cors = CORS(app, resources={r"*": {"origins": "*"}})

## Error Handling

@app.errorhandler(400)
def error400(error):
    return jsonify({"success": False,"error": 400,"description": "Malformed Request"}), 400

@app.errorhandler(404)
def error404(error):
    return jsonify({"success": False,"error": 404,"description": "Requested endpoint is not found"}), 404

@app.errorhandler(405)
def error405(error):
    return jsonify({"success": False,"error": 405,"description": "Method not setup, please make sure that the HTTP method type is set correctly"}), 405

@app.errorhandler(422)
def error422(error):
    return jsonify({"success": False,"error": 422,"description": "Unprocessable due to origin restrictions"}), 422

@app.errorhandler(500)
def error500(error):
    return jsonify({"success": False,"error": 500,"description": "Server Error, please contact administrator"}), 500

@app.errorhandler(AuthError)
def error_auth(error):
    return jsonify({"success": False,"error": error.error["code"],"description": error.error["description"]}), 401

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,true')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response


## ROUTES
@app.route('/drinks')
def drinks():
    drinks= db.session.query(Drink).all()
    return jsonify(success=True,drinks=[drink.short() for drink in drinks])

@app.route('/permissions')
def retrieveAllowedPermissions():
    return allowedPermissions()

@app.route('/drinks-detail')
@requires_auth("get:drinks-detail")
def drinksDetailed(payload):
    drinks = db.session.query(Drink).all()
    return jsonify(success=True,drinks=[drink.long() for drink in drinks])

@app.route('/drinks', methods=["POST"])
@requires_auth("post:drinks")
def createDrink(payload):
    requestData = request.json
    try:
        drink = Drink(title=requestData["title"], recipe=json.dumps(requestData["recipe"]))
    except Exception:
        return jsonify({"success": False,"error": 400,"description": "Malformed Request"}), 400
    try:
        drink.insert()
    except Exception:
        return jsonify({"success": False,"error": 500,"description": "Unable to add the drink to the database"}), 500
    return jsonify(success=True,drinks=[drink.long()])


@app.route('/drinks/<drinkid>', methods=["PATCH"])
@requires_auth("patch:drinks")
def updateDrink(payload,drinkid):
    requestData = request.json
    alterDrink = db.session.query(Drink).filter_by(id = drinkid).first()
    if alterDrink is None:
        return jsonify({"success": False,"error": 404,"description": "No drinks found with the specified id"}), 40
    try:
        if requestData.get("title") is not None:
            alterDrink.title = requestData["title"]
        if requestData.get("recipe") is not None:
            alterDrink.recipe = json.dumps(requestData["recipe"])
        db.session.commit()
    except Exception as e:
        return jsonify({"success": False,"error": 500,"description": "Unable to edit the drink"}), 500
    return jsonify(success=True,drinks=[alterDrink.long()])

@app.route('/drinks/<drinkid>', methods=["DELETE"])
@requires_auth("delete:drinks")
def deleteQuestion(payload,drinkid):
  deletedCount = db.session.query(Drink).filter_by(id = drinkid).delete()
  try:
      db.session.commit()
      if deletedCount == 1:
          return jsonify({"success": True, "delete": drinkid})
      return jsonify({"success": False,"error": 404,"description": "No drinks found with the specified id"}), 404
  except Exception as e:
      db.session.rollback()
      db.session.flush()
      abort(500)
