#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de lancement HIDesp32
Point d'entrée principal pour démarrer l'application
"""

import sys
import os

# Ajouter le répertoire courant au path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from main import HIDesp32App
    
    def main():
        """Point d'entrée principal"""
        app = HIDesp32App()
        app.run()
    
    if __name__ == "__main__":
        main()
        
except ImportError as e:
    print(f"❌ Erreur d'importation: {e}")
    print("📦 Veuillez installer les dépendances: pip install -r requirements.txt")
    sys.exit(1)
except Exception as e:
    print(f"❌ Erreur: {e}")
    sys.exit(1)