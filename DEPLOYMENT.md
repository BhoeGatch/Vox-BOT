# Deploy to GitHub

Follow these steps to upload your production-ready WNS Vox BOT to GitHub:

## 1. Create GitHub Repository

1. Go to [GitHub.com](https://github.com)
2. Click "New repository" (+ icon in top right)
3. Repository details:
   - **Name**: `wns-vox-bot` or `chatbot-production`
   - **Description**: "Production-ready enterprise document intelligence system"
   - **Visibility**: Choose Private or Public
   - **Initialize**: Leave unchecked (we already have files)
4. Click "Create repository"

## 2. Connect Local Repository to GitHub

After creating the repository, GitHub will show you commands. Use these:

```bash
# Add the remote origin (replace with your actual repository URL)
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git

# Push to GitHub
git push -u origin main
```

## 3. Repository Setup on GitHub

Once uploaded, configure your repository:

### Enable Features
- Go to Settings → Features
- Enable Issues, Wiki, Discussions (optional)
- Enable Security alerts

### Add Repository Description
- Click the gear icon next to About
- Add description: "Production-ready enterprise document intelligence system"
- Add topics: `python`, `streamlit`, `nlp`, `enterprise`, `production-ready`
- Add website URL (if deployed)

### Protection Rules (Recommended)
- Go to Settings → Branches
- Add branch protection rule for `main`:
  - Require pull request reviews
  - Require status checks
  - Restrict pushes to main

## 4. GitHub Actions CI/CD (Optional)

Create `.github/workflows/ci.yml` for automated testing:

```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.8, 3.9, '3.10']

    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v3
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest pytest-cov
    
    - name: Run tests
      run: |
        pytest --cov=. --cov-report=xml
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml

  docker:
    runs-on: ubuntu-latest
    needs: test
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Build Docker image
      run: docker build -t wns-vox-bot .
    
    - name: Test Docker image
      run: |
        docker run --rm -d --name test-container -p 8501:8501 wns-vox-bot
        sleep 30
        curl -f http://localhost:8501/health || exit 1
        docker stop test-container
```

## 5. Documentation

Your repository is now complete with:

- ✅ **Production-ready code** with enterprise features
- ✅ **Comprehensive README** with installation and deployment guides  
- ✅ **Docker support** with Dockerfile and docker-compose.yml
- ✅ **Environment configuration** with .env.example
- ✅ **Proper .gitignore** for Python projects
- ✅ **Security features** with validation and logging
- ✅ **Error handling** with circuit breakers
- ✅ **Performance monitoring** and health checks

## 6. Next Steps

After uploading to GitHub:

1. **Test the deployment** using the Docker setup
2. **Configure environment** variables for your production environment
3. **Set up monitoring** and alerts for production use
4. **Create deployment documentation** for your team
5. **Add integration tests** for continuous deployment

## 7. Team Collaboration

For team development:

1. **Create branches** for features: `feature/new-search-algorithm`
2. **Use pull requests** for code reviews
3. **Tag releases** for version management: `git tag v2.0.0`
4. **Document changes** in release notes

Your WNS Vox BOT is now enterprise-ready and GitHub-ready! 🚀