import requests
import json
from django.utils import timezone
from .models import Profile, Project, UserSkills, Evidence

class GithubScanner:
    """
    Scans a user's GitHub using their OAuth Token via the blazing-fast GraphQL API.
    Extracts high-quality Projects based on scoring, and infers Skills via Languages + Topics.
    """
    
    GRAPHQL_URL = "https://api.github.com/graphql"

    def __init__(self, access_token: str):
        self.headers = {
            "Authorization": f"bearer {access_token}",
            "Content-Type": "application/json"
        }

    def scan_and_sync(self, profile: Profile):
        """Main pipeline to fetch, score, and save GitHub data to the Profile."""
        print(f"Starting GitHub sync for {profile.user.email}...")
        
        repos = self._fetch_repositories()
        if not repos:
            print("No repositories found or API failed.")
            return

        all_skills = set()
        
        for repo in repos:
            # 1. Parse Raw Data
            name = repo.get('name', 'Unknown')
            desc = repo.get('description') or ""
            url = repo.get('url', '')
            stars = repo.get('stargazerCount', 0)
            forks = repo.get('forkCount', 0)
            
            # Extract Commits
            commits = 0
            default_branch = repo.get('defaultBranchRef')
            if default_branch and 'target' in default_branch:
                commits = default_branch['target'].get('history', {}).get('totalCount', 0)
                
            # Extract Topics (Tags)
            topics = []
            topic_nodes = repo.get('repositoryTopics', {}).get('nodes', [])
            for node in topic_nodes:
                topic_name = node.get('topic', {}).get('name')
                if topic_name:
                    topics.append(topic_name)
                    all_skills.add(topic_name)
                    
            # Extract Languages
            languages = []
            lang_nodes = repo.get('languages', {}).get('edges', [])
            for node in lang_nodes:
                lang_name = node.get('node', {}).get('name')
                if lang_name:
                    languages.append(lang_name)
                    all_skills.add(lang_name)

            # 2. Calculate Project Quality Score
            # Formula: Stars(20) + Forks(10) + Description(10) + Topics(10) + Commits(max 50)
            score = (stars * 20) + (forks * 10)
            if desc: score += 10
            if topics: score += 10
            score += min(commits, 50) 
            
            # 3. Save as Project if score > 60
            if score > 60:
                print(f"⭐ High Quality Repo Found: {name} (Score: {score})")
                
                # Create or update the project
                project, created = Project.objects.update_or_create(
                    profile=profile,
                    name=name,
                    defaults={
                        "description": desc,
                        "link": url,
                        "tools": ", ".join(languages + topics)[:255],
                        "outcomes": f"Built a highly-rated open source project with {commits} commits, {stars} stars, and {forks} forks.",
                    }
                )
                
                # Link Evidence
                evidence, _ = Evidence.objects.get_or_create(
                    profile=profile,
                    evidence_type="github_repo",
                    title=name,
                    defaults={
                        "description": desc,
                        "url": url,
                        "metadata": {"stars": stars, "commits": commits, "languages": languages, "topics": topics}
                    }
                )
                project.evidence.add(evidence)

        # 4. Save Extracted Skills
        print(f"Extracted {len(all_skills)} unique skills/technologies.")
        for skill_name in all_skills:
            # Capitalize standard tags nicely if possible, or leave as is
            clean_skill = skill_name.replace("-", " ").title()
            
            UserSkills.objects.update_or_create(
                profile=profile,
                skill_name=clean_skill,
                defaults={
                    "is_verified": True,
                    "verification_source": "GitHub Profile Scanner",
                    "proficiency_level": "Intermediate",
                }
            )
            
        # Update sync timestamp
        profile.github_last_sync = timezone.now()
        profile.save(update_fields=["github_last_sync"])
        print("GitHub sync complete!")

    def _fetch_repositories(self) -> list:
        """Fires the GraphQL query to fetch all repos in a single request."""
        query = """
        {
          viewer {
            repositories(first: 100, privacy: PUBLIC, ownerAffiliations: OWNER, isFork: false, orderBy: {field: PUSHED_AT, direction: DESC}) {
              nodes {
                name
                description
                url
                stargazerCount
                forkCount
                defaultBranchRef {
                  target {
                    ... on Commit {
                      history {
                        totalCount
                      }
                    }
                  }
                }
                repositoryTopics(first: 10) {
                  nodes {
                    topic {
                      name
                    }
                  }
                }
                languages(first: 5, orderBy: {field: SIZE, direction: DESC}) {
                  edges {
                    node {
                      name
                    }
                  }
                }
              }
            }
          }
        }
        """
        
        try:
            response = requests.post(self.GRAPHQL_URL, headers=self.headers, json={"query": query}, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            # Handle potential GraphQL errors
            if "errors" in data:
                print(f"GraphQL Errors: {data['errors']}")
                return []
                
            return data.get("data", {}).get("viewer", {}).get("repositories", {}).get("nodes", [])
            
        except Exception as e:
            print(f"Failed to fetch from GitHub GraphQL API: {e}")
            return []
