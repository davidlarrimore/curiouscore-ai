# Railway Deployment Guide

This guide covers deploying CuriousCore AI to Railway with PostgreSQL.

## Prerequisites

- Railway account (https://railway.app)
- Railway CLI installed (optional): `npm i -g @railway/cli`
- GitHub repository with your code

## Quick Deploy

### Option 1: Deploy from GitHub (Recommended)

1. **Push your code to GitHub**
   ```bash
   git add .
   git commit -m "Prepare for Railway deployment"
   git push origin main
   ```

2. **Create new project on Railway**
   - Go to https://railway.app/new
   - Click "Deploy from GitHub repo"
   - Select your repository
   - Railway will auto-detect your services

3. **Add PostgreSQL database**
   - In your Railway project, click "+ New"
   - Select "Database" → "PostgreSQL"
   - Railway will automatically set `DATABASE_URL` environment variable

4. **Configure environment variables**

   For the **backend service**, add these variables:
   ```bash
   # Railway provides DATABASE_URL automatically for PostgreSQL

   # Security (REQUIRED)
   SECRET_KEY=<generate-with-openssl-rand-hex-32>

   # LLM Providers (at least one required)
   OPENAI_API_KEY=sk-...
   OPENAI_BASE_URL=https://api.openai.com/v1/
   ANTHROPIC_API_KEY=sk-ant-...
   ANTHROPIC_BASE_URL=https://api.anthropic.com

   # Default LLM
   DEFAULT_LLM_PROVIDER=openai
   DEFAULT_LLM_MODEL=gpt-4o-mini
   ```

   For the **frontend service**, add:
   ```bash
   # Point to your Railway backend URL (get this after backend deploys)
   VITE_API_BASE_URL=https://your-backend-name.railway.app
   ```

5. **Deploy**
   - Railway will automatically deploy both services
   - Backend will be available at: `https://your-backend.railway.app`
   - Frontend will be available at: `https://your-frontend.railway.app`

### Option 2: Deploy with Railway CLI

```bash
# Install Railway CLI
npm i -g @railway/cli

# Login
railway login

# Initialize project
railway init

# Link to project
railway link

# Add PostgreSQL
railway add --database postgres

# Set environment variables
railway variables set SECRET_KEY=$(openssl rand -hex 32)
railway variables set OPENAI_API_KEY=sk-...
# ... add other variables

# Deploy
railway up
```

## Service Configuration

Railway will detect two services:

### Backend Service
- **Root Directory**: `backend/`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- **Port**: Railway sets `$PORT` automatically (usually 8000)

### Frontend Service
- **Root Directory**: `frontend/`
- **Build Command**: `npm install && npm run build`
- **Start Command**: `npm run preview -- --port $PORT --host 0.0.0.0`
- **Port**: Railway sets `$PORT` automatically

## Environment Variables Reference

### Backend Variables (Railway)

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `DATABASE_URL` | Auto-set | PostgreSQL connection (Railway provides this) | `postgresql://user:pass@host:5432/db` |
| `SECRET_KEY` | ✅ Yes | JWT signing key | Generate with `openssl rand -hex 32` |
| `OPENAI_API_KEY` | For OpenAI | OpenAI API key | `sk-proj-...` |
| `OPENAI_BASE_URL` | Optional | OpenAI API base URL | `https://api.openai.com/v1/` |
| `ANTHROPIC_API_KEY` | For Anthropic | Anthropic API key | `sk-ant-...` |
| `ANTHROPIC_BASE_URL` | Optional | Anthropic API URL | `https://api.anthropic.com` |
| `GEMINI_API_KEY` | For Gemini | Google Gemini API key | `...` |
| `DEFAULT_LLM_PROVIDER` | Optional | Default LLM provider | `openai` |
| `DEFAULT_LLM_MODEL` | Optional | Default model name | `gpt-4o-mini` |

### Frontend Variables (Railway)

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `VITE_API_BASE_URL` | ✅ Yes | Backend API URL | `https://your-backend.railway.app` |

## Database Setup

Railway's PostgreSQL includes:
- Automatic backups
- Connection pooling
- Persistent storage
- Health monitoring

### Database Migrations

The FastAPI app automatically creates tables on startup using SQLAlchemy's `create_all()`. No manual migrations needed for initial setup.

To seed initial data or run custom scripts:

```bash
# Connect via Railway CLI
railway run python backend/seed_production_git.py

# Or use the Railway web console
```

## Custom Domain Setup

1. **Backend domain**:
   - Go to your backend service settings
   - Click "Settings" → "Domains"
   - Add custom domain (e.g., `api.yourdomain.com`)
   - Update DNS records as shown

2. **Frontend domain**:
   - Go to your frontend service settings
   - Add custom domain (e.g., `app.yourdomain.com`)
   - Update `VITE_API_BASE_URL` to use your backend custom domain

3. **Update CORS**:
   - Update `backend/app/config.py` to include your custom domains in `cors_origins`

## Monitoring & Logs

### View Logs
```bash
# Via CLI
railway logs

# Via web console
# Go to your service → Deployments → View logs
```

### Metrics
- CPU usage, memory, and network stats available in Railway dashboard
- Set up alerts for errors or resource usage

## Troubleshooting

### Database Connection Errors

```bash
# Check DATABASE_URL is set
railway variables

# Test database connection
railway run python -c "from backend.app.database import engine; print('Connected!')"
```

### Frontend Can't Reach Backend

1. Verify `VITE_API_BASE_URL` is set correctly
2. Check CORS settings in `backend/app/config.py`
3. Ensure backend service is deployed and healthy

### Build Failures

```bash
# Backend: Check Python version in requirements
# Railway uses Python 3.11 by default

# Frontend: Check Node version
# Railway uses Node 18 by default

# Force specific versions with nixpacks config or Dockerfile
```

## Production Checklist

Before going live:

- [ ] Generate strong `SECRET_KEY` (use `openssl rand -hex 32`)
- [ ] Set all required LLM API keys
- [ ] Update `VITE_API_BASE_URL` to production backend URL
- [ ] Configure custom domains (optional)
- [ ] Update CORS origins for production domains
- [ ] Enable Railway's automatic backups for PostgreSQL
- [ ] Set up health check endpoints
- [ ] Test end-to-end user flows
- [ ] Monitor logs for errors

## Scaling

Railway supports automatic scaling:

1. **Horizontal scaling**: Add more instances in service settings
2. **Vertical scaling**: Upgrade RAM/CPU in service settings
3. **Database scaling**: Upgrade PostgreSQL plan as needed

## Cost Optimization

- **Free tier**: $5 credit/month (good for testing)
- **Pro tier**: Pay-as-you-go after free credit
- **Optimize**:
  - Use sleep mode for non-production environments
  - Scale down during low-traffic periods
  - Use connection pooling for database

## Backup & Recovery

Railway automatically backs up PostgreSQL databases:

- **Backups**: Daily automatic backups (retained for 7 days on Pro plan)
- **Restore**: Available through Railway dashboard
- **Manual backup**:
  ```bash
  railway run pg_dump $DATABASE_URL > backup.sql
  ```

## Security Best Practices

1. **Never commit secrets** to Git (use `.env` files locally)
2. **Rotate SECRET_KEY** regularly in production
3. **Use Railway's secret storage** for sensitive variables
4. **Enable 2FA** on Railway account
5. **Restrict database access** to Railway's private network
6. **Use HTTPS only** (Railway provides this automatically)

## Support Resources

- Railway Docs: https://docs.railway.app
- Railway Discord: https://discord.gg/railway
- Railway Status: https://railway.instatus.com

## Migration from Other Platforms

### From Heroku
Railway is Heroku-compatible. Import your Heroku app directly:
```bash
railway add --heroku <heroku-app-name>
```

### From Vercel/Netlify
1. Export your database
2. Import to Railway PostgreSQL
3. Update environment variables
4. Deploy services to Railway

---

For local development with PostgreSQL, see [DOCKER.md](./DOCKER.md).
