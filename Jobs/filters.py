import re

ROLE_KEYWORDS = {
    "ds": ["data scientist", "data science", "machine learning engineer", "ml engineer"],
    "ai": ["ai engineer", "artificial intelligence", "prompt engineer", "llm engineer"],
    "ml": ["machine learning engineer", "ml researcher", "deep learning engineer", "computer vision engineer"],
    "swe": ["software engineer", "full stack developer", "backend developer", "frontend developer", "web developer"]
}

EXCLUDE_TITLE_EXACT = {
    'careers', 'careers home', 'jobs search', 'view openings', 'share your resume/cv',
    'cookie settings', 'your careers site cookie settings', 'right to work', 'remote hiring guide',
    'hiring tips', 'media careers', 'working at snc', 'faqs', 'blog', 'jobs', 'hiring',
    'founders', 'work', 'lecturers', 'volunteers', 'contractual opportunities', 'internships',
    'unpaid', 'attachments (no pay)', 'internal applications', 'late preparation',
    'undergraduate program', 'graduate trainee program', 'management trainee',
    'privacy policy', 'terms of service', 'about us', 'contact us'
}

EXCLUDE_TITLE_PATTERNS = [
    r'^\s*careers?\s*$',
    r'^\s*jobs?\s*search\s*$',
    r'^\s*view\s*openings\s*$',
    r'^\s*share\s*your\s*resume.*$',
    r'^\s*cookie\s*settings.*$',
    r'^\s*right\s*to\s*work.*$',
    r'^\s*remote\s*hiring\s*guide.*$',
    r'^\s*hiring\s*tips.*$',
    r'^\s*media\s*careers.*$',
    r'^\s*working\s*at.*$',
    r'^\s*careers?\s*home.*$',
    r'^\s*attachments.*$',
    r'^\s*internal\s*applications.*$',
    r'^\s*late\s*preparation.*$',
    r'^\s*hiring\s*$',
    r'^\s*founders\s*$',
    r'^\s*work\s*$',
    r'^\s*lecturers\s*$',
    r'^\s*volunteers\s*$',
    r'^\s*contractual\s*opportunities.*$',
    r'^\s*internships\s*$',
    r'^\s*unpaid\s*$',
    r'^\s*undergraduate\s*program.*$',
    r'^\s*graduate\s*trainee.*$',
    r'^\s*management\s*trainee.*$',
    r'^\s*privacy\s*policy.*$',
    r'^\s*terms\s*of\s*service.*$',
]

def is_valid_job_title(title: str) -> bool:
    if not title or len(title.strip()) < 4:
        return False
    t = title.strip().lower()
    if t in EXCLUDE_TITLE_EXACT:
        return False
    for pat in EXCLUDE_TITLE_PATTERNS:
        if re.search(pat, t):
            return False
    return True

