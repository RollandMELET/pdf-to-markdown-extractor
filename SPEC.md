# SPEC.md - Spécifications complètes

## 📖 Table des matières

1. [Contexte et objectifs](#1-contexte-et-objectifs)
2. [Spécifications fonctionnelles](#2-spécifications-fonctionnelles)
3. [Architecture technique](#3-architecture-technique)
4. [Spécifications des extracteurs](#4-spécifications-des-extracteurs)
5. [Configuration](#5-configuration)
6. [API REST](#6-api-rest)
7. [Interface d'arbitrage](#7-interface-darbitrage)
8. [Formats de sortie](#8-formats-de-sortie)
9. [Déploiement Docker](#9-déploiement-docker)
10. [Tests et qualité](#10-tests-et-qualité)
11. [Ajout d'un nouvel extracteur](#11-ajout-dun-nouvel-extracteur)
12. [Évolutivité](#12-évolutivité)

---

## 1. Contexte et objectifs

### 1.1 Problématique

Les PDF complexes (rapports techniques, présentations, documents scannés) contiennent des informations organisées en **blocs sémantiques** (tableaux, colonnes, schémas, encarts) qu'une lecture linéaire ne capture pas correctement. Les outils OCR traditionnels échouent à préserver cette structure, rendant le contenu difficile à exploiter par un LLM.

### 1.2 Objectif principal

Créer un module de conversion PDF → Markdown qui :
- **Préserve les blocs sémantiques** du document original
- **Évalue automatiquement** la complexité du document
- **Utilise plusieurs extracteurs** pour les documents complexes
- **Compare les résultats** et détecte les divergences
- **Permet l'arbitrage humain** en cas de conflit
- **S'intègre facilement** dans des workflows n8n ou autres

### 1.3 Contraintes

| Contrainte | Valeur |
|------------|--------|
| **Environnement** | Docker portable (Mac M4 + VPS Linux) |
| **Volume** | 0-10 documents/jour |
| **Taille documents** | 1-50 pages (exceptionnellement plus) |
| **Priorité** | PRÉCISION > Rapidité |
| **Budget API** | À déterminer selon usage |

### 1.4 Types de documents prioritaires

1. **Rapports techniques, règlements, standards, normes** (priorité haute)
2. **Présentations (PowerPoint/Google Slides)** (priorité moyenne)
3. **Documents scannés** (priorité basse, mais supporté)

---

## 2. Spécifications fonctionnelles

### 2.1 Stratégies d'extraction

Le système supporte 4 stratégies d'extraction configurables :

| Stratégie | Comportement | Coût | Use case |
|-----------|-------------|------|----------|
| `fallback` | Docling → si échec → MinerU → si échec → Mistral | Minimal | Budget serré, documents simples |
| `parallel_local` | Docling + MinerU en parallèle, Mistral en fallback | Gratuit | Précision sans coût API |
| `parallel_all` | Docling + MinerU + Mistral en parallèle | ~$0.002/page | Précision maximale |
| `hybrid` | Local d'abord, Mistral si divergences détectées | Variable | Compromis coût/précision |

**Stratégie par défaut** : `parallel_local`

### 2.2 Flux principal

```
┌──────────────────────────────────────────────────────────────────┐
│                        ENTRÉE                                     │
│  PDF (file upload, URL, ou base64)                               │
└───────────────────────────┬──────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────────┐
│                  ÉVALUATION COMPLEXITÉ                           │
│  Score: simple | medium | complex                                │
│  Critères: pages, tableaux, colonnes, images, formules, scan     │
└───────────────────────────┬──────────────────────────────────────┘
                            │
              ┌─────────────┴─────────────┐
              │                           │
              ▼                           ▼
┌─────────────────────────┐   ┌─────────────────────────────────────┐
│   PIPELINE SIMPLE       │   │      PIPELINE COMPLEXE              │
│   (Docling seul)        │   │  ┌─────────────────────────────┐    │
│                         │   │  │    Extraction parallèle     │    │
│   PDF → Docling →       │   │  │  (selon extraction_strategy) │    │
│   Markdown → Output     │   │  │  ┌────────┐ ┌────────┐ ┌───────┐ │
│                         │   │  │  │Docling │ │MinerU  │ │Mistral│ │
│                         │   │  │  └────────┘ └────────┘ └───────┘ │
└───────────┬─────────────┘   │  └─────────────────────────────┘    │
            │                 │                 │                    │
            │                 │                 ▼                    │
            │                 │  ┌─────────────────────────────┐    │
            │                 │  │      COMPARAISON            │    │
            │                 │  │  Alignement sémantique      │    │
            │                 │  │  Détection divergences      │    │
            │                 │  └─────────────────────────────┘    │
            │                 │                 │                    │
            │                 │     ┌───────────┴───────────┐       │
            │                 │     │                       │       │
            │                 │     ▼                       ▼       │
            │                 │ ┌───────────┐       ┌────────────┐  │
            │                 │ │ Pas de    │       │ Divergences│  │
            │                 │ │ divergence│       │ détectées  │  │
            │                 │ └─────┬─────┘       └──────┬─────┘  │
            │                 │       │                    │        │
            │                 │       │                    ▼        │
            │                 │       │         ┌──────────────────┐│
            │                 │       │         │   ARBITRAGE      ││
            │                 │       │         │   Interface UI   ││
            │                 │       │         │   Choix humain   ││
            │                 │       │         └────────┬─────────┘│
            │                 │       │                  │          │
            │                 └───────┼──────────────────┼──────────┘
            │                         │                  │
            └─────────────────────────┼──────────────────┘
                                      │
                                      ▼
                        ┌─────────────────────────────┐
                        │          SORTIE             │
                        │  - document.md              │
                        │  - metadata.json            │
                        │  - images/                  │
                        │  - tables/                  │
                        │  - extraction_report.json   │
                        └─────────────────────────────┘
```

### 2.3 Évaluation de complexité

#### Critères analysés

| Critère | Poids | Méthode de détection |
|---------|-------|---------------------|
| Nombre de pages | 10% | `page_count` |
| Tableaux détectés | 25% | Layout analysis Docling |
| Multi-colonnes | 20% | Layout analysis |
| Images/schémas | 15% | Détection objets graphiques |
| Formules mathématiques | 15% | Pattern matching LaTeX/MathML |
| Document scanné | 15% | Analyse texte extractible |

#### Scores et routage

| Score | Classification | Pipeline |
|-------|---------------|----------|
| 0-30 | `simple` | Docling seul, pas de comparaison |
| 31-60 | `medium` | Docling + validation renforcée |
| 61-100 | `complex` | Multi-extraction selon strategy |

### 2.4 Gestion des états

```
┌─────────┐     ┌───────────┐     ┌────────────┐     ┌──────────┐
│ PENDING │ ──► │ ANALYZING │ ──► │ EXTRACTING │ ──► │ COMPARING│
└─────────┘     └───────────┘     └────────────┘     └────┬─────┘
                                                          │
                    ┌─────────────────────────────────────┤
                    │                                     │
                    ▼                                     ▼
            ┌──────────────┐                     ┌──────────────┐
            │ NEEDS_REVIEW │                     │  COMPLETED   │
            │ (divergences)│                     │              │
            └──────┬───────┘                     └──────────────┘
                   │
                   ▼
            ┌──────────────┐
            │  ARBITRATED  │ ──► COMPLETED
            └──────────────┘

États d'erreur possibles à tout moment :
- FAILED (erreur technique)
- TIMEOUT (dépassement délai)
```

---

## 3. Architecture technique

### 3.1 Vue d'ensemble

```
┌─────────────────────────────────────────────────────────────────┐
│                         DOCKER COMPOSE                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │   API        │    │   Worker     │    │   Redis      │      │
│  │  (FastAPI)   │◄──►│  (Celery)    │◄──►│  (Queue)     │      │
│  │  Port: 8000  │    │              │    │  Port: 6379  │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│         │                   │                                   │
│         │                   │                                   │
│         ▼                   ▼                                   │
│  ┌──────────────────────────────────────────────────────┐      │
│  │                    VOLUMES                            │      │
│  │  /data/uploads    /data/outputs    /data/cache       │      │
│  └──────────────────────────────────────────────────────┘      │
│                                                                 │
│  ┌──────────────┐                                              │
│  │  Streamlit   │  (Interface arbitrage - optionnel)           │
│  │  Port: 8501  │                                              │
│  └──────────────┘                                              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 Composants principaux

#### API (FastAPI)
- Réception des requêtes HTTP
- Validation des inputs
- Création des jobs Celery
- Exposition des résultats
- Webhooks pour callbacks

#### Worker (Celery)
- Exécution des extractions
- Gestion parallélisation
- Comparaison des résultats
- Mise à jour des statuts

#### Redis
- File d'attente des jobs
- Cache des résultats intermédiaires
- Stockage des sessions (optionnel)

#### Streamlit (optionnel)
- Interface d'arbitrage
- Visualisation des divergences
- Saisie manuelle utilisateur

### 3.3 Système de plugins extracteurs

```python
# src/extractors/base.py

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, List
from pathlib import Path

@dataclass
class ExtractionResult:
    """Résultat standardisé d'une extraction."""
    markdown: str
    metadata: dict
    images: List[Path]
    tables: List[dict]
    confidence_score: float
    extraction_time: float
    extractor_name: str
    extractor_version: str
    warnings: List[str]
    errors: List[str]

class BaseExtractor(ABC):
    """Interface commune pour tous les extracteurs."""
    
    name: str = "base"
    version: str = "0.0.0"
    
    @abstractmethod
    def extract(
        self, 
        file_path: Path, 
        options: Optional[dict] = None
    ) -> ExtractionResult:
        """Extrait le contenu d'un PDF.
        
        Args:
            file_path: Chemin vers le fichier PDF
            options: Options spécifiques à l'extracteur
            
        Returns:
            ExtractionResult avec le markdown et les métadonnées
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Vérifie si l'extracteur est disponible."""
        pass
    
    @abstractmethod
    def get_capabilities(self) -> dict:
        """Retourne les capacités de l'extracteur."""
        pass
```

---

## 4. Spécifications des extracteurs

### 4.1 Docling Extractor (Principal)

| Propriété | Valeur |
|-----------|--------|
| **Priorité** | 1 (défaut) |
| **Type** | Local (open-source) |
| **Licence** | MIT |
| **GPU** | Optionnel (accélère) |
| **RAM** | ~4GB |

### 4.2 MinerU Extractor (Haute précision)

| Propriété | Valeur |
|-----------|--------|
| **Priorité** | 2 |
| **Type** | Local (open-source) |
| **Licence** | Apache 2.0 |
| **GPU** | Recommandé |
| **RAM** | ~8GB |

### 4.3 Mistral OCR Extractor (API)

| Propriété | Valeur |
|-----------|--------|
| **Priorité** | 3 |
| **Type** | API cloud |
| **Coût** | ~$1-2/1000 pages |
| **Limite** | 50MB, 1000 pages |

### 4.4 Matrice de capacités

| Capacité | Docling | MinerU | Mistral OCR |
|----------|---------|--------|-------------|
| Texte simple | ✅ | ✅ | ✅ |
| Tableaux simples | ✅ | ✅ | ✅ |
| Tableaux complexes | ⚠️ | ✅ | ✅ |
| Multi-colonnes | ✅ | ✅ | ✅ |
| Formules LaTeX | ⚠️ | ✅ | ✅ |
| Images extraction | ✅ | ✅ | ✅ |
| OCR (scannés) | ✅ | ✅ | ✅ |
| Multilingue | ✅ | ✅ | ✅✅ |
| Vitesse | ⚡⚡ | ⚡ | ⚡⚡⚡ |
| Précision | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| Coût | Gratuit | Gratuit | Payant |

---

## 5. Configuration

### 5.1 Niveaux de configuration

Le système supporte 3 niveaux de configuration (du plus général au plus spécifique) :

1. **Variables d'environnement** (.env) - Configuration globale
2. **Fichier YAML** (config/settings.yaml) - Configuration détaillée
3. **Paramètres de requête** (API) - Configuration par job

Les paramètres de requête écrasent le YAML, qui écrase les variables d'environnement.

### 5.2 Variables d'environnement (.env)

```env
# ===========================================
# API Configuration
# ===========================================
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=INFO                    # DEBUG | INFO | WARNING | ERROR

# ===========================================
# Redis / Celery
# ===========================================
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# ===========================================
# Extracteurs API externes
# ===========================================
MISTRAL_API_KEY=your_api_key_here

# ===========================================
# Limites globales
# ===========================================
MAX_FILE_SIZE_MB=50               # Taille max upload
MAX_PAGES=100                     # Pages max par document
EXTRACTION_TIMEOUT_SECONDS=600    # Timeout global

# ===========================================
# Stockage
# ===========================================
UPLOAD_DIR=/app/data/uploads
OUTPUT_DIR=/app/data/outputs
CACHE_DIR=/app/data/cache
```

### 5.3 Fichier de configuration YAML

```yaml
# config/settings.yaml
# Configuration détaillée du service pdf-to-markdown-extractor

# ===========================================
# Stratégie d'extraction globale
# ===========================================
extraction:
  # Stratégie par défaut
  # - fallback: Docling → MinerU → Mistral (si échec)
  # - parallel_local: Docling + MinerU en parallèle
  # - parallel_all: Docling + MinerU + Mistral en parallèle
  # - hybrid: Local d'abord, Mistral si divergences
  strategy: "parallel_local"
  
  # Timeout par extracteur (secondes)
  timeout_per_extractor: 300
  
  # Nombre max d'extracteurs en parallèle
  max_parallel_extractors: 3

# ===========================================
# Configuration des extracteurs
# ===========================================
extractors:
  docling:
    enabled: true
    priority: 1
    config:
      ocr_engine: "easyocr"       # tesseract | easyocr | rapidocr | ocrmac
      table_structure: true       # Reconnaissance structure tableaux
      extract_images: true        # Extraire les images
      preserve_layout: true       # Préserver le layout
      languages: ["fra", "eng"]   # Langues OCR
      
  mineru:
    enabled: true
    priority: 2
    config:
      model: "mineru-2.5"
      use_vlm: true               # Vision Language Model (plus précis)
      table_recognition: true
      formula_recognition: true
      gpu: "auto"                 # auto | cpu | cuda
      
  mistral:
    enabled: true
    priority: 3
    config:
      model: "mistral-ocr-2512"
      table_format: "markdown"    # markdown | html
      include_images: true
      batch_mode: false           # Utiliser Batch API (moins cher, plus lent)

# ===========================================
# Évaluation de complexité
# ===========================================
complexity:
  # Seuils de classification
  thresholds:
    simple: 30                    # score <= 30 = simple
    complex: 60                   # score >= 60 = complex
                                  # entre 30-60 = medium
  
  # Poids des critères (total = 100)
  weights:
    pages: 10
    tables: 25
    columns: 20
    images: 15
    formulas: 15
    scan: 15
  
  # Scores par palier pour les pages
  page_scores:
    - max: 5
      score: 0
    - max: 20
      score: 5
    - max: 50
      score: 10

# ===========================================
# Comparaison et fusion
# ===========================================
comparison:
  # Seuil de similarité pour détecter une divergence
  # (en dessous = divergence à résoudre)
  similarity_threshold: 0.90
  
  # Seuil pour fusion automatique sans vérification
  # (au dessus = fusion auto)
  auto_merge_threshold: 0.95
  
  # Stratégie de sélection si pas d'arbitrage
  # - highest_confidence: choisir l'extraction avec meilleur score
  # - prefer_docling: préférer Docling
  # - prefer_mineru: préférer MinerU
  # - prefer_mistral: préférer Mistral
  default_selection: "highest_confidence"

# ===========================================
# Nettoyage automatique
# ===========================================
cleanup:
  # Supprimer les outputs après X jours
  retention_days: 7
  
  # Heure d'exécution du nettoyage (format HH:MM)
  schedule_time: "03:00"
  
  # Garder les jobs en erreur plus longtemps
  error_retention_days: 30

# ===========================================
# Webhooks
# ===========================================
webhooks:
  # Nombre de tentatives en cas d'échec
  max_retries: 3
  
  # Délai entre tentatives (secondes, exponential backoff)
  retry_delay: 5
  
  # Timeout pour les appels webhook
  timeout: 30
```

### 5.4 Paramètres de requête API

Voir section [6. API REST](#6-api-rest) pour les options disponibles par requête.

---

## 6. API REST

### 6.1 Endpoints principaux

#### `POST /api/v1/extract`

Soumet un document pour extraction.

**Request:**
```json
{
  "file": "<base64_encoded_pdf>",
  // OU
  "url": "https://example.com/document.pdf",
  
  "options": {
    "force_complexity": null,
    "extraction_strategy": "parallel_all",
    "extractors": ["docling", "mineru", "mistral"],
    "callback_url": "https://my-n8n.com/webhook/xxx",
    "output_format": "markdown",
    "extract_images": true,
    "extract_tables": true,
    "ocr_languages": ["fra", "eng"],
    "inline_result": false
  }
}
```

**Options disponibles:**

| Option | Type | Défaut | Description |
|--------|------|--------|-------------|
| `force_complexity` | string\|null | null | Forcer simple/medium/complex |
| `extraction_strategy` | string | config | fallback/parallel_local/parallel_all/hybrid |
| `extractors` | array | config | Liste des extracteurs à utiliser |
| `callback_url` | string\|null | null | URL webhook de notification |
| `output_format` | string | "markdown" | markdown/json/both |
| `extract_images` | bool | true | Extraire les images |
| `extract_tables` | bool | true | Extraire les tableaux |
| `ocr_languages` | array | ["fra","eng"] | Langues pour l'OCR |
| `inline_result` | bool | false | Inclure le résultat dans la réponse finale |

**Response:**
```json
{
  "job_id": "uuid-xxx-xxx",
  "status": "pending",
  "created_at": "2025-12-30T10:00:00Z",
  "estimated_time_seconds": 30
}
```

#### `GET /api/v1/status/{job_id}`

Récupère le statut d'un job.

**Response:**
```json
{
  "job_id": "uuid-xxx-xxx",
  "status": "extracting",
  "progress": 65,
  "current_step": "Running MinerU extraction",
  "complexity_score": "complex",
  "extraction_strategy": "parallel_all",
  "extractors_running": ["docling", "mineru", "mistral"],
  "started_at": "2025-12-30T10:00:00Z",
  "estimated_completion": "2025-12-30T10:02:00Z"
}
```

#### `GET /api/v1/result/{job_id}`

Récupère le résultat d'une extraction.

**Paramètres query:**
- `inline=true` : Inclure le markdown complet dans la réponse (pour petits documents)

**Response (inline=false, défaut):**
```json
{
  "job_id": "uuid-xxx-xxx",
  "status": "completed",
  "result": {
    "metadata": {
      "title": "Document Title",
      "pages": 15,
      "source": "document.pdf",
      "complexity_score": "complex",
      "extraction_strategy": "parallel_all",
      "extraction_methods": ["docling", "mineru", "mistral"],
      "extraction_time_seconds": 45.2,
      "confidence_score": 0.95
    },
    "summary": {
      "word_count": 3500,
      "tables_count": 5,
      "images_count": 8
    }
  },
  "download_urls": {
    "markdown": "/api/v1/download/uuid-xxx/document.md",
    "metadata": "/api/v1/download/uuid-xxx/metadata.json",
    "zip": "/api/v1/download/uuid-xxx/full.zip"
  }
}
```

**Response (inline=true):**
```json
{
  "job_id": "uuid-xxx-xxx",
  "status": "completed",
  "result": {
    "markdown": "# Document Title\n\nFull content here...",
    "metadata": { ... },
    "images_base64": {
      "page_1_img_1.png": "data:image/png;base64,..."
    },
    "tables": [
      {"id": "table_1", "markdown": "| A | B |...", "json": {...}}
    ]
  }
}
```

#### `POST /api/v1/test-extractor`

**Endpoint pour tester un extracteur isolément.** Utile pour :
- Évaluer un nouvel extracteur
- Comparer les performances
- Débugger des problèmes

**Request:**
```json
{
  "file": "<base64_encoded_pdf>",
  // OU
  "url": "https://example.com/document.pdf",
  
  "extractor": "docling",
  "options": {
    "ocr_engine": "tesseract",
    "table_structure": true
  },
  "return_raw": false,
  "include_timing": true
}
```

**Response:**
```json
{
  "extractor": "docling",
  "extractor_version": "2.1.0",
  "status": "success",
  "result": {
    "markdown": "# Extracted content...",
    "metadata": {
      "pages": 5,
      "tables_detected": 2,
      "images_detected": 3
    },
    "confidence_score": 0.92,
    "warnings": ["Table on page 3 may have merged cells"]
  },
  "timing": {
    "total_seconds": 12.5,
    "breakdown": {
      "initialization": 2.1,
      "layout_analysis": 3.2,
      "text_extraction": 4.8,
      "table_extraction": 1.9,
      "image_extraction": 0.5
    }
  },
  "raw_output": null
}
```

#### `GET /api/v1/extractors`

Liste les extracteurs disponibles et leur statut.

**Response:**
```json
{
  "extractors": [
    {
      "name": "docling",
      "version": "2.1.0",
      "status": "available",
      "type": "local",
      "capabilities": {
        "ocr": true,
        "tables": true,
        "formulas": false,
        "images": true,
        "languages": ["fra", "eng", "deu", "spa"]
      }
    },
    {
      "name": "mineru",
      "version": "2.5.0",
      "status": "available",
      "type": "local",
      "capabilities": {
        "ocr": true,
        "tables": true,
        "formulas": true,
        "images": true,
        "languages": ["*"]
      }
    },
    {
      "name": "mistral",
      "version": "mistral-ocr-2512",
      "status": "available",
      "type": "api",
      "capabilities": {
        "ocr": true,
        "tables": true,
        "formulas": true,
        "images": true,
        "languages": ["*"]
      }
    }
  ]
}
```

#### `POST /api/v1/arbitrate/{job_id}`

Soumet un choix d'arbitrage pour une divergence.

**Request:**
```json
{
  "divergence_id": "div-001",
  "choice": "extraction_a",
  "custom_content": null,
  "reason": "Table better formatted in extraction A"
}
```

#### `GET /api/v1/review/{job_id}`

Récupère les divergences à arbitrer.

**Response:**
```json
{
  "job_id": "uuid-xxx-xxx",
  "divergences": [
    {
      "id": "div-001",
      "type": "table",
      "page": 5,
      "block_id": "table_2",
      "extraction_a": {
        "source": "docling",
        "content": "| A | B |\n|---|---|\n| 1 | 2 |",
        "confidence": 0.88
      },
      "extraction_b": {
        "source": "mineru",
        "content": "| A | B |\n|---|---|\n| 1 | 2 |",
        "confidence": 0.92
      },
      "extraction_c": {
        "source": "mistral",
        "content": "| A | B |\n|---|---|\n| 1 | 2 |",
        "confidence": 0.95
      },
      "similarity_scores": {
        "a_vs_b": 0.85,
        "a_vs_c": 0.82,
        "b_vs_c": 0.91
      },
      "preview_image": "/api/v1/preview/uuid-xxx/page_5_block_table_2.png"
    }
  ],
  "total_divergences": 3,
  "resolved": 0
}
```

#### `GET /api/v1/health`

Vérifie l'état des services.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "services": {
    "api": "up",
    "redis": "up",
    "celery_workers": 2
  },
  "extractors": {
    "docling": {
      "status": "available",
      "version": "2.1.0"
    },
    "mineru": {
      "status": "available",
      "version": "2.5.0"
    },
    "mistral": {
      "status": "available",
      "api_key_configured": true
    }
  },
  "config": {
    "extraction_strategy": "parallel_local",
    "max_file_size_mb": 50,
    "max_pages": 100
  }
}
```

### 6.2 Webhooks

Format du callback envoyé à `callback_url` :

```json
{
  "event": "extraction.completed",
  "job_id": "uuid-xxx-xxx",
  "timestamp": "2025-12-30T10:02:00Z",
  "data": {
    "status": "completed",
    "download_url": "https://your-api.com/api/v1/download/uuid-xxx/full.zip",
    "result_url": "https://your-api.com/api/v1/result/uuid-xxx",
    "summary": {
      "pages": 15,
      "tables": 3,
      "images": 5,
      "confidence": 0.95,
      "extraction_strategy": "parallel_all",
      "extractors_used": ["docling", "mineru", "mistral"]
    }
  }
}
```

**Événements possibles:**
- `extraction.completed` - Extraction terminée avec succès
- `extraction.failed` - Extraction échouée
- `extraction.needs_review` - Divergences détectées, arbitrage requis
- `extraction.timeout` - Dépassement du timeout

---

## 7. Interface d'arbitrage

### 7.1 Écrans principaux

#### Liste des jobs en attente d'arbitrage

```
┌─────────────────────────────────────────────────────────────────┐
│  📋 Documents en attente d'arbitrage                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  🔴 rapport_Q3.pdf          3 divergences    il y a 5 min      │
│     Strategy: parallel_all (3 extracteurs)                      │
│     [Voir détails]                                              │
│                                                                 │
│  🟡 presentation_2025.pdf   1 divergence     il y a 1h         │
│     Strategy: parallel_local (2 extracteurs)                    │
│     [Voir détails]                                              │
│                                                                 │
│  ✅ Aucun autre document en attente                             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

#### Écran de comparaison (3 extracteurs)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  📄 rapport_Q3.pdf  │  Page 5  │  Divergence 1/3                            │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────┐    Similarités:                                    │
│  │   APERÇU ORIGINAL   │    A↔B: 85% │ A↔C: 82% │ B↔C: 91%                 │
│  │   [Image PDF p.5]   │    Type: Tableau                                   │
│  └─────────────────────┘                                                    │
├─────────────────────┬─────────────────────┬─────────────────────────────────┤
│  DOCLING (A)        │  MINERU (B)         │  MISTRAL (C)                    │
│  Confiance: 88%     │  Confiance: 92%     │  Confiance: 95%                 │
├─────────────────────┼─────────────────────┼─────────────────────────────────┤
│ | Produit | Prix |  │ | Produit | Prix |  │ | Produit | Prix  |             │
│ |---------|------|  │ |---------|------|  │ |---------|-------|             │
│ | Widget  | 10€  |  │ | Widget  | 10 € |  │ | Widget  | 10,00€|             │
│                     │                     │                                 │
│    [✓ Choisir A]    │    [✓ Choisir B]    │     [✓ Choisir C]              │
├─────────────────────┴─────────────────────┴─────────────────────────────────┤
│  [📝 Éditer manuellement]  [⏭️ Ignorer]  [👁️ Voir PDF original]             │
│  Navigation: [◀ Précédent]  Divergence 1 / 3  [Suivant ▶]                   │
│  [💾 Sauvegarder et terminer]                                               │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 8. Formats de sortie

### 8.1 Structure des fichiers générés

```
output/{job_id}/
├── document.md              # Markdown principal
├── metadata.json            # Méta-informations complètes
├── extraction_report.json   # Rapport détaillé du traitement
├── images/                  # Images extraites
│   ├── page_1_img_1.png
│   └── ...
├── tables/                  # Tableaux en format structuré
│   ├── table_1.json
│   ├── table_1.md
│   └── ...
└── original/                # Fichiers sources (optionnel)
    └── document.pdf
```

### 8.2 Format Markdown cible

```markdown
---
title: "Rapport Q3 2025"
source: "rapport_Q3.pdf"
pages: 15
extracted_at: "2025-12-30T10:00:00Z"
complexity_score: "complex"
extraction_strategy: "parallel_all"
extraction_methods: ["docling", "mineru", "mistral"]
confidence_score: 0.95
---

# Rapport Q3 2025

## Résumé exécutif

Lorem ipsum dolor sit amet...

## Chiffres clés

| Indicateur | Q2 2025 | Q3 2025 | Évolution |
|------------|---------|---------|-----------|
| CA         | 1.2M€   | 1.5M€   | +25%      |

![Graphique des ventes](images/page_3_img_1.png)
```

### 8.3 Format metadata.json

```json
{
  "document": {
    "title": "Rapport Q3 2025",
    "source_file": "rapport_Q3.pdf",
    "pages": 15
  },
  "extraction": {
    "job_id": "uuid-xxx-xxx",
    "duration_seconds": 120,
    "complexity_score": "complex",
    "extraction_strategy": "parallel_all",
    "extractors_used": ["docling", "mineru", "mistral"],
    "confidence_score": 0.95
  },
  "content": {
    "tables_count": 5,
    "images_count": 8,
    "total_words": 3500
  },
  "arbitration": {
    "required": true,
    "divergences_total": 3,
    "divergences_resolved": 3
  }
}
```

---

## 9. Déploiement Docker

### 9.1 docker-compose.yml

```yaml
version: '3.8'

services:
  api:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - REDIS_URL=redis://redis:6379/0
      - MISTRAL_API_KEY=${MISTRAL_API_KEY}
    volumes:
      - ./data:/app/data
      - ./config:/app/config
    depends_on:
      - redis

  worker:
    build:
      context: .
      dockerfile: Dockerfile
    command: celery -A src.core.celery_app worker --loglevel=info
    environment:
      - REDIS_URL=redis://redis:6379/0
      - MISTRAL_API_KEY=${MISTRAL_API_KEY}
    volumes:
      - ./data:/app/data
      - ./config:/app/config
    depends_on:
      - redis
    deploy:
      resources:
        limits:
          memory: 8G

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

  streamlit:
    build:
      context: .
      dockerfile: Dockerfile.streamlit
    ports:
      - "8501:8501"
    environment:
      - API_URL=http://api:8000
    profiles:
      - with-ui

volumes:
  redis_data:
```

---

## 10. Tests et qualité

### 10.1 Stratégie de tests

| Type | Couverture cible | Outils |
|------|-----------------|--------|
| Unitaires | 80%+ | pytest |
| Intégration | Endpoints API | pytest + httpx |
| E2E | Flux complets | pytest + fixtures PDF |

### 10.2 Fixtures de test

```
tests/fixtures/
├── simple/
│   ├── text_only.pdf
│   └── simple_table.pdf
├── medium/
│   ├── multi_column.pdf
│   └── mixed_content.pdf
├── complex/
│   ├── technical_report.pdf
│   ├── presentation.pdf
│   └── scanned_document.pdf
└── edge_cases/
    ├── empty.pdf
    ├── corrupted.pdf
    └── formulas.pdf
```

---

## 11. Ajout d'un nouvel extracteur

Cette section explique comment ajouter un nouvel extracteur au système.

### 11.1 Créer la classe d'extracteur

Créer un fichier dans `src/extractors/` :

```python
# src/extractors/mon_extracteur.py

from pathlib import Path
from typing import Optional
from src.extractors.base import BaseExtractor, ExtractionResult

class MonExtracteur(BaseExtractor):
    """Mon nouvel extracteur personnalisé."""
    
    name = "mon_extracteur"
    version = "1.0.0"
    
    def __init__(self, config: Optional[dict] = None):
        """Initialise l'extracteur avec sa configuration."""
        self.config = config or {}
        # Initialiser les ressources nécessaires
        self._model = None
    
    def extract(
        self, 
        file_path: Path, 
        options: Optional[dict] = None
    ) -> ExtractionResult:
        """Extrait le contenu d'un PDF.
        
        Args:
            file_path: Chemin vers le fichier PDF
            options: Options spécifiques à cette extraction
            
        Returns:
            ExtractionResult avec le markdown et les métadonnées
        """
        import time
        start_time = time.time()
        
        # Fusionner config par défaut et options
        opts = {**self.config, **(options or {})}
        
        try:
            # === VOTRE LOGIQUE D'EXTRACTION ICI ===
            # Exemple minimal :
            markdown = "# Contenu extrait\n\nTexte..."
            
            # Extraire les métadonnées
            metadata = {
                "pages": 1,
                "title": "Document",
            }
            
            # Extraire les images (liste de Paths)
            images = []
            
            # Extraire les tables (liste de dicts)
            tables = []
            
            # Calculer un score de confiance
            confidence = 0.85
            
            return ExtractionResult(
                markdown=markdown,
                metadata=metadata,
                images=images,
                tables=tables,
                confidence_score=confidence,
                extraction_time=time.time() - start_time,
                extractor_name=self.name,
                extractor_version=self.version,
                warnings=[],
                errors=[]
            )
            
        except Exception as e:
            return ExtractionResult(
                markdown="",
                metadata={},
                images=[],
                tables=[],
                confidence_score=0.0,
                extraction_time=time.time() - start_time,
                extractor_name=self.name,
                extractor_version=self.version,
                warnings=[],
                errors=[str(e)]
            )
    
    def is_available(self) -> bool:
        """Vérifie si l'extracteur est disponible.
        
        Returns:
            True si toutes les dépendances sont installées
        """
        try:
            # Vérifier que les dépendances sont présentes
            # import ma_dependance
            return True
        except ImportError:
            return False
    
    def get_capabilities(self) -> dict:
        """Retourne les capacités de l'extracteur.
        
        Returns:
            Dict décrivant ce que l'extracteur peut faire
        """
        return {
            "ocr": True,
            "tables": True,
            "formulas": False,
            "images": True,
            "languages": ["fra", "eng"],
            "max_pages": 100,
            "gpu_acceleration": False
        }
```

### 11.2 Enregistrer l'extracteur

Ajouter dans `config/settings.yaml` :

```yaml
extractors:
  # ... extracteurs existants ...
  
  mon_extracteur:
    enabled: true
    priority: 4           # Priorité (1 = plus haute)
    config:
      option_1: "valeur"
      option_2: true
```

### 11.3 Ajouter au registre

Modifier `src/extractors/__init__.py` :

```python
from .base import BaseExtractor, ExtractionResult
from .docling_extractor import DoclingExtractor
from .mineru_extractor import MinerUExtractor
from .mistral_extractor import MistralExtractor
from .mon_extracteur import MonExtracteur  # Ajouter

# Registre des extracteurs disponibles
EXTRACTORS = {
    "docling": DoclingExtractor,
    "mineru": MinerUExtractor,
    "mistral": MistralExtractor,
    "mon_extracteur": MonExtracteur,  # Ajouter
}
```

### 11.4 Tester l'extracteur

```bash
# Via l'endpoint de test
curl -X POST http://localhost:8000/api/v1/test-extractor \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com/test.pdf",
    "extractor": "mon_extracteur",
    "options": {"option_1": "test"},
    "include_timing": true
  }'

# Via les tests unitaires
pytest tests/test_extractors.py::test_mon_extracteur -v
```

### 11.5 Utiliser en comparaison

```bash
# Comparer avec les extracteurs existants
curl -X POST http://localhost:8000/api/v1/extract \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com/test.pdf",
    "options": {
      "extractors": ["docling", "mon_extracteur"],
      "force_complexity": "complex"
    }
  }'
```

### 11.6 Bonnes pratiques

1. **Toujours implémenter `is_available()`** pour vérifier les dépendances
2. **Retourner des erreurs explicites** dans `ExtractionResult.errors`
3. **Mesurer le temps d'extraction** pour le monitoring
4. **Calculer un score de confiance** réaliste
5. **Documenter les options** supportées dans `get_capabilities()`
6. **Écrire des tests unitaires** avant d'utiliser en production

---

## 12. Évolutivité

### 12.1 Points d'extension prévus

1. **Nouveaux extracteurs** - Via le système de plugins (section 11)
2. **Nouveaux formats de sortie** - HTML, JSON-LD, DocTags
3. **Pré-processeurs** - Deskew, denoising, contrast
4. **Post-processeurs** - Spell-check, NER, summarization
5. **Intégrations** - n8n, Zapier, Make

### 12.2 Roadmap future (hors scope v1)

| Feature | Priorité | Effort |
|---------|----------|--------|
| Support DOCX/PPTX natif | Haute | Moyen |
| Interface CLI complète | Moyenne | Faible |
| Mode batch (100+ docs) | Moyenne | Élevé |
| GPU acceleration (CUDA) | Basse | Élevé |
| Auto-learning des préférences | Basse | Élevé |

---

## 📝 Notes finales

Ce document constitue la spécification de référence pour le développement du module `pdf-to-markdown-extractor`. Toute modification significative doit être reflétée ici avant implémentation.

**Version** : 1.1.0  
**Dernière mise à jour** : 2025-12-30  
**Auteur** : Rolland MELET / Claude

### Changelog

- **v1.1.0** (2025-12-30)
  - Ajout du paramètre `extraction_strategy` (fallback/parallel_local/parallel_all/hybrid)
  - Ajout de l'endpoint `/api/v1/test-extractor` pour tester un extracteur isolément
  - Ajout de l'endpoint `/api/v1/extractors` pour lister les extracteurs
  - Nouvelle section 5 "Configuration" avec YAML complet
  - Nouvelle section 11 "Ajout d'un nouvel extracteur"
  - Support résultat inline avec `inline=true`
  - Mise à jour interface arbitrage pour 3 extracteurs
  
- **v1.0.0** (2025-12-30)
  - Version initiale des spécifications
