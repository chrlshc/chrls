#!/usr/bin/env python3
"""
Test simple du module IA Hunter Agency
"""

import sys
import os
sys.path.append('.')

def test_ai_basic():
    try:
        from src.ai.features.profile_features import ProfileFeatureExtractor
        from src.ai.models.scoring_models import ProfileScoringModel
        
        print("🧠 Test du module IA Hunter Agency")
        
        # Test feature extractor
        extractor = ProfileFeatureExtractor()
        test_profile = {
            'name': 'Test User',
            'email': 'test@example.com',
            'phone': '+1234567890',
            'age': 25,
            'instagram_url': 'https://instagram.com/test'
        }
        
        features = extractor.extract_features(test_profile)
        print(f"✅ Features extraites: {len(features)} caractéristiques")
        
        # Test modèle de scoring
        model = ProfileScoringModel()
        scores = model.predict_profile_quality(test_profile)
        
        print(f"🎯 Score global: {scores['overall_score']:.1f}/100")
        print(f"🎯 Qualité: {scores['quality_score']:.3f}")
        print(f"🎯 Confiance: {scores['confidence']:.3f}")
        
        print("\n✅ Module IA fonctionnel!")
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

if __name__ == '__main__':
    test_ai_basic()
