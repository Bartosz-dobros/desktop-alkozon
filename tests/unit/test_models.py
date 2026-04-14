import pytest
from desktop_alkozon.features.employees.service import JobOffer, Employee
from desktop_alkozon.features.warehouse.service import WarehouseItem
from desktop_alkozon.features.deliveries.service import Courier, Delivery


class TestJobOfferModel:
    def test_valid_job_offer(self):
        offer = JobOffer(id=1, title="Kierowca", salary=4500.0, status="Otwarta")
        assert offer.id == 1
        assert offer.title == "Kierowca"
        assert offer.salary == 4500.0
        assert offer.status == "Otwarta"

    def test_job_offer_with_all_fields(self):
        offer = JobOffer(id=5, title="Manager", salary=8000.0, status="Zamknięta")
        assert offer.title == "Manager"
        assert offer.status == "Zamknięta"

    def test_job_offer_zero_salary(self):
        offer = JobOffer(id=1, title="Wolontariusz", salary=0.0, status="Otwarta")
        assert offer.salary == 0.0

    def test_job_offer_string_salary_conversion(self):
        offer = JobOffer(id=1, title="Test", salary="5000.0", status="Otwarta")
        assert isinstance(offer.salary, (int, float))


class TestEmployeeModel:
    def test_valid_employee(self):
        emp = Employee(id=1, name="Jan Kowalski", position="Kierowca", status="Zatrudniony")
        assert emp.id == 1
        assert emp.name == "Jan Kowalski"
        assert emp.position == "Kierowca"

    def test_employee_all_statuses(self):
        statuses = ["Zatrudniony", "Na urlopie", "Zwolniony"]
        for status in statuses:
            emp = Employee(id=1, name="Test", position="Test", status=status)
            assert emp.status == status


class TestWarehouseItemModel:
    def test_valid_warehouse_item(self):
        item = WarehouseItem(id=1, name="Piwo 0.5l", quantity=100, unit="szt.", price=4.99)
        assert item.id == 1
        assert item.name == "Piwo 0.5l"
        assert item.quantity == 100
        assert item.unit == "szt."
        assert item.price == 4.99

    def test_warehouse_item_zero_quantity(self):
        item = WarehouseItem(id=1, name="Out of stock", quantity=0, unit="szt.", price=9.99)
        assert item.quantity == 0

    def test_warehouse_item_different_units(self):
        units = ["szt.", "l", "kg", "karton"]
        for unit in units:
            item = WarehouseItem(id=1, name="Test", quantity=10, unit=unit, price=9.99)
            assert item.unit == unit

    def test_warehouse_item_high_precision_price(self):
        item = WarehouseItem(id=1, name="Premium", quantity=1, unit="szt.", price=99.99)
        assert item.price == 99.99


class TestCourierModel:
    def test_valid_courier(self):
        courier = Courier(id=1, name="Jan Kowalski", status="Dostępny", vehicle="Van")
        assert courier.id == 1
        assert courier.name == "Jan Kowalski"
        assert courier.vehicle == "Van"

    def test_courier_vehicles(self):
        vehicles = ["Van", "Furgonetka", "Samochód osobowy", "Skuter"]
        for vehicle in vehicles:
            courier = Courier(id=1, name="Test", status="Dostępny", vehicle=vehicle)
            assert courier.vehicle == vehicle


class TestDeliveryModel:
    def test_valid_delivery(self):
        delivery = Delivery(
            id=1,
            courier_name="Jan Kowalski",
            destination="Warszawa",
            status="W drodze",
            announcement="Test"
        )
        assert delivery.id == 1
        assert delivery.destination == "Warszawa"

    def test_delivery_statuses(self):
        statuses = ["Nowa", "W drodze", "Dostarczona", "Anulowana"]
        for status in statuses:
            delivery = Delivery(
                id=1,
                courier_name="Test",
                destination="Test",
                status=status,
                announcement="Test"
            )
            assert delivery.status == status
