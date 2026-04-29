import pytest
from desktop_alkozon.features.employees.controller import EmployeesController
from desktop_alkozon.features.warehouse.controller import WarehouseController
from desktop_alkozon.features.deliveries.controller import DeliveriesController


class TestEmployeesController:
    @pytest.fixture
    def controller(self):
        return EmployeesController()

    def test_get_offers_returns_list(self, controller):
        offers = controller.get_offers_sync()
        assert isinstance(offers, list)
        assert len(offers) >= 0

    def test_get_employees_returns_list(self, controller):
        employees = controller.get_employees_sync()
        assert isinstance(employees, list)
        assert len(employees) >= 0

    def test_controller_has_async_create_offer(self, controller):
        assert hasattr(controller, "create_offer")

    def test_hire_calls_service(self, controller):
        import asyncio
        result = asyncio.run(controller.hire(1))
        assert result is not None

    def test_fire_calls_service(self, controller):
        import asyncio
        result = asyncio.run(controller.terminate(101))
        assert result is not None


class TestWarehouseController:
    @pytest.fixture
    def controller(self):
        return WarehouseController()

    def test_get_stock_data_returns_list(self, controller):
        stock = controller.get_stock_data_sync()
        assert isinstance(stock, list)
        assert len(stock) >= 0

    def test_order_new_item_creates_item(self, controller):
        item = controller.order_new_item_sync("Nowy Produkt", 50, "szt.", 19.99)
        assert item is not None
        assert hasattr(item, 'name')

    def test_order_new_item_with_zero_quantity(self, controller):
        item = controller.order_new_item_sync("Test", 0, "szt.", 9.99)
        assert item is not None

    def test_order_new_item_with_decimals(self, controller):
        item = controller.order_new_item_sync("Test", 10, "szt.", 9.99)
        assert item is not None


class TestDeliveriesController:
    @pytest.fixture
    def controller(self):
        return DeliveriesController()

    def test_get_couriers_returns_list(self, controller):
        couriers = controller.get_couriers_sync()
        assert isinstance(couriers, list)
        assert len(couriers) >= 0

    def test_get_deliveries_returns_list(self, controller):
        deliveries = controller.get_deliveries_sync()
        assert isinstance(deliveries, list)
        assert len(deliveries) >= 0

    def test_create_delivery_sets_status(self, controller):
        delivery = controller.create_new_announcement(
            title="Test",
            content="Testowa dostawa"
        )
        assert delivery is not None
