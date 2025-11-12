#!/bin/bash

cd ~/bench-stop-utility

echo "🔧 Fixing repository issues..."

# Remove existing remote if it's broken
git remote remove origin 2>/dev/null

# Add correct remote
git remote add origin git@github.com:rogerboy38/bench-stop-utility.git

# Verify remote
echo "📡 Remote configured:"
git remote -v

# Add all changes
git add .

# Commit changes
git commit -m "Complete repository: all files, examples, and documentation"

# Push main branch
echo "🚀 Pushing to main branch..."
git push -u origin main --force

echo "✅ Repository fixed!"
echo "💡 Now go to GitHub and set 'main' as default branch"
