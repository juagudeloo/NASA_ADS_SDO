from fastapi import FastAPI, Depends, HTTPException, Query
from sqlmodel import Session, select
from typing import List, Optional
import sys
sys.path.append("../")
from modules.database import engine
from modules.models import SDODocument, SDODocumentPublic

app = FastAPI(
    title="SDO Documents API",
    description="API for accessing Solar Dynamics Observatory research documents extracted from the NASA ADS database.",
    version="1.0.0"
)

def get_session():
    with Session(engine) as session:
        yield session

@app.get("/documents/", response_model=List[SDODocumentPublic])
def read_documents(
    skip: int = Query(0, ge=0, description="Number of documents to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of documents to return"),
    year: Optional[int] = Query(None, description="Filter by publication year"),
    session: Session = Depends(get_session)
):
    """Get a list of SDO documents with optional filtering and pagination."""
    query = select(SDODocument)
    
    if year:
        query = query.where(SDODocument.publication_date.like(f"{year}%"))
    
    query = query.offset(skip).limit(limit)
    documents = session.exec(query).all()
    return documents

@app.get("/documents/{document_id}", response_model=SDODocumentPublic)
def read_document(document_id: int, session: Session = Depends(get_session)):
    """Get a specific SDO document by ID."""
    document = session.get(SDODocument, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document

@app.get("/documents/search/", response_model=List[SDODocumentPublic])
def search_documents(
    q: str = Query(..., description="Search query for title or abstract"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    session: Session = Depends(get_session)
):
    """Search documents by title or abstract content."""
    query = select(SDODocument).where(
        (SDODocument.title.contains(q)) | (SDODocument.abstract.contains(q))
    ).offset(skip).limit(limit)
    
    documents = session.exec(query).all()
    return documents

@app.get("/stats/")
def get_stats(session: Session = Depends(get_session)):
    """Get basic statistics about the document collection."""
    total_docs = session.exec(select(SDODocument)).all()
    total_count = len(total_docs)
    
    years = [int(doc.publication_date[:4]) for doc in total_docs if doc.publication_date and len(doc.publication_date) >= 4]
    year_range = {"min": min(years), "max": max(years)} if years else None
    
    return {
        "total_documents": total_count,
        "year_range": year_range
    }

@app.get("/")
def root():
    """API root endpoint."""
    return {"message": "SDO Documents API", "version": "1.0.0"}
