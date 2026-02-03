# alpha-scraper-dashboard
git clone https://github.com/HaritsAcheiz/alpha-scraper-dashboard.git
uv init
uv venv
uv add -r requirements.txt

copy config.py to app/ folder

copy secrets.toml to .streamlit/ folder

uv run streamlit run Dashboard.py