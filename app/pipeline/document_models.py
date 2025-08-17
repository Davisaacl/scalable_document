# app/pipeline/document_models.py
"""
Defines dataclasses

Block: 
    text: from PDF, DOCX, or JSON,
    meta: metadata for each block. 

This is needed due to the embedding and vectorial index. They work with small pieces of information.


ParsedDocument:
    doc_id:
    source_path: where it was readed
    mime_type: MIME
    title: reserved for new titles
    blocks: tokenized document structure 

"""

from dataclasses import dataclass
from typing import List, Dict, Optional

@dataclass
class Block:
    text: str
    meta: Dict

@dataclass
class ParsedDocument:
    doc_id: str
    source_path: str
    mime_type: str
    title: Optional[str]
    blocks: List[Block]  
