#!/bin/bash
echo "=== AfterInstall Hook Started ==="
cd /opt/odoo-law-firm

# Configurar permisos
chmod +x scripts/*.sh
echo "Scripts made executable"

# Crear directorios necesarios
mkdir -p logs
mkdir -p temp

echo "=== AfterInstall Hook Completed ==="
