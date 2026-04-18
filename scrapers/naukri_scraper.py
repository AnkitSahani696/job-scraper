from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from utils.matcher import is_relevant
import time


def get_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--window-size=1920,1080")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver


def search_jobs(job_title: str, location: str = "", pages: int = 2) -> list:
    all_jobs = []
    driver = None
    try:
        print("[Naukri] Browser start...")
        driver = get_driver()
        for page in range(1, pages + 1):
            try:
                title_slug = job_title.strip().lower().replace(" ", "-")
                if location:
                    loc_slug = location.strip().lower().replace(" ", "-")
                    url = f"https://www.naukri.com/{title_slug}-jobs-in-{loc_slug}-{page}"
                else:
                    url = f"https://www.naukri.com/{title_slug}-jobs-{page}"
                print(f"[Naukri] Page {page}: {url}")
                driver.get(url)
                time.sleep(3)
                try:
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "div.srp-jobtuple-wrapper"))
                    )
                except Exception:
                    print(f"[Naukri] Page {page} timeout")
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
                time.sleep(1)
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1)
                job_cards = driver.find_elements(By.CSS_SELECTOR, "div.srp-jobtuple-wrapper")
                if not job_cards:
                    job_cards = driver.find_elements(By.CSS_SELECTOR, "div.cust-job-tuple")
                if not job_cards:
                    print(f"[Naukri] Page {page} - no cards")
                    break
                print(f"[Naukri] Page {page} - {len(job_cards)} cards")
                for card in job_cards:
                    job = extract_job(card, job_title)
                    if job:
                        all_jobs.append(job)
                time.sleep(2)
            except Exception as e:
                print(f"[Naukri] Page {page} error: {e}")
    except Exception as e:
        print(f"[Naukri] Error: {e}")
    finally:
        if driver:
            driver.quit()
    print(f"[Naukri] Done. Total: {len(all_jobs)}")
    return all_jobs


def extract_job(card, searched_title):
    def safe_text(*sels):
        for s in sels:
            try:
                el = card.find_element(By.CSS_SELECTOR, s)
                t = el.text.strip()
                if t: return t
            except: continue
        return "N/A"
    def safe_attr(attr, *sels):
        for s in sels:
            try:
                el = card.find_element(By.CSS_SELECTOR, s)
                v = el.get_attribute(attr)
                if v: return v
            except: continue
        return ""
    try:
        title = safe_text("a.title","a[class*='title']","h2 a",".job-title a")
        if title == "N/A" or not is_relevant(title, searched_title):
            return None
        company    = safe_text("a.comp-name","a[class*='comp-name']","span.comp-name")
        experience = safe_text("span.expwdth","span[class*='exp']","li.experience span")
        salary     = safe_text("span.sal-wrap span","span[class*='salary']","li.salary span")
        if salary == "N/A": salary = "Not disclosed"
        location   = safe_text("span.locWdth","span[class*='loc']","li.location span")
        skills = []
        try:
            els = card.find_elements(By.CSS_SELECTOR,"ul.tags-gt li,li[class*='tag']")
            skills = [e.text.strip() for e in els[:5] if e.text.strip()]
        except: pass
        job_url = safe_attr("href","a.title","a[class*='title']","h2 a")
        if not job_url: job_url = "https://www.naukri.com"
        posted = safe_text("span.job-post-day","span[class*='post']","time")
        if posted == "N/A": posted = "Recently"
        return {"title":title,"company":company,"experience":experience,
                "salary":salary,"location":location,"skills":skills,
                "url":job_url,"posted":posted,"source":"Naukri.com"}
    except Exception as e:
        print(f"[Naukri] Extract error: {e}")
        return None