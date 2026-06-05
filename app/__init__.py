#Only for local testing. 
# Reads your .env file and loads the key-value pairs into environment variables. 
from dotenv import load_dotenv
load_dotenv()      

# For cloud production. Reaches out to GCP Secret Manager and loads the secrets into environment variables.
# Secure production pattern!!
from .gcp import load_secrets_to_env
load_secrets_to_env()
