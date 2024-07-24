# views.py
from django.shortcuts import render, get_object_or_404
from .models import Case
from django.utils.html import format_html
import re



import re
from django.utils.html import format_html

def highlight_text(text, query, context=300):
    if not query:
        return text

    query = re.escape(query)  # Escape special characters in the query
    highlighted_text = []
    last_end = 0

    # Regular expression to find all occurrences of the query term
    pattern = re.compile(query, flags=re.IGNORECASE)
    matches = list(pattern.finditer(text))

    for match in matches:
        start, end = match.span()

        # Add text before the match with context
        start_context = max(0, start - context)
        before_match = text[start_context:start]

        # Add the highlighted term with context
        end_context = min(len(text), end + context)
        after_context = text[end:end_context]

        # Combine before, match, and after text
        snippet = format_html(
            '{}<span class="highlight">{}</span>{}',
            before_match,
            match.group(),
            after_context
        )

        # Append snippet with newlines and ellipses
        highlighted_text.append(snippet)

    # Join all snippets with newlines
    highlighted_text = '<br>&hellip;<br>'.join(highlighted_text)
    
    # Ensure that the highlighted_text does not become excessively long
    if len(highlighted_text) > len(text):
        highlighted_text = highlighted_text[:len(text)]

    return highlighted_text

def search_view(request):
    query = request.GET.get('q', '').strip()
    highlighted_results = []
    no_query_message = "Please enter a search term to see results."

    if query:
        # Filter the cases to match the query
        results = Case.objects.filter(
            text_content__icontains=query
        )  # Use icontains for case-insensitive search

        for case in results:
            # Get a larger slice of text content to ensure the term is included
            full_text = case.text_content  # Adjust the slice size as needed
            highlighted_preview = highlight_text(full_text, query)
            highlighted_results.append({
                'title': case.title,
                'url': case.get_absolute_url(),
                'location': case.location,
                'type': case.type,
                'witnesses': case.witnesses,
                'content': highlighted_preview,
            })

    return render(request, 'searcher/search.html', {
        'results': highlighted_results,
        'query': query,
        'no_query_message': no_query_message if not query else ''
    })

def case_detail(request, id):
    case = get_object_or_404(Case, id=id)
    return render(request, 'searcher/case_detail.html', {'case': case})

def download_all_files(request):
    pass
