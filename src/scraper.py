
import time
import os
import re
import requests
import csv
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class Project:
    def __init__(self, url=""):
        self.url = url
        self.title = ""
        self.architects = ""
        self.year = ""
        self.location = ""
        self.area = ""
        self.materials = ""
        self.refImage = ""
        self.imageUrls = ""
        self.tags = ""


def alterDriver():
    options= Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )

    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

def saveCSV(projects, path="results.csv"):
    fieldnames = ["url", "title", "architects", "year", "location", "area", "materials", "refImage", "imageUrls", "tags"]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for p in projects:
            writer.writerow(vars(p))
def searchProjects(driver, query, maxProjects):
    page = 1
    projects = []
    url = "https://www.archdaily.com/search/projects?q=" + query
    while len(projects) < maxProjects:
        currUrl = f"{url}&page={page}"
        driver.get(currUrl)
        print(currUrl)
        time.sleep(4)
        anchors = driver.find_elements(By.CSS_SELECTOR, "a[href]")

        currProjects = []
        for a in anchors:
            href = a.get_attribute("href") or ""
            parts = href.split("/")
            if (
                "archdaily.com/" in href
                and len(parts) >= 5
                and parts[3].isdigit()
                and href not in projects
                and href not in currProjects
            ):
                currProjects.append(href)
        if currProjects == []:
            break
        else:
            projects += currProjects
            page += 1
            time.sleep(1.5)
    return projects

def safeText(driver, css, default=""):
    try:
        return driver.find_element(By.CSS_SELECTOR, css).text.strip()
    except NoSuchElementException:
        return default

def safeAttr(driver, css, attr, default=""):
    try:
        el = driver.find_element(By.CSS_SELECTOR, css)
        return el.get_attribute(attr) or default
    except NoSuchElementException:
        return default

def scrapeProject(driver, url):
    newProject = Project(url)
    driver.get(url)
    time.sleep(4)
    newProject.title = safeText(driver, "h1.title, h1.afd-title, h1")
    newProject.refImage = safeText(driver, "meta[property='og:image']", "content")
    newProject.architects = safeText(driver, "a[href*='/office/']")
    newProject.year = safeAttr(driver, "meta[name='cXenseParse:project-year']", "content")
    newProject.location = safeAttr(driver, "meta[name='cXenseParse:project-location']", "content")
    newProject.area = safeText(driver, "a[href*='min_area']")

    materials = driver.find_elements(By.CSS_SELECTOR, "a[href*='/search/products?q=']")
    if materials:
        names = []
        for m in materials:
            if m.text.strip():
                names.append(m.text.strip())
        newProject.materials = ", ".join(names)
    else:
        newProject.materials = ""

    tags = driver.find_elements(By.CSS_SELECTOR, "a[href*='/search/projects/categories/'], a[href*='/tag/']")
    if tags:
        names = []
        for t in tags:
            if t.text.strip():
                names.append(t.text.strip())
        newProject.tags = ", ".join(names)
    else:
        newProject.tags = ""
    

    imgs = driver.find_elements(By.CSS_SELECTOR, ".project-gallery img, [class*='gallery'] img")
    if imgs:
        urls = []
        for img in imgs:
            src = img.get_attribute("src") or img.get_attribute("data-src") or ""
            if "adsttc.com" in src:
                src = src.replace("medium_jpg", "large_jpg")
            if src.startswith("http"):
                urls.append(src)
        newProject.imageUrls = " | ".join(urls)
    else:
        newProject.imageUrls = ""
    
    return newProject

if __name__ == "__main__":
    driver = alterDriver()
    
    try:
        urls = searchProjects(driver, "library", maxProjects=5)
        print(f"Found {len(urls)} projects")
        
        projects = []
        for i, url in enumerate(urls, 1):
            print(f"[{i}/{len(urls)}] Scraping {url}")
            project = scrapeProject(driver, url)
            projects.append(project)
            time.sleep(1.5)
    finally:
        driver.quit()

    saveCSV(projects)



