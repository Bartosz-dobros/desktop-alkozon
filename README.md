# Alkozon Desktop

  ![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
  ![SQLite](https://img.shields.io/badge/SQLite-07405E?style=for-the-badge&logo=sqlite&logoColor=white)
  ![JWT](https://img.shields.io/badge/JWT-000000?style=for-the-badge&logo=JSON%20web%20tokens&logoColor=white)
  ![Pytest](https://img.shields.io/badge/Pytest-0A9EDC?style=for-the-badge&logo=pytest&logoColor=white)
  ![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-2088FF?style=for-the-badge&logo=github-actions&logoColor=white)

Aplikacja desktopowa dla zarządu i pracowników fabryki alkoholu **Alkozon**. Stanowi kliencką część systemu ERP przeznaczoną do zarządzania magazynem, dostawami, kurierami oraz pracownikami.

Jest to desktopowy komponent wieloplatformowego ekosystemu Alkozon (web + mobile + desktop), komunikujący się z backendowym API _Alcohol Factory_.

---

## Spis treści

- [Technologie](#technologie)
- [Funkcjonalności](#funkcjonalności)
  - [Uwierzytelnianie i bezpieczeństwo](#uwierzytelnianie-i-bezpieczeństwo)
  - [Architektura offline-first](#architektura-offline-first)
  - [Zarządzanie magazynem](#zarządzanie-magazynem)
  - [Zarządzanie dostawami i kurierami](#zarządzanie-dostawami-i-kurierami)
  - [Zarządzanie pracownikami i HR](#zarządzanie-pracownikami-i-hr)
  - [Interfejs użytkownika](#interfejs-użytkownika)
- [Architektura projektu](#architektura-projektu)
- [Instalacja i uruchomienie](#instalacja-i-uruchomienie)
- [Budowanie wersji produkcyjnej](#budowanie-wersji-produkcyjnej)
- [Skrypty i komendy](#skrypty-i-komendy)
- [Testy](#testy)

---

## Technologie

| Technologia | Zastosowanie |
|---|---|
| **Python 3.11+** | Język programowania |
| **Flet** (>=0.25.0, <0.85.0) | Framework GUI (Material Design, okno natywne) |
| **httpx** | Asynchroniczny klient HTTP do komunikacji z API |
| **Pydantic v2** | Modele danych i walidacja |
| **aiosqlite** | Lokalna baza danych SQLite (async) |
| **cryptography (Fernet)** | Szyfrowanie lokalnej bazy danych |
| **keyring** | Bezpieczne przechowywanie tokenów w systemowym menedżerze poświadczeń |
| **PyJWT** | Dekodowanie tokenów JWT |
| **bcrypt** | Hashowanie haseł i kodów 2FA |
| **PyArmor** | Obfuskacja kodu źródłowego przy budowaniu |
| **PyInstaller** | Pakowanie aplikacji do pliku wykonywalnego (.exe) |
| **pytest / pytest-asyncio** | Framework testowy |
| **Black, isort, Ruff** | Formatowanie i lintowanie kodu |

---

## Funkcjonalności

### Uwierzytelnianie i bezpieczeństwo

- Logowanie pracownika za pomocą e-maila i hasła
- Dwuskładnikowe uwierzytelnianie (2FA) – kod weryfikacyjny wysyłany e-mailem (wymagany po 2 nieudanych logowaniach)
- **Twarda blokada konta** – po 5 nieudanych próbach konto zostaje zablokowane; odblokowanie wymaga specjalnego kodu bezpieczeństwa (SHA-256 hashowany w czasie budowania)
- Automatyczne wylogowanie po 30 minutach bezczynności
- Logowanie offline – po pierwszym udanym logowaniu online możliwe jest logowanie z buforowanymi danymi uwierzytelniającymi
- Tryb demo – umożliwia testowanie aplikacji bez dostępu do API
- Odświeżanie tokenów JWT za pomocą refresh tokenów
- Tokeny przechowywane w systemowym menedżerze poświadczeń (keyring)

### Architektura offline-first

- **Lokalna baza SQLite** (`~/.alkozon/alkozon_offline.db`) z pełnym schematem odzwierciedlającym API
- **Szyfrowanie bazy danych** w spoczynku przy użyciu szyfrowania Fernet (klucz przechowywany w keyring)
- **Wzorzec outboxa** – operacje wykonane offline są kolejkowane w tabeli `outbox` i synchronizowane po przywróceniu łączności
- **Monitorowanie łączności** – okresowe sprawdzanie dostępności API (ping co 30 sekund) z emitowaniem zdarzeń online/offline
- **Pełna synchronizacja** przy starcie aplikacji oraz po przetworzeniu outboxa (użytkownicy, oferty pracy, zapasy, dostawy, uzupełnienia, ogłoszenia)
- **Baner łączności** – pasek stanu informujący o trybie online (zielony), offline (pomarańczowy) lub synchronizacji (niebieski)

### Zarządzanie magazynem

- Podgląd stanu zapasów – produkty i surowce z ilościami oraz strefami magazynowymi
- Historia zamówień uzupełniających (replenishment)
- Tworzenie nowych zamówień uzupełniających z liniami (produkty lub surowce)
- Oznaczanie zamówień jako przyjęte
- Aktualizacja ilości produktów/surowców (wymagana rola managera)
- Dostęp offline do buforowanych danych magazynowych

### Zarządzanie dostawami i kurierami

- Lista oczekujących dostaw do przypisania kuriera
- Lista dostępnych (nieprzypisanych) kurierów
- Przydzielanie kurierów do dostaw
- Tworzenie i przeglądanie ogłoszeń dostaw
- Dostęp offline do buforowanych danych

### Zarządzanie pracownikami i HR

- Lista pracowników z rolami (Manager, Employee, Courier)
- Tworzenie kont pracowników (rejestracja + aktualizacja roli przez API)
- Zatrudnianie i zwalnianie pracowników
- Zarządzanie ofertami pracy – tworzenie, zamykanie, przeglądanie otwartych/zamkniętych ofert
- Dostęp offline do buforowanych danych

### Interfejs użytkownika

- Przełączanie motywu **jasny/ciemny** (zapisywany w preferencjach)
- Przełącznik języka **polski/angielski** (w pełni przetłumaczony interfejs)
- Panel ustawień dostępny z poziomu menu hamburgera
- Nowoczesny, responsywny interfejs Material Design (Flet)
- Domyślny rozmiar okna 1200×800, minimalny 800×600
- Powiadomienia snackbar dla wyników synchronizacji

---

## Architektura projektu

```text
desktop-alkozon/
├── main.py                          # Punkt wejściowy – uruchamia aplikację Flet
├── build.py                         # Skrypt budowania (PyArmor + PyInstaller)
├── Alkozon.spec                     # Plik konfiguracyjny PyInstaller
├── pyproject.toml                   # Metadane projektu, zależności, konfiguracja narzędzi
├── requirements.txt                 # Zależności (produkcyjne + deweloperskie)
├── swaggerdata.json                 # Pełna specyfikacja OpenAPI 3.1 backendu
├── .env                             # Zmienne środowiskowe (URL API, tryb demo, kod blokady)
├── .env.example                     # Wzór pliku .env
├── .pre-commit-config.yaml          # Konfiguracja pre-commit hooks
│
├── assets/                          # Zasoby statyczne
│
├── src/desktop_alkozon/
│   ├── config/                       # Konfiguracja (URL API, tryb demo, debug)
│   ├── core/                         # Warstwa logiki biznesowej
│   │   ├── auth.py                   # Serwis uwierzytelniania
│   │   ├── database.py               # Inicjalizacja i migracje lokalnej bazy SQLite
│   │   ├── connectivity.py           # Monitorowanie łączności z API
│   │   ├── encryption.py             # Szyfrowanie bazy danych (Fernet)
│   │   ├── exceptions.py             # Wyjątki (OfflineError, SyncConflictError)
│   │   ├── i18n.py                   # Internacjonalizacja (PL/EN)
│   │   ├── logger.py                 # Konfiguracja logowania
│   │   ├── outbox.py                 # Wzorzec outboxa dla operacji offline
│   │   ├── repository.py             # Lokalne repozytorium (CRUD dla encji)
│   │   └── sync_manager.py           # Zarządzanie synchronizacją
│   │
│   ├── features/                     # Moduły funkcyjne (Controller-Service-View)
│   │   ├── deliveries/               # Zarządzanie dostawami i kurierami
│   │   ├── employees/                # Zarządzanie pracownikami i ofertami pracy
│   │   └── warehouse/                # Zarządzanie magazynem
│   │
│   ├── models/                       # Modele Pydantic dla encji API
│   ├── services/                     # Klient HTTP API
│   └── ui/                           # Warstwa prezentacji
│       ├── components/               # Komponenty wielokrotnego użytku
│       │   ├── connectivity_banner.py    # Pasek stanu łączności
│       │   └── settings_drawer.py        # Panel ustawień
│       └── pages/                    # Strony aplikacji
│           ├── login_page.py             # Strona logowania
│           └── main_menu.py              # Menu główne
│
├── tests/                           # Testy
│   ├── api/                         # Testy klienta API
│   ├── feature/                     # Testy funkcjonalne
│   ├── integration/                 # Testy integracyjne
│   ├── ui/                          # Testy interfejsu użytkownika
│   └── unit/                        # Testy jednostkowe
│
└── dist/                            # Katalog wyjściowy po zbudowaniu (.exe)
```

---

## Instalacja i uruchomienie

### Wymagania

- Python 3.11 lub nowszy

### Krok po kroku

```bash
# 1. Sklonuj repozytorium
git clone <repo-url>
cd desktop-alkozon

# 2. Utwórz wirtualne środowisko
python -m venv venv
# Windows: venv\Scripts\activate
# Linux/Mac: source venv/bin/activate

# 3. Zainstaluj zależności (w tym deweloperskie)
pip install -e ".[dev]"

# 4. Skonfiguruj zmienne środowiskowe
# Skopiuj .env.example do .env i uzupełnij dane
copy .env.example .env       # Windows
# cp .env.example .env       # Linux/Mac

# 5. Uruchom aplikację w trybie deweloperskim
python main.py
```

### Zmienne środowiskowe (.env)

| Zmienna | Opis | Domyślnie |
|---|---|---|
| `API_BASE_URL` | Adres URL backendowego API | `https://api-alcozon.onrender.com` |
| `DEMO_MODE` | Włączenie trybu demo (`true`/`false`) | `false` |
| `LOCKOUT_SECURITY_CODE` | Kod bezpieczeństwa do odblokowania konta | – |

---

## Budowanie wersji produkcyjnej

```bash
python build.py
```

Proces budowania:

1. Czyszczenie artefaktów poprzedniej kompilacji
2. Kopiowanie pakietu `src/desktop_alkozon` do katalogu roboczego
3. Obfuskacja kodu źródłowego przy użyciu **PyArmor**
4. Wstrzyknięcie konfiguracji czasu budowania (hash kodu bezpieczeństwa, URL API)
5. Pakowanie za pomocą **PyInstaller** do samodzielnego pliku `.exe` w `dist/Alkozon/`
6. Czyszczenie plików tymczasowych

Gotowy plik wykonywalny znajduje się w katalogu `dist/Alkozon/`.

---

## Skrypty i komendy

| Komenda | Opis |
|---|---|
| `python main.py` | Uruchomienie aplikacji w trybie deweloperskim |
| `python build.py` | Budowanie wersji produkcyjnej |
| `pytest tests/` | Uruchomienie wszystkich testów |
| `pytest tests/unit/ -v` | Testy jednostkowe |
| `pytest tests/integration/ -v` | Testy integracyjne |
| `pytest tests/api/ -v` | Testy klienta API |
| `pytest tests/feature/ -v` | Testy funkcjonalne |
| `pytest tests/ui/ -v` | Testy interfejsu użytkownika |
| `black src/ tests/` | Formatowanie kodu (Black) |
| `isort src/ tests/` | Sortowanie importów (isort) |
| `ruff check src/ tests/` | Lintowanie kodu (Ruff) |
| `pre-commit run --all-files` | Uruchomienie wszystkich hooków pre-commit |

---

## Testy

Projekt zawiera 5 zestawów testów:

- **Unit** – testy jednostkowe poszczególnych modułów
- **Integration** – testy integracyjne (baza danych, synchronizacja)
- **API** – testy klienta HTTP i komunikacji z backendem
- **Feature** – testy funkcjonalne (scenariusze biznesowe)
- **UI** – testy interfejsu użytkownika

Testy są automatycznie uruchamiane w **GitHub Actions** (CI) na każdy push i pull request – obejmują lintowanie (Black, isort, Ruff), a następnie wszystkie 5 zestawów testów równolegle.

---

"Szczegółowy opis warstw, przepływu danych i działania trybu offline znajduje się w pliku ARCHITECTURE.md."
