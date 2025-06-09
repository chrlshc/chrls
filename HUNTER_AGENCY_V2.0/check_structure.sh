#!/bin/bash
echo "📍 Position actuelle:"
pwd
echo ""
echo "�� Structure principale:"
ls -la | grep -E "^d"
echo ""
echo "🚀 Services actifs:"
docker-compose -f docker-compose.business.yml ps
echo ""
echo "🌐 URLs disponibles:"
echo "- Grafana: http://localhost:3001"
echo "- MailHog: http://localhost:8025"
