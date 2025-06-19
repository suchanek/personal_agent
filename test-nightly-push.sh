#!/bin/bash

# Dry run script to test the nightly push logic
echo "🧪 Testing Nightly Push Logic (Dry Run)"
echo "======================================="

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "❌ Error: Not in a git repository"
    exit 1
fi

echo "📍 Current working directory: $(pwd)"
echo ""

# Step 1: Get current branch name (same as workflow)
echo "🔍 Step 1: Getting current branch name..."
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
echo "✅ Current active branch: $CURRENT_BRANCH"
echo ""

# Step 2: Get current commit hash (same as workflow)
echo "🔍 Step 2: Getting current commit hash..."
CURRENT_COMMIT=$(git rev-parse HEAD)
echo "✅ Current commit: $CURRENT_COMMIT"
echo ""

# Step 3: Check if nightly branch exists locally
echo "🔍 Step 3: Checking if nightly branch exists..."
if git show-ref --verify --quiet refs/heads/nightly; then
    echo "✅ Nightly branch exists locally"
    LOCAL_NIGHTLY_EXISTS=true
else
    echo "ℹ️  Nightly branch does not exist locally"
    LOCAL_NIGHTLY_EXISTS=false
fi

# Step 4: Check if nightly branch exists remotely
echo ""
echo "🔍 Step 4: Checking if nightly branch exists remotely..."
if git ls-remote --heads origin nightly | grep -q nightly; then
    echo "✅ Nightly branch exists remotely"
    REMOTE_NIGHTLY_EXISTS=true
    REMOTE_NIGHTLY_COMMIT=$(git ls-remote --heads origin nightly | cut -f1)
    echo "   Remote nightly commit: $REMOTE_NIGHTLY_COMMIT"
else
    echo "ℹ️  Nightly branch does not exist remotely"
    REMOTE_NIGHTLY_EXISTS=false
fi
echo ""

# Step 5: Show what would happen (dry run)
echo "🎯 Step 5: What would happen in the actual workflow..."
echo "---------------------------------------------------"

if [ "$REMOTE_NIGHTLY_EXISTS" = true ]; then
    echo "📝 Would execute: git checkout -B nightly origin/nightly"
    echo "   (Create/switch to nightly branch based on remote)"
else
    echo "📝 Would execute: git checkout -b nightly"
    echo "   (Create new nightly branch)"
fi

echo "📝 Would execute: git reset --hard $CURRENT_COMMIT"
echo "   (Reset nightly branch to current branch's commit)"

echo "📝 Would execute: git push origin nightly --force"
echo "   (Force push to remote nightly branch)"
echo ""

# Step 6: Show the difference
echo "🔄 Step 6: Showing differences..."
echo "--------------------------------"

if [ "$REMOTE_NIGHTLY_EXISTS" = true ]; then
    if [ "$REMOTE_NIGHTLY_COMMIT" = "$CURRENT_COMMIT" ]; then
        echo "✅ Remote nightly is already up to date with current branch"
        echo "   No changes would be pushed"
    else
        echo "🔄 Remote nightly would be updated:"
        echo "   From: $REMOTE_NIGHTLY_COMMIT"
        echo "   To:   $CURRENT_COMMIT"
        
        # Show commit difference if possible
        echo ""
        echo "📊 Commit difference:"
        if git cat-file -e "$REMOTE_NIGHTLY_COMMIT" 2>/dev/null; then
            git log --oneline "$REMOTE_NIGHTLY_COMMIT..$CURRENT_COMMIT" | head -5
            if [ $(git rev-list --count "$REMOTE_NIGHTLY_COMMIT..$CURRENT_COMMIT") -gt 5 ]; then
                echo "   ... and $(( $(git rev-list --count "$REMOTE_NIGHTLY_COMMIT..$CURRENT_COMMIT") - 5 )) more commits"
            fi
        else
            echo "   (Cannot show diff - remote commit not available locally)"
        fi
    fi
else
    echo "🆕 Would create new nightly branch with:"
    echo "   Branch: $CURRENT_BRANCH"
    echo "   Commit: $CURRENT_COMMIT"
fi

echo ""
echo "✅ Dry run completed successfully!"
echo ""
echo "💡 To run the actual workflow manually:"
echo "   1. Go to your GitHub repository"
echo "   2. Navigate to Actions tab"
echo "   3. Find 'Nightly Branch Push' workflow"
echo "   4. Click 'Run workflow' button"
