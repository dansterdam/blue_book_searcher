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
            after_context,
        )

        # Append snippet with newlines and ellipses
        highlighted_text.append(snippet)

    # Join all snippets with newlines
    highlighted_text = "<br>&hellip;<br>".join(highlighted_text[:snippet_count])

    # Ensure that the highlighted_text does not become excessively long
    if len(highlighted_text) > len(text):
        highlighted_text = highlighted_text[: len(text)]

    return highlighted_text


def search_view(request):
    query = request.GET.get("q", "").strip()
    text_content = request.GET.get("text_content", "").strip()
    date = request.GET.get("date", "").strip()
    location = request.GET.get("location", "").strip()
    witness_description = request.GET.get("witness_description", "").strip()

    highlighted_results = []
    no_query_message = "Please enter a search term to see results."

    # Build the Q object based on provided fields
    filters = Q()
    if query:
        filters &= Q(text_content__icontains=query) | Q(title__icontains=query) | Q(location__icontains=query) | Q(witness_description__icontains=query)
    if text_content:
        filters &= Q(text_content__icontains=text_content) | Q(summary__icontains=text_content)
    if date:
        filters &= Q(title__icontains=date)
    if location:
        filters &= Q(location__icontains=location)
    if witness_description:
        filters &= Q(witness_description__icontains=witness_description)

    # Fetch the results based on the combined filters
    if filters:
        results = Case.objects.filter(filters)
    else:
        results = []

    for case in results:
        full_text = case.text_content
        preview = ""
        if text_content:
            preview = highlight_text(full_text, text_content)
        highlighted_results.append(
            {
                "title": case.title,
                "summary": case.summary,
                "url": case.get_absolute_url(),
                "location": case.location,
                "date": case.date,
                "witness_description": case.witness_description,
                "content": preview,
                "pdf": case.get_pdf_url(),
            }
        )

    return render(
        request,
        "searcher/search.html",
        {
            "results": highlighted_results,
            "query": query,
            "text_content": text_content,
            "date": date,
            "location": location,
            "witness_description": witness_description,
            "result_count": len(highlighted_results),
            "no_query_message": no_query_message if not (query or text_content or date or location or witness_description) else "",
        },
    )


def case_detail(request, id):
    case = get_object_or_404(Case, id=id)
    view_type = request.GET.get("view", "pdf")
    show_sidebar = request.GET.get("sidebar", "true") == "true"
    context = {
        "case": case,
        "view_type": view_type,
        "show_sidebar": show_sidebar,
    }
    return render(request, "searcher/case_detail.html", context)


def serve_pdf(request, pk):
    case = get_object_or_404(Case, pk=pk)

    # Construct the file path
    file_path = case.pdf.name

    # Check if the file exists
    if not default_storage.exists(file_path):
        raise Http404("File does not exist")

    # Open the file
    file = default_storage.open(file_path, "rb")

    # Serve the file
    response = FileResponse(file, content_type="application/pdf")
    response[
        "Content-Disposition"
    ] = f'inline; filename="{case.pdf.name.split("/")[-1]}"'
    return response
