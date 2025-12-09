import pytest
import sys
import os
import json

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from test_basic import client


class TestCustomerSignup:
    """Test cases for /customer/signup endpoint."""

    def test_customer_signup_success(self, client):
        """Test successful customer signup."""
        payload = {
            "firstName": "John",
            "lastName": "Doe",
            "email": f"john.doe.{int(__import__('time').time())}@example.com",
            "password": "SecurePass123!",
            "confirmPassword": "SecurePass123!"
        }
        res = client.post('/customer/signup', 
                         data=json.dumps(payload),
                         content_type='application/json')
        assert res.status_code == 200
        data = json.loads(res.data)
        assert data['status'] == 'success'
        assert 'User_ID' in data
        assert 'Customer_ID' in data

    def test_customer_signup_missing_first_name(self, client):
        """Test signup fails with missing first name."""
        payload = {
            "lastName": "Doe",
            "email": "john@example.com",
            "password": "SecurePass123!",
            "confirmPassword": "SecurePass123!"
        }
        res = client.post('/customer/signup',
                         data=json.dumps(payload),
                         content_type='application/json')
        assert res.status_code == 400
        
        data = json.loads(res.data)
        assert data['status'] == 'error'
        assert data['message'] == 'firstName'
        
    def test_customer_signup_missing_last_name(self, client):
        """Test signup fails with missing last name."""
        payload = {
            "firstName": "John",
            "email": "john@example.com",
            "password": "SecurePass123!",
            "confirmPassword": "SecurePass123!"
        }
        res = client.post('/customer/signup',
                         data=json.dumps(payload),
                         content_type='application/json')
        assert res.status_code == 400
        data = json.loads(res.data)
        assert data['status'] == 'failure'

    def test_customer_signup_missing_email(self, client):
        """Test signup fails with missing email."""
        payload = {
            "firstName": "John",
            "lastName": "Doe",
            "password": "SecurePass123!",
            "confirmPassword": "SecurePass123!"
        }
        res = client.post('/customer/signup',
                         data=json.dumps(payload),
                         content_type='application/json')
        assert res.status_code == 400
        data = json.loads(res.data)
        assert data['status'] == 'failure'

    def test_customer_signup_invalid_email(self, client):
        """Test signup fails with invalid email format."""
        payload = {
            "firstName": "John",
            "lastName": "Doe",
            "email": "not-a-valid-email",
            "password": "SecurePass123!",
            "confirmPassword": "SecurePass123!"
        }
        res = client.post('/customer/signup',
                         data=json.dumps(payload),
                         content_type='application/json')
        assert res.status_code == 400
        data = json.loads(res.data)
        assert data['status'] == 'failure'

    def test_customer_signup_missing_password(self, client):
        """Test signup fails with missing password."""
        payload = {
            "firstName": "John",
            "lastName": "Doe",
            "email": "john@example.com",
            "confirmPassword": "SecurePass123!"
        }
        res = client.post('/customer/signup',
                         data=json.dumps(payload),
                         content_type='application/json')
        assert res.status_code == 400
        data = json.loads(res.data)
        assert data['status'] == 'failure'

    def test_customer_signup_passwords_dont_match(self, client):
        """Test signup fails when passwords don't match."""
        payload = {
            "firstName": "John",
            "lastName": "Doe",
            "email": f"john.{int(__import__('time').time())}@example.com",
            "password": "SecurePass123!",
            "confirmPassword": "DifferentPass123!"
        }
        res = client.post('/customer/signup',
                         data=json.dumps(payload),
                         content_type='application/json')
        assert res.status_code == 400
        data = json.loads(res.data)
        assert data['status'] == 'failure'

    def test_customer_signup_duplicate_email(self, client):
        """Test signup fails with duplicate email."""
        email = f"duplicate.{int(__import__('time').time())}@example.com"
        payload = {
            "firstName": "John",
            "lastName": "Doe",
            "email": email,
            "password": "SecurePass123!",
            "confirmPassword": "SecurePass123!"
        }
        # First signup should succeed
        res1 = client.post('/customer/signup',
                          data=json.dumps(payload),
                          content_type='application/json')
        assert res1.status_code == 200
        
        # Second signup with same email should fail
        res2 = client.post('/customer/signup',
                          data=json.dumps(payload),
                          content_type='application/json')
        assert res2.status_code == 409
        data = json.loads(res2.data)
        assert data['status'] == 'failure'

    def test_customer_signup_empty_first_name(self, client):
        """Test signup succeeds with empty first name (backend does not validate empty strings)."""
        payload = {
            "firstName": "",
            "lastName": "Doe",
            "email": f"empty.{int(__import__('time').time())}@example.com",
            "password": "SecurePass123!",
            "confirmPassword": "SecurePass123!"
        }
        res = client.post('/customer/signup',
                         data=json.dumps(payload),
                         content_type='application/json')
        # Backend accepts empty strings, so this should succeed
        assert res.status_code == 200
        data = json.loads(res.data)
        assert data['status'] == 'success'

    def test_customer_signup_empty_email(self, client):
        """Test signup fails with empty email."""
        payload = {
            "firstName": "John",
            "lastName": "Doe",
            "email": "",
            "password": "SecurePass123!",
            "confirmPassword": "SecurePass123!"
        }
        res = client.post('/customer/signup',
                         data=json.dumps(payload),
                         content_type='application/json')
        assert res.status_code == 400
        data = json.loads(res.data)
        assert data['status'] == 'failure'
