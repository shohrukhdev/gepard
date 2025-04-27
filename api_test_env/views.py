import logging

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated  # Import permission class
from rest_framework_simplejwt.authentication import JWTAuthentication

logger = logging.getLogger(__name__)

# --- In-memory storage for simulation (replace with actual logic if needed later) ---
# Simple way to simulate duplicate check for nomenclature
SEEN_NOMENCLATURE_IDS = set()


class NomenclatureUpdateView(APIView):
    """
    API endpoint to receive nomenclature list updates for integration testing.
    Protected by JWT Authentication.
    """
    permission_classes = (IsAuthenticated,)  # Enforce JWT authentication
    authentication_classes = (JWTAuthentication,)

    def post(self, request, *args, **kwargs):
        """
        Handles POST requests for /nomenclature/update.
        """
        data = request.data
        logger.info(f"Received nomenclature update request from user: {request.user.username}")
        logger.debug(f"Nomenclature Payload: {data}")

        # --- Basic Validation ---
        client_id = data.get('client_id')
        nomenclature = data.get('nomenclature')
        nomenclature_id = nomenclature.get('id') if isinstance(nomenclature, dict) else None
        goods = nomenclature.get('goods') if isinstance(nomenclature, dict) else None

        if not all([client_id, nomenclature, nomenclature_id, isinstance(goods, list)]):
            logger.warning("Nomenclature update: Invalid payload structure.")
            return Response(
                {"success": False,
                 "error": "Invalid payload structure. Required fields: client_id, nomenclature (with id and goods list)."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # --- Simulate Duplicate Check ---
        if nomenclature_id in SEEN_NOMENCLATURE_IDS:
            logger.info(f"Nomenclature update: Duplicate nomenclature_id received: {nomenclature_id}")
            # Decide how to handle duplicates - here we accept it but log it.
            # You could return a specific response or error if needed.
            pass  # Allow processing for testing purposes
        SEEN_NOMENCLATURE_IDS.add(nomenclature_id)

        # --- Simulate Processing (No DB interaction needed for test) ---
        logger.info(f"Processing nomenclature update for client_id: {client_id}, nomenclature_id: {nomenclature_id}")
        # In a real scenario, you would process/save the goods list here.

        # --- Success Response ---
        response_data = {
            "success": True,
            "client_id": client_id,
            "nomenclature_id": nomenclature_id
        }
        return Response(response_data, status=status.HTTP_200_OK)


class CounterpartyUpdateView(APIView):
    """
    API endpoint to receive counterparty list updates for integration testing.
    Protected by JWT Authentication.
    """
    permission_classes = (IsAuthenticated,)  # Enforce JWT authentication
    authentication_classes = (JWTAuthentication,)

    def post(self, request, *args, **kwargs):
        """
        Handles POST requests for /contr_agents/update.
        """
        data = request.data
        logger.info(f"Received counterparty update request from user: {request.user.username}")
        logger.debug(f"Counterparty Payload: {data}")

        # --- Basic Validation ---
        timestamp = data.get('timestamp')
        contr_agents = data.get('contr_agents')

        if not timestamp or not isinstance(contr_agents, list):
            logger.warning("Counterparty update: Invalid payload structure.")
            return Response(
                {"success": False,
                 "error": "Invalid payload structure. Required fields: timestamp, contr_agents (list)."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not contr_agents:  # Check if the list is empty
            logger.warning("Counterparty update: Received empty contr_agents list.")
            # Decide if empty list is acceptable or an error
            # return Response({"success": False, "error": "contr_agents list cannot be empty."}, status=status.HTTP_400_BAD_REQUEST)

        # Validate structure within the list (optional but good)
        for agent in contr_agents:
            if not isinstance(agent, dict) or 'name' not in agent or 'tin' not in agent:
                logger.warning(f"Counterparty update: Invalid agent structure found: {agent}")
                return Response(
                    {"success": False,
                     "error": "Invalid structure in contr_agents list. Each agent must have 'name' and 'tin'."},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # --- Simulate Processing ---
        logger.info(f"Processing {len(contr_agents)} counterparty updates received at {timestamp}")
        # In a real scenario, you would iterate and update/create counterparties.

        # --- Success Response ---
        response_data = {
            "success": True
        }
        return Response(response_data, status=status.HTTP_200_OK)


class CounterpartyBalanceView(APIView):
    """
    API endpoint to receive counterparty balance updates for integration testing.
    Protected by JWT Authentication.
    """
    permission_classes = (IsAuthenticated,)  # Enforce JWT authentication
    authentication_classes = (JWTAuthentication,)

    def post(self, request, *args, **kwargs):
        """
        Handles POST requests for /contr_agents/balances.
        """
        data = request.data
        logger.info(f"Received counterparty balance update request from user: {request.user.username}")
        logger.debug(f"Counterparty Balance Payload: {data}")

        # --- Basic Validation ---
        timestamp = data.get('timestamp')
        contr_agents = data.get('contr_agents')

        if not timestamp or not isinstance(contr_agents, list):
            logger.warning("Counterparty balance update: Invalid payload structure.")
            return Response(
                {"success": False,
                 "error": "Invalid payload structure. Required fields: timestamp, contr_agents (list)."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not contr_agents:  # Check if the list is empty
            logger.warning("Counterparty balance update: Received empty contr_agents list.")
            # Decide if empty list is acceptable or an error
            # return Response({"success": False, "error": "contr_agents list cannot be empty."}, status=status.HTTP_400_BAD_REQUEST)

        # Validate structure within the list (optional but good)
        for agent in contr_agents:
            if not isinstance(agent, dict) or not all(k in agent for k in ['name', 'tin', 'prepayment', 'debt']):
                logger.warning(f"Counterparty balance update: Invalid agent structure found: {agent}")
                return Response(
                    {"success": False,
                     "error": "Invalid structure in contr_agents list. Each agent must have 'name', 'tin', 'prepayment', and 'debt'."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            # Optional: Validate types for prepayment/debt
            if not isinstance(agent.get('prepayment'), (int, float)) or not isinstance(agent.get('debt'), (int, float)):
                logger.warning(
                    f"Counterparty balance update: Invalid numeric types for prepayment/debt in agent: {agent}")
                return Response(
                    {"success": False,
                     "error": "Invalid numeric type for 'prepayment' or 'debt' in contr_agents list."},
                    status=status.HTTP_400_BAD_REQUEST
                )
                # --- Simulate Processing ---
        logger.info(f"Processing {len(contr_agents)} counterparty balance updates received at {timestamp}")
        # In a real scenario, you would iterate and update counterparty balances based on TIN.

        # --- Success Response ---
        response_data = {
            "success": True
        }
        return Response(response_data, status=status.HTTP_200_OK)
