# Sentence Cards (English Learning App)

Static offline-first web app for:
- Saving good English sentences you collect (YouTube subtitles, articles, books)
- Extracting target words and storing your translations in a Lexicon
- Reviewing cards with spaced repetition (card refresh mechanism)

## Run Locally

Option A (quick): open `index.html` in a browser.

Option B (recommended, avoids browser file restrictions):
```bash
python3 -m http.server 8080
```
Then open `http://127.0.0.1:8080/english-cards/` from the `eyuansu62.github.io` folder.

## Data

Everything is stored in your browser `localStorage`. Use **Import/Export** to back up or move to another browser/device.

## Sample Deck

In the app, click **Load 50 sample cards (intermediate)** to add starter sentences to your deck.
