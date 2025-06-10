# 🔥 Hunter Agency V2.2 - Business Automation Ecosystem

**Empire SaaS d'acquisition client automatisé avec CRM intégré et automation email avancée**

[![Version](https://img.shields.io/badge/version-2.2.0-blue.svg)](https://github.com/hunter-agency/v2.2)
[![Python](https://img.shields.io/badge/python-3.11+-green.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/fastapi-0.104+-red.svg)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/license-MIT-yellow.svg)](LICENSE)

## 🌟 Fonctionnalités Principales

### 🤖 Automation Email Intelligente
- **Séquences personnalisées** : Templates adaptatifs par industrie
- **Scoring automatique** : IA intégrée pour qualifier les leads
- **Suivi en temps réel** : Analytics détaillés des performances
- **A/B Testing** : Optimisation continue des campagnes

### 🎯 CRM Smart Pipeline
- **Qualification automatique** : Scoring BANT + IA comportementale
- **Gestion d'opportunités** : Suivi complet du pipeline commercial
- **Prédiction de revenus** : Projections basées sur les probabilités
- **Analytics avancés** : Dashboards temps réel

### 📊 Dashboard Business Intelligence
- **Métriques en temps réel** : KPIs et conversions live
- **Visualisations avancées** : Graphiques et funnels interactifs
- **Rapports automatisés** : Insights business quotidiens
- **Intégration multi-sources** : Données unifiées

## 🚀 Installation & Démarrage Rapide

### Prérequis
- Python 3.11+
- 4GB RAM minimum
- 2GB espace disque

### Installation

```bash
# 1. Cloner le projet
git clone https://github.com/hunter-agency/v2.2.git
cd hunter-agency-v2.2

# 2. Installer les dépendances
pip install -r requirements.txt

# 3. Configuration
cp .env.example .env
# Éditer .env avec vos clés API

# 4. Démarrage avec le launcher
python start.py
```

### Démarrage Manuel

```bash
# Application principale (Port 8001)
python main.py

# Dashboard (Port 8000)
cd dashboard && python main.py
```

## 🔧 Configuration

### Variables d'Environnement (.env)

```bash
# Email
SENDGRID_API_KEY=votre_cle_sendgrid
SENDGRID_FROM_EMAIL=contact@votre-domaine.com

# Base de données
DATABASE_URL=sqlite+aiosqlite:///./hunter_agency.db

# API
SECRET_KEY=votre_cle_secrete_super_forte
JWT_SECRET_KEY=votre_jwt_secret

# IA (Optionnel)
OPENAI_API_KEY=votre_cle_openai
ANTHROPIC_API_KEY=votre_cle_anthropic

# Monitoring
PROMETHEUS_ENABLED=true
```

## 📡 API Endpoints

### 🔥 Application Principale (Port 8001)

```bash
# Santé
GET    /health

# Leads & Email
POST   /leads                    # Créer un lead
GET    /sequences/analytics      # Analytics sequences
POST   /webhooks/sendgrid       # Webhook SendGrid

# CRM Pipeline
POST   /api/pipeline/leads       # Créer lead CRM
GET    /api/pipeline/leads       # Lister leads
GET    /api/pipeline/analytics   # Analytics pipeline
POST   /api/pipeline/opportunities # Créer opportunité
```

### 📊 Dashboard API (Port 8000)

```bash
# Dashboard
GET    /api/overview            # Stats générales
GET    /api/activity            # Activité récente
GET    /api/charts              # Données graphiques
GET    /api/funnel              # Funnel conversion
GET    /api/sequences/performance # Performance séquences
```

## 📈 Architecture Technique

### Stack Technologique
- **Backend** : FastAPI + Async SQLite
- **Email** : SendGrid + Templates dynamiques
- **Scheduling** : APScheduler async
- **Monitoring** : Prometheus + Structlog
- **Database** : SQLite avec optimisations WAL
- **Deployment** : Docker + Uvicorn

### Structure Projet

```
hunter-agency-v2.2/
├── main.py                     # 🔥 Application principale
├── start.py                    # 🚀 Launcher interactif
├── test_main.py               # 🧪 Tests automatisés
├── requirements.txt           # 📦 Dépendances
├── Dockerfile                 # 🐳 Container
├── .env.example              # ⚙️  Config template
│
├── crm/                      # 🎯 Système CRM
│   ├── smart_pipeline/       # Pipeline intelligent
│   │   ├── api/routes.py     # Routes API CRM
│   │   ├── models/schemas.py # Modèles données
│   │   └── services/qualification.py # Service scoring
│   └── email_engine/
│       └── templates/email_templates.py # Templates email
│
├── ai/                       # 🧠 Intelligence artificielle
│   └── lead_intelligence/
│       └── scoring/engine/lead_scoring_engine.py # Moteur scoring IA
│
├── dashboard/               # 📊 Dashboard business
│   ├── main.py             # API dashboard
│   ├── index.html          # Interface web
│   ├── css/dashboard.css   # Styles
│   └── js/dashboard.js     # Logique frontend
│
└── analytics/              # 📈 Business intelligence
    └── business_intelligence/
```

## 🧪 Tests & Qualité

```bash
# Tests automatisés
pytest test_main.py -v

# Validation syntaxe
python -c "import main; print('✅ Syntax OK')"

# Test de démarrage
python start.py
# Choisir option 4 (Check System)
```

## 🔒 Sécurité

- **Validation stricte** : Pydantic schemas
- **Gestion d'erreurs** : Handlers globaux
- **Logs structurés** : Monitoring complet
- **Rate limiting** : Protection API
- **Environment variables** : Secrets sécurisés

## 📊 Monitoring & Analytics

### Métriques Automatiques
- ✅ Emails envoyés par type/statut
- ✅ Temps de traitement des séquences  
- ✅ Taux de conversion lead → opportunité
- ✅ Performance par source de lead
- ✅ Scoring automatique et confiance

### Dashboards Disponibles
- 📈 Vue d'ensemble business
- 📧 Performance email en temps réel
- 🎯 Pipeline commercial détaillé
- 🔄 Funnel de conversion
- 📊 Analytics par source/industrie

## 🚀 Déploiement Production

### Docker (Recommandé)

```bash
# Build
docker build -t hunter-agency:v2.2 .

# Run
docker run -d -p 8001:8001 \
  -e SENDGRID_API_KEY=votre_cle \
  -v $(pwd)/data:/app/data \
  hunter-agency:v2.2
```

### Serveur Direct

```bash
# Installation production
pip install -r requirements.txt
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8001
```

## 📚 Documentation API

- **Swagger UI** : http://localhost:8001/docs
- **ReDoc** : http://localhost:8001/redoc
- **Dashboard** : http://localhost:8000

## 🆘 Support & Troubleshooting

### Problèmes Courants

**Import Error CRM Routes**
```bash
# Solution : Vérifier encodage fichiers
python -c "import crm.smart_pipeline.api.routes"
```

**Database Lock**
```bash
# Solution : Redémarrer application
rm hunter_agency.db && python main.py
```

**SendGrid Errors**
```bash
# Vérifier configuration
curl -X POST "https://api.sendgrid.com/v3/mail/send" \
  -H "Authorization: Bearer $SENDGRID_API_KEY"
```

### Logs & Debug

```bash
# Logs structurés
tail -f *.log | grep ERROR

# Mode debug
export DEBUG=true && python main.py
```

## 🔄 Roadmap V2.3

- [ ] **Multi-tenancy** : Support clients multiples
- [ ] **ML avancé** : Prédictions comportementales
- [ ] **API Gateway** : Rate limiting avancé
- [ ] **Webhooks** : Intégrations tierces
- [ ] **Mobile App** : Application native
- [ ] **White Label** : Personnalisation complète

## 🤝 Contribution

1. Fork le projet
2. Créer une branche feature (`git checkout -b feature/AmazingFeature`)
3. Commit les changements (`git commit -m 'Add AmazingFeature'`)
4. Push vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrir une Pull Request

## 📄 License

Distribué sous licence MIT. Voir `LICENSE` pour plus d'informations.

## 📞 Contact

- **Email** : contact@hunter-agency.com
- **Website** : https://hunter-agency.com
- **GitHub** : https://github.com/hunter-agency

---

**🔥 Hunter Agency V2.2** - Votre empire SaaS est prêt ! 🚀
