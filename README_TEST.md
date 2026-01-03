# Guide de Test - Streamlit UI avec Mistral

## 🎯 Services Actifs

```bash
✅ Redis             (port 6379) - Healthy
✅ FastAPI API       (port 9000) - Running
✅ Celery Worker     - Running (Docling)
✅ Streamlit UI      (port 8501) - Running LOCAL avec Mistral
```

## 🧪 Test Rapide (2 minutes)

### 1. Ouvrir l'Interface

```bash
open http://localhost:8501
```

### 2. Vérifier le Mode Actif

- **Mode Réel** (USE_REAL_API=true) : PAS de banner 🎭
- **Mode Mock** (USE_REAL_API=false) : Banner jaune "MODE DÉMONSTRATION"

### 3. Tester l'Extraction Réelle

1. **Upload** : Onglet 📤 Upload
2. **Fichier** : tests/fixtures/simple/text_only.pdf
3. **Extracteur** : ✅ Docling (coché par défaut)
4. **Optionnel** : ✅ Mistral OCR API (si vous voulez comparer)
5. **Lancer** : Cliquez "🚀 Start Extraction"
6. **Observer** : Barre de progression RÉELLE (3-5 secondes)
7. **Résultat** : Métriques réelles (pages, temps, divergences)

### 4. Voir les Divergences

1. **Créer Job** : Cliquez "🔍 Créer Job & Aller à la Review"
2. **Review** : Onglet 🔍 Review
3. **Observer** :
   - Si 0 divergences → Message "Aucune divergence!" 🎈
   - Si divergences → 3 colonnes avec scoring et médailles

### 5. Voir le PDF avec Highlighting

Dans Review, scrollez vers "📄 Référence PDF" :
- ✅ Page PDF rendue
- ✅ Rectangles rouges sur zones divergentes

## 🔄 Basculer Mode Mock/Réel

### Passer en Mode Mock (pour voir 3 extracteurs)

```bash
# 1. Modifiez .env
USE_REAL_API=false

# 2. Rafraîchissez navigateur (F5)
```

Vous verrez :
- 🎭 Banners "MODE DÉMONSTRATION"
- 3 divergences avec textes différents
- 🥇 Mistral (92%) ⭐
- 🥈 Docling (89%)
- 🥉 Mineru (75%)

### Revenir en Mode Réel

```bash
# 1. Modifiez .env
USE_REAL_API=true

# 2. Rafraîchissez navigateur (F5)
```

## ✅ Vérification Services

```bash
# Tous les services
docker-compose ps

# API Health
curl http://localhost:9000/health

# Streamlit
curl http://localhost:8501
```

## 🎨 Features Testables

- [ ] Stratégies avec Mistral (sidebar → "📋 Détails de la stratégie")
- [ ] Checkbox Mistral avec warning coût
- [ ] Extraction réelle avec vraie progression
- [ ] PDF highlighting avec rectangles rouges
- [ ] 3 extracteurs côte-à-côte avec médailles
- [ ] Navigation entre divergences (Previous/Next)
- [ ] Mode mock clairement signalé

Bon test! 🚀
