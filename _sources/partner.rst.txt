Partner API
===========

The Partner API client provides access to distributor operations for managing
sub-organizations in Exoscale.

Basic Usage
-----------

Creating a client
~~~~~~~~~~~~~~~~~

.. code-block:: python

    from exoscale.api.partner import Client
    
    # Create client with API credentials
    client = Client(
        key="EXO...",
        secret="..."
    )

Managing Organizations
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # List all distributor organizations
    result = client.list_distributor_organizations()
    for org in result['organizations']:
        print(f"{org['name']} - {org['id']}")
    
    # Create a new organization
    new_org = client.create_distributor_organization(
        display_name="Customer Corp",
        billing_address={
            "name": "Customer Corp",
            "street-name": "Business Avenue",
            "building-number": "123",
            "city": "Zurich",
            "postal-code": "8001",
            "country": "CH"
        },
        owner_email="admin@customer.com",
        client_id="internal-1234"  # Optional
    )
    
    # Activate/Suspend organizations
    client.activate_distributor_organization(id=org_id)
    client.suspend_distributor_organization(id=org_id)
    
    # Get usage information
    usage = client.list_distributor_organization_usage(
        id=org_id,
        period="2025-01"
    )

Error Handling
--------------

The Partner API client uses the same error handling as the V2 API:

.. code-block:: python

    from exoscale.api.exceptions import (
        ExoscaleAPIAuthException,
        ExoscaleAPIClientException,
        ExoscaleAPIServerException
    )
    
    try:
        client.get_distributor_organization(id="invalid")
    except ExoscaleAPIClientException as e:
        print(f"Client error: {e}")
    except ExoscaleAPIServerException as e:
        print(f"Server error: {e}")

API Reference
-------------

.. autoclass:: exoscale.api.partner.Client
   :members:
   :inherited-members:
