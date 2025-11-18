#!/bin/bash
echo "=== Fixing Permissions ==="
cd /opt/odoo-law-firm

# Cambiar propietario de los archivos
sudo chown -R ubuntu:ubuntu .
echo "Permissions fixed"
