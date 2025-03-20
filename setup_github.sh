#!/bin/bash

# Initialize Git repository if not already done
if [ ! -d .git ]; then
    echo "Initializing Git repository..."
    git init
else
    echo "Git repository already initialized."
fi

# Ensure .gitignore is properly set up
if [ ! -f .gitignore ]; then
    echo "Creating .gitignore file..."
    echo "# Python" > .gitignore
    echo "__pycache__/" >> .gitignore
    echo "*.py[cod]" >> .gitignore
    echo "*$py.class" >> .gitignore
    echo "venv/" >> .gitignore
    echo "*.env" >> .gitignore
    echo "config.py" >> .gitignore
    echo "# Node.js" >> .gitignore
    echo "node_modules/" >> .gitignore
    echo "# IDE files" >> .gitignore
    echo ".idea/" >> .gitignore
    echo ".vscode/" >> .gitignore
fi

# Make sure config.py is not tracked
echo "Ensuring config.py is not tracked..."
if [ -f config.py ]; then
    git rm --cached config.py 2>/dev/null || true
fi

# Add all files
echo "Adding files to Git..."
git add .

# Check for config.py in staged files
if git diff --cached --name-only | grep -q "config.py"; then
    echo "WARNING: config.py is still being tracked. Removing from staged files..."
    git rm --cached config.py
fi

# Make initial commit
echo "Making initial commit..."
git commit -m "Initial commit of IntelliAssistant"

# Instructions for setting up remote repository
echo ""
echo "Next steps:"
echo "1. Create a new repository on GitHub (don't initialize with README, .gitignore, or license)"
echo "2. Run the following commands to push to GitHub:"
echo "   git remote add origin https://github.com/yourusername/IntelliAssistant.git"
echo "   git branch -M main"
echo "   git push -u origin main"
echo ""
echo "Replace 'yourusername' with your actual GitHub username." 