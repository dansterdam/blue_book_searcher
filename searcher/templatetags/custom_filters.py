# searcher/templatetags/page_link.py
from django import template
import re

register = template.Library()


@register.filter
def page_links(text, case_id):
    pattern = re.compile(r"\s*- page (\d+) -\s*", re.MULTILINE)

    def replace_page_link(match):
        page_number = match.group(1)
        return f'<h3><a href="?view=pdf&page={page_number}" class="page-link" onclick="showPage({page_number})">-- page {page_number} --</a></h3>'

    return pattern.sub(replace_page_link, text)
