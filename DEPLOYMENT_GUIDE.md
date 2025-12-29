# Production Deployment Guide

Complete guide for deploying CuriousCore AI to production with the Game Master architecture.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Configuration](#environment-configuration)
3. [Database Setup](#database-setup)
4. [Backend Deployment](#backend-deployment)
5. [Frontend Deployment](#frontend-deployment)
6. [LLM Configuration](#llm-configuration)
7. [Performance Optimization](#performance-optimization)
8. [Monitoring & Maintenance](#monitoring--maintenance)

---

## Prerequisites

### Required Services

- **Database**: PostgreSQL 14+ (production) or SQLite (development)
- **LLM Provider**: Anthropic Claude, OpenAI GPT, or Google Gemini
- **Python**: 3.10+
- **Node.js**: 18+

### Recommended Infrastructure

- **Backend**: Cloud hosting (AWS, GCP, Azure, Railway, Render)
- **Frontend**: Static hosting (Vercel, Netlify, Cloudflare Pages)
- **Database**: Managed PostgreSQL (Supabase, Railway, AWS RDS)

---

## Environment Configuration

### Backend Environment Variables

Create `.env` file in `backend/`:

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/dbname
# For development: sqlite+aiosqlite:///./app.db

# Authentication
SECRET_KEY=your-secret-key-here  # Generate with: openssl rand -hex 32
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# LLM Provider (choose at least one)
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=...

# CORS (Frontend URL)
CORS_ORIGINS=https://your-frontend-domain.com,http://localhost:8080

# Optional: Server Configuration
HOST=0.0.0.0
PORT=8000
```

### Frontend Environment Variables

Create `.env` file in `frontend/`:

```bash
VITE_API_BASE_URL=https://your-backend-domain.com
```

For local development:
```bash
VITE_API_BASE_URL=http://localhost:8000
```

---

## Database Setup

### PostgreSQL (Production)

**1. Create Database**:
```sql
CREATE DATABASE curiouscore;
CREATE USER curiouscore_user WITH PASSWORD 'secure-password';
GRANT ALL PRIVILEGES ON DATABASE curiouscore TO curiouscore_user;
```

**2. Update Connection String**:
```bash
DATABASE_URL=postgresql+asyncpg://curiouscore_user:secure-password@localhost:5432/curiouscore
```

**3. Run Migrations**:
```bash
cd backend
source .venv/bin/activate
python -c "from app.database import init_db; import asyncio; asyncio.run(init_db())"
```

**4. Seed Production Challenges**:
```bash
python seed_production_functions.py
python seed_production_git.py
python seed_production_api.py
```

### SQLite (Development Only)

SQLite is suitable for development and testing only. For production, use PostgreSQL.

```bash
DATABASE_URL=sqlite+aiosqlite:///./app.db
```

---

## Backend Deployment

### Option 1: Railway

**1. Install Railway CLI**:
```bash
npm install -g @railway/cli
railway login
```

**2. Create Project**:
```bash
cd backend
railway init
```

**3. Add PostgreSQL**:
```bash
railway add
# Select PostgreSQL
```

**4. Set Environment Variables**:
```bash
railway variables set SECRET_KEY=$(openssl rand -hex 32)
railway variables set ANTHROPIC_API_KEY=sk-ant-...
railway variables set CORS_ORIGINS=https://your-frontend.vercel.app
```

**5. Deploy**:
```bash
railway up
```

### Option 2: Docker

**Create `Dockerfile` in `backend/`**:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Build and Run**:
```bash
docker build -t curiouscore-backend .
docker run -p 8000:8000 --env-file .env curiouscore-backend
```

### Option 3: Manual Deployment

**1. Install Dependencies**:
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**2. Run with Uvicorn**:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

**For production, use a process manager like systemd or supervisor**.

---

## Frontend Deployment

### Option 1: Vercel (Recommended)

**1. Install Vercel CLI**:
```bash
npm install -g vercel
```

**2. Deploy**:
```bash
cd frontend
vercel
```

**3. Set Environment Variable**:
In Vercel dashboard:
- Add `VITE_API_BASE_URL` = `https://your-backend-domain.com`

**4. Redeploy**:
```bash
vercel --prod
```

### Option 2: Netlify

**1. Build**:
```bash
cd frontend
npm run build
```

**2. Deploy via CLI**:
```bash
npm install -g netlify-cli
netlify deploy --prod --dir=dist
```

**3. Set Environment Variable**:
In Netlify dashboard, add `VITE_API_BASE_URL`

### Option 3: Static Hosting

**1. Build**:
```bash
cd frontend
npm run build
```

**2. Upload `dist/` folder** to:
- AWS S3 + CloudFront
- Google Cloud Storage
- Azure Static Web Apps
- Any static hosting service

---

## LLM Configuration

### Choosing a Provider

**Anthropic Claude** (Recommended):
- Best balance of quality and cost
- Excellent at rubric-based evaluation
- Strong instruction following

**OpenAI GPT**:
- Widely available
- Good performance
- Higher cost for evaluation tasks

**Google Gemini**:
- Lower cost
- Good for high-volume
- May need more prompt engineering

### API Key Management

**Production Best Practices**:
1. Use environment variables (never commit keys)
2. Rotate keys regularly
3. Monitor usage and set budget alerts
4. Use separate keys for dev/staging/prod

**Rate Limiting**:
```python
# In app/config.py
class Settings(BaseSettings):
    llm_max_requests_per_minute: int = 60
    llm_timeout_seconds: int = 30
```

### Cost Optimization

**Estimated Costs per Challenge**:
- GM Narration: ~$0.01 per gate (2-3 gates per challenge)
- LEM Evaluation: ~$0.02 per CHAT step (2-3 per challenge)
- Hints: ~$0.01 per hint request

**Total per challenge completion**: $0.05 - $0.10

**Monthly Cost for 1000 completions**: $50 - $100

**Tips**:
- Use cheaper models for development/testing
- Cache common evaluations (future enhancement)
- Monitor and alert on unusual usage

---

## Performance Optimization

### Database Optimization

**Indexes** (automatically created):
- `game_events.session_id` (for event lookup)
- `game_events.sequence_number` (for ordering)
- `session_snapshots.session_id` (for state hydration)

**Snapshot Frequency**:
Current: Every 5 events
- Reduces events to replay
- Balances write overhead

**Connection Pooling**:
```python
# In app/database.py
engine = create_async_engine(
    settings.database_url,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True
)
```

### API Performance

**Response Times (Target)**:
- Session creation: < 100ms
- Session start: < 500ms (with GM narration)
- MCQ submission: < 200ms
- CHAT submission: < 3s (with LEM evaluation)
- State retrieval: < 200ms

**Caching Strategy** (Future):
- Cache challenge definitions (rarely change)
- Cache UI responses for common states
- Use Redis or in-memory cache

### LLM Optimization

**Timeout Configuration**:
```python
# In llm_orchestrator.py
timeout_seconds = 30  # Fail fast for poor UX
```

**Fallback Strategy**:
- On LLM timeout: Return generic message
- On LLM error: Score = 0, session continues
- Never block session progression on LLM failure

---

## Monitoring & Maintenance

### Health Checks

**Backend Health Endpoint**:
```bash
GET /health
```

Returns:
```json
{
  "status": "healthy",
  "database": "connected",
  "timestamp": "2025-12-29T..."
}
```

### Logging

**Important Logs**:
- Session creation/completion
- LLM task execution (with latency)
- Error events (with context)
- Authentication failures

**Log Levels**:
- Production: INFO
- Development: DEBUG

**Example**:
```python
import logging

logger = logging.getLogger(__name__)
logger.info(f"Session {session_id} created for user {user_id}")
logger.error(f"LEM evaluation failed: {error}", exc_info=True)
```

### Metrics to Track

**User Metrics**:
- Session completions
- Average completion time
- Passing rate per challenge
- Most failed steps

**System Metrics**:
- API response times (p50, p95, p99)
- LLM latency and success rate
- Database query performance
- Error rate

**Business Metrics**:
- Daily active users
- Challenge completion rate
- XP earned
- LLM API costs

### Backup Strategy

**Database Backups**:
- Automated daily backups
- Point-in-time recovery enabled
- Test restore procedure monthly

**Event Log**:
- Events are immutable (never delete)
- Archive old sessions to cold storage after 90 days
- Maintain audit trail for compliance

### Security

**Authentication**:
- JWT tokens with short expiration (30 min)
- Refresh token mechanism
- Rate limiting on auth endpoints

**API Security**:
- CORS properly configured
- Input validation on all endpoints
- SQL injection prevention (SQLAlchemy ORM)
- XSS prevention (React escapes by default)

**Secrets Management**:
- Use environment variables
- Never commit secrets
- Rotate keys regularly
- Use secrets manager in production (AWS Secrets Manager, etc.)

---

## Deployment Checklist

### Pre-Deployment

- [ ] Environment variables configured
- [ ] Database created and migrated
- [ ] Production challenges seeded
- [ ] LLM API keys tested
- [ ] CORS origins set correctly
- [ ] Secret key generated and set

### Backend

- [ ] Dependencies installed
- [ ] Database connection tested
- [ ] LLM integration tested
- [ ] Health check endpoint working
- [ ] Logging configured
- [ ] Process manager configured

### Frontend

- [ ] API base URL set correctly
- [ ] Build completes without errors
- [ ] Assets optimized
- [ ] Environment variables set in hosting

### Post-Deployment

- [ ] Verify frontend can reach backend
- [ ] Test user registration and login
- [ ] Complete a full challenge end-to-end
- [ ] Verify LLM evaluation works
- [ ] Check logs for errors
- [ ] Monitor performance metrics

---

## Troubleshooting

### Common Issues

**Frontend can't reach backend**:
- Check CORS configuration
- Verify API_BASE_URL is correct
- Check backend is running and accessible

**LLM evaluation fails**:
- Verify API keys are set
- Check LLM provider status
- Review timeout settings
- Check logs for specific errors

**Database connection errors**:
- Verify connection string format
- Check database is running
- Verify credentials
- Check network/firewall rules

**Session replay errors**:
- Check event log integrity
- Verify snapshot creation is working
- Review sequence numbers for gaps

---

## Scaling Considerations

### Horizontal Scaling

**Backend**:
- Stateless design allows multiple instances
- Load balancer distributes requests
- Session state in database (not in memory)

**Database**:
- Read replicas for GET /sessions/{id}/state
- Write to primary for events
- Connection pooling per instance

### Vertical Scaling

**When to Scale Up**:
- LLM requests queueing
- Database CPU > 80%
- Response times degrading

**Resource Allocation**:
- Backend: 2-4 CPU cores, 4-8GB RAM per instance
- Database: 4-8 CPU cores, 16-32GB RAM
- Frontend: Static hosting (scales automatically)

---

## Support & Maintenance

### Regular Tasks

**Weekly**:
- Review error logs
- Check LLM API usage and costs
- Monitor user feedback

**Monthly**:
- Review performance metrics
- Test backup restore
- Update dependencies
- Rotate API keys

**Quarterly**:
- Security audit
- Cost optimization review
- Capacity planning

---

## Summary

**Production deployment requires**:
1. Proper environment configuration
2. Managed database (PostgreSQL)
3. LLM API access (Anthropic/OpenAI/Gemini)
4. Secure secrets management
5. Monitoring and logging
6. Regular maintenance

**The architecture is production-ready** with:
- Event sourcing for reliability
- Deterministic state replay
- Graceful LLM error handling
- Stateless API design
- Comprehensive error handling

**For help**: Review architecture docs and commit history for implementation details.
