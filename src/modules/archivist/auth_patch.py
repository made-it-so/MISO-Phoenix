    def configure_remote(self):
        """Injects the GITHUB_TOKEN into the remote URL for passwordless push."""
        token = os.getenv("GITHUB_TOKEN")
        if not token:
            logger.warning("GITHUB_TOKEN not found. Push operations will likely fail.")
            return

        # Updates origin to include the token: https://TOKEN@github.com/user/repo.git
        try:
            remote_url = self.run_cmd("git remote get-url origin")
            if "https://" in remote_url and "@" not in remote_url:
                clean_url = remote_url.replace("https://", "")
                auth_url = f"https://{token}@{clean_url}"
                self.run_cmd(f"git remote set-url origin {auth_url}")
                logger.info("GitHub Token injected into remote URL.")
        except Exception as e:
            logger.error(f"Failed to configure auth remote: {e}")
