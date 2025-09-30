import pandas as pd
import requests
import os
from urllib.parse import urlencode
from sqlmodel import Session
from dotenv import load_dotenv
load_dotenv("../.env")

import sys
sys.path.append("../")
from modules.database import create_db_and_tables, engine
from modules.models import SDODocument

token = os.getenv("NASA_ADS_API_KEY")

search_url = "https://api.adsabs.harvard.edu/v1/search/query"


def main():
    create_db_and_tables()
    docs = extract_sdo_documents()
    load_sdo_documents(docs)

def extract_sdo_documents():
    # Extract SDODocument attributes for the 'fl' parameter
    fl_fields = ",".join([col.name for col in SDODocument.__table__.columns])

    encoded_url = urlencode({
        "q": "abstract:SDO, year:2010",
        "fq": "property:refereed",
        "sort": "date desc",
        "fl": fl_fields,
        "rows": 2000
    })
    
    results = requests.get(f"{search_url}?{encoded_url}", 
                           headers={"Authorization": f"Bearer {token}"}).json()

    return results['response']['docs']

def load_sdo_documents(docs):
    with Session(engine) as session:
        for doc in docs:
            sdo_doc = SDODocument(
                id=int(doc.get('id')),
                title=doc.get('title', [''])[0],
                abstract=doc.get('abstract', ''),
                authors=", ".join(doc.get('author', [])),
                publication_date=int(doc.get('year', 0)),
                doi=doc.get('doi', [None])[0],
                bibcode=doc.get('bibcode', None),
                citation_count=doc.get('citation_count', None)
            )
            session.add(sdo_doc)
        session.commit()
        
if __name__ == "__main__":
    main()