# Deployment Guide

This guide shows you how to deploy the AAP Sizing Calculator to various free hosting platforms.

## Quick Deploy Options

### Option 1: Railway (Recommended - Easiest)

**Free tier:** 500 hours/month, no credit card required

1. Go to [Railway](https://railway.app/)
2. Click "Start a New Project"
3. Select "Deploy from GitHub repo"
4. Choose your `aap-sizing-guide` repository
5. Railway auto-detects the Dockerfile and deploys
6. Get your live URL in seconds!

**One-click deploy:**
[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new/template?template=https://github.com/arnav3000/aap-sizing-guide)

---

### Option 2: Render

**Free tier:** 750 hours/month, sleeps after 15 min of inactivity

1. Go to [Render](https://render.com/)
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Render auto-detects the `render.yaml` configuration
5. Click "Deploy"
6. Access your app at the provided URL

**One-click deploy:**
[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/arnav3000/aap-sizing-guide)

---

### Option 3: Docker (Self-hosted)

**Run locally with Docker:**

```bash
# Build the image
docker build -t aap-sizing-calculator .

# Run the container
docker run -p 5002:5002 aap-sizing-calculator

# Access at http://localhost:5002
```

**Push to Docker Hub:**

```bash
# Tag the image
docker tag aap-sizing-calculator yourusername/aap-sizing-calculator

# Push to Docker Hub
docker push yourusername/aap-sizing-calculator

# Others can pull and run
docker pull yourusername/aap-sizing-calculator
docker run -p 5002:5002 yourusername/aap-sizing-calculator
```

---

### Option 4: Fly.io

**Free tier:** 3 VMs with 256MB RAM each

```bash
# Install flyctl
curl -L https://fly.io/install.sh | sh

# Login
flyctl auth login

# Launch app (from project directory)
flyctl launch

# Deploy
flyctl deploy

# Open in browser
flyctl open
```

---

### Option 5: Heroku

**Note:** Heroku no longer has a free tier, but offers $5/month hobby tier

```bash
# Install Heroku CLI
# Visit: https://devcenter.heroku.com/articles/heroku-cli

# Login
heroku login

# Create app
heroku create your-app-name

# Deploy
git push heroku main

# Open in browser
heroku open
```

---

## Environment Variables

The app currently doesn't require any environment variables, but you can configure:

```
FLASK_ENV=production
PORT=5002
```

## Port Configuration

The app runs on port **5002** by default. Some platforms (like Heroku) require dynamic port binding:

Update `app.py` line 88 to:
```python
port = int(os.environ.get('PORT', 5002))
app.run(debug=False, host='0.0.0.0', port=port)
```

## Production Considerations

1. **Debug Mode:** Set `debug=False` in production
2. **WSGI Server:** Use gunicorn instead of Flask's dev server:
   ```bash
   pip install gunicorn
   gunicorn app:app
   ```
3. **Environment Variables:** Set `FLASK_ENV=production`
4. **HTTPS:** Most platforms provide free SSL/TLS

## Recommended: Railway or Render

Both offer:
- ✅ Free tier with generous limits
- ✅ Automatic HTTPS
- ✅ GitHub integration
- ✅ Auto-deploy on push
- ✅ Easy environment variable management
- ✅ No credit card required (Railway)

## Support

If you encounter issues deploying:
1. Check the platform's logs
2. Verify all dependencies are in `requirements.txt`
3. Ensure port configuration matches the platform
4. Check that `Dockerfile` builds successfully locally first
