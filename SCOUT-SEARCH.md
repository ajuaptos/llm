# Scout Search Configuration Guide

The Scout agent can search the internet using two methods:

## 🔍 Search Methods

### Method 1: Google Custom Search API (Recommended for Production)

**Pros:**
- ✅ Most accurate results
- ✅ Better relevance ranking
- ✅ Reliable and fast
- ✅ Structured data
- ✅ 100 free queries/day

**Cons:**
- ❌ Requires API key setup
- ❌ Limited free tier
- ❌ Need Google Cloud account

**Setup Instructions:**

1. **Get Google API Key:**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing
   - Enable "Custom Search API"
   - Navigate to "Credentials"
   - Create API Key

2. **Create Custom Search Engine:**
   - Go to [Programmable Search Engine](https://programmablesearchengine.google.com/)
   - Click "Add" to create new search engine
   - Choose "Search the entire web"
   - Get your "Search engine ID" (cx parameter)

3. **Configure Application:**
   Edit `.env` file:
   ```bash
   GOOGLE_API_KEY=your_actual_api_key_here
   GOOGLE_CSE_ID=your_search_engine_id_here
   ```

### Method 2: Public Web Scraping (Works Out of the Box!)

**Pros:**
- ✅ No API key required
- ✅ Works immediately
- ✅ No rate limits
- ✅ Free forever
- ✅ Multiple search engines as fallback

**Cons:**
- ❌ Slightly slower
- ❌ Results may vary
- ❌ Dependent on public services

**How It Works:**
The system automatically uses web scraping when Google API is not configured:

1. **Primary:** DuckDuckGo HTML search (no API needed)
2. **Fallback:** Public Searx instances
3. **Smart caching:** Reduces redundant searches

**No Setup Required!** Just start using the application.

## 🎯 How Scout Decides to Search

The Scout agent analyzes every response and triggers search when:

### 1. Uncertainty Detection
```python
Phrases like:
- "I don't know"
- "I'm not sure"
- "I don't have access to"
- "I cannot confirm"
- "unclear"
```

### 2. Time-Sensitive Queries
```python
Patterns like:
- "current", "latest", "recent", "today", "now"
- Mentions of specific years (2024, 2025)
- "news", "updates", "happening"
- "price", "stock", "weather", "score"
```

### 3. Confidence Analysis
Uses the smaller LLM (llama3.2:1b) to evaluate if the response is confident or uncertain.

## 📊 Search Flow

```
User Query
    ↓
LLM Generates Response
    ↓
Scout Analyzes Response
    ↓
Is Search Needed?
    ├─ No → Return original response
    └─ Yes → Trigger Search
         ↓
    Google API Configured?
         ├─ Yes → Use Google Custom Search
         └─ No → Use Web Scraping
              ↓
         Get Search Results
              ↓
         Augment Response with LLM
              ↓
         Return Enhanced Response
```

## 🔧 Configuration Options

### Enable/Disable Scout
```bash
SCOUT_ENABLED=true  # or false
```

### Confidence Threshold
```bash
# Lower value = more searches triggered
# Range: 0.0 - 1.0
SCOUT_UNCERTAINTY_THRESHOLD=0.6
```

### Number of Results
```bash
SEARCH_MAX_RESULTS=5
```

### Force Web Scraping
```bash
# Even if Google API is configured, you can force web scraping:
USE_WEB_SCRAPING_FALLBACK=true
```

## 🧪 Testing the Scout

### Test 1: Time-Sensitive Query
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is the current Bitcoin price?"
  }'
```

Expected: Scout should trigger search

### Test 2: General Knowledge
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is Python programming language?"
  }'
```

Expected: Scout should NOT trigger (confident response)

### Test 3: Recent Events
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What happened in the news today?"
  }'
```

Expected: Scout should trigger search

## 📈 Response Format

When Scout triggers, the response includes:

```json
{
  "response": "Enhanced response with current information...",
  "session_id": "abc123",
  "firewall_passed": true,
  "scout_triggered": true,
  "rag_used": false,
  "search_results": [
    {
      "title": "Result Title",
      "snippet": "Result description...",
      "link": "https://example.com",
      "displayLink": "example.com",
      "source": "duckduckgo"
    }
  ]
}
```

## 🌐 Supported Search Sources

### With Web Scraping (No API Key)
1. **DuckDuckGo** (Primary)
   - Privacy-focused
   - No tracking
   - Good results

2. **Searx** (Fallback)
   - Meta-search engine
   - Aggregates multiple sources
   - Public instances available

### With Google API
1. **Google Custom Search**
   - Best accuracy
   - Structured data
   - Commercial-grade

## 🔒 Privacy Considerations

### Web Scraping Mode
- ✅ No API keys stored
- ✅ Direct HTTP requests
- ✅ No user tracking
- ⚠️ Search queries sent to public engines

### Google API Mode
- ⚠️ Google tracks API usage
- ⚠️ Queries logged by Google
- ✅ Better control with your account
- ✅ Can review usage in Cloud Console

## 🚀 Examples

### Example 1: Weather Query (Works Without API)
```
User: "What's the weather in Tokyo?"
LLM: "I don't have access to real-time weather..."
Scout: 🔍 Triggers DuckDuckGo search
Results: [Weather sites, forecasts]
Final: "According to current sources, Tokyo weather is..."
```

### Example 2: Stock Price (Works Without API)
```
User: "Tesla stock price today"
LLM: "I cannot provide real-time stock prices..."
Scout: 🔍 Searches web
Results: [Finance sites, stock data]
Final: "Based on recent data, Tesla is trading at..."
```

### Example 3: Historical Fact (No Search Needed)
```
User: "When was Python created?"
LLM: "Python was created in 1991 by Guido van Rossum..."
Scout: ✓ Response is confident, no search needed
Final: Original response (no augmentation)
```

## 🛠️ Troubleshooting

### Search Not Working

**Check 1: Scout Enabled?**
```bash
# In .env
SCOUT_ENABLED=true
```

**Check 2: Test Search Directly**
```bash
curl http://localhost:8000/api/scout/search?query=test
```

**Check 3: View Logs**
```bash
# Docker
docker-compose logs -f local-ai-rag

# Local
# Check terminal output
```

### Web Scraping Fails

**Issue:** DuckDuckGo not accessible
**Solution:** Application automatically tries Searx fallback

**Issue:** Both sources fail
**Solution:** Configure Google API for reliability

### Getting "Search Unavailable"

This means all search methods failed. Options:
1. Configure Google API (recommended)
2. Check internet connection
3. Try again later (public services may be down)

## 📊 Performance Comparison

| Feature | Google API | Web Scraping |
|---------|-----------|--------------|
| Setup Time | 10-15 min | 0 min |
| Cost | Free tier | Always free |
| Accuracy | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| Speed | Very Fast | Fast |
| Reliability | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| Rate Limits | 100/day free | None |
| Privacy | Medium | High |

## 🎯 Recommendations

**For Development:**
- ✅ Use web scraping (no setup)
- Perfect for testing
- No API key management

**For Production:**
- ✅ Use Google Custom Search API
- More reliable
- Better quality results
- Can handle higher traffic

**For Privacy-Focused:**
- ✅ Use web scraping with DuckDuckGo
- No tracking
- No API keys
- Direct searches

## 🔄 Migration Path

**Starting with Web Scraping:**
1. Start using immediately (no setup)
2. Test Scout functionality
3. Evaluate if sufficient for your needs

**Upgrading to Google API:**
1. Create Google Cloud account
2. Set up Custom Search Engine
3. Add credentials to `.env`
4. Application automatically switches to API
5. Keep web scraping as fallback

## 📝 Best Practices

1. **Start Simple:** Use web scraping first
2. **Monitor Usage:** Check if Scout helps your use case
3. **Upgrade When Needed:** Add Google API for production
4. **Adjust Threshold:** Fine-tune `SCOUT_UNCERTAINTY_THRESHOLD`
5. **Review Logs:** Check which queries trigger searches
6. **User Feedback:** Ask users if enhanced responses help

## 🆘 Support

- Web scraping uses public services (free)
- Google API requires account setup
- Both methods work together (automatic fallback)
- No breaking changes - just works!

---

**Summary:** The Scout agent now works out of the box with web scraping! No API keys needed for basic functionality. Add Google API later for production-grade reliability.
