from flask import Flask, jsonify, request, render_template
from scrapers.naukri_scraper   import search_jobs as naukri_search
from scrapers.indeed_scraper   import search_jobs as indeed_search
from scrapers.linkedin_scraper import search_jobs as linkedin_search
import concurrent.futures

app = Flask(__name__)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/search")
def search():
    title    = request.args.get("title", "").strip()
    location = request.args.get("location", "").strip()
    source   = request.args.get("source", "all").lower()
    pages    = int(request.args.get("pages", 2))

    if not title:
        return jsonify({"error": "Job title required hai!"}), 400

    pages = min(pages, 5)

    print(f"\n[Search] Title: '{title}' | Location: '{location}' | Source: '{source}'")

    jobs = []

    if source == "naukri":
        jobs = naukri_search(title, location, pages)

    elif source == "indeed":
        jobs = indeed_search(title, location, pages)

    elif source == "linkedin":
        jobs = linkedin_search(title, location, pages)

    else:
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            naukri_future   = executor.submit(naukri_search,   title, location, pages)
            indeed_future   = executor.submit(indeed_search,   title, location, pages)
            linkedin_future = executor.submit(linkedin_search, title, location, pages)

            naukri_jobs   = naukri_future.result()
            indeed_jobs   = indeed_future.result()
            linkedin_jobs = linkedin_future.result()

        jobs = naukri_jobs + indeed_jobs + linkedin_jobs

        print(
            f"[+] Naukri: {len(naukri_jobs)} | "
            f"Indeed: {len(indeed_jobs)} | "
            f"LinkedIn: {len(linkedin_jobs)} | "
            f"Total: {len(jobs)}"
        )

    return jsonify({
        "jobs": jobs,
        "count": len(jobs),
        "query": title,
        "location": location,
        "source": source
    })


@app.route("/health")
def health():
    return jsonify({
        "status": "running",
        "scrapers": ["Naukri.com", "Indeed.com", "LinkedIn"],
        "message": "Job scraper chal raha hai!"
    })


if __name__ == "__main__":
    print("=" * 50)
    print("  Job Scraper Server Start Ho Raha Hai...")
    print("  Scrapers: Naukri + Indeed + LinkedIn")
    print("  URL: http://localhost:5000")
    print("=" * 50)
    # debug=False -- watchdog band, server stable rahega
    # use_reloader=False -- file changes pe restart nahi hoga
    app.run(debug=False, port=5000, use_reloader=False)