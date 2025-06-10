#!/usr/bin/env python3
"""
Hunter Agency - Recovery Scripts pour V2.0 existant
Version simplifiée compatible avec le système actuel
"""

import sqlite3
import requests
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

class SimpleRecovery:
    def __init__(self):
        self.db_path = 'hunter_agency.db'
        self.sg_api_key = os.getenv('SENDGRID_API_KEY')
    
    def cleanup_database(self):
        """Nettoie la base de données des emails test"""
        print("🧹 Nettoyage de la base de données...")
        
        if not os.path.exists(self.db_path):
            print(f"❌ Base de données non trouvée: {self.db_path}")
            return {"error": "DB not found"}
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Domaines test à supprimer
        test_domains = [
            'testcompany.com', 'example.com', 'test.com', 'fake.com',
            '10minutemail.com', 'guerrillamail.com', 'tempmail.org'
        ]
        
        total_deleted = 0
        for domain in test_domains:
            cursor.execute('SELECT COUNT(*) FROM leads WHERE email LIKE ?', (f'%@{domain}',))
            count = cursor.fetchone()[0]
            
            if count > 0:
                cursor.execute('DELETE FROM leads WHERE email LIKE ?', (f'%@{domain}',))
                total_deleted += count
                print(f"   ❌ Supprimé {count} emails @{domain}")
        
        # Marquer emails avec bounces comme invalides
        try:
            cursor.execute('''
                UPDATE leads 
                SET status = 'invalid' 
                WHERE id IN (
                    SELECT DISTINCT lead_id 
                    FROM email_campaigns 
                    WHERE status IN ('bounce', 'blocked', 'dropped')
                )
            ''')
            bounced_updated = cursor.rowcount
        except:
            bounced_updated = 0
        
        conn.commit()
        conn.close()
        
        print(f"✅ Nettoyage terminé:")
        print(f"   📧 {total_deleted} emails test supprimés")
        print(f"   🚫 {bounced_updated} emails marqués invalides")
        
        return {"deleted": total_deleted, "marked_invalid": bounced_updated}
    
    def get_metrics(self, days: int = 7):
        """Affiche les métriques système"""
        print(f"📊 Métriques système ({days} derniers jours)...")
        
        if not os.path.exists(self.db_path):
            print(f"❌ Base de données non trouvée: {self.db_path}")
            return
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Métriques générales
        try:
            # Leads
            cursor.execute('SELECT COUNT(*) FROM leads WHERE status = "active"')
            active_leads = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM leads WHERE status = "invalid"')
            invalid_leads = cursor.fetchone()[0]
            
            # Campagnes récentes
            date_limit = datetime.now() - timedelta(days=days)
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_sent,
                    COUNT(CASE WHEN status IN ('bounce', 'blocked', 'dropped') THEN 1 END) as bounces,
                    COUNT(CASE WHEN opened_at IS NOT NULL THEN 1 END) as opens
                FROM email_campaigns 
                WHERE sent_at >= ?
            ''', (date_limit,))
            
            stats = cursor.fetchone()
            total_sent = stats[0] or 1
            
            bounce_rate = (stats[1] / total_sent) * 100
            open_rate = (stats[2] / total_sent) * 100
            
            print(f"\n📈 MÉTRIQUES:")
            print(f"   👥 Leads actifs: {active_leads}")
            print(f"   ❌ Leads invalides: {invalid_leads}")
            print(f"   📧 Emails envoyés: {stats[0]}")
            print(f"   📊 Taux de bounce: {bounce_rate:.1f}%")
            print(f"   👁️ Taux d'ouverture: {open_rate:.1f}%")
            
            # Status réputation
            if bounce_rate < 2:
                print(f"   🎯 Réputation: 🟢 EXCELLENTE")
            elif bounce_rate < 5:
                print(f"   🎯 Réputation: 🟡 ATTENTION")
            else:
                print(f"   🎯 Réputation: 🔴 CRITIQUE")
            
        except Exception as e:
            print(f"❌ Erreur: {e}")
        
        conn.close()
    
    def purge_sendgrid(self, force=False):
        """Purge SendGrid suppressions"""
        if not self.sg_api_key:
            print("❌ SENDGRID_API_KEY non trouvée")
            print("💡 Utilise: export SENDGRID_API_KEY='ton_api_key'")
            return False
        
        print("🧹 Purge SendGrid suppressions...")
        
        headers = {
            'Authorization': f'Bearer {self.sg_api_key}',
            'Content-Type': 'application/json'
        }
        
        suppression_types = [
            ('bounces', 'https://api.sendgrid.com/v3/suppression/bounces'),
            ('blocks', 'https://api.sendgrid.com/v3/suppression/blocks'),
            ('invalid_emails', 'https://api.sendgrid.com/v3/suppression/invalid_emails')
        ]
        
        for name, url in suppression_types:
            try:
                response = requests.get(url, headers=headers)
                if response.status_code == 200:
                    data = response.json()
                    count = len(data) if isinstance(data, list) else 0
                    print(f"   📊 {count} entrées dans {name}")
                    
                    if count > 0:
                        if force:
                            confirm = 'y'
                            print(f"   🤖 Force mode: purging {count} entries from {name}")
                        else:
                            confirm = input(f"❓ Purger {count} entrées de {name}? (y/N): ")
                        
                        if confirm.lower() == 'y':
                            delete_response = requests.delete(url, headers=headers, json={"delete_all": True})
                            if delete_response.status_code == 204:
                                print(f"   ✅ {name} purgées")
                            else:
                                print(f"   ❌ Erreur purge {name}: {delete_response.status_code}")
                        else:
                            print(f"   ⏭️ Purge {name} ignorée")
                    else:
                        print(f"   ℹ️ Aucune entrée dans {name}")
                else:
                    print(f"   ❌ Erreur lecture {name}: {response.status_code}")
            except Exception as e:
                print(f"   ❌ Erreur {name}: {e}")
        
        return True
    
    def status_check(self):
        """Vérification status système"""
        print("🔍 Status système Hunter Agency V2.0...")
        
        # Check DB
        if os.path.exists(self.db_path):
            print("✅ Base de données trouvée")
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            print(f"📋 Tables: {', '.join(tables)}")
            
            # Counts
            if 'leads' in tables:
                cursor.execute('SELECT COUNT(*) FROM leads')
                print(f"👥 Total leads: {cursor.fetchone()[0]}")
            
            if 'email_campaigns' in tables:
                cursor.execute('SELECT COUNT(*) FROM email_campaigns')
                print(f"📧 Total campagnes: {cursor.fetchone()[0]}")
            
            conn.close()
        else:
            print("❌ Base de données non trouvée")
        
        # Check API
        if self.sg_api_key:
            print("✅ SendGrid API key configurée")
        else:
            print("❌ SendGrid API key manquante")
        
        # Check server
        try:
            response = requests.get('http://localhost:8001/health', timeout=5)
            if response.status_code == 200:
                print("✅ Serveur API accessible")
            else:
                print(f"⚠️ Serveur API: status {response.status_code}")
        except:
            print("❌ Serveur API non accessible")

def main():
    # Parse arguments avec --force
    force_mode = '--force' in sys.argv
    if force_mode:
        sys.argv.remove('--force')
    
    if len(sys.argv) < 2:
        print("""
🔥 Hunter Agency V2.0 - Recovery Scripts

Commandes:
  cleanup                # Nettoie la base des emails test
  monitor               # Affiche les métriques
  purge_sendgrid        # Purge SendGrid suppressions
  status                # Status système
  
Options:
  --force               # Skip confirmations

Exemples:
  python recovery_scripts.py status
  python recovery_scripts.py cleanup
  python recovery_scripts.py monitor
  python recovery_scripts.py purge_sendgrid --force
        """)
        return
    
    action = sys.argv[1]
    recovery = SimpleRecovery()
    
    if action == "cleanup":
        recovery.cleanup_database()
    elif action == "monitor":
        recovery.get_metrics()
    elif action == "purge_sendgrid":
        recovery.purge_sendgrid(force=force_mode)
    elif action == "status":
        recovery.status_check()
    else:
        print(f"❌ Action inconnue: {action}")
        print("Utilise: python recovery_scripts.py pour voir l'aide")

if __name__ == "__main__":
    main()
