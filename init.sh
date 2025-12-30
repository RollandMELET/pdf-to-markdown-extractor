#!/bin/bash
# init.sh - Script d'initialisation pour pdf-to-markdown-extractor
# Utilisé par le pattern Agent Harness pour démarrer chaque session

set -e

echo "=========================================="
echo "  PDF-to-Markdown Extractor - Init"
echo "=========================================="
echo "  Repo: github.com/RollandMELET/pdf-to-markdown-extractor"
echo "=========================================="
echo ""

# 1. Vérifier le répertoire de travail
echo "📁 Répertoire de travail:"
pwd
echo ""

# 2. Vérifier Git
if [ -d ".git" ]; then
    echo "📊 État Git:"
    git status --short
    echo ""
    echo "📜 Derniers commits:"
    git log --oneline -5 2>/dev/null || echo "Aucun commit"
    echo ""
else
    echo "⚠️  Git non initialisé - à faire en Feature #15"
    echo ""
fi

# 3. Vérifier les fichiers clés du projet
echo "📋 Fichiers du projet:"
for file in CLAUDE.md SPEC.md feature_list.json claude-progress.txt; do
    if [ -f "$file" ]; then
        echo "  ✅ $file"
    else
        echo "  ❌ $file (manquant)"
    fi
done
echo ""

# 4. Afficher le statut des features
if [ -f "feature_list.json" ]; then
    echo "📈 Progression des features:"
    total=$(grep -c '"id":' feature_list.json)
    completed=$(grep -c '"status": "passing"' feature_list.json || echo "0")
    pending=$(grep -c '"status": "pending"' feature_list.json || echo "0")
    failing=$(grep -c '"status": "failing"' feature_list.json || echo "0")
    echo "  Total: $total"
    echo "  ✅ Passing: $completed"
    echo "  ⏳ Pending: $pending"
    echo "  ❌ Failing: $failing"
    echo ""
    
    # Afficher les 3 prochaines features pending
    echo "🎯 Prochaines features à implémenter:"
    grep -A5 '"status": "pending"' feature_list.json | grep '"name":' | head -3 | sed 's/.*"name": "\(.*\)".*/  → \1/'
    echo ""
fi

# 5. Vérifier Docker (si disponible)
if command -v docker &> /dev/null; then
    echo "🐳 Docker:"
    if docker info &> /dev/null; then
        echo "  ✅ Docker est actif"
        if [ -f "docker-compose.yml" ]; then
            echo "  📦 Services définis:"
            grep -E "^\s+\w+:" docker-compose.yml | head -5 | sed 's/://' | sed 's/^/    /'
        fi
    else
        echo "  ⚠️  Docker n'est pas démarré"
    fi
else
    echo "🐳 Docker: non installé"
fi
echo ""

# 6. Vérifier Python (si disponible)
if command -v python3 &> /dev/null; then
    echo "🐍 Python:"
    python3 --version
    if [ -f "requirements.txt" ]; then
        echo "  📦 requirements.txt présent"
    fi
fi
echo ""

# 7. Rappel du protocole
echo "=========================================="
echo "  📋 RAPPEL: Protocole de session"
echo "=========================================="
echo ""
echo "1. Lire claude-progress.txt"
echo "2. Consulter feature_list.json"
echo "3. Choisir UNE feature à implémenter"
echo "4. Implémenter, tester, commiter"
echo "5. Mettre à jour feature_list.json (status)"
echo "6. Mettre à jour claude-progress.txt"
echo ""
echo "⚠️  UNE FEATURE PAR SESSION - Ne pas paralléliser!"
echo ""
# 8. Start services (optional)
if [ "$1" = "--start-services" ]; then
    echo "=========================================="
    echo "  🚀 Démarrage des services"
    echo "=========================================="
    echo ""

    if [ -f "docker-compose.yml" ]; then
        echo "📦 Démarrage docker-compose..."
        docker-compose up -d
        echo ""

        echo "⏳ Attente des services (5s)..."
        sleep 5
        echo ""

        echo "📊 État des services:"
        docker-compose ps
        echo ""

        # 9. Health check
        echo "=========================================="
        echo "  🏥 Health Check"
        echo "=========================================="
        echo ""

        # Check Redis
        echo "🔍 Redis:"
        if docker-compose exec -T redis redis-cli ping &> /dev/null; then
            echo "  ✅ Redis is healthy"
        else
            echo "  ❌ Redis health check failed"
        fi

        # Check API
        echo "🔍 API:"
        if curl -sf http://localhost:8000/health &> /dev/null; then
            echo "  ✅ API is healthy"
        else
            echo "  ⚠️  API not reachable (might still be starting)"
        fi

        # Check Worker
        echo "🔍 Worker:"
        if docker-compose exec -T worker celery -A src.core.celery_app inspect ping &> /dev/null; then
            echo "  ✅ Worker is healthy"
        else
            echo "  ⚠️  Worker not reachable"
        fi

        echo ""
    else
        echo "❌ docker-compose.yml non trouvé"
    fi
fi

echo "=========================================="
echo "  ✅ Initialisation terminée"
echo "=========================================="
echo ""
if [ "$1" != "--start-services" ]; then
    echo "💡 Astuce: Utilisez './init.sh --start-services' pour démarrer les services"
    echo ""
fi
