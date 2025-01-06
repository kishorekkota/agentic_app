import pandas as pd
from azure.core.exceptions import ResourceNotFoundError
from azure.search.documents.indexes.models import SearchIndex, SearchableField, HnswAlgorithmConfiguration, VectorSearch, VectorSearchProfile, SearchFieldDataType, SearchField, SemanticConfiguration, SemanticPrioritizedFields, SemanticField, SemanticSearch
from libs.aisearch_index import AISearchIndex


class CuratedIndex(AISearchIndex):
    def __init__(self, index_name, service_name, azure_search_api_key, openai_api_key,
                  openai_api_version, openai_api_endpoint, openai_embedding_model, vector_length,  data):
        super().__init__(index_name, service_name, azure_search_api_key, openai_api_key,
                         openai_api_version, openai_api_endpoint, openai_embedding_model)
        self.data = data
        self.vector_length = vector_length



    def create_index(self):
        fields = [
            SearchableField(name="id", type="Edm.String", key=True, searchable=True, retrievable=True, filterable=True),
            SearchableField(name="industry", type="Edm.String", searchable=True, retrievable=True, filterable=False),
            SearchableField(name="state", type="Edm.String", searchable=True, retrievable=True, filterable=False),
            SearchableField(name="number_active_employees", type="Edm.Int32", searchable=False, retrievable=True, filterable=False),
            SearchableField(name="number_total_1099s", type="Edm.Int32", searchable=False, retrievable=True, filterable=False),
            SearchableField(name="question_text", type="Edm.String", searchable=True, retrievable=True, filterable=True),
            SearchableField(name="topic", type="Edm.String", searchable=True, retrievable=True, filterable=True),
            SearchableField(name="short_reason", type="Edm.String", searchable=True, retrievable=True, filterable=True),
            SearchableField(name="is_hr_matter", type="Edm.String", searchable=True, retrievable=True, filterable=False),
            SearchableField(name="hr_matter_detail", type="Edm.String",searchable=True, retrievable=True, filterable=False),
            SearchableField(name="case_resolution_guidance_text", type="Edm.String",searchable=True, retrievable=True, filterable=False),
            SearchableField(name="federal_regulations", type="Edm.String",searchable=True, retrievable=True, filterable=False),
            SearchableField(name="state_regulations", type="Edm.String",searchable=True, retrievable=True, filterable=False),
            SearchableField(name="compliance_feedback", type="Edm.String",searchable=True, retrievable=True, filterable=False),
            SearchableField(name="legal_feedback", type="Edm.String", searchable=True, retrievable=True, filterable=False),
            
            SearchField(name="question_vector", type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                        searchable=True, vector_search_dimensions=self.vector_length, vector_search_profile_name="copilot-vector-config-Profile"),
            SearchField(name="case_resolution_guidance_vector", type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                        searchable=True, vector_search_dimensions=self.vector_length, vector_search_profile_name="copilot-vector-config-Profile")
        ]


        vector_search = VectorSearch(
            algorithms=[
                HnswAlgorithmConfiguration(
                    name="copilot-vector-config",
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
                    name="copilot-vector-config-Profile",
                    algorithm_configuration_name="copilot-vector-config",
                )
            ]
        )


        semantic_config = SemanticConfiguration(
            name="curated-semantic-config",
            prioritized_fields=SemanticPrioritizedFields(
                title_field=SemanticField(field_name="short_reason"),
                content_fields=[
                    SemanticField(field_name="question_text"),
                    SemanticField(field_name="case_resolution_guidance_text"),
                    
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

        
    def prep_data(self):
        data.columns = [col.strip() for col in data.columns]
        data.rename(columns={
                            "NAICSLevel01": "industry",
                            "LegalState": "state",
                            "NbrActEEs": "number_active_employees",
                            "NbrTotal1099s": "number_total_1099s",
                            "Is there any additional clients specifics we need to know  and documents we need to have before we answer? If so, please list. If not, leave blank.": 'client_specifics',
                            'Should this be considered an HR Matter?(Y/N)': 'is_hr_matter',
                            'If Yes to previous answer what are the documents and specific information we need from the client? If NO to previous answer continue to the next step.': 'hr_matter_details',
                            'What are the general guidelines for this kind of clients request?(Include how specific federal/state/local regulations impact the answer)': 'general_guidelines',
                            'What are the variations of the guidelines dependent of client demogaphics ?': 'guideline_variations',
                            'Are there any federal regulations applicable, if so cite(only federal website link)': 'federal_regulations',
                            'Are there any state regulations applicable, if so cite :(only state website link)': 'state_regulations',
                            'What are the variations of the guidelines dependent of client/employee demographics ?': 'client_demographics',
                            'Compliance feedback': 'compliance_feedback',
                            'Legal feedback': 'legal_feedback'
                        }, inplace=True)
        
        data = data.dropna(subset=['general_guidelines', 'guideline_variations', 'client_specifics'], how='all').reset_index(drop=True)
        data['case_resolution_guidance'] = ("-GENERAL GUIDELINES: "
                                            + data['general_guidelines'].fillna('')
                                            + " -GUIDELINE VARIATIONS: "
                                            + data['guideline_variations'].fillna('')
                                            + " -CLIENT SPECIFICS: "
                                            + data['client_demographics'].fillna('')) 
   
        data = data.where(pd.notnull(data), None)
        return data
    

    def populate_index(self, data):
        all_rows = []
        for i in range(len(data)):
            try:
                new_row = {}
                #text fields
                new_row["id"] = data.loc[i, "id"]
                new_row["industry"] = data.loc[i, "industry"]
                new_row["state"] = data.loc[i, "state"]
                new_row["number_active_employees"] = data.loc[i, "number_active_employees"]
                new_row["number_total_1099s"] = data.loc[i, "number_total_1099s"]
                new_row["source"] = data.loc[i, "source"]
                new_row["question_text"] = data.loc[i, "question"]
                new_row["short_reason"] = data.loc[i, "short_reason"]
                new_row["topic"] = data.loc[i, "topic"]
                new_row["is_hr_matter"] = data.loc[i, "is_hr_matter"]
                new_row["hr_matter_detail"] = data.loc[i, "hr_matter_detail"]
                new_row["case_resolution_guidance_text"] = data.loc[i, "case_resolution_guidance"]
                new_row["federal_regulations"] = data.loc[i, "federal_regulations"]
                new_row["state_regulations"] = data.loc[i, "state_regulations"]
                new_row["compliance_feedback"] = data.loc[i, "compliance_feedback"]
                new_row["legal_feedback"] = data.loc[i, "legal_feedbac"]

                #vector fields
                new_row["question_vector"] = self.generate_embeddings_oai(data.loc[i, "question"])
                new_row["case_resolution_guidance_vector"] = self.generate_embeddings_oai(data.loc[i, "case_resolution_guidance"])

                all_rows.append(new_row)

            except Exception as e:
                print(f"An error occurred: {e}")
        
        self.search_client.upload_documents(all_rows)

        
