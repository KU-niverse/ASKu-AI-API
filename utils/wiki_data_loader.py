# wiki_data_loder

from django.db import connection


def wiki_data_load():
    with connection.cursor() as cursor:
        sql = """
        SELECT DISTINCT wd.title, wd.recent_filtered_content
        FROM wiki_history wh
        JOIN wiki_docs wd ON wh.doc_id = wd.id
        WHERE wh.created_at >= CURDATE() - INTERVAL 30 DAY
        AND wh.created_at < CURDATE();
        """
        cursor.execute(sql)
        wiki_data = cursor.fetchall()
    wiki_data_list = [list(t) for t in wiki_data]
    if wiki_data_list:
        return wiki_data_list
    return None
