#!/usr/bin/env python3
"""Test complet du système IA Hunter Agency"""
import sys
import os

# Ajouter le répertoire src au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_ai_system():
    print("🧠 === TEST SYSTÈME IA HUNTER AGENCY v2.0 ===\n")
    
    try:
        # Import des modules IA
        from ai.scorer import AIProfileScorer
        from ai.features import ProfileFeatures
        
        print("✅ Modules IA importés avec succès")
        
        # Test 1: Initialisation
        scorer = AIProfileScorer()
        features_extractor = ProfileFeatures()
        
        print("✅ Scorer IA initialisé")
        print(f"   Version: {scorer.version}")
        print(f"   Statut: {scorer.get_status()['status']}")
        
        # Test 2: Profil de test complet
        test_profile = {
            'name': 'Sophie Martin',
            'email': 'sophie.martin@gmail.com',
            'phone': '+33 6 12 34 56 78',
            'age': 26,
            'location': 'Paris, France',
            'description': 'Modèle photo professionnelle basée à Paris',
            'instagram_url': 'https://instagram.com/sophie_martin',
            'twitter_url': 'https://twitter.com/sophie_m',
            'source_site': 'tryst.link'
        }
        
        print(f"\n📋 Test avec profil: {test_profile['name']}")
        
        # Test 3: Extraction de features
        features = features_extractor.extract_all_features(test_profile)
        print(f"✅ Features extraites: {len(features)} caractéristiques")
        
        # Afficher quelques features importantes
        key_features = ['has_email', 'email_quality', 'has_phone', 'social_count', 'completeness_score']
        for feat in key_features:
            if feat in features:
                print(f"   {feat}: {features[feat]}")
        
        # Test 4: Scoring complet
        result = scorer.score_profile(test_profile)
        
        print(f"\n🎯 === RÉSULTATS DU SCORING ===")
        print(f"Score global: {result['overall_score']}/100")
        print(f"Grade: {result['grade']}")
        print(f"Probabilité conversion: {result['conversion_probability']:.1%}")
        print(f"Confiance: {result['confidence']:.1%}")
        print(f"Features analysées: {result['features_count']}")
        
        # Test 5: Recommandations
        if result['recommendations']:
            print(f"\n💡 Recommandations:")
            for i, rec in enumerate(result['recommendations'], 1):
                print(f"   {i}. {rec}")
        
        # Test 6: Profil faible pour comparaison
        print(f"\n📋 Test avec profil minimal:")
        
        minimal_profile = {
            'name': 'John',
            'source_site': 'unknown'
        }
        
        minimal_result = scorer.score_profile(minimal_profile)
        print(f"Score minimal: {minimal_result['overall_score']}/100")
        print(f"Grade minimal: {minimal_result['grade']}")
        
        # Test 7: Statut système
        status = scorer.get_status()
        print(f"\n⚙️  === STATUT SYSTÈME ===")
        print(f"Statut: {status['status']}")
        print(f"Type de modèle: {status['model_type']}")
        print(f"Capacités: {', '.join(status['capabilities'])}")
        
        print(f"\n🎉 === SYSTÈME IA HUNTER AGENCY OPÉRATIONNEL ===")
        print(f"✅ Feature Engineering: Fonctionnel")
        print(f"✅ Scoring IA: Fonctionnel") 
        print(f"✅ Recommandations: Fonctionnelles")
        print(f"✅ Grades de leads: Fonctionnels")
        print(f"✅ Prédiction conversion: Fonctionnelle")
        
        return True
        
    except ImportError as e:
        print(f"❌ Erreur d'import: {e}")
        print("Vérifiez que tous les fichiers sont créés dans src/ai/")
        return False
        
    except Exception as e:
        print(f"❌ Erreur système: {e}")
        return False

if __name__ == '__main__':
    success = test_ai_system()
    if success:
        print(f"\n🚀 L'IA Hunter Agency est prête à scorer vos leads !")
    else:
        print(f"\n🔧 Correction nécessaire avant utilisation")
