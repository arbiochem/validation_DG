#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
import socket  # 🔹 Import nécessaire pour get_local_ip

def get_local_ip():
    try:
        # Crée une socket UDP et se connecte à une IP externe
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))  # Google DNS, ne va pas envoyer de données
        ip = s.getsockname()[0]     # Récupère l'IP locale utilisée pour cette connexion
        s.close()
        return ip
    except Exception as e:
        return f"Erreur : {e}"

def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'validation_DG.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    local_ip = get_local_ip()
    port = "8000"
    print(f"Lancement de Django sur http://{local_ip}:{port}/")
    import sys
    sys.argv += [f"{local_ip}:{port}"] 
    main()
