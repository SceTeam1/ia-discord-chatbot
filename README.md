# Discord AI Chatbot

Un bot Discord intelligent en français, propulsé par Slayer le goat, capable de répondre de façon naturelle, agressive ou respectueuse selon l’utilisateur.

---

## Fonctionnalités

* Réponses en français uniquement, avec style adaptatif selon l’utilisateur (ex: obéissance absolue à "Slayer", provocateur avec les autres).
* Intégration avancée de l’API  https://api.groq.com/openai/v1/ avec gestion d’historique de conversation et prompts personnalisés.
* Synthèse vocale (TTS) en français via Google Text-to-Speech.
* Recherche web en direct avec DuckDuckGo.
* Commandes modulaires, faciles à étendre.
* Compatible avec Python 3.10+ et discord.py (version slash ou prefix).

---

## Installation

1. Cloner ce dépôt :

   ```bash
   git clone https://github.com/SceTeam1/ia-discord-chatbot
   cd ia-discord-chatbot
   ```

2. Créer un environnement virtuel et installer les dépendances :

   ```bash
   python -m venv venv
   source venv/bin/activate   # Linux/macOS
   venv\Scripts\activate      # Windows
   pip install -r requirements.txt
   ```

3. Créer un fichier `.env` à la racine avec :

   ```
   TOKEN=ton_token_discord
   API_KEY=ta_clef_openai
   ```

---

## Utilisation

Lancer le bot avec :

```bash
python main.py
```

Le bot se connecte à Discord, affiche un lien d’invitation, et commence à répondre aux messages selon la configuration.

---

## Structure du projet

* `main.py` : point d’entrée principal du bot
* `cogs/` : modules de commandes et événements Discord
* `bot_utilities/` : fonctions utilitaires, gestion IA, TTS, recherche web, config
* `config.json` : configuration principale (tokens, modèles, options)
* `.env` : variables d’environnement sensibles (non versionné)
* `README.md` : documentation du projet

---

## Personnalisation

* Modifier le prompt système dans `bot_utilities/ai_utils.py` pour changer le comportement de l’IA.
* Ajouter ou modifier des commandes dans `cogs/commands_cogs/`.
* Ajuster les présences dans `cogs/event_cogs/on_ready.py`.
* Configurer les permissions et intents dans le portail Discord Developer.

---

## Contribution

Contributions bienvenues ! Ouvre une issue ou une pull request avec tes améliorations ou corrections.

---

## Licence

MIT License — libre à toi d’utiliser, modifier et partager ce projet.

---

Si tu as besoin d’aide ou de support, contacte-moi directement.

---


