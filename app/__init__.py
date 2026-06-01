from dotenv import load_dotenv
load_dotenv()

from .gcp import load_secrets_to_env
load_secrets_to_env()
