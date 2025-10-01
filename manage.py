#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    # Detectar automáticamente el entorno
    import os
    from pathlib import Path
    
    settings_dir = Path(__file__).parent / 'motorcycle_world'
    
    # Prioridad de configuraciones por entorno
    if (settings_dir / 'settings_local.py').exists():
        settings_module = 'motorcycle_world.settings_local'
    elif (settings_dir / 'settings_production.py').exists():
        settings_module = 'motorcycle_world.settings_production'
    elif (settings_dir / 'settings_development.py').exists():
        settings_module = 'motorcycle_world.settings_development'
    else:
        settings_module = 'motorcycle_world.settings'
    
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', settings_module)
    
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
    main()
