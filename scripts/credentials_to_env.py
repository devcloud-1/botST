"""
Este script lee tu google_credentials.json y lo convierte en una
variable de entorno GOOGLE_CREDENTIALS_JSON para Railway.

No necesitas Python local — este script corre en Railway al iniciar.
"""
import json
import os
import base64

CREDENTIALS_PATH = "config/google_credentials.json"


def load_credentials_from_env():
    """
    Si no existe el archivo de credenciales pero sí la variable de entorno,
    reconstruye el archivo. Llamar al inicio de la app.
    """
    if os.path.exists(CREDENTIALS_PATH):
        return  # Ya existe, nada que hacer

    env_value = os.environ.get("GOOGLE_CREDENTIALS_JSON")
    if not env_value:
        return  # No hay variable de entorno tampoco

    os.makedirs("config", exist_ok=True)
    try:
        # Intentar decodificar base64
        try:
            decoded = base64.b64decode(env_value).decode("utf-8")
            data = json.loads(decoded)
        except Exception:
            # Si no es base64, asumir JSON directo
            data = json.loads(env_value)

        with open(CREDENTIALS_PATH, "w") as f:
            json.dump(data, f)

        print(f"✅ google_credentials.json reconstruido desde variable de entorno")
    except Exception as e:
        print(f"⚠️  No se pudo reconstruir credentials desde env: {e}")


def print_env_value(credentials_path: str = CREDENTIALS_PATH):
    """
    Lee el credentials.json y muestra el valor listo para pegar en Railway.
    Ejecutar localmente si tienes el archivo.
    """
    if not os.path.exists(credentials_path):
        print(f"❌ No se encontró {credentials_path}")
        return

    with open(credentials_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("utf-8")

    print("\n" + "="*60)
    print("Variable de entorno para Railway:")
    print("="*60)
    print(f"Nombre:  GOOGLE_CREDENTIALS_JSON")
    print(f"Valor:   {encoded}")
    print("="*60)
    print("\nPega esto en Railway → tu proyecto → Variables → Nueva variable\n")


if __name__ == "__main__":
    print_env_value()
