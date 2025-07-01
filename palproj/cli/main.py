import click
import requests
import os

# It's better to fetch the API URL from an environment variable
# or a config file, but for this example, we'll hardcode it.
# This assumes the gateway is running and accessible.
API_BASE_URL = os.getenv("PALANTIR_API_URL", "http://nginx/api")

@click.group()
def cli():
    """A CLI to interact with the Palantir backend."""
    pass

@cli.command()
@click.argument('query')
def chat(query):
    """Sends a query to the chat agent."""
    try:
        response = requests.get(f"{API_BASE_URL}/chat/{query}")
        response.raise_for_status()  # Raises an HTTPError for bad responses (4xx or 5xx)
        click.echo(response.json().get("response", "No response content."))
    except requests.exceptions.RequestException as e:
        click.echo(f"Error connecting to the API: {e}", err=True)

if __name__ == "__main__":
    cli()
