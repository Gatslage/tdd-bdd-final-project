######################################################################
# Copyright 2016, 2022 John J. Rofrano. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
######################################################################

# spell: ignore Rofrano jsonify restx dbname
"""
Product Store Service with UI
"""
from flask import jsonify, request, abort
from flask import url_for  # noqa: F401 pylint: disable=unused-import
from service.models import Product, Category
from service.common import status  # HTTP Status Codes
from . import app


######################################################################
# H E A L T H   C H E C K
######################################################################
@app.route("/health")
def healthcheck():
    """Let them know our heart is still beating"""
    return jsonify(status=200, message="OK"), status.HTTP_200_OK


######################################################################
# H O M E   P A G E
######################################################################
@app.route("/")
def index():
    """Base URL for our service"""
    return app.send_static_file("index.html")


######################################################################
#  U T I L I T Y   F U N C T I O N S
######################################################################
def check_content_type(content_type):
    """Checks that the media type is correct"""
    if "Content-Type" not in request.headers:
        app.logger.error("No Content-Type specified.")
        abort(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            f"Content-Type must be {content_type}",
        )

    if request.headers["Content-Type"] == content_type:
        return

    app.logger.error("Invalid Content-Type: %s", request.headers["Content-Type"])
    abort(
        status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        f"Content-Type must be {content_type}",
    )


######################################################################
# C R E A T E   A   N E W   P R O D U C T
######################################################################
@app.route("/products", methods=["POST"])
def create_products():
    """
    Creates a Product
    This endpoint will create a Product based the data in the body that is posted
    """
    app.logger.info("Request to Create a Product...")
    check_content_type("application/json")

    data = request.get_json()
    app.logger.info("Processing: %s", data)
    product = Product()
    product.deserialize(data)
    product.create()
    app.logger.info("Product with new id [%s] saved!", product.id)

    message = product.serialize()

    #
    # Uncomment this line of code once you implement READ A PRODUCT
    #
    # location_url = url_for("get_products", product_id=product.id, _external=True)
    location_url = "/"  # delete once READ is implemented
    return jsonify(message), status.HTTP_201_CREATED, {"Location": location_url}


######################################################################
# L I S T   A L L   P R O D U C T S, BY NAME, CATEGORY, AVAILABLE
######################################################################

@app.route("/products", methods=["GET"])
def list_products():
    """Returns a list of Products"""
    app.logger.info("Request to list Products...")
    # use the Product.all() method to retrieve all products
    
    # create a list of serialize() products
    name = request.args.get("name")
    category = request.args.get("category")
    available = request.args.get("available")

    if name:
        products = Product.find_by_name(name)
        final_products = [prod.serialize() for prod in products]
        app.logger.info("[%s] Products final by name", len(final_products))
    elif category:
        products = Product.find_by_category(getattr(Category,category))
        final_products = [prod.serialize() for prod in products]
        app.logger.info("[%s] Products final by category", len(final_products))    
    elif available:
        products = Product.find_by_availability(available)
        final_products = [prod.serialize() for prod in products]
        app.logger.info("[%s] Products final by available", len(final_products))
    else:
        products = Product.all()
        final_products = [prod.serialize() for prod in products]
        # log the number of products being returned in the list 
        app.logger.info("[%s] Products final", len(final_products))
    # return the list with a return code of status.HTTP_200_OK
    return final_products, status.HTTP_200_OK



######################################################################
# R E A D   A   P R O D U C T
######################################################################

@app.route("/products/<product_id>", methods=["GET"])
def get_products(product_id):
    """
    retrieve specific product from database by id inside link
    """
    app.logger.info("Request to Retrieve a Product...")
    prods = Product.find(product_id)
    if not prods:
        return {}, status.HTTP_404_NOT_FOUND
    return prods.serialize(), status.HTTP_200_OK




######################################################################
# U P D A T E   A   P R O D U C T
######################################################################

@app.route("/products/<product_id>", methods=["PUT"])
def update_products(product_id):
    """
    Update an Product
    This endpoint will update a Product based on the body that is posted
    """
    app.logger.info("Request to Update a product with id [%s]", product_id)
    check_content_type("application/json")
    prod_upt = Product.find(product_id)
    # abort() with a status.HTTP_404_NOT_FOUND if it cannot be found
    if not prod_upt:
        return {}, status.HTTP_404_NOT_FOUND
    try:
        prod_upt.deserialize(request.get_json())
        prod_upt.update()
        return prod_upt.serialize(), status.HTTP_200_OK
    except TypeError:
        return {}, status.HTTP_400_BAD_REQUEST

######################################################################
# D E L E T E   A   P R O D U C T
######################################################################


@app.route("/products/<product_id>", methods=["DELETE"])
def delete_products(product_id):
    """
    Delete a Product
    This endpoint will delete a Product based the id specified in the path
    """
    app.logger.info("Request to Delete a product with id [%s]", product_id)
    # use the Product.find() method to retrieve the product by the product_id
    prod_upt = Product.find(product_id)
    # abort() with a status.HTTP_404_NOT_FOUND if it cannot be found
    if not prod_upt:
        return {}, status.HTTP_404_NOT_FOUND

    # if found, call the delete() method on the product
    prod_upt.delete()
    # return and empty body ("") with a return code of status.HTTP_204_NO_CONTENT
    return {}, status.HTTP_204_NO_CONTENT
