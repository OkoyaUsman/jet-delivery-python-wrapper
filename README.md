# Jet Delivery Python Wrapper

A Python client library for interacting with the [Jet Delivery API](https://api-docs.jetdelivery.com/).

## Features

- 🚚 **Schedule and cancel shipments**
- 📍 **Real-time shipment tracking** with GPS location
- 💰 **Get rate quotes** and estimate transit times
- 📄 **Upload and manage shipment documents**
- 🔍 **Retrieve shipment documents and information**

## Installation

### Install from PyPI

```bash
pip install jet-delivery
```

### Install from Source

```bash
git clone https://github.com/okoyausman/jet-delivery-python-wrapper.git
cd jet-delivery-python-wrapper
pip install -e .
```

## Quick Start

```python
from jetdelivery import JetDeliveryClient

# Initialize the client (API key is optional for some endpoints)
client = JetDeliveryClient(api_key="your-api-key")

# Get a rate quote
quote = client.get_quote(
    origin="90021",
    destination="91750",
    pieces=1,
    weight=5
)

print(f"Available services: {len(quote['services'])}")
for service in quote['services']:
    print(f"{service['service_name']}: ${service['charge_total']}")
```

## Usage Examples

### Track a Shipment

```python
# Track without API key (zip-code level location only)
tracking = client.track_shipment(
    tracking_id="2345678",
    use_api_key=False
)

# Track with API key (exact GPS locations)
tracking = client.track_shipment(
    tracking_id="2345678",
    use_api_key=True
)

print(f"Status: {tracking['status_description']}")
print(f"Tracking Number: {tracking['track_no']}")
print(f"Origin: {tracking['origin_geolocation']}")
print(f"Destination: {tracking['destination_geolocation']}")

# View event history
for event in tracking['events']:
    print(f"{event['datetime']}: {event['description']}")
```

### Get Rate Quote

```python
quote = client.get_quote(
    origin="90021",  # 5-digit zip code
    destination="91750",  # 5-digit zip code
    pieces=1,
    weight=5,
    pickup_req_date="12/25/2024",  # MM/DD/YYYY format
    pickup_req_time="14:00",  # 24-hour format HH:MM
    deliver_req_date="12/25/2024",
    deliver_req_time="18:00"
)

print(f"Rate Miles: {quote['rate_miles']}")
print(f"Origin: {quote['origin_city']}, {quote['origin_state']}")
print(f"Destination: {quote['destination_city']}, {quote['destination_state']}")

# View available services
for service in quote['services']:
    print(f"\n{service['service_name']}")
    print(f"  Description: {service['service_full_text_description']}")
    print(f"  Estimated Delivery: {service['estimated_delivery']}")
    print(f"  Guaranteed Delivery: {service['guaranteed_delivery']}")
    print(f"  Total Charge: ${service['charge_total']}")
```

### Schedule a Shipment

```python
# API key is required for scheduling shipments
client = JetDeliveryClient(api_key="your-api-key")

shipment = client.schedule_shipment(
    # Required contact information
    Contact="John Doe",
    Email="john@example.com",
    Phone=1234567890,
    
    # Required pickup information
    PickupName="ABC Company",
    PickupAddress="123 Main St",
    PickupCity="Los Angeles",
    PickupState="CA",
    PickupZip=90021,
    PickupContact="Jane Smith",
    PickupPhone=9876543210,
    PickupSpecinst="Ring doorbell, leave at front desk",
    
    # Required delivery information
    DeliverName="XYZ Corporation",
    DeliverAddress="456 Oak Ave",
    DeliverCity="La Verne",
    DeliverState="CA",
    DeliverZip=91750,
    DeliverContact="Bob Johnson",
    DeliverPhone=5551234567,
    DeliverSpecinst="Call upon arrival",
    
    # Required shipment details
    Pieces=1,
    Weight=10,
    ServiceType="1",  # Service type code
    VehicleType="CAR",  # Vehicle type code
    
    # Optional timing
    Pickupdate="12/25/2024",  # MM/DD/YYYY
    PickuptimeFrom="09:00",  # HH:MM
    PickuptimeTo="17:00",
    Deliverdate="12/25/2024",
    DelivertimeFrom="10:00",
    DelivertimeTo="18:00",
    
    # Optional references
    BillingReference="ORDER-12345",
    Bol="BOL-67890",
    Po="PO-11111",
    
    # Optional service options
    NotifyOption="Y",  # Email notification on delivery
    LiftgateReq="N",
    BolReq="Y",
    SignatureReq="Y"
)

print(f"Tracking Number: {shipment['shipments'][0]['track_no']}")
print(f"Billing Reference: {shipment['shipments'][0]['billing_reference']}")
print(f"Estimated Delivery: {shipment['shipments'][0]['estimated_delivery']}")
print(f"Estimated Charge: ${shipment['shipments'][0]['estimated_charge']}")
```

### Cancel a Shipment

```python
# API key is required for canceling shipments
result = client.cancel_shipment(tracking_id="2345678")
print("Shipment cancelled successfully")
```

### Get Shipment Documents

```python
# Get documents (API key optional)
documents = client.get_documents(
    tracking_id="2345678",
    use_api_key=True
)

for order in documents['orders']:
    print(f"Control Number: {order['control_no']}")
    print(f"Reference: {order['reference']}")
    print(f"Invoice: {order['invoice']}")
    print(f"Documents: {len(order['documents'])}")
```

### Upload a Document

```python
# API key is required for uploading documents
result = client.upload_document(
    file_path="/path/to/bol.pdf",
    job_id="3546030",
    user_id="999",
    document_type="bol",  # Optional, defaults to "bol"
    app_version="0.3.0",
    system_name="Chrome",
    system_version="128",
    user_agent="Mozilla",
    legacy="true"
)

print("Document uploaded successfully")
```

### Delete/Flag Document for Removal

```python
# API key is required for deleting documents
result = client.delete_document(document_id="3316407")
print("Document flagged for removal")
```

## Error Handling

The wrapper includes custom exceptions for better error handling:

```python
from jetdelivery import (
    JetDeliveryClient,
    JetDeliveryError,
    JetDeliveryAPIError,
    JetDeliveryAuthenticationError,
    JetDeliveryNotFoundError,
    JetDeliveryValidationError,
)

client = JetDeliveryClient(api_key="your-api-key")

try:
    tracking = client.track_shipment("2345678")
except JetDeliveryNotFoundError:
    print("Shipment not found")
except JetDeliveryAuthenticationError:
    print("Authentication failed - check your API key")
except JetDeliveryValidationError as e:
    print(f"Validation error: {e}")
except JetDeliveryAPIError as e:
    print(f"API error: {e}")
```

## Configuration

You can customize the client with additional options:

```python
client = JetDeliveryClient(
    api_key="your-api-key",  # Optional for some endpoints
    base_url="https://www.jetdelivery.com/api/v1",  # Default
    timeout=30,  # Request timeout in seconds
)
```

## API Key Requirements

Some endpoints require an API key, while others work without one:

- **Requires API Key**: `schedule_shipment()`, `cancel_shipment()`, `upload_document()`, `delete_document()`
- **Optional API Key**: `track_shipment()`, `get_quote()`, `get_documents()`

When an API key is not provided for endpoints that support it, you may receive limited information (e.g., zip-code level locations instead of exact GPS coordinates).

## API Documentation

For detailed API documentation, visit:
- [Jet Delivery API Docs](https://api-docs.jetdelivery.com/)
- [Developer Learning Center](https://www.jetdelivery.com/developer/)

## Requirements

- Python 3.8+
- requests >= 2.31.0

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For API support, visit the [Jet Delivery Developer Center](https://www.jetdelivery.com/developer/).