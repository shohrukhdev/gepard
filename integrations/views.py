import decimal
from decimal import Decimal

from django.db import transaction

from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated  # Import permission class
from rest_framework_simplejwt.authentication import JWTAuthentication
import logging
from datetime import datetime
from .models import Nomenclature, Product, ContrAgent, ContrAgentBalance
import json

from .utils.supply_send_request import send_nomenclature_to_supply

logger = logging.getLogger(__name__)

# --- In-memory storage for simulation (replace with actual logic if needed later) ---
# Simple way to simulate duplicate check for nomenclature
SEEN_NOMENCLATURE_IDS = set()


@method_decorator(csrf_exempt, name='dispatch')
class NomenclatureUpdateView(APIView):
    """
    API endpoint to receive and process nomenclature data from 1C service.
    """
    permission_classes = (IsAuthenticated,)  # Enforce JWT authentication
    authentication_classes = (JWTAuthentication,)

    def post(self, request, *args, **kwargs):
        """
        Handles POST requests from 1C service.
        Processes and stores nomenclature data with products.
        """

        # Get JSON data from request
        try:
            if isinstance(request.data, dict):
                data = request.data
            else:
                data = json.loads(request.body)
        except json.JSONDecodeError:
            logger.error("Invalid JSON in request body")
            return Response(
                {"success": False, "error": "Invalid JSON format"},
                status=status.HTTP_400_BAD_REQUEST
            )

        logger.info("Received nomenclature update request")
        logger.debug(f"Nomenclature Payload: {data}")

        # Extract data from the request
        client_id = data.get('client_id')
        client_name = data.get('client_name')
        customer_tin = data.get('customer_tin')
        contract = data.get('contract')
        date_str = data.get('date')

        nomenclature_data = data.get('nomenclature')

        # Validate required fields
        if not all([client_id, nomenclature_data]):
            logger.warning("Nomenclature update: Invalid payload structure")
            return Response(
                {"success": False, "error": "Missing required fields: client_id or nomenclature"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Extract nomenclature id and products
        nomenclature_id = nomenclature_data.get('id')
        products_data = nomenclature_data.get('products', [])

        if not nomenclature_id or not isinstance(products_data, list):
            logger.warning("Nomenclature update: Invalid nomenclature structure")
            return Response(
                {"success": False, "error": "Invalid nomenclature structure. Required: id and products list"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Parse date if provided
        date_obj = None
        if date_str:
            try:
                date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                logger.warning(f"Invalid date format: {date_str}")
                # Continue processing but with None date

        try:
            # Start DB transaction
            with transaction.atomic():
                # Create or update Nomenclature
                nomenclature, created = Nomenclature.objects.update_or_create(
                    external_id=nomenclature_id,
                    defaults={
                        'client_id': client_id,
                        'client_name': client_name,
                        'customer_tin': customer_tin,
                        'contract': contract if isinstance(contract, str) else json.dumps(contract),
                        'date': date_obj,
                    }
                )

                # Log creation or update
                if created:
                    logger.info(f"Created new Nomenclature: {nomenclature_id}")
                else:
                    logger.info(f"Updated existing Nomenclature: {nomenclature_id}")

                # Delete existing products if updating
                if not created:
                    Product.objects.filter(nomenclature=nomenclature).delete()

                # Create products
                products_to_create = []
                for product_data in products_data:
                    products_to_create.append(Product(
                        nomenclature=nomenclature,
                        code=product_data.get('code'),
                        catalog_code=product_data.get('catalog_code'),
                        barcode=product_data.get('barcode'),
                        package_code=product_data.get('package_code'),
                        code1c=product_data.get('code1C'),  # Note the casing difference
                        name=product_data.get('name'),
                    ))

                # Bulk create products for efficiency
                if products_to_create:
                    Product.objects.bulk_create(products_to_create)
                    logger.info(f"Created {len(products_to_create)} products for nomenclature {nomenclature_id}")

                # Try to send to Supply service
                try:
                    # Send asynchronously or in background task for better performance
                    # For now, we'll do it synchronously
                    send_result = send_nomenclature_to_supply(nomenclature.id)
                    if send_result:
                        logger.info(f"Successfully sent nomenclature {nomenclature_id} to Supply")
                    else:
                        logger.warning(f"Failed to send nomenclature {nomenclature_id} to Supply. Will retry later.")
                except Exception as e:
                    logger.error(f"Error sending nomenclature to Supply: {str(e)}")
                    # Continue processing - don't fail the request if Supply integration fails

                # Prepare response
                response_data = {
                    "success": True,
                    "nomenclature_id": nomenclature_id,
                    "client_id": client_id,
                    "products_count": len(products_to_create)
                }

                return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error processing nomenclature update: {str(e)}")
            return Response(
                {"success": False, "error": "Server error while processing request"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ContrAgentUpdateView(APIView):
    """
    API endpoint to receive and process contracting agents data from 1C service.
    Protected by JWT Authentication.
    """
    permission_classes = (IsAuthenticated,)
    authentication_classes = (JWTAuthentication,)

    def post(self, request, *args, **kwargs):
        """
        Handles POST requests for contracting agents update.
        Request format:
        {
            "timestamp": "2025-04-01T12:00:00Z",
            "contr_agents": [
                {
                    "name": "Any Name",
                    "tin": "1234567890"
                }
            ]
        }
        """
        data = request.data
        logger.info(f"Received contracting agents update request from user: {request.user.username}")
        logger.debug(f"ContrAgent Payload: {data}")

        # Extract and validate data
        timestamp = data.get('timestamp')
        contr_agents = data.get('contr_agents')

        # Basic validation
        if not timestamp or not isinstance(contr_agents, list):
            logger.warning("ContrAgent update: Invalid payload structure")
            return Response(
                {"success": False,
                 "error": "Invalid payload structure. Required fields: timestamp, contr_agents (list)"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Parse timestamp
        try:
            timestamp_obj = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        except ValueError:
            logger.warning(f"Invalid timestamp format: {timestamp}")
            return Response(
                {"success": False, "error": "Invalid timestamp format. Use ISO format (YYYY-MM-DDTHH:MM:SSZ)"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Process contracting agents
        try:
            with transaction.atomic():
                agents_created = 0
                agents_updated = 0

                for agent_data in contr_agents:
                    # Validate required fields
                    name = agent_data.get('name')
                    tin = agent_data.get('tin')

                    if not name or not tin:
                        logger.warning(f"ContrAgent update: Missing required fields in agent data: {agent_data}")
                        continue

                    # Create or update agent
                    agent, created = ContrAgent.objects.update_or_create(
                        tin=tin,
                        defaults={
                            'name': name,
                            # cr_on will be updated automatically due to auto_now
                        }
                    )

                    if created:
                        agents_created += 1
                        logger.info(f"Created new ContrAgent: {name} (TIN: {tin})")
                    else:
                        agents_updated += 1
                        logger.info(f"Updated existing ContrAgent: {name} (TIN: {tin})")

                # Prepare response
                response_data = {
                    "success": True,
                    "timestamp": timestamp,
                }

                return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error processing contracting agents update: {str(e)}")
            return Response(
                {"success": False, "error": f"Server error while processing request: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ContrAgentBalanceView(APIView):
    """
    API endpoint to receive and process contracting agents balance data from 1C service.
    Protected by JWT Authentication.
    """
    permission_classes = (IsAuthenticated,)
    authentication_classes = (JWTAuthentication,)

    def post(self, request, *args, **kwargs):
        """
        Handles POST requests for contracting agents balance update.
        Request format:
        {
            "timestamp": "2025-04-01T12:00:00Z",
            "contr_agents": [
                {
                    "name": "Any Name",
                    "tin": "1234567890",
                    "prepayment": 500.50,
                    "debt": 1200.75
                }
            ]
        }
        """
        data = request.data
        logger.info(f"Received contracting agents balance update request from user: {request.user.username}")
        logger.debug(f"ContrAgent Balance Payload: {data}")

        # Extract and validate data
        timestamp = data.get('timestamp')
        contr_agents = data.get('contr_agents')

        # Basic validation
        if not timestamp or not isinstance(contr_agents, list):
            logger.warning("ContrAgent balance update: Invalid payload structure")
            return Response(
                {"success": False,
                 "error": "Invalid payload structure. Required fields: timestamp, contr_agents (list)"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Parse timestamp
        try:
            timestamp_obj = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        except ValueError:
            logger.warning(f"Invalid timestamp format: {timestamp}")
            return Response(
                {"success": False, "error": "Invalid timestamp format. Use ISO format (YYYY-MM-DDTHH:MM:SSZ)"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Process contracting agents balances
        try:
            with transaction.atomic():
                agents_created = 0
                balances_created = 0
                balances_updated = 0

                for agent_data in contr_agents:
                    # Validate required fields
                    name = agent_data.get('name')
                    tin = agent_data.get('tin')
                    prepayment = agent_data.get('prepayment')
                    debt = agent_data.get('debt')

                    # Validate all required fields exist
                    if not all([name, tin, prepayment is not None, debt is not None]):
                        logger.warning(f"ContrAgent balance update: Missing required fields in agent data: {agent_data}")
                        continue

                    # Validate numeric fields
                    try:
                        prepayment = Decimal(str(prepayment))
                        debt = Decimal(str(debt))
                    except (ValueError, TypeError, decimal.InvalidOperation):
                        logger.warning(f"ContrAgent balance update: Invalid numeric value in agent data: {agent_data}")
                        continue

                    # First ensure the ContrAgent exists (create if not)
                    agent, agent_created = ContrAgent.objects.update_or_create(
                        tin=tin,
                        defaults={
                            'name': name,
                        }
                    )

                    if agent_created:
                        agents_created += 1
                        logger.info(f"Created new ContrAgent: {name} (TIN: {tin})")

                    # Now update or create the balance
                    balance, balance_created = ContrAgentBalance.objects.update_or_create(
                        contr_agent=agent,
                        defaults={
                            'prepayment': prepayment,
                            'debt': debt,
                            'last_sync_timestamp': timestamp_obj,
                        }
                    )

                    if balance_created:
                        balances_created += 1
                        logger.info(f"Created new balance for ContrAgent: {name} (TIN: {tin})")
                    else:
                        balances_updated += 1
                        logger.info(f"Updated balance for ContrAgent: {name} (TIN: {tin})")

                # Prepare response
                response_data = {
                    "success": True,
                    "timestamp": timestamp
                }

                return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error processing contracting agents balance update: {str(e)}")
            return Response(
                {"success": False, "error": f"Server error while processing request: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
