# utils/matcher.py
# Smart job title matching — broad search support karta hai

# Agar user ye search kare to in titles ko bhi accept karo
KEYWORD_ALIASES = {
    "web development": [
        "web developer", "frontend developer", "front end developer",
        "full stack developer", "fullstack developer", "react developer",
        "angular developer", "vue developer", "javascript developer",
        "ui developer", "web engineer", "frontend engineer"
    ],
    "android development": [
        "android developer", "android engineer", "mobile developer",
        "mobile engineer", "kotlin developer", "java developer",
        "flutter developer", "react native developer"
    ],
    "ios development": [
        "ios developer", "ios engineer", "swift developer",
        "objective-c developer", "mobile developer", "apple developer"
    ],
    "mobile development": [
        "mobile developer", "android developer", "ios developer",
        "flutter developer", "react native developer", "mobile engineer"
    ],
    "data science": [
        "data scientist", "data science", "ml engineer",
        "machine learning engineer", "ai engineer", "data analyst",
        "research scientist", "applied scientist"
    ],
    "machine learning": [
        "ml engineer", "machine learning engineer", "ai engineer",
        "data scientist", "deep learning engineer", "nlp engineer",
        "computer vision engineer", "research engineer"
    ],
    "devops": [
        "devops engineer", "site reliability engineer", "sre",
        "cloud engineer", "infrastructure engineer", "platform engineer",
        "devsecops", "kubernetes engineer", "docker engineer"
    ],
    "backend development": [
        "backend developer", "backend engineer", "server side developer",
        "api developer", "node developer", "django developer",
        "spring developer", "java developer", "python developer",
        "golang developer", "ruby developer"
    ],
    "frontend development": [
        "frontend developer", "front end developer", "ui developer",
        "react developer", "angular developer", "vue developer",
        "javascript developer", "web developer", "ui engineer"
    ],
    "cybersecurity": [
        "security engineer", "cybersecurity engineer", "information security",
        "penetration tester", "ethical hacker", "security analyst",
        "soc analyst", "network security engineer"
    ],
    "cloud computing": [
        "cloud engineer", "aws engineer", "azure engineer",
        "gcp engineer", "cloud architect", "solutions architect",
        "cloud developer", "cloud infrastructure"
    ],
    "ui ux": [
        "ui designer", "ux designer", "ui/ux designer",
        "product designer", "interaction designer", "visual designer",
        "user experience designer", "user interface designer"
    ],
    "game development": [
        "game developer", "unity developer", "unreal engine developer",
        "game engineer", "gameplay programmer", "graphics programmer"
    ],
    "blockchain": [
        "blockchain developer", "smart contract developer",
        "solidity developer", "web3 developer", "defi developer",
        "cryptocurrency developer"
    ],
}


def is_relevant(job_title: str, searched_title: str) -> bool:
    """
    Smart matching function.

    1. Pehle exact word match try karo
    2. Phir alias list check karo
    3. Partial match bhi check karo

    Examples:
        search: "web development"
        match:  "React Developer"    -> True  (alias match)
        match:  "Web Developer"      -> True  (alias match)
        match:  "Data Scientist"     -> False

        search: "data science"
        match:  "Data Scientist"     -> True  (alias match)
        match:  "ML Engineer"        -> True  (alias match)
        match:  "Android Developer"  -> False
    """
    job_lower    = job_title.lower().strip()
    search_lower = searched_title.lower().strip()
    search_words = search_lower.split()

    # 1. Exact word match (original logic)
    if all(word in job_lower for word in search_words):
        return True

    # 2. Alias match — search term ke aliases check karo
    aliases = KEYWORD_ALIASES.get(search_lower, [])
    for alias in aliases:
        alias_words = alias.lower().split()
        if all(word in job_lower for word in alias_words):
            return True

    # 3. Partial alias match — job title ka koi bhi alias word match kare
    for alias in aliases:
        alias_words = alias.lower().split()
        # At least half the alias words match karne chahiye
        match_count = sum(1 for w in alias_words if w in job_lower)
        if match_count >= max(1, len(alias_words) // 2):
            return True

    # 4. Search words ka koi significant word job me ho
    significant = [w for w in search_words if len(w) > 3]  # short words ignore karo
    if significant:
        match_count = sum(1 for w in significant if w in job_lower)
        if match_count >= max(1, len(significant) - 1):
            return True

    return False