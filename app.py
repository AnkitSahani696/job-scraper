from flask import Flask, jsonify, request, render_template
from scrapers.jsearch_scraper import search_jobs as jsearch

app = Flask(__name__)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/search")
def search():
    """
    Job search API — JSearch (RapidAPI) use karta hai.
    Cloud pe perfectly kaam karta hai.

    Query params:
        title    : Job title (required)
        location : City/Country (optional)
        source   : ignored (JSearch sab sources cover karta hai)
        pages    : Kitne pages (default: 2)
    """
    title    = request.args.get("title", "").strip()
    location = request.args.get("location", "").strip()
    pages    = int(request.args.get("pages", 2))

    if not title:
        return jsonify({"error": "Job title required hai!"}), 400

    pages = min(pages, 3)  # Free plan me limit raho

    print(f"\n[Search] Title: '{title}' | Location: '{location}'")

    jobs = jsearch(title, location, pages)

    return jsonify({
        "jobs":     jobs,
        "count":    len(jobs),
        "query":    title,
        "location": location,
        "source":   "all"
    })


@app.route("/health")
def health():
    import os
    key_set = bool(os.environ.get("RAPIDAPI_KEY"))
    return jsonify({
        "status":  "running",
        "api_key": "set" if key_set else "NOT SET!",
        "message": "JobRadar chal raha hai!"
    })


if __name__ == "__main__":
    print("=" * 50)
    print("  JobRadar Server Start Ho Raha Hai...")
    print("  URL: http://localhost:5000")
    print("=" * 50)
    app.run(debug=False, port=5000, use_reloader=False)