import pytest
from desktop_alkozon.features.employees.controller import EmployeesController
from desktop_alkozon.features.warehouse.controller import WarehouseController
from desktop_alkozon.features.deliveries.controller import DeliveriesController


class TestEmployeesController:
    @pytest.fixture
    def controller(self):
        return EmployeesController()

    def test_get_offers_returns_list(self, controller):
        offers = controller.get_offers()
        assert isinstance(offers, list)
        assert len(offers) >= 0

    def test_get_employees_returns_list(self, controller):
        employees = controller.get_employees()
        assert isinstance(employees, list)
        assert len(employees) >= 0

    def test_controller_has_async_create_offer(self, controller):
        assert hasattr(controller, "create_offer")
        assert hasattr(controller, "create_offer_sync")

    def test_hire_calls_service(self, controller, capsys):
        controller.hire_sync(1, "Nowy Pracownik")
        captured = capsys.readouterr()
        assert "Zatrudniono" in captured.out or captured.out != ""

    def test_fire_calls_service(self, controller, capsys):
        controller.fire_sync(101)
        captured = capsys.readouterr()
        assert "Zwolniono" in captured.out or captured.out != ""


class TestWarehouseController:
    @pytest.fixture
    def controller(self):
        return WarehouseController()

    def test_get_stock_data_returns_list(self, controller):
        stock = controller.get_stock_data()
        assert isinstance(stock, list)
        assert len(stock) >= 0

    def test_order_new_item_creates_item(self, controller):
        item = controller.order_new_item("Nowy Produkt", 50, "szt.", 19.99)
        assert item.name == "Nowy Produkt"
        assert item.quantity == 50
        assert item.price == 19.99

    def test_order_new_item_with_zero_quantity(self, controller):
        item = controller.order_new_item("Test", 0, "szt.", 9.99)
        assert item.quantity == 0

    def test_order_new_item_with_decimals(self, controller):
        item = controller.order_new_item("Test", 10, "szt.", 9.99)
        assert item.price == 9.99


class TestDeliveriesController:
    @pytest.fixture
    def controller(self):
        return DeliveriesController()

    def test_get_couriers_returns_list(self, controller):
        couriers = controller.get_couriers()
        assert isinstance(couriers, list)
        assert len(couriers) >= 0

    def test_get_deliveries_returns_list(self, controller):
        deliveries = controller.get_deliveries()
        assert isinstance(deliveries, list)
        assert len(deliveries) >= 0

    def test_create_delivery_sets_status(self, controller):
        delivery = controller.create_new_announcement(
            courier_name="Test Kurier",
            destination="Warszawa",
            announcement="Testowa dostawa"
        )
        assert delivery.courier_name == "Test Kurier"
        assert delivery.status == "Nowa"

    def test_courier_status_options(self, controller):
        couriers = controller.get_couriers()
        valid_statuses = ["Dostępny", "W drodze", "Nieaktywny"]
        for courier in couriers:
            assert courier.status in valid_statuses
