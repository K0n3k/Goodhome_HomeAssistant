"""Constants for GoodHome integration."""

# Constantes pour le polling de confirmation
POLLING_MAX_ATTEMPTS = 8  # Nombre maximum de tentatives (8 × 5s = 40s)
POLLING_INTERVAL = 5  # Intervalle entre chaque tentative (secondes)
DEBOUNCE_DELAY = 3  # Délai avant d'envoyer la commande de température (secondes)
