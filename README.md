# Chinese English Mixed Writing

A small Streamlit app and CLI tool that uses Google Gemini/Gemma models to turn an English article into mixed English-Chinese writing.

## Run locally

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the Streamlit app:

```bash
streamlit run streamlit_app.py
```

Run the CLI:

```bash
python3 main.py
```

## Notes

- The app defaults to `gemma-3-27b-it`.
- You can provide your API key in the sidebar or via the `GEMINI_API_KEY` environment variable.
- The workflow enforces at least 4.2 seconds between requests to stay under 15 requests per minute.
