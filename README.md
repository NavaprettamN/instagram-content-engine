# Instagram Content Engine

This project orchestrates multiple AI agents to research trends, generate content, design visuals, and publish to Instagram automatically.

## Structure

- `dashboard.py` - Streamlit dashboard (main interface)
- `orchestrator.py` - Coordinates all agents; typically run on a schedule
- `config.yaml` - Configuration for API keys, niche, etc.

### Agents

Located in `agents/`:
- `research_agent.py` - Trend scanning + idea generation
- `content_agent.py` - Full content generation
- `design_agent.py` - Image/carousel creation
- `publishing_agent.py` - Instagram API publishing
- `analytics_agent.py` - Metrics pulling + AI analysis
- `hashtag_agent.py` - Hashtag set generation

### Other

- `templates/` - HTML templates for posts
- `generated_content/` - Output directory for generated images
- `data/` - SQLite database
- `fonts/` - Custom fonts for image generation

## Getting Started

1. Create a virtual environment and install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Populate `.env` with your API keys.
3. Configure `config.yaml` as needed.
4. Run the dashboard or orchestrator to begin.

## License

MIT License. Feel free to adapt for your own use.
