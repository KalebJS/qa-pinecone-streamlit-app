import json

import openai
import pinecone
import torch
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

from config import ENCODING_MODEL
from libraries.notion.notion_api import NotionAPI

with open("credentials.json", "r") as f:
    credentials = json.load(f)

notion_api = NotionAPI(credentials["notion"])
pages = notion_api._get_database_pages(credentials["notion"]["DOCS_NOTION_DATABASE_ID"])
page_content = []
for page_id, page in tqdm(pages.items()):
    paragraphs = notion_api.get_page_content(page_id)
    page_url = page["url"]
    page_content.extend([(page_id, page_url, paragraph) for paragraph in paragraphs if paragraph])


if ENCODING_MODEL == "remote":
    openai.api_key = credentials["openai"]["api_key"]
else:
    device = "cuda" if torch.cuda.is_available() else "cpu"
    if device != "cuda":
        print(
            f"You are using {device}. This is much slower than using "
            "a CUDA-enabled GPU. If on Colab you can change this by "
            "clicking Runtime > Change runtime type > GPU."
        )

    model = SentenceTransformer("all-MiniLM-L6-v2", device=device)


# get api key from app.pinecone.io
api_key = credentials["pinecone"]["api_key"]
# find your environment next to the api key in pinecone console
env = credentials["pinecone"]["environment"]

pinecone.init(api_key=api_key, environment=env)

if ENCODING_MODEL == "remote":
    index_name = "notion-documents-openai"
else:
    index_name = "notion-documents-local"

if index_name not in pinecone.list_indexes():
    # if does not exist, create index
    if ENCODING_MODEL == "remote":
        pinecone.create_index(
            index_name,
            dimension=1536,  # dimensionality of text-embedding-ada-002
            metric="cosine",
        )
    else:
        pinecone.create_index(name=index_name, dimension=model.get_sentence_embedding_dimension(), metric="cosine")
# connect to index
index = pinecone.GRPCIndex(index_name)

batch_size = 128
vector_limit = 100000
sample = page_content[:vector_limit]

for i in tqdm(range(0, len(sample), batch_size)):
    # find end of batch
    i_end = min(i + batch_size, len(sample))
    # create IDs batch
    ids = [str(x) for x in range(i, i_end)]
    # create metadata batch
    metadatas = [
        {"id": page_id, "url": page_url, "text": paragraph} for page_id, page_url, paragraph in sample[i:i_end]
    ]
    # create embeddings
    texts = [paragraph for _, _, paragraph in sample[i:i_end]]
    if ENCODING_MODEL == "remote":
        res = openai.Embedding.create(input=texts, engine="text-embedding-ada-002")
        xc = [x["embedding"] for x in res["data"]]
    else:
        xc = model.encode(texts)

    # create records list for upsert
    records = zip(ids, xc, metadatas)
    # upsert to Pinecone
    index.upsert(vectors=records)
