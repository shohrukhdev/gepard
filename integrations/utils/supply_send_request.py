import json
import logging
import time
from datetime import datetime
import requests
from django.conf import settings
from django.db import transaction

from integrations.utils.supply_auth import create_supply_auth_service
from integrations.models import Nomenclature, Product

logger = logging.getLogger(__name__)

# Configuration constants
SUPPLY_API_BASE_URL = "https://apisupply.smartpos.uz"
SUPPLY_ORDER_ENDPOINT = "/api/cabinet/v1/orders/1c"
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds


# Create auth service with credentials from settings
def get_auth_service():
    return create_supply_auth_service(
        phone=settings.SUPPLY_API_PHONE,
        password=settings.SUPPLY_API_PASSWORD
    )


def transform_nomenclature_to_supply_order(nomenclature):
    """
    Transform a Nomenclature object into the format required by the Supply API.

    Args:
        nomenclature: Nomenclature model instance

    Returns:
        dict: Data formatted for Supply API
    """
    # Parse contract data
    contract_data = {}
    if nomenclature.contract:
        try:
            contract_data = json.loads(nomenclature.contract)
        except json.JSONDecodeError:
            # If not valid JSON, use as a string
            contract_data = {
                "number": nomenclature.contract,
                "date": datetime.now().strftime("%Y-%m-%d")
            }

    # Get products related to this nomenclature
    products = Product.objects.filter(nomenclature=nomenclature)

    # Format products for Supply API
    formatted_products = []
    for product in products:
        formatted_products.append({
            "barcode": product.barcode or "",
            "baseSumma": 0,  # Default value, update based on your business logic
            "catalogCode": product.catalog_code or "",
            "catalogName": product.name or "",
            "hasMark": "false",  # Default value, update based on your business logic
            "committentTin": "",  # Default value, update based on your business logic
            "committentName": "",  # Default value, update based on your business logic
            "committentVatRegCode": "",  # Default value, update based on your business logic
            "committentVatRegStatus": 0,  # Default value, update based on your business logic
            "count": 1,  # Default value, update based on your business logic
            "deliverySum": 0,  # Default value, update based on your business logic
            "deliverySumWithVat": 0,  # Default value, update based on your business logic
            "expiryDate": datetime.now().strftime("%Y-%m-%d"),  # Default value
            "lgotaId": 0,  # Default value, update based on your business logic
            "lgotaName": "",  # Default value, update based on your business logic
            "lgotaType": "0",  # Default value, update based on your business logic
            "lgotaVatSum": 0,  # Default value, update based on your business logic
            "name": product.name or "",
            "packageCode": product.package_code or "",
            "packageName": "",  # Default value, update based on your business logic
            "profitRate": 0,  # Default value, update based on your business logic
            "serial": "",  # Default value, update based on your business logic
            "summa": 0,  # Default value, update based on your business logic
            "vatRate": "null",  # Default value, update based on your business logic
            "vatSum": 0,  # Default value, update based on your business logic
            "code1C": product.code1c or "",
            "warehouseId": "null"  # Default value, update based on your business logic
        })

    # Create order payload
    order_data = {
        "branchId": settings.SUPPLY_BRANCH_ID,  # Get from settings
        "contract": {
            "date": contract_data.get("date", datetime.now().strftime("%Y-%m-%d")),
            "number": contract_data.get("number", "1")
        },
        "createStockIn": True,
        "customerTin": nomenclature.customer_tin or "",
        "description": f"Order from 1C: {nomenclature.external_id}",
        "orderDate": datetime.now().isoformat(timespec='milliseconds') + "Z",
        "orderNumber": nomenclature.external_id,
        "advancePaymentPercent": "0",  # Default value, update based on your business logic
        "advancePaymentAmount": "0",  # Default value, update based on your business logic
        "specificationDate": datetime.now().isoformat(timespec='milliseconds'),
        "specificationNumber": f"SPEC-{nomenclature.external_id}",
        "products": formatted_products,
        "warehouseId": settings.SUPPLY_WAREHOUSE_ID  # Get from settings
    }

    return order_data


def send_nomenclature_to_supply(nomenclature_id):
    """
    Sends a Nomenclature to the Supply service.

    Args:
        nomenclature_id: ID of the Nomenclature to send

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        nomenclature = Nomenclature.objects.get(id=nomenclature_id)

        # Skip if already sent successfully
        if nomenclature.sent_successfully:
            logger.info(f"Nomenclature {nomenclature.external_id} already sent successfully. Skipping.")
            return True

        # Get auth service
        auth_service = get_auth_service()

        # Transform data for Supply API
        order_data = transform_nomenclature_to_supply_order(nomenclature)

        # Send request with retries
        success, response_data = send_to_supply_with_retry(order_data, auth_service)

        # Update Nomenclature with response
        with transaction.atomic():
            nomenclature.sent_on = datetime.now()
            nomenclature.response = json.dumps(response_data)
            nomenclature.sent_successfully = success
            nomenclature.save()

        if success:
            logger.info(f"Successfully sent Nomenclature {nomenclature.external_id} to Supply")
        else:
            logger.warning(f"Failed to send Nomenclature {nomenclature.external_id} to Supply: {response_data}")

        return success

    except Nomenclature.DoesNotExist:
        logger.error(f"Nomenclature with ID {nomenclature_id} not found")
        return False
    except Exception as e:
        logger.exception(f"Error sending Nomenclature {nomenclature_id} to Supply: {str(e)}")
        # If an exception occurred, try to update the nomenclature record with the error
        try:
            nomenclature = Nomenclature.objects.get(id=nomenclature_id)
            with transaction.atomic():
                nomenclature.sent_on = datetime.now()
                nomenclature.response = json.dumps({
                    "error": str(e),
                    "success": False,
                    "exception_type": type(e).__name__
                })
                nomenclature.sent_successfully = False
                nomenclature.save()
        except:
            # If we can't even update the record, just log it
            logger.exception("Failed to update nomenclature with error details")

        return False


def send_to_supply_with_retry(order_data, auth_service, retries=MAX_RETRIES):
    """
    Send data to Supply API with retry mechanism.

    Args:
        order_data: Formatted data to send
        auth_service: SupplyAuthService instance
        retries: Number of retries allowed

    Returns:
        tuple: (success, response_data)
            - success (bool): Whether the request was successful
            - response_data (dict): Response data or error information
    """
    url = f"{SUPPLY_API_BASE_URL}{SUPPLY_ORDER_ENDPOINT}"
    attempt = 0

    while attempt < retries:
        attempt += 1
        try:
            # Get auth headers (token will be refreshed if needed)
            headers = {
                "Content-Type": "application/json",
                **auth_service.get_auth_header()
            }

            logger.debug(f"Sending request to Supply API. Attempt {attempt}/{retries}")

            # Send request
            response = requests.post(
                url,
                headers=headers,
                json=order_data,
                timeout=30  # 30 seconds timeout
            )

            # Try to parse response as JSON
            response_data = {}
            try:
                response_data = response.json()
            except json.JSONDecodeError:
                # If not JSON, store as text
                response_data = {"raw_response": response.text}

            # Add status code to response data for better tracking
            response_data["status_code"] = response.status_code

            # Handle response based on status code
            if response.status_code in (401, 403):
                # Authentication issues, force refresh token and retry
                logger.warning(f"Authentication failed. Status: {response.status_code}. Refreshing token...")
                auth_service.get_auth_token(force_refresh=True)

                # Store the auth error in response_data
                response_data["error"] = "Authentication failed, retrying with refreshed token"

                # Continue to next retry attempt
                continue

            elif response.status_code >= 400:
                # Other error responses
                logger.error(f"Supply API error. Status: {response.status_code}, Response: {response_data}")

                # If this was the last retry, return the error
                if attempt >= retries:
                    return False, {
                        "success": False,
                        "status_code": response.status_code,
                        "error": "Failed after maximum retries",
                        "response": response_data,
                        "last_attempt": attempt
                    }

                # Wait before retrying for non-auth errors
                time.sleep(RETRY_DELAY * attempt)  # Exponential backoff
                continue

            # Success response
            logger.info(f"Supply API response: {response_data}")
            return True, {
                "success": True,
                "status_code": response.status_code,
                "response": response_data,
                "attempt": attempt
            }

        except requests.exceptions.RequestException as e:
            # Network or request errors
            error_message = str(e)
            logger.error(f"Request error on attempt {attempt}/{retries}: {error_message}")

            # If this was the last attempt, return the error
            if attempt >= retries:
                return False, {
                    "success": False,
                    "error": error_message,
                    "error_type": type(e).__name__,
                    "last_attempt": attempt
                }

            # Wait before retrying
            time.sleep(RETRY_DELAY * attempt)  # Exponential backoff

    # Should not reach here, but just in case
    return False, {
        "success": False,
        "error": f"Failed to send data to Supply API after {retries} attempts",
        "last_attempt": attempt
    }


def process_pending_nomenclatures(max_count=50):
    """
    Process nomenclatures that haven't been sent to Supply yet or failed previously.

    Args:
        max_count: Maximum number of nomenclatures to process

    Returns:
        tuple: (success_count, fail_count)
    """
    pending_nomenclatures = Nomenclature.objects.filter(
        sent_successfully=False
    ).order_by('created_at')[:max_count]

    success_count = 0
    fail_count = 0

    for nomenclature in pending_nomenclatures:
        try:
            result = send_nomenclature_to_supply(nomenclature.id)
            if result:
                success_count += 1
            else:
                fail_count += 1
        except Exception as e:
            logger.exception(f"Error processing nomenclature {nomenclature.id}: {str(e)}")
            fail_count += 1

    return success_count, fail_count
