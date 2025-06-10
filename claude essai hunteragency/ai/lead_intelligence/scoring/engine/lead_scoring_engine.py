"""
🧠 IA SCORING ENGINE - Hunter Agency v3.0
Score automatique de 1-10 pour 400+ profils/jour
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, Any, Optional

class LeadScoringEngine:
    def __init__(self):
        self.weights = {
            'algorithmic': 0.5,
            'ai_contextual': 0.3, 
            'ml_prediction': 0.2
        }
        print("🧠 IA Scoring Engine initialisé")
        
    async def score_profile(self, profile) -> Dict[str, Any]:
        """🎯 FONCTION PRINCIPALE : Scorer un profil"""
        try:
            print(f"🔍 Scoring du profil {getattr(profile, 'id', 'unknown')}")
            
            # 1. Scoring algorithmique (règles business)
            algo_score = self._algorithmic_scoring(profile)
            
            # 2. Scoring IA contextuel (analyse sémantique)
            ai_score = await self._ai_contextual_scoring(profile)
            
            # 3. Score ML (prédictif - placeholder pour l'instant)
            ml_score = 5.0
            
            # 4. Score final pondéré
            final_score = (
                algo_score * self.weights['algorithmic'] +
                ai_score * self.weights['ai_contextual'] +
                ml_score * self.weights['ml_prediction']
            )
            
            # 5. Classification et métadonnées
            classification = self._classify_lead(final_score)
            next_action = self._suggest_next_action(classification)
            estimated_value = self._estimate_value(final_score, profile)
            
            result = {
                'profile_id': getattr(profile, 'id', 0),
                'final_score': round(final_score, 2),
                'classification': classification,
                'confidence': self._calculate_confidence(algo_score, ai_score),
                'scores_breakdown': {
                    'algorithmic': round(algo_score, 2),
                    'ai_contextual': round(ai_score, 2),
                    'ml_prediction': round(ml_score, 2)
                },
                'next_action': next_action,
                'estimated_value': estimated_value,
                'scored_at': datetime.utcnow().isoformat(),
                'scoring_method': 'hybrid_ai_algorithm'
            }
            
            print(f"✅ Profil scoré: {final_score}/10 ({classification})")
            return result
            
        except Exception as e:
            print(f"❌ Erreur scoring: {e}")
            return self._default_score_result(getattr(profile, 'id', 0))
    
    def _algorithmic_scoring(self, profile) -> float:
        """🔢 SCORING ALGORITHMIQUE - Règles business"""
        score = 0.0
        
        try:
            # Contact Information (40% du score total)
            if getattr(profile, 'email', None):
                if self._is_valid_email(profile.email):
                    score += 2.0  # Email valide
                else:
                    score += 1.0  # Email présent mais suspect
            
            if getattr(profile, 'phone', None):
                if self._is_valid_phone(profile.phone):
                    score += 2.0  # Téléphone valide
                else:
                    score += 1.0  # Téléphone présent
            
            # Social Presence (25% du score)
            social_score = 0
            if getattr(profile, 'instagram_url', None):
                social_score += 1.0
            if getattr(profile, 'onlyfans_url', None):
                social_score += 1.5  # OnlyFans = monetization intent
            if getattr(profile, 'twitter_url', None):
                social_score += 0.5
                
            score += min(social_score, 2.5)
            
            # Content Quality (25% du score)
            description = getattr(profile, 'description', '')
            if description:
                content_score = 0
                desc_length = len(description)
                
                # Score basé sur la longueur
                if desc_length > 200:
                    content_score += 1.0
                elif desc_length > 100:
                    content_score += 0.6
                elif desc_length > 50:
                    content_score += 0.3
                
                # Mots-clés business
                business_keywords = ['serious', 'professional', 'booking', 'available', 'rates', 'outcall', 'incall']
                keyword_count = sum(1 for kw in business_keywords if kw.lower() in description.lower())
                content_score += min(keyword_count * 0.3, 1.5)
                
                score += min(content_score, 2.5)
            
            # Geographic Factor (10% du score)
            location = getattr(profile, 'location', '')
            if location:
                major_cities = ['new york', 'los angeles', 'chicago', 'miami', 'san francisco', 'las vegas']
                if any(city in location.lower() for city in major_cities):
                    score += 1.0
                else:
                    score += 0.5
            
            # Normaliser sur 10
            final_score = min(score, 10.0)
            print(f"📊 Score algorithmique: {final_score}/10")
            return final_score
            
        except Exception as e:
            print(f"❌ Erreur scoring algorithmique: {e}")
            return 5.0
    
    async def _ai_contextual_scoring(self, profile) -> float:
        """🤖 SCORING IA CONTEXTUEL - Analyse sémantique"""
        description = getattr(profile, 'description', '')
        if not description or len(description) < 20:
            return 5.0  # Score neutre si pas assez de contenu
        
        try:
            # Simulation d'analyse IA (remplacer par vraie API OpenAI si clé disponible)
            await asyncio.sleep(0.1)  # Simuler appel API
            
            # Analyse basique des mots-clés pour simulation
            positive_indicators = ['professional', 'serious', 'discreet', 'upscale', 'verified', 'elite']
            negative_indicators = ['cheap', 'quick', 'fast', 'low', 'discount']
            
            positive_count = sum(1 for word in positive_indicators if word in description.lower())
            negative_count = sum(1 for word in negative_indicators if word in description.lower())
            
            # Score basé sur l'analyse
            base_score = 5.0
            base_score += positive_count * 0.8
            base_score -= negative_count * 0.5
            
            # Analyse de la structure du texte
            if len(description.split('.')) > 3:  # Phrases complètes
                base_score += 0.5
            if description.count('!') <= 2:  # Pas trop d'exclamations
                base_score += 0.3
                
            ai_score = max(1.0, min(10.0, base_score))
            print(f"🤖 Score IA contextuel: {ai_score}/10")
            return ai_score
            
        except Exception as e:
            print(f"❌ Erreur scoring IA: {e}")
            return 5.0
    
    def _classify_lead(self, score: float) -> str:
        """Classification du lead selon le score"""
        if score >= 8.0:
            return "HOT"      # Contact immédiat
        elif score >= 6.5:
            return "WARM"     # Séquence email
        elif score >= 4.0:
            return "COLD"     # Nurturing
        else:
            return "TRASH"    # Ignorer
    
    def _suggest_next_action(self, classification: str) -> str:
        """Suggérer la prochaine action"""
        actions = {
            "HOT": "CONTACT_IMMEDIATELY",
            "WARM": "EMAIL_SEQUENCE", 
            "COLD": "NURTURE_CAMPAIGN",
            "TRASH": "DISCARD"
        }
        return actions.get(classification, "MANUAL_REVIEW")
    
    def _estimate_value(self, score: float, profile) -> Dict[str, Any]:
        """Estimer la valeur potentielle du lead"""
        base_value = 100  # Valeur de base
        
        # Multiplier selon le score
        estimated_value = base_value * (score / 5.0)
        
        # Bonus selon les critères
        if getattr(profile, 'onlyfans_url', None):
            estimated_value *= 1.8  # OnlyFans = plus de potentiel
        
        location = getattr(profile, 'location', '')
        if location and any(city in location.lower() for city in ['new york', 'los angeles', 'miami']):
            estimated_value *= 1.4  # Grandes villes = plus de budget
        
        return {
            'estimated_value_usd': round(estimated_value, 2),
            'confidence': 'high' if score >= 7 else 'medium' if score >= 5 else 'low',
            'value_range': {
                'min': round(estimated_value * 0.6, 2),
                'max': round(estimated_value * 2.0, 2)
            }
        }
    
    def _calculate_confidence(self, algo_score: float, ai_score: float) -> float:
        """Calculer la confiance dans le scoring"""
        # Si les scores sont cohérents, confiance élevée
        score_diff = abs(algo_score - ai_score)
        
        if score_diff <= 1.0:
            return 0.95
        elif score_diff <= 2.0:
            return 0.80
        elif score_diff <= 3.0:
            return 0.65
        else:
            return 0.50
    
    def _is_valid_email(self, email: str) -> bool:
        """Validation basique d'email"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    def _is_valid_phone(self, phone: str) -> bool:
        """Validation basique de téléphone"""
        import re
        clean_phone = re.sub(r'[^\d+]', '', phone)
        return len(clean_phone) >= 10
    
    def _default_score_result(self, profile_id: int) -> Dict[str, Any]:
        """Résultat par défaut en cas d'erreur"""
        return {
            'profile_id': profile_id,
            'final_score': 5.0,
            'classification': 'UNKNOWN',
            'confidence': 0.5,
            'scores_breakdown': {
                'algorithmic': 5.0,
                'ai_contextual': 5.0,
                'ml_prediction': 5.0
            },
            'next_action': 'MANUAL_REVIEW',
            'estimated_value': {'estimated_value_usd': 100.0},
            'scored_at': datetime.utcnow().isoformat()
        }
