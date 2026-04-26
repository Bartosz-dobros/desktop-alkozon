import pytest
from desktop_alkozon.features.employees.service import JobOffer, Employee
from desktop_alkozon.features.warehouse.service import WarehouseItem
from desktop_alkozon.features.deliveries.service import Courier, Delivery, DeliveryAnnouncement
from desktop_alkozon.models.api_models import (
    User, UserRole, Product, InventoryItem, Order, OrderStatus,
    Delivery as ApiDelivery, DeliveryStatus, JobOfferStatus, WorkLog
)


class TestJobOfferModel:
    def test_valid_job_offer(self):
        offer = JobOffer(id=1, title="Kierowca", salary=4500.0, status="Otwarta")
        assert offer.id == 1
        assert offer.title == "Kierowca"
        assert offer.salary == 4500.0
        assert offer.status == "Otwarta"

    def test_job_offer_with_all_fields(self):
        offer = JobOffer(id=5, title="Manager", description="Test", salary=8000.0, status="Zamknięta")
        assert offer.title == "Manager"
        assert offer.status == "Zamknięta"
        assert offer.description == "Test"


class TestEmployeeModel:
    def test_valid_employee(self):
        emp = Employee(id=1, name="Jan Kowalski", email="jan@example.com", position="Kierowca", role="EMPLOYEE", status="Aktywny")
        assert emp.id == 1
        assert emp.name == "Jan Kowalski"
        assert emp.role == "EMPLOYEE"


class TestWarehouseItemModel:
    def test_valid_warehouse_item(self):
        item = WarehouseItem(id=1, name="Piwo 0.5l", quantity=100, unit="szt.", price=4.99)
        assert item.id == 1
        assert item.name == "Piwo 0.5l"
        assert item.quantity == 100

    def test_warehouse_item_zero_quantity(self):
        item = WarehouseItem(id=1, name="Out of stock", quantity=0, unit="szt.", price=9.99)
        assert item.quantity == 0

    def test_warehouse_item_with_category(self):
        item = WarehouseItem(id=1, name="Wodka", quantity=50, unit="szt.", price=29.99, category="Wodka")
        assert item.category == "Wodka"


class TestCourierModel:
    def test_valid_courier(self):
        courier = Courier(id=1, name="Jan Kowalski", email="jan@example.com", status="Dostępny", vehicle="Van")
        assert courier.id == 1
        assert courier.name == "Jan Kowalski"
        assert courier.vehicle == "Van"

    def test_courier_optional_vehicle(self):
        courier = Courier(id=1, name="Test", email="test@example.com", status="Dostępny")
        assert courier.vehicle is None


class TestDeliveryModel:
    def test_valid_delivery(self):
        delivery = Delivery(id=1, courier_name="Jan", destination="Warszawa", status="W drodze", announcement="Test")
        assert delivery.id == 1
        assert delivery.destination == "Warszawa"

    def test_delivery_announcement(self):
        announcement = DeliveryAnnouncement(id=1, title="Test", content="Content")
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
        order = Order(id=1, customerId=1, status=OrderStatus.SUBMITTED, deliveryAddress="Warszawa", totalAmount=99.99)
        assert order.id == 1
        assert order.status == OrderStatus.SUBMITTED

    def test_work_log_model(self):
        from datetime import datetime
        work_log = WorkLog(id=1, employeeId=1, clockInAt=datetime.now())
        assert work_log.employeeId == 1
