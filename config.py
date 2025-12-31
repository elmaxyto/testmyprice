from __future__ import annotations

APP_NAME = "StreamSaver by Budget Tech ITA"
TAGLINE = "Tech che ti fa risparmiare soldi — in modo condivisibile."
DEFAULT_FREE_LIMIT = 3

CATEGORIES = [
    "Streaming",
    "Musica",
    "Gaming",
    "Cloud",
    "Produttività",
    "Fitness & Mind",
    "Finanza",
    "Telefonia",
    "Altro",
]

# Template setup “content-ready” (TikTok)
TEMPLATES = [
    {
        "id": "tech_minimal",
        "title": "Tech Minimal (Budget Killer)",
        "hook": "Stavo pagando senza usare: ho tagliato 2 abbonamenti e ho risparmiato subito.",
        "script": [
            "1) Apro StreamSaver e guardo il COSTO PER UTILIZZO.",
            "2) Quello sopra 1€ per utilizzo lo metto in review.",
            "3) Cancello 1 abbonamento oggi. Ripeto ogni settimana.",
        ],
        "hashtags": ["#risparmio", "#abbonamenti", "#budget", "#tech", "#italia"],
        "items": [
            {"nome": "Google One 200GB", "utilizzi_mese": 10},
            {"nome": "Microsoft 365", "utilizzi_mese": 12},
            {"nome": "Amazon Prime", "utilizzi_mese": 6},
        ],
    },
    {
        "id": "streaming_addict",
        "title": "Streaming Addict (Reality Check)",
        "hook": "Paghi 4 streaming e ne guardi 1? Ecco come ho ridotto del 30% al mese.",
        "script": [
            "1) Inserisco i miei streaming.",
            "2) Metto utilizzi/mese REALI.",
            "3) Tengo solo i 2 con costo/uso più basso.",
        ],
        "hashtags": ["#netflix", "#streaming", "#soldi", "#consigli", "#tiktokitalia"],
        "items": [
            {"nome": "Netflix", "utilizzi_mese": 6},
            {"nome": "Disney+", "utilizzi_mese": 2},
            {"nome": "Amazon Prime Video", "utilizzi_mese": 3},
        ],
    },
    {
        "id": "fitness_focus",
        "title": "Fitness Focus (No Sprechi)",
        "hook": "Se lo paghi e non lo usi, ti sta usando lui. Ho sistemato così.",
        "script": [
            "1) Fitness app + palestra + wearable: metto tutto.",
            "2) Costo per utilizzo → se è alto, cambio piano o cancello.",
            "3) Challenge 30 giorni: 1 check-in al giorno.",
        ],
        "hashtags": ["#fitness", "#abitudini", "#budget", "#mindset", "#soldi"],
        "items": [
            {"nome": "Strava", "utilizzi_mese": 8},
            {"nome": "Apple Fitness+", "utilizzi_mese": 10},
            {"nome": "Headspace", "utilizzi_mese": 6},
        ],
    },
]

CHALLENGE_PRESETS = [
    {
        "id": "cut_one_weekly",
        "title": "Taglia 1 abbonamento a settimana",
        "days": 30,
        "description": "Ogni settimana scegli 1 abbonamento con costo/uso più alto e mettilo in pausa o cancellalo.",
    },
    {
        "id": "reduce_20_30d",
        "title": "Riduci del 20% in 30 giorni",
        "days": 30,
        "description": "Imposta un budget mensile e scendi almeno del 20%. Check-in giornaliero per lo streak.",
    },
    {
        "id": "no_waste_14d",
        "title": "14 giorni zero sprechi",
        "days": 14,
        "description": "Per 14 giorni: niente nuovi abbonamenti, revisione costo/uso, e 1 micro-taglio se serve.",
    },
]

EXPORT_SIZE = (1080, 1920)
