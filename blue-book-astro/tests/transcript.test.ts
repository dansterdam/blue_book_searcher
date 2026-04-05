import { describe, it, expect } from 'vitest';
import { buildPdfUrl, splitIntoPages, S3_BASE } from '../src/utils/transcript';

// ---------------------------------------------------------------------------
// buildPdfUrl
// ---------------------------------------------------------------------------

describe('buildPdfUrl', () => {
  it('replaces .txt with .pdf', () => {
    const url = buildPdfUrl('1947-06-9668679-Hamburg-NewYork.txt');
    expect(url).toBe(`${S3_BASE}/1947-06-9668679-Hamburg-NewYork.pdf`);
  });

  it('handles filenames with trailing dash before extension', () => {
    const url = buildPdfUrl('1945-11-7276022-TomsRiver-NewJersey-2853-.txt');
    expect(url).toBe(`${S3_BASE}/1945-11-7276022-TomsRiver-NewJersey-2853-.pdf`);
  });

  it('is case-insensitive for the extension', () => {
    const url = buildPdfUrl('1952-01-0001-Roswell-NewMexico.TXT');
    expect(url).toContain('.pdf');
    expect(url).not.toContain('.TXT');
  });

  it('includes the S3 base URL', () => {
    const url = buildPdfUrl('some-case.txt');
    expect(url).toMatch(/^https:\/\/blue-book-searcher\.s3\.us-east-1\.amazonaws\.com\//);
  });
});

// ---------------------------------------------------------------------------
// splitIntoPages — no markers
// ---------------------------------------------------------------------------

describe('splitIntoPages — no page markers', () => {
  it('returns a single section with pageNum 0', () => {
    const result = splitIntoPages('plain text with no markers', 'https://example.com/doc.pdf');
    expect(result).toHaveLength(1);
    expect(result[0].pageNum).toBe(0);
    expect(result[0].text).toBe('plain text with no markers');
  });

  it('returns empty pdfUrl when no markers', () => {
    const result = splitIntoPages('no markers here', 'https://example.com/doc.pdf');
    expect(result[0].pdfUrl).toBe('');
  });
});

// ---------------------------------------------------------------------------
// splitIntoPages — with markers (footer style)
// ---------------------------------------------------------------------------

const PDF = 'https://example.com/doc.pdf';

const SAMPLE = `
Content of page one here.
More page one text.
- page 1 -
Content of page two here.
- page 2 -
Content of page three here.
`.trim();

describe('splitIntoPages — footer-style markers', () => {
  it('returns the correct number of sections', () => {
    const sections = splitIntoPages(SAMPLE, PDF);
    expect(sections).toHaveLength(3);
  });

  it('assigns page numbers correctly (footer = number of content before it)', () => {
    const sections = splitIntoPages(SAMPLE, PDF);
    expect(sections[0].pageNum).toBe(1); // content before "- page 1 -"
    expect(sections[1].pageNum).toBe(2); // content before "- page 2 -"
    expect(sections[2].pageNum).toBe(3); // last block: 2 + 1
  });

  it('each section contains the right text', () => {
    const sections = splitIntoPages(SAMPLE, PDF);
    expect(sections[0].text).toContain('page one');
    expect(sections[1].text).toContain('page two');
    expect(sections[2].text).toContain('page three');
  });

  it('builds correct pdfUrls with #page fragment', () => {
    const sections = splitIntoPages(SAMPLE, PDF);
    expect(sections[0].pdfUrl).toBe(`${PDF}#page=1`);
    expect(sections[1].pdfUrl).toBe(`${PDF}#page=2`);
    expect(sections[2].pdfUrl).toBe(`${PDF}#page=3`);
  });

  it('handles flexible whitespace in markers', () => {
    const text = 'page A content\n-  page  3  -\npage B content\n- page 4 -\nlast'.trim();
    const sections = splitIntoPages(text, PDF);
    expect(sections[0].pageNum).toBe(3);
    expect(sections[1].pageNum).toBe(4);
  });

  it('handles case-insensitive markers', () => {
    const text = 'first\n- Page 1 -\nsecond\n- PAGE 2 -\nthird'.trim();
    const sections = splitIntoPages(text, PDF);
    expect(sections).toHaveLength(3);
    expect(sections[0].pageNum).toBe(1);
    expect(sections[1].pageNum).toBe(2);
    expect(sections[2].pageNum).toBe(3);
  });

  it('skips empty sections', () => {
    // Two markers back-to-back with no content between
    const text = 'real content\n- page 1 -\n\n- page 2 -\nmore content';
    const sections = splitIntoPages(text, PDF);
    // The empty section between markers should be skipped
    const nonEmpty = sections.filter(s => s.text.trim());
    expect(nonEmpty.every(s => s.text.trim().length > 0)).toBe(true);
  });

  it('last section page number is previous + 1', () => {
    const text = 'first\n- page 5 -\nlast content';
    const sections = splitIntoPages(text, PDF);
    const last = sections[sections.length - 1];
    expect(last.pageNum).toBe(6);
  });

  it('single marker splits into two sections', () => {
    const text = 'before\n- page 1 -\nafter';
    const sections = splitIntoPages(text, PDF);
    expect(sections).toHaveLength(2);
    expect(sections[0].text).toContain('before');
    expect(sections[1].text).toContain('after');
  });
});
