from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from utils.matcher import is_relevant
import urllib.parse, time


def get_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--window-size=1920,1080")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver


def search_jobs(job_title: str, location: str = "", pages: int = 2) -> list:
    all_jobs = []
    driver = None
    try:
        print("[LinkedIn] Browser start...")
        driver = get_driver()
        et = urllib.parse.quote_plus(job_title)
        el = urllib.parse.quote_plus(location if location else "India")
        for page in range(pages):
            try:
                url = f"https://www.linkedin.com/jobs/search/?keywords={et}&location={el}&start={page*25}&f_TPR=r2592000"
                print(f"[LinkedIn] Page {page+1} loading...")
                driver.get(url)
                time.sleep(4)
                try:
                    WebDriverWait(driver, 12).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "div.base-card"))
                    )
                except: print(f"[LinkedIn] Page {page+1} timeout")
                for _ in range(3):
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(1.5)
                job_cards = driver.find_elements(By.CSS_SELECTOR, "div.base-card")
                if not job_cards:
                    job_cards = driver.find_elements(By.CSS_SELECTOR, "li.jobs-search-results__list-item")
                if not job_cards:
                    print(f"[LinkedIn] Page {page+1} no cards")
                    break
                print(f"[LinkedIn] Page {page+1} - {len(job_cards)} cards")
                seen = set()
                for card in job_cards:
                    job = extract_job(card, job_title)
                    if job and job["title"] not in seen:
                        seen.add(job["title"])
                        all_jobs.append(job)
                time.sleep(2)
            except Exception as e:
                print(f"[LinkedIn] Page {page+1} error: {e}")
    except Exception as e:
        print(f"[LinkedIn] Error: {e}")
    finally:
        if driver: driver.quit()
    print(f"[LinkedIn] Done. Total: {len(all_jobs)}")
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
        title = safe_text("h3.base-search-card__title","h3[class*='title']","span[class*='title']")
        if title == "N/A" or not is_relevant(title, searched_title):
            return None
        company  = safe_text("h4.base-search-card__subtitle","h4[class*='subtitle']","a[class*='company']")
        location = safe_text("span.job-search-card__location","span[class*='location']")
        posted   = safe_text("time.job-search-card__listdate","time[class*='listdate']","time")
        if posted == "N/A": posted = "Recently"
        job_url  = safe_attr("href","a.base-card__full-link","a[class*='full-link']","a[href*='linkedin.com/jobs/view']")
        if not job_url: job_url = "https://www.linkedin.com/jobs/"
        if "?" in job_url: job_url = job_url.split("?")[0]
        return {"title":title,"company":company,"experience":"N/A","salary":"Not disclosed",
                "location":location,"skills":[],"url":job_url,"posted":posted,"source":"LinkedIn"}
    except Exception as e:
        print(f"[LinkedIn] Extract error: {e}")
        return None