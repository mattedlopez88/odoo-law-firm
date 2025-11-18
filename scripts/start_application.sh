#!/bin/bash
echo "=== Starting Application ==="
cd /opt/odoo-law-firm/docker

# Detener y levantar contenedores
sudo docker-compose down
sudo docker-compose up -d

echo "=== Application Started Successfully ==="
echo "Containers running:"
sudo docker ps