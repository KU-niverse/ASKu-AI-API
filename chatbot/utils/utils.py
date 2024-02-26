from typing import List

from langchain.schema import Document
from json import dumps


def getUserIpAddress(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
    
def formatReference(context: List[Document]):
    reference = {"Rule": ""}
    for document in context:
        if "title" in document.metadata.keys():
            reference[document.metadata["title"]] = document.page_content
        else:
            reference["Rule"] = reference["Rule"] + document.page_content + "\n"
    
    return dumps(reference, ensure_ascii=False)
