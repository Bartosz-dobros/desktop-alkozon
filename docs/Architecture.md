# OPIS PROJEKTU – Alkozon Desktop

## 1. WYKORZYSTANE TECHNOLOGIE

**Python 3.11+**
Podstawowy język programowania. Aplikacja w całości napisana w Pythonie, wykorzystującym mechanizmy asynchroniczne (asyncio).

**Flet (>=0.25.0, <0.85.0)**
Framework GUI umożliwiający budowanie natywnych aplikacji desktopowych przy użyciu kontrolek Fluttera. Zapewnia material design, responsywność oraz działanie w natywnym oknie systemowym. Aplikacja uruchamiana jest przez wywołanie `flet.app(main)` w pliku `main.py`.

**httpx**
Asynchroniczna biblioteka HTTP używana do komunikacji z REST API backendu (Alcohol Factory API). Obsługuje automatyczne odświeżanie tokenów JWT oraz mechanizm ponawiania zapytań.

**Pydantic v2**
Biblioteka do walidacji danych przez type hinty. Używana do definiowania modeli zapytań i odpowiedzi API (`src/desktop_alkozon/models/api_models.py`). Zapewnia type safety i automatyczną serializację/deserializację JSON.

**aiosqlite**
Asynchroniczny driver SQLite. Używany do lokalnej bazy danych offline. Umożliwia wykonywanie zapytań SQL bez blokowania pętli zdarzeń asyncio.

**cryptography (Fernet)**
Biblioteka kryptograficzna. Szyfruje lokalny plik bazy SQLite na dysku przy użyciu szyfrowania symetrycznego Fernet (AES-128-CBC z HMAC). Klucz szyfrujący przechowywany jest w systemowym menedżerze poświadczeń.

**keyring**
Dostęp do systemowego menedżera poświadczeń (Windows Credential Manager, macOS Keychain, Linux Secret Service). Przechowuje:

- tokeny dostępu JWT (access_token, refresh_token)
- klucz szyfrowania lokalnej bazy danych

**PyJWT**
Dekodowanie tokenów JWT (bez weryfikacji podpisu) w celu wydobycia danych użytkownika (user_id, email, rola) z lokalnie przechowywanego tokena.

**bcrypt**
Hashowanie i weryfikacja haseł oraz kodów 2FA. Używany lokalnie do uwierzytelniania offline – po pierwszym poprawnym logowaniu online hash hasła jest buforowany w lokalnej bazie.

**PyArmor**
Obfuskacja kodu źródłowego Pythona. Używana w procesie budowania wersji produkcyjnej w celu ochrony własności intelektualnej.

**PyInstaller**
Pakowanie aplikacji wraz z interpreterem Pythona i zależnościami do pojedynczego pliku wykonywalnego (.exe) dla systemu Windows.

**python-dotenv**
Ładowanie konfiguracji środowiskowej z pliku .env (URL API, tryb demo, kod bezpieczeństwa blokady).

**pytest / pytest-asyncio**
Framework testowy z wsparciem dla testów asynchronicznych.

**Black, isort, Ruff**
Narzędzia do formatowania kodu (Black), sortowania importów (isort) i lintowania (Ruff). Zintegrowane z pre-commit hooks.

## 2. SPOSÓB TESTOWANIA

Projekt zawiera 5 zestawów testów, każdy w osobnym podkatalogu `tests/`:

- **tests/unit/** – Testy jednostkowe – izolowane testy pojedynczych funkcji i klas. Mockują wszystkie zależności zewnętrzne (API, baza danych, keyring).

- **tests/integration/** – Testy integracyjne – weryfikują współdziałanie komponentów:
  - lokalna baza SQLite (tworzenie schematu, migracje, CRUD)
  - mechanizm outboxa (kolejkowanie i przetwarzanie operacji offline)
  - synchronizacja (sync_manager)
  - szyfrowanie i deszyfrowanie bazy danych

- **tests/api/** – Testy klienta HTTP – weryfikują:
  - poprawne składanie żądań HTTP
  - automatyczne dołączanie tokena Bearer
  - odświeżanie tokena po wygaśnięciu
  - obsługę błędów (timeout, 401, 500)

- **tests/feature/** – Testy funkcjonalne – scenariusze biznesowe testujące pełne przepływy:
  - logowanie z 2FA i blokadą konta
  - tworzenie zamówienia uzupełniającego offline i synchronizacja
  - przypisywanie kuriera do dostawy
  - zatrudnianie pracownika

- **tests/ui/** – Testy interfejsu użytkownika – testują:
  - poprawność renderowania stron (login, menu główne, widoki)
  - reakcję na zmiany stanu łączności (baner online/offline)
  - przełączanie motywu i języka
  - walidację pól formularzy

**Wspólne elementy:**

- `tests/conftest.py` – współdzielone fixture'y (mock keyring, mock szyfrowania)
- CI/CD przez GitHub Actions (`.github/workflows/tests.yml`): każdy push i PR uruchamia lint (black, isort, ruff), a następnie wszystkie 5 zestawów testów równolegle.

**Uruchomienie testów:**

```bash
pytest tests/                    # wszystkie testy
pytest tests/unit/ -v            # tylko jednostkowe
pytest tests/integration/ -v     # tylko integracyjne
pytest tests/api/ -v             # tylko API
pytest tests/feature/ -v         # tylko funkcjonalne
pytest tests/ui/ -v              # tylko UI
```

## 3. ARCHITEKTURA

Aplikacja zbudowana jest w architekturze warstwowej z wzorcem Controller-Service-View dla każdego modułu funkcyjnego. Dodatkowo zastosowano wzorce: Repository, Outbox, Singleton (dla klienta API).

### WARSTWY

**a) Warstwa konfiguracji (config/)**
Ładuje zmienne środowiskowe z pliku `.env`. Udostępnia globalne stałe: `API_BASE_URL`, `DEMO_MODE`, `DEBUG`.

**b) Warstwa modeli (models/)**
Definicje Pydantic dla encji API: User, Product, RawMaterial, Order, Delivery, Courier, JobOffer, Announcement itd.

**c) Warstwa usług (services/)**
`api_client.py` – singleton klienta HTTP. Zarządza:

- autoryzacją (dołączanie tokena Bearer)
- automatycznym odświeżaniem tokena (refresh_token)
- mapowaniem odpowiedzi JSON na modele Pydantic
- obsługą błędów i timeoutów

**d) Warstwa rdzenia (core/)**
Zawiera logikę biznesową niezależną od UI:

- `auth.py` – uwierzytelnianie (online, offline, demo, 2FA, blokada)
- `database.py` – inicjalizacja/migracje lokalnej bazy SQLite
- `encryption.py` – szyfrowanie bazy Fernet
- `connectivity.py` – monitorowanie łączności (ping co 30s)
- `outbox.py` – wzorzec outboxa (kolejka operacji offline)
- `repository.py` – warstwa dostępu do danych (CRUD na lokalnej bazie)
- `sync_manager.py` – orchestrator synchronizacji (full sync + outbox)
- `i18n.py` – internacjonalizacja PL/EN
- `exceptions.py` – wyjątki (OfflineError, SyncConflictError)
- `logger.py` – konfiguracja logowania (plik + konsola)

**e) Warstwa funkcjonalna (features/)**
Każdy moduł biznesowy dzieli się na trzy komponenty:

- **Controller** – inicjalizuje widok, łączy Service z View, obsługuje zdarzenia UI (przyciski, zmiany pól)
- **Service** – logika biznesowa modułu, wywołuje API, zarządza danymi offline (przez repository), kolejkuje operacje w outboxie
- **View** – definicja interfejsu użytkownika (kontrolki Flet)

Moduły:

- `warehouse/` – zarządzanie magazynem (zapasy, uzupełnienia)
- `deliveries/` – zarządzanie dostawami i kurierami
- `employees/` – zarządzanie pracownikami i ofertami pracy

#### f) Warstwa prezentacji (ui/)

- `pages/` – pełne strony aplikacji
  - `login_page.py` – logowanie, 2FA, blokada, menu główne
  - `main_menu.py` – menu główne (wersja legacy)
- `components/` – komponenty wielokrotnego użytku
  - `connectivity_banner.py` – pasek stanu łączności
  - `settings_drawer.py` – panel ustawień (motyw, język)

**g) Punkt wejściowy (main.py)**
Inicjalizuje konfigurację, logger, bazę danych, monitor łączności. Tworzy stronę logowania i uruchamia aplikację Flet.

### STRUKTURA KATALOGÓW (skrócona)

```text
main.py
build.py
pyproject.toml
requirements.txt
swaggerdata.json
.env / .env.example
src/desktop_alkozon/
    config/__init__.py
    core/
        auth.py, database.py, connectivity.py, encryption.py,
        exceptions.py, i18n.py, logger.py, outbox.py,
        repository.py, sync_manager.py
    features/
        deliveries/ (controller.py, service.py, views.py)
        employees/  (controller.py, service.py, views.py)
        warehouse/  (controller.py, service.py, views.py)
    models/__init__.py, api_models.py
    services/__init__.py, api_client.py
    ui/
        components/ (connectivity_banner.py, settings_drawer.py)
        pages/ (login_page.py, main_menu.py)
tests/
    conftest.py
    unit/, integration/, api/, feature/, ui/
```

## 4. OPIS DZIAŁANIA I PRZEPŁYW DANYCH

### 4.1 URUCHOMIENIE APLIKACJI

`main.py`:

1. Ładuje konfigurację z `.env` (`config/__init__.py`)
2. Inicjalizuje logger (`core/logger.py`)
3. Inicjalizuje lokalną bazę SQLite (`core/database.py`):
   - tworzy/otwiera szyfrowany plik `.db`
   - uruchamia migracje schematu
4. Inicjalizuje monitor łączności (`core/connectivity.py`):
   - uruchamia cykliczne pingowanie API (co 30s)
   - emituje zdarzenia on_online / on_offline
5. Tworzy stronę logowania (`ui/pages/login_page.py`)
6. Uruchamia pętlę zdarzeń Flet: `flet.app(main)`

### 4.2 LOGOWANIE (PRZEPŁYW DANYCH)

a) Użytkownik wprowadza email i hasło na stronie logowania.

b) LoginPage przekazuje dane do AuthService (`core/auth.py`):

- jeśli `DEMO_MODE=true` → logowanie demo (pomija API)
- jeśli offline i istnieje buforowany hash → logowanie offline (weryfikacja bcrypt lokalnie)
- jeśli online → żądanie POST /auth/login do API

c) API zwraca tokeny JWT (access_token, refresh_token) oraz dane użytkownika. AuthService:

- zapisuje tokeny w keyring
- zapisuje hash hasła w lokalnej bazie (na potrzeby offline)
- dekoduje JWT w celu wydobycia roli (manager/employee/courier)
- jeśli API wymaga 2FA (status 202) → wyświetla formularz kodu 2FA
- jeśli konto zablokowane (status 423) → wymaga kodu bezpieczeństwa

d) Po udanym logowaniu:

- uruchamiana jest pełna synchronizacja (`sync_manager.full_sync()`)
- przekierowanie do widoku właściwego dla roli użytkownika

### 4.3 PRACA ONLINE (NORMALNY PRZEPŁYW)

a) Użytkownik wykonuje operację (np. tworzy zamówienie uzupełniające).

b) Controller odbiera zdarzenie UI → wywołuje metodę Service.

c) Service (np. WarehouseService):

1. Waliduje dane wejściowe
2. Wywołuje `api_client.post()` z modelem Pydantic jako ciałem żądania
3. api_client dołącza nagłówek `Authorization: Bearer <token>`
4. Jeśli token wygasł → api_client automatycznie odświeża go przez refresh_token
5. Otrzymuje odpowiedź, mapuje JSON na model Pydantic
6. Aktualizuje lokalną bazę danych (`repository.update()`)
7. Zwraca wynik do Controller → Controller odświeża widok

d) View wyświetla zaktualizowane dane (np. nowe zamówienie na liście).

### 4.4 PRACA OFFLINE (PRZEPŁYW DANYCH)

a) Monitor łączności wykrywa brak odpowiedzi API (timeout/błąd sieci). Emituje zdarzenie on_offline. ConnectivityBanner zmienia kolor na pomarańczowy.

b) Użytkownik wykonuje operację (np. przypisuje kuriera do dostawy).

c) Service próbuje wywołać API → catches OfflineError (lub ConnectionError).

d) Service zapisuje operację w outboxie (`core/outbox.py`):

- tabela outbox zawiera: endpoint, metoda HTTP, ciało (JSON), timestamp, próba synchronizacji
- dane są również zapisywane lokalnie (repository) dla natychmiastowej aktualizacji UI

e) View odświeża się z danymi lokalnymi – użytkownik widzi efekt operacji, jakby była wykonana online.

f) Gdy łączność zostaje przywrócona:

1. Monitor emituje zdarzenie on_online
2. SyncManager odbiera zdarzenie i uruchamia przetwarzanie outboxa
3. Dla każdej operacji w outboxie:
   - wysyła żądanie HTTP do API
   - jeśli sukces → usuwa wpis z outboxa
   - jeśli błąd (np. konflikt) → zapisuje błąd, pozostawia w outboxie
4. Po przetworzeniu outboxa uruchamia pełną synchronizację (pull najnowszych danych z API)
5. Wyświetla snackbar z podsumowaniem (ile operacji zsynchronizowano, ile zakończyło się błędem)

### 4.5 SYNCHRONIZACJA (PRZEPŁYW DANYCH)

Wywoływana:

- po udanym logowaniu
- po przetworzeniu outboxa
- ręcznie (przycisk w ustawieniach)

`sync_manager.full_sync()`:

1. Pobiera z API: users, job_offers, inventory (products + raw_materials), deliveries, couriers, replenishments, announcements
2. Dla każdej encji:
   - API zwraca listę obiektów JSON
   - mapowanie na modele Pydantic
   - porównanie z lokalną bazą (na podstawie ID i timestampu modyfikacji)
   - aktualizacja/dodanie nowych rekordów w lokalnej bazie
3. Zapisuje timestamp ostatniej synchronizacji
4. Zwraca raport (ile rekordów zaktualizowano, dodano)

### 4.6 MAGAZYN – PRZYKŁADOWY PRZEPŁYW

a) Użytkownik otwiera widok magazynu.

b) `WarehouseController.init()` → `WarehouseService.get_inventory()`

c) Service:

- jeśli online → pobiera z API, zapisuje w lokalnej bazie, zwraca
- jeśli offline → odczytuje z lokalnej bazy (repository)

d) View renderuje tabelę z produktami/surowcami (nazwa, ilość, strefa).

e) Użytkownik klika "Utwórz zamówienie uzupełniające".

f) Controller pokazuje formularz → użytkownik wypełnia → zatwierdza.

g) Service waliduje, wysyła do API (lub kolejkuje w outboxie), zapisuje w lokalnej bazie.

h) View odświeża listę zamówień.

### 4.7 DOSTAWY – PRZYKŁADOWY PRZEPŁYW

a) Widok dostaw ładuje:

- listę oczekujących dostaw (pending deliveries)
- listę dostępnych kurierów

b) Użytkownik wybiera dostawę i kuriera, klika "Przypisz".

c) `DeliveriesService.assign_courier(delivery_id, courier_id)`:

- żądanie `PATCH /admin/deliveries/{id}/assign`
- aktualizacja lokalnej bazy
- odświeżenie list (dostawa znika z "oczekujących", kurier znika z "dostępnych")

### 4.8 PRACOWNICY – PRZYKŁADOWY PRZEPŁYW

a) Widok pracowników ładuje listę pracowników i ofert pracy.

b) Manager może:

- utworzyć nowe konto (`POST /auth/register` + `PUT /admin/users/{id}/role`)
- zwolnić pracownika (`DELETE /admin/users/{id}`)
- utworzyć ofertę pracy (`POST /admin/job-offers`)
- zamknąć ofertę (`PATCH /admin/job-offers/{id}/close`)

c) Każda operacja przechodzi przez Service → API (lub outbox) → repository → odświeżenie widoku.

### 4.9 BLOKADA KONTA (BEZPIECZEŃSTWO)

a) Przy 3. nieudanym logowaniu API zwraca wymóg 2FA.
b) Przy 5. nieudanym logowaniu API zwraca status 423 (locked).
c) Aplikacja wyświetla formularz kodu bezpieczeństwa.
d) Użytkownik musi wprowadzić kod wygenerowany przy buildzie (`LOCKOUT_SECURITY_CODE` w `.env`). Kod jest hashowany SHA-256 w czasie budowania (`build.py`) i wstrzykiwany do `_build_config.py`.
e) Po poprawnym kodzie następuje odblokowanie (`POST /auth/unlock`).

### 4.10 OBSŁUGA BŁĘDÓW

- **OfflineError** – brak łączności z API (przechwytywany przez Service, kieruje do outboxa)
- **SyncConflictError** – konflikt danych podczas synchronizacji (np. ktoś zmodyfikował ten sam rekord wcześniej)
- **HTTP 401** – nieautoryzowany → api_client automatycznie próbuje odświeżyć token; jeśli refresh też fail → wylogowanie
- **HTTP 403** – brak uprawnień (rola nie ma dostępu)
- **HTTP 423** – konto zablokowane (wymaga kodu bezpieczeństwa)
- **Timeout/ConnectionError** → przejście w tryb offline

### 4.11 INTERNACJONALIZACJA

`core/i18n.py` zawiera słownik z tłumaczeniami PL/EN dla wszystkich komunikatów w aplikacji. Wybór języka jest przechowywany w preferencjach użytkownika (shared_preferences). Po zmianie języka UI jest odświeżany.

### 4.12 MOTYW (JASNY/CIEMNY)

Ustawienie motywu jest przechowywane w `shared_preferences`. SettingsDrawer umożliwia przełączanie. Flet stosuje odpowiedni `theme_mode` (`ThemeMode.LIGHT` / `ThemeMode.DARK`).
