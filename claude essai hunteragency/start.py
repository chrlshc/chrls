#!/usr/bin/env python3
"""
🚀 Hunter Agency V2.2 - Application Launcher
Script de démarrage pour l'application Hunter Agency
"""

import os
import sys
import asyncio
import subprocess
from pathlib import Path

def check_requirements():
    """Vérifier que les dépendances sont installées"""
    try:
        import fastapi
        import uvicorn
        import aiosqlite
        import structlog
        import httpx
        print("✅ Dependencies check passed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Run: pip install -r requirements.txt")
        return False

def create_env_if_missing():
    """Créer le fichier .env s'il n'existe pas"""
    env_path = Path(".env")
    if not env_path.exists():
        print("📝 Creating .env file from template...")
        env_example = Path(".env.example")
        if env_example.exists():
            with open(env_example, 'r') as f:
                content = f.read()
            with open(env_path, 'w') as f:
                f.write(content)
            print("✅ .env file created")
        else:
            print("⚠️  .env.example not found, creating basic .env")
            with open(env_path, 'w') as f:
                f.write("# Hunter Agency V2.2 Environment\n")
                f.write("SENDGRID_API_KEY=your_key_here\n")
                f.write("SENDGRID_FROM_EMAIL=contact@hunter-agency.com\n")

def run_tests():
    """Exécuter les tests"""
    print("🧪 Running tests...")
    try:
        result = subprocess.run([sys.executable, "-m", "pytest", "test_main.py", "-v"], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ All tests passed")
            return True
        else:
            print("❌ Some tests failed:")
            print(result.stdout)
            print(result.stderr)
            return False
    except FileNotFoundError:
        print("⚠️  pytest not found, skipping tests")
        return True

def start_main_app():
    """Démarrer l'application principale"""
    print("🔥 Starting Hunter Agency V2.2 Main Application...")
    print("📍 Access at: http://localhost:8001")
    print("📊 Health check: http://localhost:8001/health")
    print("🔗 API docs: http://localhost:8001/docs")
    print("\n" + "="*50)
    
    os.system(f"{sys.executable} main.py")

def start_dashboard():
    """Démarrer le dashboard"""
    print("📊 Starting Hunter Agency Dashboard...")
    print("📍 Access at: http://localhost:8000")
    print("🔗 Dashboard API: http://localhost:8000/api/overview")
    print("\n" + "="*50)
    
    os.chdir("dashboard")
    os.system(f"{sys.executable} main.py")

def show_menu():
    """Afficher le menu de démarrage"""
    print("\n" + "="*60)
    print("🔥 HUNTER AGENCY V2.2 - LAUNCHER")
    print("="*60)
    print("1. Start Main Application (Port 8001)")
    print("2. Start Dashboard (Port 8000)")
    print("3. Run Tests")
    print("4. Check System")
    print("5. Exit")
    print("="*60)

def main():
    """Fonction principale"""
    print("🚀 Hunter Agency V2.2 Startup Sequence")
    print("Checking system requirements...")
    
    # Vérifications préliminaires
    if not check_requirements():
        sys.exit(1)
    
    create_env_if_missing()
    
    while True:
        show_menu()
        choice = input("\nSelect option (1-5): ").strip()
        
        if choice == "1":
            start_main_app()
        elif choice == "2":
            start_dashboard()
        elif choice == "3":
            run_tests()
        elif choice == "4":
            print("🔍 System Check:")
            print(f"✅ Python version: {sys.version}")
            print(f"✅ Working directory: {os.getcwd()}")
            print(f"✅ Requirements: {'OK' if check_requirements() else 'FAILED'}")
            print(f"✅ .env file: {'EXISTS' if Path('.env').exists() else 'MISSING'}")
        elif choice == "5":
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please select 1-5.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Application stopped by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)