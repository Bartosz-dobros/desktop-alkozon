import hashlib
import os
import shutil
import subprocess
import sys

from dotenv import load_dotenv

if sys.stdout.encoding and sys.stdout.encoding.upper() != "UTF-8":
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()


def build_with_obfuscation():
    print("Rozpoczynam proces budowania...\n")
    print("1. Czyszczenie starych katalogów...")
    shutil.rmtree("build", ignore_errors=True)
    shutil.rmtree("dist/Alkozon", ignore_errors=True)
    shutil.rmtree("obfuscated_src", ignore_errors=True)
    shutil.rmtree("desktop_alkozon", ignore_errors=True)
    print("2. Kopiowanie pakietu ze src/...")
    shutil.copytree("src/desktop_alkozon", "desktop_alkozon")
    print("3. Szyfrowanie kodu źródłowego (PyArmor)...")
    try:
        subprocess.run(
            ["pyarmor", "gen", "-O", "obfuscated_src", "main.py", "desktop_alkozon"],
            check=True,
        )
    except subprocess.CalledProcessError:
        shutil.rmtree("desktop_alkozon", ignore_errors=True)
        print("Błąd: Obfuskacja kodu nie powiodła się.")
        sys.exit(1)
    shutil.rmtree("desktop_alkozon", ignore_errors=True)

    print("4. Generowanie konfiguracji budowania...")
    lockout_code = os.environ.get("LOCKOUT_CODE")
    if not lockout_code:
        print("Error: LOCKOUT_CODE environment variable not set!")
        sys.exit(1)
    lockout_hash = hashlib.sha256(lockout_code.encode()).hexdigest()
    api_base_url = os.environ.get("API_BASE_URL")
    if not api_base_url:
        print("Error: API_BASE_URL environment variable not set!")
        sys.exit(1)
    config_path = "obfuscated_src/desktop_alkozon/_build_config.py"
    with open(config_path, "w") as f:
        f.write(f'LOCKOUT_SECURITY_CODE_HASH = "{lockout_hash}"\n')
        f.write(f'API_BASE_URL = "{api_base_url}"\n')
    print(f"   Kod zabezpieczający: {lockout_code} -> hash wygenerowany")
    print(f"   API URL: {api_base_url}")

    print("5. Pakowanie do pliku wykonywalnego (PyInstaller)...")
    try:
        subprocess.run(["pyinstaller", "Alkozon.spec", "--clean", "-y"], check=True)
    except subprocess.CalledProcessError:
        print("Błąd: Budowanie paczki przez PyInstaller nie powiodło się.")
        sys.exit(1)

    print("6. Sprzątanie plików tymczasowych...")
    shutil.rmtree("build", ignore_errors=True)
    shutil.rmtree("obfuscated_src", ignore_errors=True)
    shutil.rmtree("desktop_alkozon", ignore_errors=True)
    print("\nGotowe! Plik wykonywalny znajduje się w katalogu 'dist/Alkozon/'.")


if __name__ == "__main__":
    if not os.path.exists("main.py"):
        print(
            "Błąd: Uruchom ten skrypt z głównego katalogu projektu (tam gdzie jest main.py)."
        )
        sys.exit(1)
    build_with_obfuscation()
