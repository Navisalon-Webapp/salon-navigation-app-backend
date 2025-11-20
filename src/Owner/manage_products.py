from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from mysql.connector import Error
from .owner_func import *

manage_products = Blueprint("manage_products", __name__, url_prefix='/owner')

@manage_products.route('/products', methods=["GET"])
@login_required
def get_products():
    try:
        bid = get_curr_bid()
        products = get_products_by_bid(bid)
        
        result = []
        for product in products:
            result.append({
                "pid": product["pid"],
                "name": product["name"],
                "price": float(product["price"]),
                "stock": product["stock"],
                "description": product.get("description"),
                "image": product.get("image")
            })
        
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({
            "status": "failure",
            "message": str(e)
        }), 401
    except Error as e:
        return jsonify({
            "status": "failure",
            "message": "Database error",
            "error": str(e)
        }), 500


@manage_products.route('/products', methods=["POST"])
@login_required
def add_new_product():
    try:
        bid = get_curr_bid()
        data = request.get_json()
        
        if not data or "name" not in data or "price" not in data or "stock" not in data:
            return jsonify({
                "status": "failure",
                "message": "Missing required fields: name, price, stock"
            }), 400
        
        name = data["name"]
        price = data["price"]
        stock = data["stock"]
        description = data.get("description")
        image = data.get("image")
        
        pid = add_product(bid, name, price, stock, description, image)
        
        return jsonify({
            "status": "success",
            "product": {
                "pid": pid,
                "name": name,
                "price": float(price),
                "stock": stock,
                "description": description,
                "image": image
            }
        }), 201
    except ValueError as e:
        return jsonify({
            "status": "failure",
            "message": str(e)
        }), 401
    except Error as e:
        return jsonify({
            "status": "failure",
            "message": "Database error",
            "error": str(e)
        }), 500


@manage_products.route('/products/<int:pid>', methods=["PUT"])
@login_required
def update_product(pid):
    try:
        data = request.get_json()
        
        if not data or "stock" not in data:
            return jsonify({
                "status": "failure",
                "message": "Missing required field: stock"
            }), 400
        
        stock = data["stock"]
        
        product = get_product_by_id(pid)
        if not product:
            return jsonify({
                "status": "failure",
                "message": "Product not found"
            }), 404
        
        bid = get_curr_bid()
        if product["bid"] != bid:
            return jsonify({
                "status": "failure",
                "message": "Unauthorized to modify this product"
            }), 403
        
        update_product_stock_by_pid(pid, stock)
        
        return jsonify({
            "status": "success",
            "message": "Product stock updated",
            "product": {
                "pid": pid,
                "stock": stock
            }
        }), 200
    except ValueError as e:
        return jsonify({
            "status": "failure",
            "message": str(e)
        }), 401
    except Error as e:
        return jsonify({
            "status": "failure",
            "message": "Database error",
            "error": str(e)
        }), 500


@manage_products.route('/products/<int:pid>/purchase', methods=["POST"])
@login_required
def record_purchase(pid):
    try:
        data = request.get_json()
        
        if not data or "quantity" not in data:
            return jsonify({
                "status": "failure",
                "message": "Missing required field: quantity"
            }), 400
        
        quantity = data["quantity"]
        
        product = get_product_by_id(id)
        if not product:
            return jsonify({
                "status": "failure",
                "message": "Product not found"
            }), 404
        
        bid = get_curr_bid()
        if product["bid"] != bid:
            return jsonify({
                "status": "failure",
                "message": "Unauthorized to modify this product"
            }), 403
        
        new_stock = max(0, product["stock"] - quantity)
        
        update_product_stock_by_pid(pid, new_stock)
        
        return jsonify({
            "status": "success",
            "message": "Purchase recorded",
            "product": {
                "pid": pid,
                "stock": new_stock,
                "quantity_purchased": quantity
            }
        }), 200
    except ValueError as e:
        return jsonify({
            "status": "failure",
            "message": str(e)
        }), 401
    except Error as e:
        return jsonify({
            "status": "failure",
            "message": "Database error",
            "error": str(e)
        }), 500


@manage_products.route('/products/<int:pid>', methods=["DELETE"])
@login_required
def delete_product(pid):
    try:
        product = get_product_by_id(pid)
        if not product:
            return jsonify({
                "status": "failure",
                "message": "Product not found"
            }), 404
        
        bid = get_curr_bid()
        if product["bid"] != bid:
            return jsonify({
                "status": "failure",
                "message": "Unauthorized to delete this product"
            }), 403
        
        delete_product_by_pid(pid)
        
        return jsonify({
            "status": "success",
            "message": "Product deleted successfully"
        }), 200
    except ValueError as e:
        return jsonify({
            "status": "failure",
            "message": str(e)
        }), 401
    except Error as e:
        return jsonify({
            "status": "failure",
            "message": "Database error",
            "error": str(e)
        }), 500
