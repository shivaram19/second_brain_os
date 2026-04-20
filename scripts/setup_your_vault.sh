#!/bin/bash
# Setup Second Brain OS with YOUR actual Obsidian vault
#
# This script helps users connect Second Brain OS to their real Obsidian vault:
#   1. Prompts for the vault path
#   2. Validates the directory exists and counts markdown notes
#   3. Updates config/paths.yaml with the vault location
#   4. Clears old vector indexes to avoid stale data
#   5. Activates the virtual environment
#   6. Runs `brainos ingest` to index the vault
#
# After running, the user's knowledge base is fully queryable via CLI or
# Claude Desktop MCP integration.
#
# Usage: bash scripts/setup_your_vault.sh

set -e

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║         SETUP: Use Your Real Obsidian Vault                    ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Find Obsidian vault
read -p "Enter path to your Obsidian vault (default: ~/ObsidianVault): " VAULT_PATH
VAULT_PATH="${VAULT_PATH:-~/ObsidianVault}"
VAULT_PATH="${VAULT_PATH/#\~/$HOME}"

if [ ! -d "$VAULT_PATH" ]; then
    echo "❌ Vault not found at: $VAULT_PATH"
    echo ""
    echo "Create one at that path, or provide a different path."
    exit 1
fi

echo "✅ Found vault at: $VAULT_PATH"

# Count notes
NOTE_COUNT=$(find "$VAULT_PATH" -name "*.md" -type f | wc -l)
echo "   📝 Contains $NOTE_COUNT notes"
echo ""

# Update config
CONFIG_FILE="config/paths.yaml"
if [ -f "$CONFIG_FILE" ]; then
    # Update the vault path in paths.yaml
    sed -i '' "s|obsidian_vault: .*|obsidian_vault: \"$VAULT_PATH\"|" "$CONFIG_FILE"
    echo "✅ Updated config/paths.yaml"
fi

# Clear old index
echo "🗑️  Clearing old vector index..."
rm -rf .brainos/vector_db

# Activate venv
source venv/bin/activate

# Ingest
echo ""
echo "⏳ Ingesting vault (this may take a minute for large vaults)..."
python -m brainos.orchestration.cli ingest

echo ""
echo "✅ Ready to query!"
echo ""
echo "Try:"
echo "  brainos ask \"your question here\""
echo "  brainos graph-stats"
echo ""

deactivate
