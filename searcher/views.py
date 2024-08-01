# views.py
from django.shortcuts import render, get_object_or_404
from .models import Case
from django.utils.html import format_html
from django.http import FileResponse, Http404
import re
from django.db.models import Q
from django.core.files.storage import default_storage

def highlight_text(text, query, context=30, snippet_count=2):
    if not query:
        return text

    query = re.escape(query)  # Escape special characters in the query
    highlighted_text = []

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
    highlighted_text = '<br>&hellip;<br>'.join(highlighted_text[:snippet_count])
    
    # Ensure that the highlighted_text does not become excessively long
    if len(highlighted_text) > len(text):
        highlighted_text = highlighted_text[:len(text)]

    return highlighted_text

def search_view(request):
    query = request.GET.get('q', '').strip()
    field = request.GET.get('field', '').strip()

    highlighted_results = []
    no_query_message = "Please enter a search term to see results."

    if query:
        if field == 'title':
            results = Case.objects.filter(Q(title__icontains=query))
        elif field == 'location':
            results = Case.objects.filter(Q(location__icontains=query))
        elif field == 'witnesses':
            results = Case.objects.filter(Q(witnesses__icontains=query))

        else:
            results = Case.objects.filter(
                text_content__icontains=query
            )

        for case in results:
            # Get a larger slice of text content to ensure the term is included
            full_text = case.text_content
            if field == 'text_content':
                preview = highlight_text(full_text, query)
            else:
                preview = ''
            highlighted_results.append({
                'title': case.title,
                'summary': case.summary,
                'url': case.get_absolute_url(),
                'location': case.location,
                'type': case.type,
                'witnesses': case.witnesses,
                'content': preview,
                'pdf': case.get_pdf_url()
            })

    return render(request, 'searcher/search.html', {
        'results': highlighted_results,
        'field': field,
        'query': query,
        'result_count': len(highlighted_results),
        'no_query_message': no_query_message if not query else ''
    })

def case_detail(request, id):
    case = get_object_or_404(Case, id=id)
    view_type = request.GET.get('view', 'pdf')
    show_sidebar = request.GET.get('sidebar', 'true') == 'true'
    context = {
        'case': case,
        'view_type': view_type,
        'show_sidebar': show_sidebar,
    }
    return render(request, 'searcher/case_detail.html', context)

def serve_pdf(request, pk):
    case = get_object_or_404(Case, pk=pk)

    # Construct the file path
    file_path = case.pdf.name

    # Check if the file exists
    if not default_storage.exists(file_path):
        raise Http404("File does not exist")

    # Open the file
    file = default_storage.open(file_path, 'rb')

    # Serve the file
    response = FileResponse(file, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="{case.pdf.name.split("/")[-1]}"'
    return response