import json
import logging
import requests
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Union, Any

from django.db import transaction
from .supply_auth import SupplyAuthService, create_supply_auth_service

# Base URL for all API calls
BASE_URL = "https://apisupply.smartpos.uz"
BRANCHES_ENDPOINT = "/api/cabinet/v1/branches/lookup"
WAREHOUSES_ENDPOINT = "/api/cabinet/v1/warehouses/lookup"
ORDER_CREATE_ENDPOINT = "/api/cabinet/v1/orders/1c"

# Endpoint 5: Send stock-in from Supply to 1C
STOCK_IN_ENDPOINT = "/api/cabinet/v1/stock-in/1c"

# Endpoint 6: Get electronic invoices (factura) from Supply
FACTURA_INCOMING_ENDPOINT = "/api/integration/v1/1C/factura/incoming"
FACTURA_OUTGOING_ENDPOINT = "/api/integration/v1/1C/factura/outgoing"

# Endpoint 7: Get waybills from Supply
WAYBILL_INCOMING_ENDPOINT = "/api/integration/v1/1C/waybill/incoming"
WAYBILL_OUTGOING_ENDPOINT = "/api/integration/v1/1C/waybill/outgoing"

# Configure logging
logger = logging.getLogger(__name__)

# Retry settings for API calls
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds


def get_auth_service(phone: Optional[str] = None, password: Optional[str] = None) -> SupplyAuthService:
    """
    Get a configured auth service for Supply API.

    Args:
        phone (str, optional): Phone number for authentication. If not provided,
                              will use environment variables or settings.
        password (str, optional): Password for authentication. If not provided,
                                 will use environment variables or settings.

    Returns:
        SupplyAuthService: Configured auth service instance
    """
    # In a real implementation, you would get these from environment variables or Django settings
    # if not provided explicitly
    if not phone or not password:
        from django.conf import settings
        phone = getattr(settings, 'SUPPLY_API_PHONE', None)
        password = getattr(settings, 'SUPPLY_API_PASSWORD', None)

        if not phone or not password:
            raise ValueError("Supply API credentials not provided and not found in settings")

    return create_supply_auth_service(phone, password)


def get_branches(
        auth_service: Optional[SupplyAuthService] = None,
        branch_id: Optional[int] = None
) -> Tuple[bool, List[Dict[str, Any]]]:
    """
    Endpoint 1: Get list of branches from Supply API.

    Args:
        auth_service (SupplyAuthService, optional): Auth service instance.
                                                   If not provided, a new one will be created.
        branch_id (int, optional): Filter by specific branch ID

    Returns:
        Tuple[bool, List[Dict]]: (success, branches list)
    """
    # Get auth service if not provided
    if not auth_service:
        auth_service = get_auth_service()

    # Build URL
    url = f"{BASE_URL}{BRANCHES_ENDPOINT}"
    if branch_id:
        url += f"?branchId={branch_id}"

    # Set headers
    headers = {
        "Content-Type": "application/json",
        **auth_service.get_auth_header()
    }

    try:
        # Make the request
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        # Process response
        branches = response.json()
        return True, branches

    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching branches from Supply API: {str(e)}")
        return False, []


def get_warehouses(
        auth_service: Optional[SupplyAuthService] = None,
        warehouse_id: Optional[int] = None
) -> Tuple[bool, List[Dict[str, Any]]]:
    """
    Endpoint 2: Get list of warehouses from Supply API.

    Args:
        auth_service (SupplyAuthService, optional): Auth service instance.
                                                   If not provided, a new one will be created.
        warehouse_id (int, optional): Filter by specific warehouse ID

    Returns:
        Tuple[bool, List[Dict]]: (success, warehouses list)
    """
    # Get auth service if not provided
    if not auth_service:
        auth_service = get_auth_service()

    # Build URL
    url = f"{BASE_URL}{WAREHOUSES_ENDPOINT}"
    if warehouse_id:
        url += f"?warehouseId={warehouse_id}"

    # Set headers
    headers = {
        "Content-Type": "application/json",
        **auth_service.get_auth_header()
    }

    try:
        # Make the request
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        # Process response
        warehouses = response.json()
        return True, warehouses

    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching warehouses from Supply API: {str(e)}")
        return False, []


def create_order(
        order_data: Dict[str, Any],
        auth_service: Optional[SupplyAuthService] = None,
        max_retries: int = MAX_RETRIES
) -> Tuple[bool, Union[int, str]]:
    """
    Endpoint 3: Create an order in Supply system.

    Args:
        order_data (Dict): Order data according to the API specification
        auth_service (SupplyAuthService, optional): Auth service instance.
                                                   If not provided, a new one will be created.
        max_retries (int): Maximum number of retry attempts

    Returns:
        Tuple[bool, Union[int, str]]: (success, order_id or error_message)
    """
    # Get auth service if not provided
    if not auth_service:
        auth_service = get_auth_service()

    # Validate required fields
    required_fields = ['branchId', 'customerTin', 'contract', 'orderNumber', 'orderDate', 'products']

    missing_fields = [field for field in required_fields if field not in order_data]
    if missing_fields:
        error_msg = f"Missing required fields: {', '.join(missing_fields)}"
        logger.error(error_msg)
        return False, error_msg

    # Contract fields validation
    if 'contract' in order_data:
        if not isinstance(order_data['contract'], dict):
            error_msg = "Contract must be an object with 'number' and 'date' fields"
            logger.error(error_msg)
            return False, error_msg

        if 'number' not in order_data['contract'] or 'date' not in order_data['contract']:
            error_msg = "Contract object must contain 'number' and 'date' fields"
            logger.error(error_msg)
            return False, error_msg

    # Products validation
    if not order_data.get('products') or not isinstance(order_data['products'], list) or len(
            order_data['products']) == 0:
        error_msg = "Products list is required and must contain at least one product"
        logger.error(error_msg)
        return False, error_msg

    # Set defaults
    if 'createStockIn' not in order_data:
        order_data['createStockIn'] = True

    # Validate each product has required fields
    for idx, product in enumerate(order_data['products']):
        product_required_fields = ['catalogCode', 'barcode', 'baseSumma', 'name', 'packageCode', 'count', 'summa',
                                   'deliverySum']
        product_missing_fields = [field for field in product_required_fields if field not in product]

        if product_missing_fields:
            error_msg = f"Product at index {idx} is missing required fields: {', '.join(product_missing_fields)}"
            logger.error(error_msg)
            return False, error_msg

    # Endpoint URL
    url = f"{BASE_URL}{ORDER_CREATE_ENDPOINT}"

    # Set headers
    headers = {
        "Content-Type": "application/json",
        **auth_service.get_auth_header()
    }

    # Implement retry logic
    retry_count = 0
    while retry_count < max_retries:
        try:
            # Make the request
            response = requests.post(
                url,
                headers=headers,
                data=json.dumps(order_data)
            )

            # If successful, return the order ID
            if response.status_code == 200:
                try:
                    # The response should be just an ID
                    order_id = response.json()
                    logger.info(f"Successfully created order in Supply. Order ID: {order_id}")
                    return True, order_id
                except json.JSONDecodeError:
                    # If can't parse JSON but status is 200, consider it a success
                    logger.warning("Received 200 OK but couldn't parse JSON response")
                    return True, response.text

            # Handle various error responses
            if response.status_code == 401:
                # Token might be expired, refresh and retry
                logger.warning("Authentication error. Refreshing token and retrying...")
                auth_service.get_auth_token(force_refresh=True)
                retry_count += 1
                continue

            if response.status_code >= 400:
                # Try to get error details from response
                try:
                    error_details = response.json()
                    error_msg = f"API error: {response.status_code} - {json.dumps(error_details)}"
                except json.JSONDecodeError:
                    error_msg = f"API error: {response.status_code} - {response.text}"

                logger.error(error_msg)
                return False, error_msg

        except requests.exceptions.RequestException as e:
            # Network-related errors
            error_msg = f"Request error: {str(e)}"
            logger.error(error_msg)
            retry_count += 1

            if retry_count >= max_retries:
                return False, error_msg

    # If we get here, all retries failed
    return False, "Maximum retry attempts reached"


def send_stock_in_to_1c(
        stock_in_data: Dict[str, Any],
        auth_service: Optional[SupplyAuthService] = None,
        one_c_url: Optional[str] = None,
        one_c_username: Optional[str] = None,
        one_c_password: Optional[str] = None,
        max_retries: int = MAX_RETRIES
) -> Tuple[bool, Dict[str, Any]]:
    """
    Endpoint 5: Send stock-in (receipt) data from Supply to 1C.

    This function sends completed receipt data from Supply to 1C system.

    Args:
        stock_in_data (Dict): Stock-in data according to the API specification
        auth_service (SupplyAuthService, optional): Auth service instance for Supply.
                                                   If not provided, a new one will be created.
        one_c_url (str, optional): URL to 1C system API endpoint.
                                  If not provided, will use settings.
        one_c_username (str, optional): Username for 1C authentication.
                                       If not provided, will use settings.
        one_c_password (str, optional): Password for 1C authentication.
                                       If not provided, will use settings.
        max_retries (int): Maximum number of retry attempts

    Returns:
        Tuple[bool, Dict[str, Any]]: (success, response_data)
    """
    # Get auth service if not provided
    if not auth_service:
        auth_service = get_auth_service()

    # Get 1C credentials if not provided
    if not one_c_url or not one_c_username or not one_c_password:
        from django.conf import settings
        one_c_url = getattr(settings, 'ONE_C_RECEIPT_URL',
                            None) or "https://1c-server/hs/ReceiptGoodsServices/GetAdmission"
        one_c_username = getattr(settings, 'ONE_C_USERNAME', None)
        one_c_password = getattr(settings, 'ONE_C_PASSWORD', None)

        if not one_c_username or not one_c_password:
            error_msg = "1C credentials not provided and not found in settings"
            logger.error(error_msg)
            return False, {"error": error_msg}

    # Validate required fields
    required_fields = ['facturaId', 'facturaNo', 'facturaDate', 'status', 'statusName', 'id', 'products']

    missing_fields = [field for field in required_fields if field not in stock_in_data]
    if missing_fields:
        error_msg = f"Missing required fields: {', '.join(missing_fields)}"
        logger.error(error_msg)
        return False, {"error": error_msg}

    # Products validation
    if not stock_in_data.get('products') or not isinstance(stock_in_data['products'], list) or len(
            stock_in_data['products']) == 0:
        error_msg = "Products list is required and must contain at least one product"
        logger.error(error_msg)
        return False, {"error": error_msg}

    # Validate each product has required fields
    for idx, product in enumerate(stock_in_data['products']):
        product_required_fields = ['barcode', 'basePrice', 'hasMark', 'name', 'purchasePrice',
                                   'purchasePriceWithoutVat',
                                   'qty', 'sellingPrice', 'sellingPriceWithoutVat', 'stockProductId',
                                   'stockProductName',
                                   'unitId', 'vatBarCode', 'vatRate']

        product_missing_fields = [field for field in product_required_fields if field not in product]

        if product_missing_fields:
            error_msg = f"Product at index {idx} is missing required fields: {', '.join(product_missing_fields)}"
            logger.error(error_msg)
            return False, {"error": error_msg}

    # Supply API endpoint
    supply_url = f"{BASE_URL}{STOCK_IN_ENDPOINT}"

    # Set headers for Supply API
    supply_headers = {
        "Content-Type": "application/json",
        **auth_service.get_auth_header()
    }

    # Prepare for 1C API call
    from requests.auth import HTTPBasicAuth
    one_c_auth = HTTPBasicAuth(one_c_username, one_c_password)
    one_c_headers = {
        "Content-Type": "application/json"
    }

    # Implement retry logic
    retry_count = 0
    while retry_count < max_retries:
        try:
            # Make the request to Supply first
            supply_response = requests.post(
                supply_url,
                headers=supply_headers,
                data=json.dumps(stock_in_data)
            )

            supply_response.raise_for_status()

            # If successful, now send to 1C
            one_c_response = requests.post(
                one_c_url,
                auth=one_c_auth,
                headers=one_c_headers,
                data=json.dumps(stock_in_data)
            )

            # Check 1C response
            if one_c_response.status_code == 200:
                try:
                    response_data = one_c_response.json()
                    logger.info(f"Successfully sent stock-in data to 1C. Stock-in ID: {stock_in_data['id']}")
                    return True, response_data
                except json.JSONDecodeError:
                    # If can't parse JSON but status is 200, consider it a success
                    logger.warning("Received 200 OK from 1C but couldn't parse JSON response")
                    return True, {"raw_response": one_c_response.text}

            # Handle various error responses from 1C
            if one_c_response.status_code == 401:
                error_msg = "Authentication error with 1C system"
                logger.error(error_msg)
                return False, {"error": error_msg}

            if one_c_response.status_code >= 400:
                # Try to get error details from response
                try:
                    error_details = one_c_response.json()
                    error_msg = f"1C API error: {one_c_response.status_code} - {json.dumps(error_details)}"
                except json.JSONDecodeError:
                    error_msg = f"1C API error: {one_c_response.status_code} - {one_c_response.text}"

                logger.error(error_msg)
                return False, {"error": error_msg}

        except requests.exceptions.RequestException as e:
            # Network-related errors
            error_msg = f"Request error: {str(e)}"
            logger.error(error_msg)
            retry_count += 1

            if retry_count >= max_retries:
                return False, {"error": error_msg}

    # If we get here, all retries failed
    return False, {"error": "Maximum retry attempts reached"}


def get_facturas(
        tin: str,
        direction: str = "incoming",
        status: Optional[str] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        page: int = 0,
        size: int = 20,
        order_by: str = "id",
        sort_order: str = "desc",
        search: Optional[str] = None,
        auth_service: Optional[SupplyAuthService] = None
) -> Tuple[bool, Dict[str, Any]]:
    """
    Endpoint 6: Get electronic invoices (facturas) from Supply.

    Args:
        tin (str): TIN of the company
        direction (str): "incoming" or "outgoing"
        status (str, optional): Filter by status (DRAFT, SENT, QUEUED, etc.)
        from_date (str, optional): Start date in format YYYY-MM-DDTHH:MM:SS
        to_date (str, optional): End date in format YYYY-MM-DDTHH:MM:SS
        page (int): Page number (default: 0)
        size (int): Page size (default: 20)
        order_by (str): Field to order by (default: "id")
        sort_order (str): "asc" or "desc" (default: "desc")
        search (str, optional): Search term
        auth_service (SupplyAuthService, optional): Auth service instance.
                                                   If not provided, a new one will be created.

    Returns:
        Tuple[bool, Dict[str, Any]]: (success, facturas data)
    """
    # Get auth service if not provided
    if not auth_service:
        auth_service = get_auth_service()

    # Validate direction
    if direction not in ["incoming", "outgoing"]:
        error_msg = "Direction must be 'incoming' or 'outgoing'"
        logger.error(error_msg)
        return False, {"error": error_msg}

    # Validate required fields
    if not tin:
        error_msg = "TIN is required"
        logger.error(error_msg)
        return False, {"error": error_msg}

    # Build URL
    endpoint = FACTURA_INCOMING_ENDPOINT if direction == "incoming" else FACTURA_OUTGOING_ENDPOINT
    url = f"{BASE_URL}{endpoint}?tin={tin}&page={page}&size={size}"

    # Add optional parameters
    if from_date:
        url += f"&from={from_date}"

    if to_date:
        url += f"&to={to_date}"

    if status:
        url += f"&status={status}"

    if order_by:
        url += f"&orderBy={order_by}"

    if sort_order:
        url += f"&sortOrder={sort_order}"

    if search:
        url += f"&search={search}"

    # Set headers
    headers = {
        "Content-Type": "application/json",
        **auth_service.get_auth_header()
    }

    try:
        # Make the request
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        # Process response
        facturas_data = response.json()
        return True, facturas_data

    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching facturas from Supply API: {str(e)}")
        return False, {"error": str(e)}


def get_waybills(
        tin: str,
        direction: str = "incoming",
        status: Optional[str] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        page: int = 0,
        size: int = 20,
        search: Optional[str] = None,
        auth_service: Optional[SupplyAuthService] = None
) -> Tuple[bool, Dict[str, Any]]:
    """
    Endpoint 7: Get waybills (TTNs) from Supply.

    Args:
        tin (str): TIN of the company
        direction (str): "incoming" or "outgoing"
        status (str, optional): Filter by status (DRAFT, ConsignorSent, etc.)
        from_date (str, optional): Start date in format YYYY-MM-DDTHH:MM:SS
        to_date (str, optional): End date in format YYYY-MM-DDTHH:MM:SS
        page (int): Page number (default: 0)
        size (int): Page size (default: 20)
        search (str, optional): Search term
        auth_service (SupplyAuthService, optional): Auth service instance.
                                                   If not provided, a new one will be created.

    Returns:
        Tuple[bool, Dict[str, Any]]: (success, waybills data)
    """
    # Get auth service if not provided
    if not auth_service:
        auth_service = get_auth_service()

    # Validate direction
    if direction not in ["incoming", "outgoing"]:
        error_msg = "Direction must be 'incoming' or 'outgoing'"
        logger.error(error_msg)
        return False, {"error": error_msg}

    # Validate required fields
    if not tin:
        error_msg = "TIN is required"
        logger.error(error_msg)
        return False, {"error": error_msg}

    # Build URL
    endpoint = WAYBILL_INCOMING_ENDPOINT if direction == "incoming" else WAYBILL_OUTGOING_ENDPOINT
    url = f"{BASE_URL}{endpoint}?tin={tin}&page={page}&size={size}"

    # Add optional parameters
    if from_date:
        url += f"&from={from_date}"

    if to_date:
        url += f"&to={to_date}"

    if status:
        url += f"&status={status}"

    if search:
        url += f"&search={search}"

    # Set headers
    headers = {
        "Content-Type": "application/json",
        **auth_service.get_auth_header()
    }

    try:
        # Make the request
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        # Process response
        waybills_data = response.json()
        return True, waybills_data

    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching waybills from Supply API: {str(e)}")
        return False, {"error": str(e)}


def prepare_order_data_from_nomenclature(nomenclature):
    """
    Prepares order data for Supply API from a Nomenclature object.

    Args:
        nomenclature (Nomenclature): The nomenclature object to convert

    Returns:
        dict: Order data formatted for the Supply API
    """
    try:
        # Parse the contract information
        contract_data = json.loads(nomenclature.contract) if isinstance(nomenclature.contract,
                                                                        str) else nomenclature.contract

        # Get all products for this nomenclature
        products = nomenclature.products.all()

        # Format products for the order
        order_products = []
        for product in products:
            product_data = {
                "name": product.name,
                "code": product.code,
                "serial": product.code,
                "barcode": product.barcode,
                "count": product.count,
                "baseSumma": product.summa,
                "catalogCode": product.catalog_code,
                "packageCode": product.package_code,
                "profitRate": 0,
                "summa": product.summa,
                "deliverySum": product.delivery_sum
            }
            order_products.append(product_data)

        # Construct the order data
        order_data = {
            "branchId": "GLOBAL",
            "customerTin": nomenclature.customer_tin,
            "orderDate": nomenclature.date.isoformat() if nomenclature.date else None,
            "contract": contract_data,
            "orderNumber": nomenclature.external_id,
            "products": order_products
        }

        return order_data

    except Exception as e:
        logger.error(f"Error preparing order data from nomenclature {nomenclature.id}: {str(e)}")
        raise Exception(f"Failed to prepare order data: {str(e)}")


# New constants for endpoints 8 and 9
RECEIPT_ENDPOINT = "/api/integration/v1/1C/receipt"
PRODUCT_QTY_ENDPOINT = "/api/integration/v1/1C/product-qty"


def get_receipts(
        tin: str,
        from_date: str,
        to_date: str,
        status: str = "PAID",
        page: int = 0,
        size: int = 20,
        search: Optional[str] = None,
        auth_service: Optional[SupplyAuthService] = None
) -> Tuple[bool, Dict[str, Any]]:
    """
    Endpoint 8: Get receipts from Supply.

    Args:
        tin (str): TIN of the company
        from_date (str): Start date in format YYYY-MM-DDTHH:MM:SS
        to_date (str): End date in format YYYY-MM-DDTHH:MM:SS
        status (str): Filter by status (DRAFT, PAID, RETURNED)
        page (int): Page number (default: 0)
        size (int): Page size (default: 20)
        search (str, optional): Search term
        auth_service (SupplyAuthService, optional): Auth service instance.
                                                   If not provided, a new one will be created.

    Returns:
        Tuple[bool, Dict[str, Any]]: (success, receipts data)
    """
    # Get auth service if not provided
    if not auth_service:
        auth_service = get_auth_service()

    # Validate required fields
    if not tin:
        error_msg = "TIN is required"
        logger.error(error_msg)
        return False, {"error": error_msg}

    if not from_date or not to_date:
        error_msg = "Both from_date and to_date are required"
        logger.error(error_msg)
        return False, {"error": error_msg}

    # Validate status
    valid_statuses = ["DRAFT", "PAID", "RETURNED"]
    if status and status not in valid_statuses:
        error_msg = f"Status must be one of: {', '.join(valid_statuses)}"
        logger.error(error_msg)
        return False, {"error": error_msg}

    # Build URL
    url = f"{BASE_URL}{RECEIPT_ENDPOINT}?tin={tin}&page={page}&size={size}"

    # Add required parameters
    url += f"&from={from_date}&to={to_date}&status={status}"

    # Add optional search parameter
    if search:
        url += f"&search={search}"

    # Set headers
    headers = {
        "Content-Type": "application/json",
        **auth_service.get_auth_header()
    }

    try:
        # Make the request
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        # Process response
        receipts_data = response.json()
        return True, receipts_data

    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching receipts from Supply API: {str(e)}")
        return False, {"error": str(e)}


def get_product_qty(
        branch_id: int,
        warehouse_id: int,
        auth_service: Optional[SupplyAuthService] = None
) -> Tuple[bool, Dict[str, Any]]:
    """
    Endpoint 9: Get product quantities in warehouse.

    Args:
        branch_id (int): ID of the branch
        warehouse_id (int): ID of the warehouse
        auth_service (SupplyAuthService, optional): Auth service instance.
                                                   If not provided, a new one will be created.

    Returns:
        Tuple[bool, Dict[str, Any]]: (success, product quantities data)
    """
    # Get auth service if not provided
    if not auth_service:
        auth_service = get_auth_service()

    # Validate required fields
    if not branch_id:
        error_msg = "branch_id is required"
        logger.error(error_msg)
        return False, {"error": error_msg}

    if not warehouse_id:
        error_msg = "warehouse_id is required"
        logger.error(error_msg)
        return False, {"error": error_msg}

    # Build URL
    url = f"{BASE_URL}{PRODUCT_QTY_ENDPOINT}?branchId={branch_id}&warehouseId={warehouse_id}"

    # Set headers
    headers = {
        "Content-Type": "application/json",
        **auth_service.get_auth_header()
    }

    try:
        # Make the request
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        # Process response
        product_qty_data = response.json()
        return True, product_qty_data

    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching product quantities from Supply API: {str(e)}")
        return False, {"error": str(e)}
