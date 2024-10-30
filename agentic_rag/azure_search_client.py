import os
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient

class AzureSearchClient:
    def __init__(self, service_endpoint=None, index_name=None, api_key=None):
        """
        Initializes the AzureSearchClient with the necessary credentials.

        Parameters:
            service_endpoint (str): The endpoint of your Azure Cognitive Search service.
            index_name (str): The name of the index you want to search.
            api_key (str): Your Azure Cognitive Search API key.
        """

        # Use provided values or fall back to environment variables
        self.service_endpoint = service_endpoint or os.getenv("AZURE_SEARCH_SERVICE_ENDPOINT")
        self.index_name = index_name or os.getenv("AZURE_SEARCH_INDEX_NAME")
        api_key = api_key or os.getenv("AZURE_SEARCH_API_KEY")

        if not self.service_endpoint or not self.index_name or not api_key:
            raise ValueError("Missing required Azure Cognitive Search configurations.")

        # Create a credential object
        self.credential = AzureKeyCredential(api_key)

        # Initialize the SearchClient
        self.search_client = SearchClient(endpoint=self.service_endpoint,
                                          index_name=self.index_name,
                                          credential=self.credential)

    def search(self, query, **kwargs):
        """
        Executes a search query against the Azure Cognitive Search index.

        Parameters:
            query (str): The search text to query.
            **kwargs: Additional parameters for the search (optional).

        Returns:
            list: A list of search results.
        """

        # Execute the search
        results = self.search_client.search(search_text=query, **kwargs)

        # Collect results into a list
        search_results = []
        for result in results:
            search_results.append(result)

        return search_results