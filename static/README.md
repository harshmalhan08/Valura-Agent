# Valura AI - System Flow Visualization UI

## Overview

This is a real-time visualization interface that shows how user queries travel through the entire Valura AI agent ecosystem. Watch each step of the pipeline in action with beautiful animations and detailed metrics.

## Features

### 🎯 Real-Time Flow Visualization
- **Step-by-step tracking**: See your query progress through each component
- **Live status updates**: Active, completed, and error states with visual feedback
- **Animated transitions**: Smooth animations show the flow of data

### 📊 Detailed Metrics
- **Component timing**: See how long each step takes
- **Performance cards**: Total time, safety guard, classifier, and agent metrics
- **Latency tracking**: Monitor first token and end-to-end latency

### 🔍 Pipeline Stages

1. **Request Received** 📥
   - Query validation and user loading
   
2. **Safety Guard** 🛡️
   - Pattern-based safety check (<10ms)
   - Blocks harmful queries
   - Allows educational queries
   
3. **Intent Classifier** 🧠
   - OpenAI structured outputs
   - Entity extraction
   - Conversation context
   
4. **Router** 🔀
   - Dispatches to specialist agents
   - 10 agent types supported
   
5. **Agent Processing** 🤖
   - Portfolio Health Agent (fully implemented)
   - Market data via MCP
   - LLM-generated insights
   
6. **Response Generated** ✅
   - Streaming response delivery
   - Session management

### 💡 Example Queries

The UI includes pre-built example queries:
- Portfolio health checks
- Concentration risk analysis
- Investment advice
- Safety guard tests (harmful queries)
- Educational queries

### 📈 Results Display

- **Classification Results**: Intent, target agent, confidence, entities
- **Agent Response**: Full JSON response with all data
- **Performance Metrics**: Detailed timing breakdown

## Usage

### Starting the Server

```bash
# From project root
cd valura-ai-ai-engineer-assignment-harshmalhan08-main/valura-ai-ai-engineer-assignment-harshmalhan08-main

# Start the FastAPI server
py -3.12 -m uvicorn src.api.app:app --reload --host 0.0.0.0 --port 8000
```

### Accessing the UI

Open your browser and navigate to:
```
http://localhost:8000
```

The UI will automatically load and be ready to use.

### Making Queries

1. **Select a user profile** from the dropdown
2. **Enter your query** or click an example query
3. **Click "Send Query"** to start processing
4. **Watch the flow** as your query travels through the system
5. **View results** in the results panel below

## Technical Details

### Architecture

- **Frontend**: Pure HTML/CSS/JavaScript (no frameworks)
- **Backend**: FastAPI with SSE (Server-Sent Events)
- **Communication**: Real-time streaming via SSE
- **Styling**: Modern gradient design with animations

### SSE Events

The UI listens for these events from the backend:

- `safety_check`: Safety guard verdict
- `classification`: Intent classification result
- `routing`: Router dispatch information
- `agent_start`: Agent processing started
- `data`: Agent response data
- `done`: Processing complete with metrics
- `error`: Error occurred

### Browser Compatibility

- Chrome/Edge: ✅ Full support
- Firefox: ✅ Full support
- Safari: ✅ Full support
- IE11: ❌ Not supported (uses modern JavaScript)

## Customization

### Changing Colors

Edit the CSS variables in `index.html`:

```css
/* Primary gradient */
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);

/* Active step color */
border-left-color: #667eea;

/* Completed step color */
border-left-color: #4caf50;

/* Error step color */
border-left-color: #f44336;
```

### Adding New Example Queries

Add to the example queries section:

```html
<div class="example-query" onclick="setQuery('Your new query here')">
    Your new query here
</div>
```

### Modifying Step Icons

Change the emoji icons in the flow steps:

```html
<div class="step-icon">🆕</div>
```

## Troubleshooting

### UI Not Loading

1. Check server is running: `http://localhost:8000/health`
2. Check browser console for errors (F12)
3. Verify `static/` directory exists

### CORS Errors

The server has CORS enabled for all origins. If you still see CORS errors:

1. Check the server logs
2. Verify the request URL is correct
3. Try clearing browser cache

### SSE Connection Issues

If the stream disconnects:

1. Check network tab in browser dev tools
2. Verify server is still running
3. Check for rate limiting (max 10 requests/minute)

### No Response from Agent

If the agent doesn't respond:

1. Check MCP client is connected
2. Verify Azure OpenAI credentials in `.env`
3. Check server logs for errors

## Performance

- **Safety Guard**: <10ms (target: <10ms) ✅
- **Intent Classifier**: ~2-3s (Azure OpenAI)
- **Agent Processing**: 1-5s (depends on complexity)
- **Total End-to-End**: 3-8s typical

## Security

- ⚠️ **Development Only**: CORS is set to allow all origins
- 🔒 **Production**: Update CORS settings to specific origins
- 🛡️ **Rate Limiting**: 10 requests per minute per user
- 🔐 **No Secrets**: UI doesn't expose API keys

## Future Enhancements

- [ ] WebSocket support for bidirectional communication
- [ ] Dark/light theme toggle
- [ ] Export results to JSON/CSV
- [ ] Query history and replay
- [ ] Real-time performance graphs
- [ ] Multi-language support
- [ ] Mobile-responsive design improvements

## License

MIT License - See LICENSE file for details

---

**Built with ❤️ for the Valura AI Agent Ecosystem**
