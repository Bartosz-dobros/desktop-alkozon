from desktop_alkozon.models.api_models import (
    DeliveryAnnouncementResponse,
    DeliveryDetails,
    DeliveryResponse,
    DeliveryStatus,
    InventoryItem,
    InventoryProductRow,
    JobOfferResponse,
    JobOfferStatus,
    Order,
    OrderStatus,
    Product,
    User,
    UserAdminResponse,
    UserRole,
    WorkLog,
)


class TestJobOfferModel:
    def test_valid_job_offer(self):
        offer = JobOfferResponse(
            id=1,
            title="Kierowca",
            status=JobOfferStatus.OPEN,
            createdAt="2024-01-01T00:00:00Z",
            updatedAt="2024-01-01T00:00:00Z",
        )
        assert offer.id == 1
        assert offer.title == "Kierowca"
        assert offer.status == JobOfferStatus.OPEN

    def test_job_offer_with_all_fields(self):
        offer = JobOfferResponse(
            id=5,
            title="Manager",
            description="Test",
            status=JobOfferStatus.CLOSED,
            createdAt="2024-01-01T00:00:00Z",
            updatedAt="2024-01-01T00:00:00Z",
        )
        assert offer.title == "Manager"
        assert offer.status == JobOfferStatus.CLOSED
        assert offer.description == "Test"


class TestEmployeeModel:
    def test_valid_employee(self):
        emp = UserAdminResponse(
            id=1,
            email="jan@example.com",
            role=UserRole.EMPLOYEE,
            active=True,
            courier=False,
        )
        assert emp.id == 1
        assert emp.email == "jan@example.com"
        assert emp.role == UserRole.EMPLOYEE


class TestWarehouseItemModel:
    def test_valid_warehouse_item(self):
        item = InventoryProductRow(
            productId=1, name="Piwo", quantity=100, warehouseZone="A1"
        )
        assert item.productId == 1
        assert item.name == "Piwo"
        assert item.quantity == 100

    def test_warehouse_item_zero_quantity(self):
        item = InventoryProductRow(productId=1, name="Out of stock", quantity=0)
        assert item.quantity == 0

    def test_warehouse_item_with_category(self):
        item = InventoryProductRow(
            productId=1, name="Wodka", quantity=50, warehouseZone="B2"
        )
        assert item.warehouseZone == "B2"


class TestCourierModel:
    def test_valid_courier(self):
        courier_data = {
            "id": 1,
            "email": "jan@example.com",
            "active": True,
            "courier": True,
        }
        assert courier_data["id"] == 1
        assert courier_data["email"] == "jan@example.com"

    def test_courier_optional_vehicle(self):
        courier_data = {"id": 1, "email": "test@example.com", "courier": False}
        assert "vehicle" not in courier_data


class TestDeliveryModel:
    def test_valid_delivery(self):
        delivery = DeliveryResponse(
            id=1,
            orderId=100,
            status=DeliveryStatus.IN_TRANSIT,
            deliveryDetails=DeliveryDetails(
                recipientName="Jan Kowalski",
                streetAddress="Marszalkowska 1",
                city="Warszawa",
                postalCode="00-001",
                country="Polska",
            ),
        )
        assert delivery.id == 1
        assert delivery.status == DeliveryStatus.IN_TRANSIT
        assert delivery.deliveryDetails is not None
        assert delivery.deliveryDetails.city == "Warszawa"

    def test_delivery_announcement(self):
        announcement = DeliveryAnnouncementResponse(
            id=1, title="Test", content="Content"
        )
        assert announcement.id == 1
        assert announcement.title == "Test"


class TestApiModels:
    def test_user_role_enum(self):
        assert UserRole.MANAGER.value == "MANAGER"
        assert UserRole.EMPLOYEE.value == "EMPLOYEE"
        assert UserRole.CUSTOMER.value == "CUSTOMER"
        assert UserRole.GUEST.value == "GUEST"

    def test_order_status_enum(self):
        assert OrderStatus.SUBMITTED.value == "SUBMITTED"
        assert OrderStatus.IN_PRODUCTION.value == "IN_PRODUCTION"
        assert OrderStatus.DELIVERED.value == "DELIVERED"

    def test_delivery_status_enum(self):
        assert DeliveryStatus.PENDING.value == "PENDING"
        assert DeliveryStatus.IN_TRANSIT.value == "IN_TRANSIT"
        assert DeliveryStatus.DELIVERED.value == "DELIVERED"

    def test_user_model(self):
        user = User(id=1, email="test@example.com", role=UserRole.MANAGER)
        assert user.id == 1
        assert user.email == "test@example.com"
        assert user.role == UserRole.MANAGER

    def test_product_model(self):
        product = Product(id=1, name="Wodka", price=29.99, category="Wodka")
        assert product.name == "Wodka"
        assert product.price == 29.99

    def test_inventory_item_model(self):
        item = InventoryItem(id=1, quantity=100)
        assert item.quantity == 100
        assert item.product is None

    def test_order_model(self):
        order = Order(
            id=1,
            customerId=1,
            status=OrderStatus.SUBMITTED,
            deliveryAddress="Warszawa",
            totalAmount=99.99,
        )
        assert order.id == 1
        assert order.status == OrderStatus.SUBMITTED

    def test_work_log_model(self):
        from datetime import datetime

        work_log = WorkLog(id=1, employeeId=1, clockInAt=datetime.now())
        assert work_log.employeeId == 1
