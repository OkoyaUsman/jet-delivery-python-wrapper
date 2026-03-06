"""
Main client class for interacting with the Jet Delivery API.
"""

import requests
from typing import Dict, Optional, Any
from .exceptions import (
    JetDeliveryAPIError,
    JetDeliveryAuthenticationError,
    JetDeliveryNotFoundError,
    JetDeliveryValidationError,
)

class JetDeliveryClient:
    """
    Client for interacting with the Jet Delivery API.

    Example:
        >>> client = JetDeliveryClient(api_key="your-api-key")
        >>> shipment = client.schedule_shipment(...)
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://www.jetdelivery.com/api/v1",
        timeout: int = 30,
    ):
        """
        Initialize the Jet Delivery API client.

        Args:
            api_key: Your Jet Delivery API key (optional for some endpoints)
            base_url: Base URL for the API (default: https://www.jetdelivery.com/api/v1)
            timeout: Request timeout in seconds (default: 30)
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
        )

    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
        json: Optional[Dict] = None,
        files: Optional[Dict] = None,
        include_api_key: bool = True,
    ) -> Dict[str, Any]:
        """
        Make an HTTP request to the API.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint (relative to base_url)
            params: URL parameters
            data: Form data
            json: JSON data
            files: Files to upload (for multipart/form-data)
            include_api_key: Whether to include API key in request (default: True)

        Returns:
            Response JSON as a dictionary

        Raises:
            JetDeliveryAPIError: For API errors
            JetDeliveryAuthenticationError: For authentication errors
            JetDeliveryNotFoundError: For 404 errors
            JetDeliveryValidationError: For validation errors
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        # Add API key to params if provided and requested
        request_params = params.copy() if params else {}
        if include_api_key and self.api_key:
            request_params["key"] = self.api_key

        try:
            response = self.session.request(
                method=method,
                url=url,
                params=request_params,
                data=data,
                json=json,
                files=files,
                timeout=self.timeout,
            )
            return self._handle_response(response)
        except requests.exceptions.RequestException as e:
            raise JetDeliveryAPIError(f"Request failed: {str(e)}")

    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """
        Handle API response and raise appropriate exceptions.

        Args:
            response: Requests response object

        Returns:
            Response JSON as a dictionary

        Raises:
            JetDeliveryAPIError: For API errors
            JetDeliveryAuthenticationError: For authentication errors
            JetDeliveryNotFoundError: For 404 errors
            JetDeliveryValidationError: For validation errors
        """
        status_code = response.status_code

        # Try to parse JSON response
        try:
            response_data = response.json()
        except ValueError:
            response_data = {"message": response.text}

        # Check for error field in response (Jet Delivery API format)
        if isinstance(response_data, dict) and response_data.get("error"):
            error_msg = response_data.get("error")
            if status_code == 401:
                raise JetDeliveryAuthenticationError(
                    error_msg or "Authentication failed",
                    status_code=status_code,
                    response=response_data,
                )
            elif status_code == 404:
                raise JetDeliveryNotFoundError(
                    error_msg or "Resource not found",
                    status_code=status_code,
                    response=response_data,
                )
            else:
                raise JetDeliveryAPIError(
                    error_msg or f"API error: {status_code}",
                    status_code=status_code,
                    response=response_data,
                )

        # Handle different status codes
        if status_code == 200 or status_code == 201:
            return response_data
        elif status_code == 401:
            raise JetDeliveryAuthenticationError(
                response_data.get("message", "Authentication failed"),
                status_code=status_code,
                response=response_data,
            )
        elif status_code == 404:
            raise JetDeliveryNotFoundError(
                response_data.get("message", "Resource not found"),
                status_code=status_code,
                response=response_data,
            )
        elif status_code == 400 or status_code == 422:
            raise JetDeliveryValidationError(
                response_data.get("message", "Validation error"),
                status_code=status_code,
                response=response_data,
            )
        else:
            raise JetDeliveryAPIError(
                response_data.get("message", f"API error: {status_code}"),
                status_code=status_code,
                response=response_data,
            )

    def track_shipment(
        self,
        tracking_id: str,
        ref: Optional[str] = None,
        use_api_key: bool = True,
    ) -> Dict[str, Any]:
        """
        Track a shipment with real-time location and status.
        
        You can use our tracking endpoint to get the real-time status of your shipment.
        The results include the GPS location of the driver (when available), reference,
        signature, event history, and more.
        
        No API key is required to use this endpoint. For security reasons, unless you
        provide an API key we will display only the weighted center of each zip-code
        rather than the exact origin and destination locations.

        Args:
            tracking_id: Required. This can be the 6-8 digit tracking number assigned to your
                shipment at the time of booking, or it can be the unique billing reference
                provided to us. Up to 23 characters.
            ref: Optional. Sending "link-ref" attempts to match the tracking_id to a billing
                 reference in our system rather than our tracking number.
            use_api_key: Whether to include API key in request (default: True).
                        Set to False if you don't have an API key or want zip-code level
                        location data only.

        Returns:
            Tracking information including GPS location and status.
            Response structure: {"error": null, "data": {...}}
        """
        params = {"id": tracking_id}
        if ref:
            params["ref"] = ref

        response = self._request(
            "GET",
            "/utilities/track/",
            params=params,
            include_api_key=use_api_key and self.api_key is not None,
        )

        # Return the data portion if present, otherwise return full response
        if isinstance(response, dict) and "data" in response:
            return response["data"]
        return response

    def get_quote(
        self,
        origin: str,
        destination: str,
        pieces: Optional[int] = None,
        weight: Optional[float] = None,
        pickup_req_date: Optional[str] = None,
        pickup_req_time: Optional[str] = None,
        deliver_req_date: Optional[str] = None,
        deliver_req_time: Optional[str] = None,
        use_api_key: bool = True,
    ) -> Dict[str, Any]:
        """
        Get rates and estimate transit times for a shipment.
        
        You can use our quote endpoint to check rates and estimate transit times.
        Depending on the zip-codes you enter, different services may or may not be available.
        
        No API key is required to use this endpoint. However, if you don't send an API key
        in your request, you will not get any special pricing that applies to your specific account.

        Args:
            origin: Required. The 5-digit zip code the shipment is originating from.
            destination: Required. The 5-digit zip code the shipment is delivering to.
            pieces: Optional. Total number of pieces.
            weight: Optional. Total weight of shipment.
            pickup_req_date: Optional. Date shipment will be ready for pickup.
                           Use MM/DD/YYYY format. If left blank, defaults to current day.
                           Note: Weekends and holidays may have an impact on pricing.
            pickup_req_time: Optional. Time shipment will be ready for pickup.
                            Use 24-hour format HH:MM. If left blank, defaults to current time.
            deliver_req_date: Optional. Date shipment must be delivered on.
                             Use MM/DD/YYYY format. If left blank, defaults to ASAP.
            deliver_req_time: Optional. Time shipment should be delivered by.
                             Use 24-hour format HH:MM. If left blank, defaults to ASAP.
            use_api_key: Whether to include API key in request (default: True).
                        Set to False if you don't have an API key or don't need special pricing.

        Returns:
            Quote information including available services, rates, and transit times.
            Response structure: {"error": null, "data": {...}}
        """
        params = {
            "origin": origin,
            "destination": destination,
        }

        if pieces is not None:
            params["pieces"] = pieces
        if weight is not None:
            params["weight"] = weight
        if pickup_req_date:
            params["pickup_req_date"] = pickup_req_date
        if pickup_req_time:
            params["pickup_req_time"] = pickup_req_time
        if deliver_req_date:
            params["deliver_req_date"] = deliver_req_date
        if deliver_req_time:
            params["deliver_req_time"] = deliver_req_time

        response = self._request(
            "GET",
            "/utilities/quote/",
            params=params,
            include_api_key=use_api_key and self.api_key is not None,
        )

        # Return the data portion if present, otherwise return full response
        if isinstance(response, dict) and "data" in response:
            return response["data"]
        return response

    def schedule_shipment(
        self,
        # Contact information (required)
        Contact: str,
        # Pickup information (required)
        PickupName: str,
        PickupAddress: str,
        PickupCity: str,
        PickupState: str,
        PickupZip: int,
        # Delivery information (required)
        DeliverName: str,
        DeliverAddress: str,
        DeliverCity: str,
        DeliverState: str,
        DeliverZip: int,
        # Shipment details (required)
        Pieces: int,
        Weight: int,
        ServiceType: str,
        VehicleType: str,
        # Optional contact information
        Email: Optional[str] = None,
        Phone: Optional[int] = None,
        Extn: Optional[int] = None,
        NotifyOption: Optional[str] = None,
        # Optional references
        BillingReference: Optional[str] = None,
        Bol: Optional[str] = None,
        Po: Optional[str] = None,
        jsonstrn: Optional[str] = None,
        # Optional pickup information
        PickupContact: Optional[str] = None,
        PickupPhone: Optional[int] = None,
        PickupExtn: Optional[int] = None,
        PickupSpecinst: Optional[str] = None,
        # Optional delivery information
        DeliverContact: Optional[str] = None,
        DeliverPhone: Optional[int] = None,
        DeliverExtn: Optional[int] = None,
        DeliverSpecinst: Optional[str] = None,
        # Optional timing information
        Pickupdate: Optional[str] = None,
        PickuptimeFrom: Optional[str] = None,
        PickuptimeTo: Optional[str] = None,
        Deliverdate: Optional[str] = None,
        DelivertimeFrom: Optional[str] = None,
        DelivertimeTo: Optional[str] = None,
        # Optional service options
        LiftgateReq: Optional[str] = None,
        BolReq: Optional[str] = None,
        SignatureReq: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Schedule a new shipment.
        
        You can use our order endpoint to book new shipments. An API key is required
        to use this endpoint.

        Args:
            Contact: Required. Name of the person to contact for additional information
                    about the shipment (max 16 characters).
            PickupName: Required. Name of the pickup location (max 35 characters).
            PickupAddress: Required. Address of the pickup location (max 30 characters).
            PickupCity: Required. City where pickup is located (max 16 characters).
            PickupState: Required. State's two letter code (max 2 characters).
            PickupZip: Required. Five digit zip code for pickup city.
            DeliverName: Required. Name of the delivery location (max 35 characters).
            DeliverAddress: Required. Address of the delivery location (max 30 characters).
            DeliverCity: Required. City where delivery is located (max 16 characters).
            DeliverState: Required. State's two letter code (max 2 characters).
            DeliverZip: Required. Five digit zip code for delivery city.
            Pieces: Required. Number of pieces expected at pickup (bulk pieces, not
                   pieces per container) (max 4 digits).
            Weight: Required. Weight in pounds (max 5 digits).
            ServiceType: Required. Type of service requested (max 255 characters).
            VehicleType: Required. Type of vehicle requested (max 3 characters).
            
            Email: Optional. Email address for contact person (max 50 characters).
            Phone: Optional. Phone number of contact person (10 digits).
            Extn: Optional. Extension number of contact person (4 digits).
            NotifyOption: Optional. Set to "Y" to receive email upon delivery.
            BillingReference: Optional. Reference that will appear on invoice (max 23 characters).
                            Note: Required if account administrator has instructed Jet Delivery
                            to require references.
            Bol: Optional. Bill of lading number (max 15 characters).
            Po: Optional. Purchase order (max 20 characters).
            jsonstrn: Optional. Unique key that will be returned in response.
            
            PickupContact: Optional. Name of contact person at pickup location (max 16 characters).
            PickupPhone: Optional. Phone number for contact at pickup location (10 digits).
            PickupExtn: Optional. Phone extension at pickup location (4 digits).
            PickupSpecinst: Optional. Special instructions for driver at pickup (max 71 characters).
            
            DeliverContact: Optional. Name of contact person at delivery location (max 16 characters).
            DeliverPhone: Optional. Phone number for contact at delivery location (10 digits).
            DeliverExtn: Optional. Phone extension at delivery location (4 digits).
            DeliverSpecinst: Optional. Special instructions for driver at delivery (max 71 characters).
            
            Pickupdate: Optional. Date shipment is ready for pickup (format: MM/DD/YYYY).
            PickuptimeFrom: Optional. Time shipment is ready (format: HH:MM). If blank, assumes now.
            PickuptimeTo: Optional. Time shipment must be picked up by (format: HH:MM). If blank, assumes ASAP.
            Deliverdate: Optional. Earliest date shipment can be delivered (format: MM/DD/YYYY).
                        Usually same as Pickupdate.
            DelivertimeFrom: Optional. Earliest time shipment can be delivered (format: HH:MM).
                            If blank, assumes ASAP.
            DelivertimeTo: Optional. Latest time shipment can be delivered (format: HH:MM).
                          If blank, assumes ASAP.
            
            LiftgateReq: Optional. Set to "Y" to request vehicle with liftgate.
            BolReq: Optional. Set to "Y" to notify driver that BOL is required.
            SignatureReq: Optional. Set to "Y" to notify driver that signature is required.

        Returns:
            Shipment details including tracking number, billing reference, and delivery estimates.
            Response structure: {"error": null, "data": {...}}
            
        Raises:
            JetDeliveryAPIError: If API key is not provided (required for this endpoint)
        """
        if not self.api_key:
            raise JetDeliveryAPIError(
                "API key is required to schedule shipments. "
                "Please provide an API key when initializing the client."
            )

        # Build the payload with required fields
        payload = {
            "key": self.api_key,
            "Contact": Contact,
            "PickupName": PickupName,
            "PickupAddress": PickupAddress,
            "PickupCity": PickupCity,
            "PickupState": PickupState,
            "PickupZip": PickupZip,
            "DeliverName": DeliverName,
            "DeliverAddress": DeliverAddress,
            "DeliverCity": DeliverCity,
            "DeliverState": DeliverState,
            "DeliverZip": DeliverZip,
            "Pieces": Pieces,
            "Weight": Weight,
            "ServiceType": ServiceType,
            "VehicleType": VehicleType,
        }

        # Add optional fields if provided
        optional_fields = {
            "Email": Email,
            "Phone": Phone,
            "Extn": Extn,
            "NotifyOption": NotifyOption,
            "BillingReference": BillingReference,
            "Bol": Bol,
            "Po": Po,
            "jsonstrn": jsonstrn,
            "PickupContact": PickupContact,
            "PickupPhone": PickupPhone,
            "PickupExtn": PickupExtn,
            "PickupSpecinst": PickupSpecinst,
            "DeliverContact": DeliverContact,
            "DeliverPhone": DeliverPhone,
            "DeliverExtn": DeliverExtn,
            "DeliverSpecinst": DeliverSpecinst,
            "Pickupdate": Pickupdate,
            "PickuptimeFrom": PickuptimeFrom,
            "PickuptimeTo": PickuptimeTo,
            "Deliverdate": Deliverdate,
            "DelivertimeFrom": DelivertimeFrom,
            "DelivertimeTo": DelivertimeTo,
            "LiftgateReq": LiftgateReq,
            "BolReq": BolReq,
            "SignatureReq": SignatureReq,
        }

        for key, value in optional_fields.items():
            if value is not None:
                payload[key] = value

        response = self._request(
            "POST",
            "/order/json/",
            json=payload,
            include_api_key=False,  # API key is already in the payload
        )

        # Return the data portion if present, otherwise return full response
        if isinstance(response, dict) and "data" in response:
            return response["data"]
        return response

    def cancel_shipment(
        self,
        tracking_id: str,
    ) -> Dict[str, Any]:
        """
        Cancel a shipment.
        
        You can use our cancel shipments endpoint for orders not yet assigned to a driver.
        An API key is required to use this endpoint.

        Args:
            tracking_id: Required. The 6-8 digit tracking number assigned to your shipment
                       at the time of booking. Up to 8 characters.

        Returns:
            Cancellation confirmation.
            Response structure: {"error": null, "data": {}}
            
        Raises:
            JetDeliveryAPIError: If API key is not provided (required for this endpoint)
        """
        if not self.api_key:
            raise JetDeliveryAPIError(
                "API key is required to cancel shipments. "
                "Please provide an API key when initializing the client."
            )

        params = {"id": tracking_id}

        response = self._request(
            "POST",
            "/order/cancel/json/",
            params=params,
            include_api_key=True,  # API key is required and sent as query parameter
        )

        # Return the data portion if present, otherwise return full response
        if isinstance(response, dict) and "data" in response:
            return response["data"]
        return response

    def get_documents(
        self,
        tracking_id: str,
        use_api_key: bool = True,
    ) -> Dict[str, Any]:
        """
        Get documents associated with a shipment.
        
        You can use our documents endpoint to retrieve documents for a shipment.
        No API key is required to use this endpoint, but providing one may give
        you access to additional information.

        Args:
            tracking_id: Required. This can be the 6-8 digit tracking number assigned to your
                        shipment at the time of booking, or it can be the unique billing
                        reference provided to us. Up to 23 characters.
            use_api_key: Whether to include API key in request (default: True).

        Returns:
            Document information including control number, reference, invoice, and documents.
            Response structure: {"error": null, "data": {"orders": [...]}}
        """
        params = {"id": tracking_id}

        response = self._request(
            "GET",
            "/order/docs/",
            params=params,
            include_api_key=use_api_key and self.api_key is not None,
        )

        # Return the data portion if present, otherwise return full response
        if isinstance(response, dict) and "data" in response:
            return response["data"]
        return response

    def upload_document(
        self,
        file_path: str,
        job_id: str,
        user_id: str,
        document_type: Optional[str] = "bol",
        app_version: Optional[str] = "0.3.0",
        system_name: Optional[str] = "Chrome",
        system_version: Optional[str] = "128",
        user_agent: Optional[str] = "Mozilla",
        legacy: Optional[str] = "true",
    ) -> Dict[str, Any]:
        """
        Upload a document for a shipment.
        
        You can use our file upload endpoint to upload documents such as BOLs
        and other shipment-related files.

        Args:
            file_path: Required. Path to the file to upload.
            job_id: Required. The job/shipment ID.
            user_id: Required. The user ID.
            document_type: Optional. Type of document (e.g., "bol").
            app_version: Optional. Application version (default: "0.3.0").
            system_name: Optional. System name (e.g., "Chrome").
            system_version: Optional. System version (e.g., "128").
            user_agent: Optional. User agent string (e.g., "Mozilla").
            legacy: Optional. Legacy flag (default: "true").

        Returns:
            Upload confirmation.
            Response structure: {"error": null, "data": {}}
            
        Raises:
            JetDeliveryAPIError: If file cannot be read or upload fails
        """
        import os
        
        if not os.path.exists(file_path):
            raise JetDeliveryAPIError(f"File not found: {file_path}")

        params = {
            "jobId": job_id,
            "userId": user_id,
        }
        
        if document_type:
            params["type"] = document_type
        if app_version:
            params["appVersion"] = app_version
        if system_name:
            params["systemName"] = system_name
        if system_version:
            params["systemVersion"] = system_version
        if user_agent:
            params["userAgent"] = user_agent
        if legacy:
            params["legacy"] = legacy

        # Prepare file for upload
        try:
            with open(file_path, "rb") as f:
                file_name = os.path.basename(file_path)
                files = {"file": (file_name, f, "application/octet-stream")}

                # For file uploads, we need to make the request directly
                # since we need to handle multipart/form-data properly
                url = f"{self.base_url}/utilities/wireless/documents/upload/"

                response = self.session.post(
                    url,
                    params=params,
                    files=files,
                    timeout=self.timeout,
                )

                return self._handle_response(response)
        except IOError as e:
            raise JetDeliveryAPIError(f"Failed to read file: {str(e)}")

    def delete_document(
        self,
        document_id: str,
    ) -> Dict[str, Any]:
        """
        Flag a document for removal.
        
        You can use this endpoint to flag documents for removal from a shipment.

        Args:
            document_id: Required. The document/shipment ID (idx parameter).

        Returns:
            Deletion confirmation.
            Response structure: {"error": null, "data": {}}
            
        Raises:
            JetDeliveryAPIError: If API key is not provided (required for this endpoint)
        """
        if not self.api_key:
            raise JetDeliveryAPIError(
                "API key is required to delete documents. "
                "Please provide an API key when initializing the client."
            )

        params = {
            "action": "flag_for_removal",
            "idx": document_id,
        }

        response = self._request(
            "GET",
            "/utilities/wireless/documents/upload/",
            params=params,
            include_api_key=True,  # API key is required
        )

        # Return the data portion if present, otherwise return full response
        if isinstance(response, dict) and "data" in response:
            return response["data"]
        return response