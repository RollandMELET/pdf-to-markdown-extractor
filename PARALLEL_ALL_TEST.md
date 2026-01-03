# 🧪 Test parallel_all: Docling + Mistral

## Test Réalisé

**Date**: 2026-01-02 23:40
**Job ID**: `23af6455-11b1-4aa2-80aa-ec4e246db2e1`
**Fichier**: text_only.pdf (1 page, 2KB)
**Stratégie**: parallel_all

## ✅ Résultats

### Extraction Parallèle Confirmée

Les logs worker montrent clairement:
```
INFO | Running parallel extraction with 2 extractors: 
      ['DoclingExtractor', 'MistralExtractor']

INFO | Starting MistralExtractor extraction: text_only.pdf
INFO | Extractor MistralExtractor completed (success=True, time=1.09s)
INFO | Extractor DoclingExtractor completed (success=True, time=3.35s)
```

### Métriques

| Métrique | Valeur |
|----------|--------|
| **Extracteurs utilisés** | 2 (Docling + Mistral) |
| **Succès** | 2/2 extractors |
| **Confiance moyenne** | 0.925 (92.5%) |
| **Temps Mistral** | 1.09s |
| **Temps Docling** | 3.35s |
| **Temps total** | 3.39s (parallèle !) |

### Validation Extraction Parallèle

✅ **Mistral a bien été appelé** (1.09s API call)
✅ **Docling a bien été appelé** (3.35s local)
✅ **Exécution parallèle** (total = max(1.09, 3.35) = 3.35s, pas somme)
✅ **Aggregation calculée** (2 extractors, avg confidence 0.925)

## ⚠️ Limitation Backend Actuelle

**all_results non exposé**: L'endpoint `/api/v1/result/{job_id}` ne retourne pas:
- `all_results` (résultats par extracteur)
- `divergences` (comparaison détaillée)

Ces données sont calculées en backend mais pas incluses dans ResultResponse.

**Workaround actuel**: L'UI Streamlit utilise mock data pour les divergences quand all_results est null.

## 🎯 Validation

**L'extraction parallel_all fonctionne!** ✅

Confirmé par:
1. Logs worker: "Running parallel extraction with 2 extractors"
2. Temps d'exécution: cohérent avec parallèle (3.35s vs 4.44s séquentiel)
3. Aggregation: extractor_count=2, successful_count=2

## 💡 Prochaine Étape

Pour voir les vraies divergences Docling vs Mistral dans l'UI:
- Étendre ResultResponse pour inclure `all_results` et `divergences`
- Modifier src/api/routes/extraction.py ligne 349-354
- Ou implémenter réellement l'endpoint /review (actuellement mock)

---

**Test validé**: L'extraction parallèle fonctionne, l'UI est prête, seul l'endpoint /result doit être enrichi.
