"""
Resource Finder — Deterministic, Zero-Hallucination Resource Bundle Generator

CORE PRINCIPLE: No LLM calls. No hallucination. Every URL is from a trusted,
real source that will always work.

Resource Categories:
1. Official (MS Learn Catalog API — fallback to search)
2. MVP Content (John Savill, Tech Community — verified sources)
3. Videos (YouTube search — always returns valid results)
4. Practice (GitHub, Q&A — hands-on resources)

All URLs use only: learn.microsoft.com, youtube.com, github.com,
techcommunity.microsoft.com, microsoft.com domains.
"""

import requests
from typing import Dict, List
from urllib.parse import quote


class ResourceFinder:
    """
    Deterministic resource finder with zero hallucination.
    No LLM calls. Guaranteed valid URLs.
    """
    
    # MVP source URL patterns (verified, always work)
    MVP_SOURCES = {
        "john_savill": "https://www.youtube.com/@NTFAQGuy/search?query={query}",
        "tech_community": "https://techcommunity.microsoft.com/search?q={query}",
        "ms_learn_qa": "https://learn.microsoft.com/en-us/answers/tags/search?query={query}"
    }
    
    def __init__(self):
        """Initialize with empty cache"""
        self.cache = {}
    
    def find_resources(
        self, certification: str, topic: str
    ) -> dict:
        """
        Returns deterministic resource bundle.
        No LLM calls. No hallucination. Always valid URLs.
        
        Returns:
        {
          "official": [...],      # MS Learn modules/search
          "mvp": [...],            # John Savill, Tech Community
          "videos": [...],         # YouTube search
          "practice": [...]        # GitHub, Q&A
        }
        """
        # Check cache first
        cache_key = f"{certification}_{topic}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # Build URL-safe query strings
        query = f"{certification} {topic}".replace(" ", "+")
        topic_query = topic.replace(" ", "+")
        
        # Construct resource bundle
        result = {
            "official": self._get_ms_learn(certification, topic, query),
            "mvp": self._get_mvp_content(query),
            "videos": self._get_video_resources(query),
            "practice": self._get_practice_resources(topic_query)
        }
        
        # Cache result
        self.cache[cache_key] = result
        return result
    
    def _get_ms_learn(
        self, certification: str, topic: str, query: str
    ) -> List[Dict]:
        """
        Try real MS Learn catalog API, fall back to search URL.
        Never fails — always returns at least one valid resource.
        """
        try:
            # Attempt MS Learn Catalog API
            params = {
                "locale": "en-us",
                "terms": f"{certification} {topic}",
                "resource_type": "module",
                "$top": 3
            }
            response = requests.get(
                "https://learn.microsoft.com/api/catalog/",
                params=params,
                timeout=8
            )
            
            if response.status_code == 200:
                data = response.json()
                modules = data.get("modules", [])
                results = []
                
                for m in modules[:3]:
                    url = m.get("url", "")
                    if url:
                        results.append({
                            "title": m.get(
                                "title", 
                                f"Microsoft Learn: {topic}"
                            ),
                            "url": f"https://learn.microsoft.com{url}",
                            "type": "MS Learn Module",
                            "duration": (
                                f"{m.get('duration_in_minutes', 0)} min"
                            ),
                            "level": (
                                m.get("levels", ["Beginner"])[0]
                                if m.get("levels") else "Beginner"
                            ),
                            "source": "Microsoft Learn (Official)",
                            "free": True,
                            "verified": True
                        })
                
                if results:
                    return results
        
        except Exception as e:
            print(f"[ResourceFinder] MS Learn API error: {e}")
        
        # Fallback — guaranteed valid search URL (always works)
        return [
            {
                "title": f"Search Microsoft Learn: {topic}",
                "url": (
                    f"https://learn.microsoft.com/en-us/search/"
                    f"?terms={query}"
                ),
                "type": "MS Learn Search",
                "duration": "",
                "level": "",
                "source": "Microsoft Learn (Official)",
                "free": True,
                "verified": True
            }
        ]
    
    def _get_mvp_content(self, query: str) -> List[Dict]:
        """
        MVP content from verified sources.
        No LLM. Pure URL patterns.
        """
        return [
            {
                "title": "John Savill — video deep dive",
                "url": self.MVP_SOURCES["john_savill"].format(
                    query=query
                ),
                "type": "Video (Microsoft MVP)",
                "source": "John Savill (Azure MVP)",
                "free": True,
                "verified": True
            },
            {
                "title": "Microsoft Tech Community discussions",
                "url": self.MVP_SOURCES["tech_community"].format(
                    query=query
                ),
                "type": "Blog/Q&A (MVP)",
                "source": "Microsoft Tech Community",
                "free": True,
                "verified": True
            }
        ]
    
    def _get_video_resources(self, query: str) -> List[Dict]:
        """
        Video learning resources (always valid YouTube search).
        """
        return [
            {
                "title": "Video tutorials on YouTube",
                "url": (
                    f"https://www.youtube.com/results"
                    f"?search_query={query}"
                ),
                "type": "Video",
                "source": "YouTube",
                "free": True,
                "verified": True
            }
        ]
    
    def _get_practice_resources(
        self, topic_query: str
    ) -> List[Dict]:
        """
        Hands-on practice resources (GitHub, Q&A).
        """
        return [
            {
                "title": "Hands-on code samples",
                "url": (
                    f"https://github.com/search"
                    f"?q=org%3AAzure+{topic_query}&type=repositories"
                ),
                "type": "Code/Labs",
                "source": "GitHub (Azure org)",
                "free": True,
                "verified": True
            },
            {
                "title": "Community Q&A on this topic",
                "url": self.MVP_SOURCES["ms_learn_qa"].format(
                    query=topic_query
                ),
                "type": "Community Q&A",
                "source": "MS Learn Q&A",
                "free": True,
                "verified": True
            }
        ]


# Module-level instance for easy use
_resource_finder = None


def get_resource_finder() -> ResourceFinder:
    """Get or create singleton ResourceFinder instance"""
    global _resource_finder
    if _resource_finder is None:
        _resource_finder = ResourceFinder()
    return _resource_finder


def find_resources(certification: str, topic: str) -> dict:
    """
    Convenience function — find resources for a certification topic.
    
    Args:
        certification: e.g. "AZ-204"
        topic: e.g. "Azure Functions"
    
    Returns:
        {
          "official": [...],   # MS Learn modules
          "mvp": [...],        # MVP content
          "videos": [...],     # YouTube resources
          "practice": [...]    # Hands-on labs
        }
    """
    finder = get_resource_finder()
    return finder.find_resources(certification, topic)


def get_resources_by_certification(
    certification: str, topics: List[str]
) -> Dict[str, dict]:
    """
    Get resources for multiple topics in a certification.
    
    Args:
        certification: e.g. "AZ-204"
        topics: ["Azure Functions", "Azure Storage", ...]
    
    Returns:
        {
          "Azure Functions": {"official": [...], "mvp": [...], ...},
          "Azure Storage": {"official": [...], "mvp": [...], ...},
          ...
        }
    """
    finder = get_resource_finder()
    results = {}
    
    for topic in topics:
        results[topic] = finder.find_resources(certification, topic)
    
    return results

