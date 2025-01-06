import pandas as pd
import re 
import uuid
from azure.core.exceptions import ResourceNotFoundError
from azure.search.documents.indexes.models import SearchIndex, SimpleField, SearchableField, HnswAlgorithmConfiguration, VectorSearch, VectorSearchProfile, SearchFieldDataType, SearchField, SemanticConfiguration, SemanticPrioritizedFields, SemanticField, SemanticSearch
from libs.web_scraper import WebScraper
from libs.aisearch_index import AISearchIndex


class RegulationIndex(AISearchIndex):
    def __init__(self, index_name, service_name, azure_search_api_key, openai_api_key, openai_api_version,
                  openai_api_endpoint, openai_embedding_model, vector_length, data):
        super().__init__(index_name, service_name, azure_search_api_key, openai_api_key,
                         openai_api_version, openai_api_endpoint, openai_embedding_model)
        self.vector_length = vector_length
        self.data = data


    def create_index(self):
        fields = [
            SearchableField(name="id", type="Edm.String", key=True, searchable=True, retrievable=True, filterable=True),
            SearchableField(name="title", type="Edm.String",
                            searchable=True, retrievable=True, filterable=True),
            SearchableField(name="hrbp_document_id", type="Edm.String",
                        searchable=True, retrievable=True, filterable=False),
            SearchableField(name="is_federal", typoe="Edm.Boolean", searchable=False, retrievalbe=True, filterable=True),
            SearchableField(name="state", type="Edm.String",
                            searchable=True, retrievable=True, filterable=True),         
            SearchableField(name="title", type="Edm.String",
                            searchable=True, retrievable=True, filterable=True),  
            SearchableField(name="regulation_link", type="Edm.String",
                            searchable=True, retrievable=True, filterable=True),
            SearchableField(name="chunk_position", type="Edm.String",
                            searchable=True, retrievable=True, filterable=False),
            SearchableField(name="chunk_text", type="Edm.String",
                            searchable=True, retrievable=True, filterable=False),
            
            SearchField(name="chunk_text_vector", type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                        searchable=True, vector_search_dimensions=self.vector_length, vector_search_profile_name="regulation-vector-config-Profile")
        ]

        vector_search = VectorSearch(
            algorithms=[
                HnswAlgorithmConfiguration(
                    name="regulation-vector-config",
                    kind="hnsw",
                    parameters={
                        "m": 4,
                        "efConstruction": 400,
                        "efSearch": 1000,
                        "metric": "cosine"}
                )
            ],
            profiles=[
                VectorSearchProfile(
                    name="regulation-vector-config-Profile",
                    algorithm_configuration_name="regulation-vector-config",
                )
            ]
        )


        semantic_config = SemanticConfiguration(
            name="regulation-semantic-config",
            prioritized_fields=SemanticPrioritizedFields(
                title_field=SemanticField(field_name="regulation_link"),
                content_fields=[
                    SemanticField(field_name="chunk_text")
                ],
            ),
        )

        
        semantic_search = SemanticSearch(configurations=[semantic_config])

        index = SearchIndex(name=self.index_name, fields=fields, vector_search=vector_search, semantic_search=semantic_search)


        # Check if the index exists
        try:
            self.index_client.get_index(self.index_name)
            # If the index exists, delete it
            self.index_client.delete_index(self.index_name)
            print(f"Index '{self.index_name}' deleted.")
        except ResourceNotFoundError:
            print(f"Index '{self.index_name}' does not exist. Creating a new one.")

        # Create the index
        self.index_client.create_index(index)
        print(f"Index '{self.index_name}' created.")


    def extract_urls(self, text): 
        url_pattern = r'(https?://[^\s)]+)'  # Modified pattern
        urls = re.findall(url_pattern, text)
        cleaned_urls = [url.rstrip('.') for url in urls]  # Remove trailing periods and parentheses
        return cleaned_urls
    

    def prep_url_df(self):
        results = []
        for _, row in self.data.iterrows():
            row_id = row['id']
            is_federal = None
            state = row['LegalState']
            for col in self.data.select_dtypes(include='object').columns:
                urls = self.extract_urls(str(row[col]))
                for url in urls:
                    results.append({'id': row_id, 'is_federal': is_federal, 'state': state, 'url': url})

        # Convert results to a new DataFrame
        url_df = pd.DataFrame(results)
        return url_df
    
    def chunk_text(self, text, max_chunk_size=512):
        sentences = re.split(r'(?<=[.!?]) +', text)  # Split by sentences
        chunks = []
        current_chunk = []

        for sentence in sentences:
            if len(" ".join(current_chunk + [sentence]).split()) <= max_chunk_size:
                current_chunk.append(sentence)
            else:
                chunks.append(" ".join(current_chunk))
                current_chunk = [sentence]

        if current_chunk:  # Add the last chunk
            chunks.append(" ".join(current_chunk))

        return chunks


    def populate_index(self, data):
        for i in range(len(data)):
            url = data.loc[i, "url"]
            scraper = WebScraper(url)

            try:
                full_text = scraper.extract_main_text()
                chunks = self.chunk_text(full_text)

                for chunk_position, chunk_text in enumerate(chunks):
                    new_row = {
                        "id": str(uuid.uuid4()),
                        "hrbp_document_id": data.loc[i, "id"],
                        "regulation_link": url,
                        "chunk_position": str(chunk_position),
                        "chunk_text": chunk_text,
                        "chunk_text_vector": self.generate_embeddings_oai(chunk_text)  
                    }
                    self.search_client.upload_documents(new_row)

            except Exception as e:
                print(f"Error processing {url}: {e}")
        


