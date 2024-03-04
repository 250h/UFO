# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import requests
from ..config.config import load_config
from langchain.text_splitter import HTMLHeaderTextSplitter
from langchain.docstore.document import Document
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS


configs = load_config()


class BingWebRetriever:
    """
    Class to retrieve web documents.
    """
    
    def __init__(self):
        """
        Create a new WebRetriever.
        """
        self.api_key = configs["BING_API_KEY"]


    def search(self, query: str, top_k: int = 1):
        """
        Retrieve the web document from the given URL.
        :param url: The URL to retrieve the web document from.
        :return: The web document from the given URL.
        """
        url = f"https://api.bing.microsoft.com/v7.0/search?q={query}"
        if top_k > 0:
            url += f"&count={top_k}"
        try:
            response = requests.get(url, headers={"Ocp-Apim-Subscription-Key": self.api_key})
        except requests.RequestException as e:
            print(f"Error when searching: {e}")
            return None
        result_list = []

        for item in response.json()["webPages"]["value"]:
            result_list.append({"name": item["name"], "url": item["url"], "snippet": item["snippet"]})

        return result_list


    def get_url_text(self, url: str):
        """
        Retrieve the web document from the given URL.
        :param url: The URL to retrieve the web document from.
        :return: The web text from the given URL.
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                html_splitter = HTMLHeaderTextSplitter(headers_to_split_on=[])
                document = html_splitter.split_text(response.text)
                return document
            else:
                print("Error in  getting search result for {url}, error code: {status_code}.".format(url=url, status_code=response.status_code))
                return None
        except requests.exceptions.RequestException as e:
            print("Error in  getting search result for {url}: {e}.".format(url=url, e=e))
            return None


    def create_documents(self, result_list: list):
        """
        Create documents from the given result list.
        :param result_list: The result list to create documents from.
        :return: The documents from the given result list.
        """
        document_list = []

        for result in result_list:
            documents = self.get_url_text(result["url"])
            for document in documents:
                page_content = document.page_content
                metadata = document.metadata
                metadata["url"] = result["url"]
                metadata["name"] = result["name"]
                metadata["snippet"] = result["snippet"]

                document = Document(page_content=page_content, metadata=metadata)
                document_list.append(document)

        return document_list
    
    def create_indexer(self, documents: list):
        """
        Create an indexer for the given query.
        :param query: The query to create an indexer for.
        :return: The created indexer.
        """
        embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")

        db = FAISS.from_documents(documents, embeddings)

        return db
    

        

        
    

    