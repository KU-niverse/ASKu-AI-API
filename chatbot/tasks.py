from celery import shared_task
from django.conf import settings

from evaluation.product.haho_v1 import ready_chain
from script.manage_wikiUpdated import manage_wiki_update


@shared_task
def wiki_data_schedule():
    manage_wiki_update(update=True)
    if getattr(settings, "query_chain", None):
        delattr(settings, "query_chain")
    query_chain = ready_chain()
    setattr(settings, "query_chain", query_chain)
