/**
 * Utilities for splitting OCR transcript text into page sections.
 *
 * Page markers in the raw text are footers: "- page N -" appears at the END
 * of page N's content, so the content before each marker belongs to that page.
 */

export const ARCHIVE_BASE = 'https://archive.org/download';

/** Pattern that matches "- page N -" page footer markers (case-insensitive). */
export const PAGE_PATTERN = /(-\s*page\s+(\d+)\s*-)/gi;

export interface PageSection {
  pageNum: number;
  text: string;
  pdfUrl: string;
}

/**
 * Build the Internet Archive download URL for a case's original PDF, or null if
 * the filename can't be mapped to a known archive.org item.
 *
 * Our local filename is the original PDF's name, verbatim. But archive.org's item
 * identifier (the directory) is derived from that name with characters outside
 * [A-Za-z0-9._-] stripped, while the stored PDF file keeps the original name. So the
 * directory and the file portion of the URL differ. We only resolve the bracket case
 * ("[ILLEGIBLE]", "[Blank]", ...) — verified to exist on archive.org with the brackets
 * removed from the id and kept (percent-encoded) in the file. Filenames with other
 * special chars (e.g. '&') have no archive.org item, so we return null and the caller
 * hides the link rather than emit a dead one.
 */
export function buildPdfUrl(filename: string): string | null {
  const base = filename.replace(/\.txt$/i, '');
  if (base.includes('..')) return null; // path-traversal guard
  // Allow only safe characters plus square brackets; anything else is unresolvable.
  if (!/^[a-zA-Z0-9_\-./[\]]+$/.test(base)) return null;
  const identifier = base.replace(/[[\]]/g, ''); // directory: brackets removed
  const file = encodeURIComponent(base); // file: brackets -> %5B/%5D, dashes/dots preserved
  return `${ARCHIVE_BASE}/${identifier}/${file}.pdf`;
}

/**
 * Split raw OCR text into page sections using the footer markers.
 *
 * Returns an array of { pageNum, text, pdfUrl } objects, one per page.
 * If no markers are found, returns a single section with pageNum 0
 * and an empty pdfUrl (caller should render as plain text).
 */
export function splitIntoPages(rawText: string, pdfBase: string): PageSection[] {
  const parts = rawText.split(PAGE_PATTERN);

  // No page markers found
  if (parts.length <= 1) {
    return [{ pageNum: 0, text: rawText, pdfUrl: '' }];
  }

  // parts layout (split with two capturing groups):
  //   [content0, fullMatch1, num1, content1, fullMatch2, num2, content2, ...]
  // Markers are footers: content0 is page num1, content1 is page num2, etc.
  // The last content block has no trailing marker → its pageNum is lastNum + 1.

  const sections: PageSection[] = [];

  // First block: page number comes from the first marker (parts[2])
  if (parts.length >= 3 && parts[0].trim()) {
    const pageNum = parseInt(parts[2], 10);
    sections.push({
      pageNum,
      text: parts[0],
      pdfUrl: `${pdfBase}#page=${pageNum}`,
    });
  }

  // Middle + last blocks (i = 3, 6, 9, ...)
  for (let i = 3; i < parts.length; i += 3) {
    const text = parts[i] || '';
    if (!text.trim()) continue;

    const pageNum =
      i + 2 < parts.length
        ? parseInt(parts[i + 2], 10)      // trailing marker exists
        : parseInt(parts[i - 1], 10) + 1; // last block — increment

    sections.push({
      pageNum,
      text,
      pdfUrl: `${pdfBase}#page=${pageNum}`,
    });
  }

  return sections;
}
