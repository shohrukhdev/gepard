import requests
import json
from datetime import datetime, timedelta

# Base URL for all API calls
BASE_URL = "https://apisupply.smartpos.uz"
AUTH_ENDPOINT = "/api/cabinet/v1/account/login"


class SupplyAuthService:
    def __init__(self, phone, password):
        """
        Initialize the auth service with credentials

        Args:
            phone (str): Phone number for authentication
            password (str): Password for authentication
        """
        self.phone = phone
        self.password = password
        self.access_token = None
        self.token_expiry = None
        # Default token expiry time (can be adjusted based on actual token lifetime)
        self.token_lifetime = timedelta(hours=1)

    def get_auth_token(self, force_refresh=False):
        """
        Get authentication token. If token exists and is not expired, return it,
        otherwise request a new one.

        Args:
            force_refresh (bool): If True, force a new token request regardless of expiry

        Returns:
            str: The access token

        Raises:
            Exception: If authentication fails
        """
        # Check if we need to get a new token
        if force_refresh or not self.is_token_valid():
            self._request_new_token()

        return self.access_token

    def is_token_valid(self):
        """
        Check if the current token is valid and not expired

        Returns:
            bool: True if token exists and is not expired, False otherwise
        """
        if not self.access_token or not self.token_expiry:
            return False

        return datetime.now() < self.token_expiry

    def _request_new_token(self):
        """
        Request a new authentication token from the API

        Raises:
            Exception: If the authentication request fails
        """
        url = f"{BASE_URL}{AUTH_ENDPOINT}"

        payload = {
            "phone": self.phone,
            "password": self.password,
            "rememberMe": True
        }

        headers = {
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(url, data=json.dumps(payload), headers=headers)
            response.raise_for_status()  # Raise exception for non-200 status codes

            data = response.json()
            self.access_token = data.get("access_token")

            if not self.access_token:
                raise Exception("Authentication failed: No access token in response")

            # Set token expiry time
            self.token_expiry = datetime.now() + self.token_lifetime

        except requests.exceptions.RequestException as e:
            raise Exception(f"Authentication request failed: {str(e)}")

    def get_auth_header(self):
        """
        Get the authorization header for API requests

        Returns:
            dict: Headers with Authorization token
        """
        token = self.get_auth_token()
        return {
            "Authorization": f"Bearer {token}"
        }


# Function to create a pre-configured auth service instance
def create_supply_auth_service(phone, password):
    """
    Create and return a configured SupplyAuthService instance

    Args:
        phone (str): Phone number for authentication
        password (str): Password for authentication

    Returns:
        SupplyAuthService: Configured auth service instance
    """
    return SupplyAuthService(phone, password)
