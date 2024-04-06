######################################################################
# Copyright 2016, 2023 John J. Rofrano. All Rights Reserved.
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
"""
Product API Service Test Suite

Test cases can be run with the following:
  nosetests -v --with-spec --spec-color
  coverage report -m
  codecov --token=$CODECOV_TOKEN

  While debugging just these tests it's convenient to use this:
    nosetests --stop tests/test_service.py:TestProductService
"""
import os
import logging
from decimal import Decimal
from urllib.parse import quote_plus
from unittest import TestCase
from service import app
from service.common import status
from service.models import db, init_db, Product
from tests.factories import ProductFactory

# Disable all but critical errors during normal test run
# uncomment for debugging failing tests
# logging.disable(logging.CRITICAL)

# DATABASE_URI = os.getenv('DATABASE_URI', 'sqlite:///../db/test.db')
DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)
BASE_URL = "/products"


######################################################################
#  T E S T   C A S E S
######################################################################
# pylint: disable=too-many-public-methods
class TestProductRoutes(TestCase):
    """Product Service tests"""

    @classmethod
    def setUpClass(cls):
        """Run once before all tests"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        # Set up the test database
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        init_db(app)

    @classmethod
    def tearDownClass(cls):
        """Run once after all tests"""
        db.session.close()

    def setUp(self):
        """Runs before each test"""
        self.client = app.test_client()
        db.session.query(Product).delete()  # clean up the last tests
        db.session.commit()

    def tearDown(self):
        db.session.remove()

    ############################################################
    # Utility function to bulk create products
    ############################################################
    def _create_products(self, count: int = 1) -> list:
        """Factory method to create products in bulk"""
        products = []
        for _ in range(count):
            test_product = ProductFactory()
            response = self.client.post(BASE_URL, json=test_product.serialize())
            self.assertEqual(
                response.status_code, status.HTTP_201_CREATED, "Could not create test product"
            )
            new_product = response.get_json()
            test_product.id = new_product["id"]
            products.append(test_product)
        return products

    ############################################################
    #  T E S T   C A S E S
    ############################################################
    def test_index(self):
        """It should return the index page"""
        response = self.client.get("/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(b"Product Catalog Administration", response.data)

    def test_health(self):
        """It should be healthy"""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(data['message'], 'OK')

    # ----------------------------------------------------------
    # TEST CREATE
    # ----------------------------------------------------------
    def test_create_product(self):
        """It should Create a new Product"""
        test_product = ProductFactory()
        logging.debug("Test Product: %s", test_product.serialize())
        response = self.client.post(BASE_URL, json=test_product.serialize())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Make sure location header is set
        location = response.headers.get("Location", None)
        self.assertIsNotNone(location)

        # Check the data is correct
        new_product = response.get_json()
        self.assertEqual(new_product["name"], test_product.name)
        self.assertEqual(new_product["description"], test_product.description)
        self.assertEqual(Decimal(new_product["price"]), test_product.price)
        self.assertEqual(new_product["available"], test_product.available)
        self.assertEqual(new_product["category"], test_product.category.name)

        #
        # Uncomment this code once READ is implemented
        #

        # # Check that the location header was correct
        # response = self.client.get(location)
        # self.assertEqual(response.status_code, status.HTTP_200_OK)
        # new_product = response.get_json()
        # self.assertEqual(new_product["name"], test_product.name)
        # self.assertEqual(new_product["description"], test_product.description)
        # self.assertEqual(Decimal(new_product["price"]), test_product.price)
        # self.assertEqual(new_product["available"], test_product.available)
        # self.assertEqual(new_product["category"], test_product.category.name)

    def test_create_product_with_no_name(self):
        """It should not Create a Product without a name"""
        product = ProductFactory()
        new_product = product.serialize()
        del new_product["name"]
        logging.debug("Product no name: %s", new_product)
        response = self.client.post(BASE_URL, json=new_product)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_product_no_content_type(self):
        """It should not Create a Product with no Content-Type"""
        response = self.client.post(BASE_URL, data="bad data")
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    def test_create_product_wrong_content_type(self):
        """It should not Create a Product with wrong Content-Type"""
        response = self.client.post(BASE_URL, data={}, content_type="plain/text")
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    #
    # ADD YOUR TEST CASES HERE
    #

    ######################################################################
    # Utility functions
    ######################################################################

    def get_product_count(self):
        """save the current number of products"""
        response = self.client.get(BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        # logging.debug("data = %s", data)
        return len(data)

    def test_read_product(self):
        """it should test read process"""
        test_product = self._create_products()[0]
        result_read = self.client.get(f"{BASE_URL}/{test_product.id}")
        self.assertEqual(result_read.status_code, status.HTTP_200_OK)
        self.assertEqual(result_read.get_json(), test_product.serialize())

    def test_get_product_not_found(self):
        """it should test read process not found"""
        result_read = self.client.get(f"{BASE_URL}/22")
        self.assertEqual(result_read.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_product(self):
        """it should test update process by create and change value and verify """
        prod = self._create_products()[0]
        #update product
        prod.description = "new_description_for_test"
        result_upt = self.client.put(f"{BASE_URL}/{prod.id}",json=prod.serialize())
        self.assertEqual(result_upt.status_code,status.HTTP_200_OK) 
        self.assertEqual(result_upt.get_json()["description"],"new_description_for_test")

    def test_can_not_update(self):
        """it should fail by id bad request and not found"""
        #try with bad product_id
        result_not_found = self.client.put(f"{BASE_URL}/22",json=ProductFactory().serialize())
        self.assertEqual(result_not_found.status_code,status.HTTP_404_NOT_FOUND)
        #try to update a true product but by bad request , (empty json)
        prod = self._create_products()[0]
        result_bad_request = self.client.put(f"{BASE_URL}/{prod.id}",json={})
        self.assertEqual(result_bad_request.status_code,status.HTTP_400_BAD_REQUEST)

    def test_delete_product(self):
        """it should test delete route """
        prod = self._create_products()[0]
        #start deletion
        result_delete = self.client.delete(f"{BASE_URL}/{prod.id}")
        self.assertEqual(result_delete.status_code,status.HTTP_204_NO_CONTENT)
        #try to find
        result_read = self.client.get(f"{BASE_URL}/{prod.id}")
        self.assertEqual(result_read.status_code, status.HTTP_404_NOT_FOUND)

    def test_can_not_delete_product(self):
        """it should verify , delete error response for not found"""
        #start deletion
        result_delete = self.client.delete(f"{BASE_URL}/22")
        self.assertEqual(result_delete.status_code,status.HTTP_404_NOT_FOUND)

    def test_list_all_products(self):
        """should list all products"""
        prods = self._create_products(10)
        result_list = self.client.get(f"{BASE_URL}")
        self.assertEqual(result_list.status_code,status.HTTP_200_OK)
        self.assertEqual(len(result_list.get_json()),10)

    def test_list_by_name(self):
        """should list by name testing"""
        prods = self._create_products(10)
        name_t = prods[0].name
        numberOccurence = len([prod for prod in prods if prod.name == name_t])
        response = self.client.get(
            BASE_URL, query_string=f"name={quote_plus(name_t)}"
        )        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.get_json()),numberOccurence)

    def test_list_by_category(self):
        """should list by category testing"""
        prods = self._create_products(10)
        category_t = prods[0].category.name
        numberOccurence = len([prod for prod in prods if prod.category.name == category_t])
        response = self.client.get(
            BASE_URL, query_string=f"category={quote_plus(category_t)}"
        )        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.get_json()),numberOccurence)

    def test_list_by_available(self):
        """should list by available testing"""
        prods = self._create_products(10)
        ava_t = prods[0].available
        numberOccurence = len([prod for prod in prods if prod.available == ava_t])
        response = self.client.get(
            BASE_URL, query_string=f"available={ava_t}"
        )        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.get_json()),numberOccurence)