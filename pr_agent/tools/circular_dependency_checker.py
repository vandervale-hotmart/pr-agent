import re
import yaml
import requests
from typing import Dict, List, Set, Optional
from pr_agent.algo.ai_handlers.base_ai_handler import BaseAiHandler
from pr_agent.algo.ai_handlers.litellm_ai_handler import LiteLLMAIHandler
from pr_agent.config_loader import get_settings
from pr_agent.git_providers import get_git_provider
from pr_agent.log import get_logger


class CircularDependencyChecker:
    def __init__(self, git_provider, ai_handler: BaseAiHandler):
        self.git_provider = git_provider
        self.ai_handler = ai_handler
        self.logger = get_logger()
        self.settings = get_settings()

    def check_circular_dependencies(self, pr_url: str) -> Optional[str]:
        """
        Check for circular dependencies in application.yml configurations
        """
        try:
            # Get PR files
            pr_files = self.git_provider.get_pr_files()
            
            # Find application.yml changes
            yml_changes = self._find_yml_changes(pr_files)
            if not yml_changes:
                return None

            # Extract service URLs from changes
            service_urls = self._extract_service_urls(yml_changes)
            if not service_urls:
                return None

            # Get current repository name
            current_repo = self._get_current_repo_name(pr_url)
            
            # Check for circular dependencies
            circular_deps = self._check_for_circular_deps(current_repo, service_urls)
            
            if circular_deps:
                return self._generate_warning_comment(current_repo, circular_deps)
                
        except Exception as e:
            self.logger.error(f"Error checking circular dependencies: {e}")
            
        return None

    def _find_yml_changes(self, pr_files: List[Dict]) -> List[Dict]:
        """Find application.yml file changes in PR"""
        yml_changes = []
        
        for file_data in pr_files:
            filename = file_data.get('filename', '')
            if 'application.yml' in filename or 'application.yaml' in filename:
                yml_changes.append(file_data)
                
        return yml_changes

    def _extract_service_urls(self, yml_changes: List[Dict]) -> Set[str]:
        """Extract service URLs from YAML changes"""
        service_urls = set()
        url_pattern = r'url:\s*https?://([^.\s]+)\.buildstaging\.com'
        
        for file_data in yml_changes:
            patch = file_data.get('patch', '')
            
            # Look for added lines (starting with +)
            for line in patch.split('\n'):
                if line.startswith('+') and 'url:' in line:
                    matches = re.findall(url_pattern, line)
                    for match in matches:
                        # Extract service name (e.g., api-club-settings)
                        service_urls.add(match)
                        
        return service_urls

    def _get_current_repo_name(self, pr_url: str) -> str:
        """Extract repository name from PR URL"""
        # Extract from URL like: https://github.com/Hotmart-Org/api-club-content/pull/123
        match = re.search(r'/([^/]+)/pull/', pr_url)
        if match:
            return match.group(1)
        return ""

    def _check_for_circular_deps(self, current_repo: str, service_urls: Set[str]) -> List[str]:
        """Check if any of the service URLs have dependencies back to current repo"""
        circular_deps = []
        
        for service_name in service_urls:
            if self._has_dependency_to_repo(service_name, current_repo):
                circular_deps.append(service_name)
                
        return circular_deps

    def _has_dependency_to_repo(self, service_name: str, target_repo: str) -> bool:
        """Check if service has dependency to target repository"""
        try:
            # Construct GitHub API URL
            api_url = f"https://api.github.com/repos/Hotmart-Org/{service_name}/contents/src/main/resources/application.yml"
            
            headers = {}
            if hasattr(self.settings, 'github_token') and self.settings.github_token:
                headers['Authorization'] = f'token {self.settings.github_token}'
            
            response = requests.get(api_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                content = response.json()
                # Decode base64 content
                import base64
                yml_content = base64.b64decode(content['content']).decode('utf-8')
                
                # Check if target repo is referenced in the YAML
                target_pattern = f'{target_repo}.buildstaging.com'
                return target_pattern in yml_content
                
        except Exception as e:
            self.logger.warning(f"Could not check dependency for {service_name}: {e}")
            
        return False

    def _generate_warning_comment(self, current_repo: str, circular_deps: List[str]) -> str:
        """Generate warning comment for circular dependencies"""
        deps_list = ', '.join([f"`{dep}`" for dep in circular_deps])
        
        comment = f"""## ⚠️ Circular Dependency Warning

This PR introduces dependencies to services that already depend on `{current_repo}`:

**Potential circular dependencies detected:**
- {deps_list}

**Impact:**
- This may create circular dependencies between services
- Could cause deployment issues or runtime problems
- May affect service startup order

**Recommendation:**
Please review the architecture and consider:
1. Breaking the circular dependency through an intermediary service
2. Using event-driven communication instead of direct API calls
3. Refactoring to remove the bidirectional dependency

**Services checked:**
{chr(10).join([f'- https://github.com/Hotmart-Org/{dep}' for dep in circular_deps])}
"""
        return comment


def run_circular_dependency_check(pr_url: str) -> Optional[str]:
    """Main function to run circular dependency check"""
    try:
        git_provider = get_git_provider()
        ai_handler = LiteLLMAIHandler()
        
        checker = CircularDependencyChecker(git_provider, ai_handler)
        return checker.check_circular_dependencies(pr_url)
        
    except Exception as e:
        get_logger().error(f"Failed to run circular dependency check: {e}")
        return None