import os
import shutil
import subprocess
import sys


def build_with_obfuscation():
    print("Rozpoczynam proces budowania...\n")
    print("1. Czyszczenie starych katalogów...")
    shutil.rmtree("build", ignore_errors=True)
    shutil.rmtree("dist/Alkozon", ignore_errors=True)
    shutil.rmtree("obfuscated_src", ignore_errors=True)
    print("2. Szyfrowanie kodu źródłowego (PyArmor)...")
    try:
        subprocess.run(
            ["pyarmor", "gen", "-O", "obfuscated_src", "main.py", "desktop_alkozon"],
            check=True,
        )
    except subprocess.CalledProcessError:
        print("Błąd: Obfuskacja kodu nie powiodła się.")
        sys.exit(1)

    print("3. Pakowanie do pliku wykonywalnego (PyInstaller)...")
    try:
        # Budujemy z pliku .spec
        subprocess.run(["pyinstaller", "Alkozon.spec", "--clean", "-y"], check=True)
    except subprocess.CalledProcessError:
        print("Błąd: Budowanie paczki przez PyInstaller nie powiodło się.")
        sys.exit(1)

    # 4. Sprzątanie
    print("4. Sprzątanie plików tymczasowych...")
    shutil.rmtree("build", ignore_errors=True)
    shutil.rmtree("obfuscated_src", ignore_errors=True)

    print("\nGotowe! Plik wykonywalny znajduje się w katalogu 'dist/Alkozon/'.")


if __name__ == "__main__":
    # Sprawdzenie, czy jesteśmy w dobrym miejscu
    if not os.path.exists("main.py"):
        print(
            "Błąd: Uruchom ten skrypt z głównego katalogu projektu (tam gdzie jest main.py)."
        )
        sys.exit(1)
    build_with_obfuscation()
