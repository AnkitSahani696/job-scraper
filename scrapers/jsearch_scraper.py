import requests
import os
from utils.matcher import is_relevant

RAPIDAPI_KEY  = os.environ.get("RAPIDAPI_KEY", "")
RAPIDAPI_HOST = "jsearch.p.rapidapi.com"


def search_jobs(job_title: str, location: str = "", pages: int = 2) -> list:
    """
    JSearch API se real jobs fetch karta hai.
    Cloud pe perfectly kaam karta hai — Selenium ki zaroorat nahi.
    """
    all_jobs = []

    if not RAPIDAPI_KEY:
        print("[JSearch] ERROR: RAPIDAPI_KEY not set!")
        return []

    for page in range(1, pages + 1):
        try:
            query = job_title
            if location:
                query += f" in {location}"

            url = "https://jsearch.p.rapidapi.com/search"
            params = {
                "query":           query,
                "page":            str(page),
                "num_pages":       "1",
                "date_posted":     "month",
                "country":         "in",   # India by default
            }

            # Location ke hisaab se country set karo
            loc_lower = location.lower() if location else ""
            if any(x in loc_lower for x in ["usa","united states","california","new york","texas","florida"]):
                params["country"] = "us"
            elif any(x in loc_lower for x in ["uk","united kingdom","england","london"]):
                params["country"] = "gb"
            elif any(x in loc_lower for x in ["canada","ontario","toronto"]):
                params["country"] = "ca"
            elif any(x in loc_lower for x in ["australia","sydney","melbourne"]):
                params["country"] = "au"
            elif any(x in loc_lower for x in ["germany","berlin","munich"]):
                params["country"] = "de"
            elif any(x in loc_lower for x in ["singapore"]):
                params["country"] = "sg"
            elif any(x in loc_lower for x in ["uae","dubai","abu dhabi"]):
                params["country"] = "ae"
            elif "remote" in loc_lower:
                params["employment_types"] = "FULLTIME,PARTTIME,CONTRACTOR,INTERN"
                params["remote_jobs_only"]  = "true"

            headers = {
                "X-RapidAPI-Key":  RAPIDAPI_KEY,
                "X-RapidAPI-Host": RAPIDAPI_HOST
            }

            print(f"[JSearch] Page {page}: '{query}'")
            response = requests.get(url, headers=headers, params=params, timeout=15)

            if response.status_code == 429:
                print("[JSearch] Rate limit hit — free plan quota khatam")
                break

            if response.status_code != 200:
                print(f"[JSearch] Error: {response.status_code}")
                break

            data = response.json()
            jobs_data = data.get("data", [])

            if not jobs_data:
                print(f"[JSearch] Page {page} — no results")
                break

            print(f"[JSearch] Page {page} — {len(jobs_data)} jobs found")

            for job in jobs_data:
                parsed = parse_job(job, job_title)
                if parsed:
                    all_jobs.append(parsed)

        except requests.exceptions.Timeout:
            print(f"[JSearch] Page {page} timeout")
            continue
        except Exception as e:
            print(f"[JSearch] Page {page} error: {e}")
            continue

    print(f"[JSearch] Total: {len(all_jobs)} jobs")
    return all_jobs


def parse_job(job: dict, searched_title: str) -> dict | None:
    """JSearch API response se job details extract karo."""
    try:
        title   = job.get("job_title", "N/A")
        company = job.get("employer_name", "N/A")

        if not title or title == "N/A":
            return None

        # Smart matching
        if not is_relevant(title, searched_title):
            return None

        # Location
        city    = job.get("job_city", "")
        state   = job.get("job_state", "")
        country = job.get("job_country", "")
        location_parts = [x for x in [city, state, country] if x]
        location = ", ".join(location_parts) if location_parts else "N/A"

        # Remote check
        is_remote = job.get("job_is_remote", False)
        if is_remote:
            location = "Remote"

        # Salary
        min_sal = job.get("job_min_salary")
        max_sal = job.get("job_max_salary")
        sal_cur = job.get("job_salary_currency", "")
        sal_per = job.get("job_salary_period", "")
        if min_sal and max_sal:
            salary = f"{sal_cur} {int(min_sal):,} - {int(max_sal):,} / {sal_per}"
        elif min_sal:
            salary = f"{sal_cur} {int(min_sal):,}+ / {sal_per}"
        else:
            salary = "Not disclosed"

        # Employment type
        emp_type = job.get("job_employment_type", "")
        exp_map  = {
            "FULLTIME": "Full-time",
            "PARTTIME": "Part-time",
            "CONTRACTOR": "Contract",
            "INTERN": "Internship"
        }
        experience = exp_map.get(emp_type, emp_type) if emp_type else "N/A"

        # Required skills
        highlights = job.get("job_highlights", {})
        qual_list  = highlights.get("Qualifications", [])
        skills = []
        skill_keywords = ["python","java","sql","react","javascript","flutter","kotlin",
                         "android","machine learning","data","aws","docker","git","api"]
        for q in qual_list[:10]:
            q_lower = q.lower()
            for sk in skill_keywords:
                if sk in q_lower and sk.title() not in skills:
                    skills.append(sk.title())
                    break
        skills = skills[:5]

        # Posted date
        posted_at = job.get("job_posted_at_datetime_utc", "")
        if posted_at:
            try:
                from datetime import datetime, timezone
                posted_dt = datetime.fromisoformat(posted_at.replace("Z", "+00:00"))
                now       = datetime.now(timezone.utc)
                days_ago  = (now - posted_dt).days
                if days_ago == 0:
                    posted = "Today"
                elif days_ago == 1:
                    posted = "Yesterday"
                elif days_ago < 7:
                    posted = f"{days_ago} days ago"
                elif days_ago < 30:
                    posted = f"{days_ago // 7} weeks ago"
                else:
                    posted = f"{days_ago // 30} months ago"
            except Exception:
                posted = "Recently"
        else:
            posted = "Recently"

        # Source
        publisher = job.get("job_publisher", "")
        if "linkedin" in publisher.lower():
            source = "LinkedIn"
        elif "indeed" in publisher.lower():
            source = "Indeed.com"
        elif "naukri" in publisher.lower():
            source = "Naukri.com"
        elif "glassdoor" in publisher.lower():
            source = "Glassdoor"
        else:
            source = publisher if publisher else "JSearch"

        # Apply URL
        job_url = job.get("job_apply_link") or job.get("job_google_link") or "https://jsearch.p.rapidapi.com"

        return {
            "title":      title,
            "company":    company,
            "experience": experience,
            "salary":     salary,
            "location":   location,
            "skills":     skills,
            "url":        job_url,
            "posted":     posted,
            "source":     source
        }

    except Exception as e:
        print(f"[JSearch] Parse error: {e}")
        return None