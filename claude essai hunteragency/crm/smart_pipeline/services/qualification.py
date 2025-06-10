"""
<� CRM SMART PIPELINE - SERVICE DE QUALIFICATION
Qualification automatique et scoring des leads
"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import aiosqlite
from ..models.schemas import Lead, QualificationCriteria, LeadScoreBreakdown

class LeadQualificationService:
    """
    Service de qualification automatique des leads
    Int�gre scoring IA + crit�res BANT + analyse comportementale
    """
    
    def __init__(self):
        self.bant_weights = {
            'budget': 0.30,
            'authority': 0.25, 
            'need': 0.25,
            'timeline': 0.20
        }
        
        self.scoring_thresholds = {
            'hot': 8.0,
            'warm': 6.0,
            'cold': 4.0
        }
    
    async def qualify_lead(self, lead_id: int) -> Dict[str, Any]:
        """
        Qualification compl�te d'un lead
        Retourne le score, la classification et les recommandations
        """
        try:
            # 1. R�cup�rer les donn�es du lead
            lead_data = await self._get_lead_data(lead_id)
            if not lead_data:
                raise ValueError(f"Lead {lead_id} non trouv�")
            
            # 2. Analyse BANT (Budget, Authority, Need, Timeline)
            bant_score = await self._analyze_bant_criteria(lead_data)
            
            # 3. Scoring comportemental
            behavioral_score = await self._analyze_behavioral_data(lead_id)
            
            # 4. Scoring d�mographique/firmographique
            demographic_score = await self._analyze_demographic_fit(lead_data)
            
            # 5. Engagement scoring
            engagement_score = await self._analyze_engagement_level(lead_id)
            
            # 6. Score final pond�r�
            final_score = self._calculate_weighted_score(
                bant_score, behavioral_score, demographic_score, engagement_score
            )
            
            # 7. Classification et recommandations
            classification = self._classify_lead(final_score)
            recommendations = await self._generate_recommendations(lead_data, final_score, classification)
            
            # 8. Mise � jour en base
            await self._update_lead_qualification(lead_id, final_score, classification)
            
            return {
                'lead_id': lead_id,
                'qualification_score': round(final_score, 2),
                'classification': classification,
                'score_breakdown': {
                    'bant_score': round(bant_score, 2),
                    'behavioral_score': round(behavioral_score, 2),
                    'demographic_score': round(demographic_score, 2),
                    'engagement_score': round(engagement_score, 2)
                },
                'recommendations': recommendations,
                'qualified_at': datetime.now().isoformat(),
                'next_actions': self._suggest_next_actions(classification, lead_data)
            }
            
        except Exception as e:
            print(f"L Erreur qualification lead {lead_id}: {e}")
            return self._default_qualification_result(lead_id)
    
    async def _get_lead_data(self, lead_id: int) -> Optional[Dict]:
        """R�cup�rer les donn�es compl�tes du lead"""
        try:
            async with aiosqlite.connect("hunter_agency.db") as db:
                cursor = await db.execute("""
                    SELECT * FROM pipeline_leads WHERE id = ?
                """, (lead_id,))
                row = await cursor.fetchone()
                
                if row:
                    columns = [desc[0] for desc in cursor.description]
                    return dict(zip(columns, row))
                return None
        except Exception as e:
            print(f"Erreur r�cup�ration lead {lead_id}: {e}")
            return None
    
    async def _analyze_bant_criteria(self, lead_data: Dict) -> float:
        """
        Analyse des crit�res BANT (Budget, Authority, Need, Timeline)
        Score sur 10 bas� sur les informations disponibles
        """
        score = 0.0
        
        # Budget - bas� sur budget_range et company size
        budget_score = 0.0
        budget_range = lead_data.get('budget_range', '')
        if budget_range:
            if 'enterprise' in budget_range.lower() or '50k+' in budget_range:
                budget_score = 10.0
            elif 'mid-market' in budget_range.lower() or '10k-50k' in budget_range:
                budget_score = 7.5
            elif 'small' in budget_range.lower() or '1k-10k' in budget_range:
                budget_score = 5.0
            else:
                budget_score = 2.5
        
        # Authority - bas� sur le titre/fonction
        authority_score = 0.0
        company = lead_data.get('company', '')
        first_name = lead_data.get('first_name', '')
        
        # Indicateurs d'autorit� dans les donn�es
        authority_indicators = ['ceo', 'founder', 'director', 'vp', 'head', 'manager', 'owner']
        notes = lead_data.get('notes', '').lower()
        
        if any(indicator in notes for indicator in authority_indicators):
            authority_score = 8.0
        elif company:  # A une entreprise = potentiellement d�cideur
            authority_score = 6.0
        else:
            authority_score = 3.0
        
        # Need - bas� sur l'industrie et les notes
        need_score = 0.0
        industry = lead_data.get('industry', '').lower()
        
        # Industries � fort besoin pour nos services
        high_need_industries = ['saas', 'ecommerce', 'agency', 'consulting', 'fintech', 'marketing']
        if any(ind in industry for ind in high_need_industries):
            need_score = 8.0
        elif industry:
            need_score = 5.0
        else:
            need_score = 3.0
        
        # Timeline - bas� sur l'urgence per�ue
        timeline_score = 5.0  # Score neutre par d�faut
        if 'urgent' in notes or 'asap' in notes:
            timeline_score = 9.0
        elif 'soon' in notes or 'quick' in notes:
            timeline_score = 7.0
        
        # Score BANT pond�r�
        weighted_score = (
            budget_score * self.bant_weights['budget'] +
            authority_score * self.bant_weights['authority'] +
            need_score * self.bant_weights['need'] +
            timeline_score * self.bant_weights['timeline']
        )
        
        return min(weighted_score, 10.0)
    
    async def _analyze_behavioral_data(self, lead_id: int) -> float:
        """
        Analyse comportementale bas�e sur les interactions
        """
        try:
            async with aiosqlite.connect("hunter_agency.db") as db:
                # Historique des emails
                cursor = await db.execute("""
                    SELECT COUNT(*) as email_count,
                           COUNT(CASE WHEN opened_at IS NOT NULL THEN 1 END) as opens,
                           COUNT(CASE WHEN clicked_at IS NOT NULL THEN 1 END) as clicks
                    FROM email_campaigns 
                    WHERE lead_id = (SELECT id FROM leads WHERE id = ?)
                """, (lead_id,))
                email_data = await cursor.fetchone()
                
                if email_data and email_data[0] > 0:  # A re�u des emails
                    email_count, opens, clicks = email_data
                    
                    # Scoring bas� sur l'engagement email
                    engagement_rate = (opens + clicks * 2) / email_count
                    behavioral_score = min(engagement_rate * 5, 10.0)
                    
                    # Bonus pour les clics (plus engag�)
                    if clicks > 0:
                        behavioral_score += 2.0
                    
                    return min(behavioral_score, 10.0)
                else:
                    return 5.0  # Score neutre si pas d'historique
                    
        except Exception as e:
            print(f"Erreur analyse comportementale: {e}")
            return 5.0
    
    async def _analyze_demographic_fit(self, lead_data: Dict) -> float:
        """
        Analyse d�mographique et firmographique
        """
        score = 5.0  # Score de base
        
        # Qualit� de l'email
        email = lead_data.get('email', '')
        if email:
            domain = email.split('@')[1].lower() if '@' in email else ''
            
            # Emails professionnels = meilleur fit
            free_domains = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com']
            if domain and domain not in free_domains:
                score += 2.0
            
            # Domaines d'entreprise connus
            if any(indicator in domain for indicator in ['.co', '.inc', '.llc', '.corp']):
                score += 1.0
        
        # Pr�sence d'informations compl�tes
        completeness_score = 0
        fields_to_check = ['first_name', 'company', 'phone', 'industry']
        
        for field in fields_to_check:
            if lead_data.get(field):
                completeness_score += 0.5
        
        score += completeness_score
        
        # Source de qualit�
        source = lead_data.get('source', '').lower()
        source_scores = {
            'referral': 2.0,
            'linkedin': 1.5,
            'website': 1.0,
            'webinar': 1.5,
            'manual': 0.5
        }
        
        score += source_scores.get(source, 0)
        
        return min(score, 10.0)
    
    async def _analyze_engagement_level(self, lead_id: int) -> float:
        """
        Analyse du niveau d'engagement global
        """
        try:
            async with aiosqlite.connect("hunter_agency.db") as db:
                # Derni�re activit�
                cursor = await db.execute("""
                    SELECT last_contact FROM pipeline_leads WHERE id = ?
                """, (lead_id,))
                result = await cursor.fetchone()
                
                if result and result[0]:
                    last_contact = datetime.fromisoformat(result[0])
                    days_since_contact = (datetime.now() - last_contact).days
                    
                    # Score bas� sur la r�cence du contact
                    if days_since_contact <= 7:
                        return 9.0  # Tr�s r�cent
                    elif days_since_contact <= 30:
                        return 7.0  # R�cent
                    elif days_since_contact <= 90:
                        return 5.0  # Moyen
                    else:
                        return 3.0  # Ancien
                else:
                    return 6.0  # Nouveau lead, potentiel moyen
                    
        except Exception as e:
            print(f"Erreur analyse engagement: {e}")
            return 5.0
    
    def _calculate_weighted_score(self, bant: float, behavioral: float, demographic: float, engagement: float) -> float:
        """
        Calcul du score final pond�r�
        """
        weights = {
            'bant': 0.40,
            'behavioral': 0.25,
            'demographic': 0.20,
            'engagement': 0.15
        }
        
        final_score = (
            bant * weights['bant'] +
            behavioral * weights['behavioral'] +
            demographic * weights['demographic'] +
            engagement * weights['engagement']
        )
        
        return min(final_score, 10.0)
    
    def _classify_lead(self, score: float) -> str:
        """Classification du lead selon le score"""
        if score >= self.scoring_thresholds['hot']:
            return 'HOT'
        elif score >= self.scoring_thresholds['warm']:
            return 'WARM'
        elif score >= self.scoring_thresholds['cold']:
            return 'COLD'
        else:
            return 'UNQUALIFIED'
    
    async def _generate_recommendations(self, lead_data: Dict, score: float, classification: str) -> List[str]:
        """
        G�n�rer des recommandations personnalis�es
        """
        recommendations = []
        
        if classification == 'HOT':
            recommendations.extend([
                "Contacter imm�diatement par t�l�phone",
                "Proposer un appel de d�couverte dans les 24h",
                "Pr�parer une proposition personnalis�e"
            ])
        elif classification == 'WARM':
            recommendations.extend([
                "Lancer une s�quence email personnalis�e",
                "Programmer un suivi dans 3-5 jours",
                "Envoyer du contenu �ducatif pertinent"
            ])
        elif classification == 'COLD':
            recommendations.extend([
                "Ajouter � la campagne de nurturing",
                "Envoyer du contenu de valeur r�guli�rement",
                "Requalifier dans 30 jours"
            ])
        else:
            recommendations.extend([
                "Enrichir les donn�es du lead",
                "V�rifier la validit� des informations",
                "Consid�rer l'archivage si pas de r�ponse"
            ])
        
        # Recommandations sp�cifiques bas�es sur les donn�es
        if not lead_data.get('phone'):
            recommendations.append("Rechercher le num�ro de t�l�phone")
        
        if not lead_data.get('company'):
            recommendations.append("Identifier l'entreprise du prospect")
        
        return recommendations
    
    def _suggest_next_actions(self, classification: str, lead_data: Dict) -> List[Dict[str, Any]]:
        """
        Suggerer les prochaines actions concr�tes
        """
        actions = []
        
        if classification == 'HOT':
            actions.extend([
                {
                    "action": "CALL",
                    "priority": "HIGH",
                    "due_date": (datetime.now() + timedelta(hours=2)).isoformat(),
                    "description": "Appel de d�couverte urgent"
                },
                {
                    "action": "EMAIL",
                    "priority": "HIGH", 
                    "due_date": (datetime.now() + timedelta(hours=1)).isoformat(),
                    "description": "Email de prise de contact personnalis�"
                }
            ])
        
        elif classification == 'WARM':
            actions.extend([
                {
                    "action": "EMAIL_SEQUENCE",
                    "priority": "MEDIUM",
                    "due_date": (datetime.now() + timedelta(days=1)).isoformat(),
                    "description": "D�marrer s�quence email 5 �tapes"
                },
                {
                    "action": "LINKEDIN_CONNECT",
                    "priority": "LOW",
                    "due_date": (datetime.now() + timedelta(days=2)).isoformat(),
                    "description": "Connexion LinkedIn avec message personnalis�"
                }
            ])
        
        elif classification == 'COLD':
            actions.append({
                "action": "NURTURE_CAMPAIGN",
                "priority": "LOW",
                "due_date": (datetime.now() + timedelta(days=7)).isoformat(),
                "description": "Ajouter � la campagne de nurturing mensuelle"
            })
        
        return actions
    
    async def _update_lead_qualification(self, lead_id: int, score: float, classification: str):
        """
        Mettre � jour les informations de qualification en base
        """
        try:
            async with aiosqlite.connect("hunter_agency.db") as db:
                await db.execute("""
                    UPDATE pipeline_leads 
                    SET score = ?, status = ?, updated_at = ?
                    WHERE id = ?
                """, (score, classification.lower(), datetime.now(), lead_id))
                await db.commit()
        except Exception as e:
            print(f"Erreur mise � jour qualification: {e}")
    
    def _default_qualification_result(self, lead_id: int) -> Dict[str, Any]:
        """R�sultat par d�faut en cas d'erreur"""
        return {
            'lead_id': lead_id,
            'qualification_score': 5.0,
            'classification': 'UNKNOWN',
            'score_breakdown': {
                'bant_score': 5.0,
                'behavioral_score': 5.0,
                'demographic_score': 5.0,
                'engagement_score': 5.0
            },
            'recommendations': ["Revoir manuellement ce lead"],
            'qualified_at': datetime.now().isoformat(),
            'next_actions': [{
                "action": "MANUAL_REVIEW",
                "priority": "MEDIUM",
                "due_date": (datetime.now() + timedelta(days=1)).isoformat(),
                "description": "Qualification manuelle n�cessaire"
            }]
        }
    
    async def bulk_qualify_leads(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Qualification en lot des leads non qualifi�s
        """
        results = []
        
        try:
            async with aiosqlite.connect("hunter_agency.db") as db:
                cursor = await db.execute("""
                    SELECT id FROM pipeline_leads 
                    WHERE score IS NULL OR score = 0
                    ORDER BY created_at DESC 
                    LIMIT ?
                """, (limit,))
                
                lead_ids = [row[0] for row in await cursor.fetchall()]
                
                for lead_id in lead_ids:
                    result = await self.qualify_lead(lead_id)
                    results.append(result)
                    
                    # Pause entre chaque qualification
                    await asyncio.sleep(0.1)
                
                print(f" {len(results)} leads qualifi�s avec succ�s")
                return results
                
        except Exception as e:
            print(f"L Erreur qualification en lot: {e}")
            return results
