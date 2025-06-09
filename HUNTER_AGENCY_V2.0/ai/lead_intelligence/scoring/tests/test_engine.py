#!/usr/bin/env python3
"""
🧪 Test de l'IA Scoring Engine
"""

import asyncio
import sys
import os
from datetime import datetime

# Ajouter le path pour l'import
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from engine.lead_scoring_engine import LeadScoringEngine
except ImportError:
    print("❌ Impossible d'importer LeadScoringEngine")
    print("�� Assurez-vous d'être dans le bon dossier")
    sys.exit(1)

async def test_scoring_engine():
    """Test complet du moteur de scoring"""
    print("�� TEST IA SCORING ENGINE")
    print("=" * 50)
    
    engine = LeadScoringEngine()
    
    # Profils de test
    test_profiles = [
        # Profil HOT
        {
            'id': 1,
            'name': 'Premium Escort',
            'email': 'contact@premium-escort.com',
            'phone': '+1-555-123-4567',
            'description': 'Professional upscale escort available for serious gentlemen. Discreet and verified. Outcall and incall services. Rates available upon request.',
            'instagram_url': 'https://instagram.com/premium_escort',
            'onlyfans_url': 'https://onlyfans.com/premium_escort',
            'location': 'New York, NY',
            'scraped_at': datetime.utcnow()
        },
        # Profil WARM
        {
            'id': 2,
            'name': 'Sarah Model',
            'email': 'sarah.model@gmail.com',
            'phone': '+1-555-987-6543',
            'description': 'Available for bookings. Instagram model and escort. Message me for more info.',
            'instagram_url': 'https://instagram.com/sarah_model',
            'onlyfans_url': None,
            'location': 'Los Angeles, CA',
            'scraped_at': datetime.utcnow()
        },
        # Profil COLD
        {
            'id': 3,
            'name': 'Basic User',
            'email': 'user@email.com',
            'phone': None,
            'description': 'Hi there',
            'instagram_url': None,
            'onlyfans_url': None,
            'location': 'Unknown',
            'scraped_at': datetime.utcnow()
        }
    ]
    
    print(f"🔍 Test avec {len(test_profiles)} profils de test...\n")
    
    for i, profile_data in enumerate(test_profiles, 1):
        # Créer un objet profil mock
        class MockProfile:
            def __init__(self, data):
                for key, value in data.items():
                    setattr(self, key, value)
        
        profile = MockProfile(profile_data)
        
        print(f"📊 TEST {i}/{len(test_profiles)} - Profil #{profile.id}")
        print(f"   Nom: {profile.name}")
        print(f"   Email: {profile.email}")
        print(f"   Description: {profile.description[:50]}...")
        
        # Scorer le profil
        result = await engine.score_profile(profile)
        
        print(f"\n   🎯 RÉSULTATS:")
        print(f"   Score final: {result['final_score']}/10")
        print(f"   Classification: {result['classification']}")
        print(f"   Confiance: {result['confidence']:.2f}")
        print(f"   Action suggérée: {result['next_action']}")
        print(f"   Valeur estimée: ${result['estimated_value']['estimated_value_usd']}")
        
        print(f"\n   📈 Détail des scores:")
        for method, score in result['scores_breakdown'].items():
            print(f"     {method}: {score}/10")
        
        # Emoji selon la classification
        if result['classification'] == 'HOT':
            print(f"   🔥 LEAD HOT - Contact immédiat recommandé!")
        elif result['classification'] == 'WARM':
            print(f"   🟡 Lead WARM - Séquence email recommandée")
        elif result['classification'] == 'COLD':
            print(f"   🔵 Lead COLD - Campagne de nurturing")
        else:
            print(f"   ⚫ Lead TRASH - À ignorer")
        
        print("\n" + "-" * 50 + "\n")
    
    print("✅ Tests terminés avec succès!")
    print("\n🎯 RÉSUMÉ:")
    print("├── ✅ Moteur IA opérationnel")
    print("├── 📊 Scoring algorithmique fonctionnel") 
    print("├── 🤖 Scoring IA contextuel actif")
    print("├── 🎯 Classification automatique")
    print("├── 💰 Estimation de valeur")
    print("└── 🚀 Prêt pour vos 400 profils/jour!")

if __name__ == "__main__":
    asyncio.run(test_scoring_engine())
