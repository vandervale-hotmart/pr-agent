from pr_agent.algo.ai_handlers.base_ai_handler import BaseAiHandler
from pr_agent.config_loader import get_settings
from pr_agent.git_providers import get_git_provider
from pr_agent.log import get_logger
from pr_agent.tools.circular_dependency_checker import run_circular_dependency_check


class PRCircularDeps:
    def __init__(self, pr_url: str, args: list = None):
        self.pr_url = pr_url
        self.git_provider = get_git_provider()
        self.settings = get_settings()
        self.logger = get_logger()

    async def run(self):
        """
        Run circular dependency check and post comment if issues found
        """
        try:
            self.logger.info("Running circular dependency check...")
            
            # Run the circular dependency check
            warning_comment = run_circular_dependency_check(self.pr_url)
            
            if warning_comment:
                self.logger.info("Circular dependencies detected, posting warning comment")
                
                # Post comment to PR
                self.git_provider.publish_comment(warning_comment)
                
                self.logger.info("Circular dependency warning posted successfully")
            else:
                self.logger.info("No circular dependencies detected")
                
        except Exception as e:
            self.logger.error(f"Error in circular dependency check: {e}")
            raise