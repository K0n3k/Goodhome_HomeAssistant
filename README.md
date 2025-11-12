# GoodHome Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2024.1+-brightgreen.svg)

Intégration Home Assistant complète pour les radiateurs connectés **GoodHome** (marque Kingfisher - Castorama/Brico Dépôt).

## 📋 Fonctionnalités

### Plateformes supportées
- ✅ **Climate** - Contrôle complet du thermostat
- ✅ **Sensor** - Température, humidité, duty cycle, etc.
- ✅ **Binary Sensor** - Connectivité, problèmes, auto-apprentissage
- ✅ **Switch** - Détection fenêtre ouverte, présence, auto-apprentissage, mode manuel
- ✅ **Select** - Sélection des modes targetMode (12 modes disponibles)

### Caractéristiques principales
- 🔐 Authentification par email/password avec refresh token automatique
- 🚀 Cache HTTP 304 Not Modified pour optimiser les performances
- 🔄 État optimiste avec polling de confirmation (40s max)
- 🌐 Support complet de l'API GoodHome officielle
- 🎯 100% compatible avec le projet ESPHome_GoodHome
- 🇫🇷 Interface en français
- ⚙️ Configuration via interface utilisateur (config flow)

## 📦 Installation

### Pré-requis

⚠️ **Important** : Avant d'installer cette intégration, votre radiateur GoodHome doit être connecté au cloud GoodHome. Cette opération se fait depuis l'application mobile officielle **GoodHome** (disponible sur Android et iOS).

### Via HACS (recommandé)

1. Ouvrez HACS dans Home Assistant
2. Allez dans "Intégrations"
3. Cliquez sur les 3 points en haut à droite
4. Sélectionnez "Dépôts personnalisés"
5. Ajoutez l'URL : `https://github.com/K0n3k/Goodhome_HomeAssistant`
6. Catégorie : "Integration"
7. Recherchez "GoodHome" et installez-le
8. Redémarrez Home Assistant

### Installation manuelle

1. Copiez le dossier `custom_components/goodhome` dans votre dossier `custom_components` de Home Assistant
2. Redémarrez Home Assistant

## ⚙️ Configuration

### Via l'interface utilisateur (recommandé)

1. Allez dans **Paramètres** → **Appareils et services**
2. Cliquez sur **Ajouter une intégration**
3. Recherchez **GoodHome**
4. Entrez vos identifiants GoodHome (email et mot de passe)
5. Vos thermostats apparaîtront automatiquement !

### Via YAML (optionnel)

```yaml
goodhome:
  email: !secret goodhome_email
  password: !secret goodhome_password
```

Dans `secrets.yaml` :
```yaml
goodhome_email: "votre@email.com"
goodhome_password: "votre_mot_de_passe"
```

## 📱 Entités créées

Pour chaque thermostat GoodHome, les entités suivantes sont créées :

### Climate
- `climate.xxx` - Contrôle du thermostat
  - Température cible
  - Modes HVAC (Heat, Off)
  - Presets (Confort, Éco, Manuel, Absence)

### Sensors
- `sensor.xxx_temperature` - Température actuelle
- `sensor.xxx_humidity` - Humidité
- `sensor.xxx_duty_cycle` - Cycle de chauffe (%)
- `sensor.xxx_comfort_temperature` - Température confort
- `sensor.xxx_eco_temperature` - Température éco
- `sensor.xxx_target_temperature` - Température cible

### Binary Sensors
- `binary_sensor.xxx_connectivity` - État de connexion
- `binary_sensor.xxx_self_learning_improve` - Amélioration auto-apprentissage
- `binary_sensor.xxx_problem` - Détection de problème

### Switches
- `switch.xxx_open_window_detection` - Détection fenêtre ouverte
- `switch.xxx_presence_sensor` - Détecteur de présence
- `switch.xxx_self_learning` - Mode auto-apprentissage
- `switch.xxx_manual_mode` - Mode manuel (noprog)

### Select
- `select.xxx_target_mode` - Sélection du mode de fonctionnement
  - Par défaut (provisoire)
  - Manuel Confort / Éco / Hors-gel
  - Override
  - Forcé Confort / Éco
  - Auto Confort / Éco
  - Absence courte / longue

## 🎯 Modes targetMode

L'entité `select.xxx_target_mode` permet de contrôler finement le comportement du radiateur avec les 12 modes disponibles :

| Mode | Valeur | Description |
|------|--------|-------------|
| Par défaut | 0 | Mode provisoire, retour au défaut |
| Manuel Confort | 1 | Manuel à température confort |
| Manuel Éco | 2 | Manuel à température éco |
| Manuel Hors-gel | 3 | Manuel anti-gel (OFF) |
| Absence longue | 5 | Absence longue durée (holidayTimeout) |
| Override | 8 | Manuel avec température override |
| Forcé Confort | 9 | Forcé confort avec retour auto |
| Forcé Éco | 10 | Forcé éco avec retour auto |
| Absence courte | 12 | Absence courte (overrideTime) |
| Auto Confort | 60 | Mode auto période présence |
| Auto Éco | 61 | Mode auto période absence |
| Manuel | 70 | Mode manuel (mise à jour récente) |

## 🔌 Compatibilité API

Cette intégration utilise les mêmes endpoints et headers que l'application GoodHome officielle :

- **Socket.io** : `authorization: Bearer {token}`
- **API v1** : `access-token: {token}` + `if-none-match: {etag}`
- **Cache HTTP 304** : Optimisation de la bande passante
- **Paramètres booléens** : Format `true/false` JSON

Référence : Compatible avec [ESPHome_GoodHome](https://github.com/Benichou34/ESPHome_GoodHome)

## 📊 Performances

Grâce au cache HTTP 304 Not Modified :
- **Sans cache** : ~1-2 secondes par requête
- **Avec cache 304** : ~0.3-0.6 secondes par requête
- **Gain** : 50-70% de réduction du temps de réponse

## 🔧 Suivi d'énergie

Pour suivre la consommation de vos radiateurs GoodHome (ex: DLRIRFH1800 - 1800W) :

```yaml
template:
  - sensor:
    - name: "Chauffage Salon Power"
      unique_id: chauffage_salon_power
      unit_of_measurement: "W"
      device_class: power
      state_class: measurement
      state: >
        {% set duty = states('sensor.xxx_duty_cycle') | float(0) %}
        {{ (duty * 1800 / 100) | round(0) }}
```

Puis ajoutez dans `configuration.yaml` :
```yaml
sensor:
  - platform: integration
    source: sensor.chauffage_salon_power
    name: "Chauffage Salon Energy"
    unit_prefix: k
    round: 2
```

## 🐛 Dépannage

### Les entités n'apparaissent pas
1. Vérifiez que l'intégration est bien activée dans **Paramètres** → **Appareils et services**
2. Consultez les logs : **Paramètres** → **Système** → **Journaux**
3. Redémarrez Home Assistant

### Erreur 401 (Unauthorized)
- Vérifiez vos identifiants GoodHome
- Le token est automatiquement rafraîchi, attendez 1 minute

### Les modifications ne sont pas prises en compte
- L'intégration utilise un système optimiste avec polling de confirmation (40 secondes max)
- Vérifiez la connectivité de vos radiateurs

## 📝 Logs

Pour activer les logs de debug (temporairement) :

```yaml
logger:
  default: info
  logs:
    custom_components.goodhome: debug
```

## 🤝 Contribution

Les contributions sont les bienvenues ! N'hésitez pas à :
- Ouvrir une issue pour signaler un bug
- Proposer une pull request pour une amélioration
- Partager vos retours d'expérience

## 📄 Licence

Ce projet est sous licence MIT.

## 👏 Remerciements

- [ESPHome_GoodHome](https://github.com/Benichou34/ESPHome_GoodHome) pour la documentation de l'API
- La communauté Home Assistant

## 🔗 Liens utiles

- [Documentation Home Assistant](https://www.home-assistant.io/)
- [Forum Home Assistant](https://community.home-assistant.io/)
- [GoodHome (Kingfisher)](https://www.kingfisher.com/en/about-us/goodhome.html)

---

**Développé avec ❤️ pour la communauté Home Assistant**
