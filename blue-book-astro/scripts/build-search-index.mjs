/**
 * Build Pagefind search index from all case data.
 * Runs after `astro build` to create the search index in dist/pagefind/.
 *
 * Uses Pagefind's programmatic Node.js API so we don't need 10,807 HTML pages.
 * Each case is added as a custom record with filters for faceted search.
 */
import * as pagefind from 'pagefind';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, '..');
const CASES_JSON = path.resolve(__dirname, '../../cases.json');
const OUTPUT_PATH = path.join(ROOT, 'dist', 'pagefind');

console.log('🔍 Building Pagefind search index...');
console.log('  Reading cases.json...');
const cases = JSON.parse(fs.readFileSync(CASES_JSON, 'utf8'));
console.log(`  → ${cases.length} cases loaded`);

// Create pagefind index
const { index } = await pagefind.createIndex({
  forceLanguage: 'en',
});

console.log('  Adding records to index...');
let processed = 0;
const BATCH_SIZE = 500;

for (let i = 0; i < cases.length; i++) {
  const c = cases[i];

  // Normalize witness count into groups for filtering
  let witnessGroup = 'unknown';
  if (c.witnesses !== null && c.witnesses !== undefined) {
    if (c.witnesses === 0) witnessGroup = '0';
    else if (c.witnesses === 1) witnessGroup = '1';
    else if (c.witnesses === 2) witnessGroup = '2';
    else if (c.witnesses <= 5) witnessGroup = '3-5';
    else if (c.witnesses <= 10) witnessGroup = '6-10';
    else witnessGroup = '10+';
  }

  // Build content for indexing:
  // Include rich metadata plus first 3000 chars of raw text for full-text search.
  // Truncating the full text keeps the index size manageable while still allowing
  // meaningful keyword searches across the document.
  const truncatedText = (c.text_content || '').slice(0, 3000);
  const content = [
    c.summary || '',
    c.interesting_points || '',
    c.sighted_object || '',
    c.witness_description || '',
    c.location || '',
    c.conclusion || '',
    truncatedText,
  ].join('\n\n');

  const filters = {};
  if (c.year) filters.year = [String(c.year)];
  if (c.state && c.state.length > 1 && c.state !== 'US') filters.state = [c.state];
  filters.witnesses = [witnessGroup];
  filters.photos = [c.contains_photographs ? 'Yes' : 'No'];

  await index.addCustomRecord({
    url: `/case?id=${c.id}`,
    content: content,
    meta: {
      title: c.summary || c.location || c.filename,
      image: '',
      image_alt: '',
    },
    filters,
    language: 'en',
  });

  processed++;
  if (processed % BATCH_SIZE === 0) {
    process.stdout.write(`\r  → ${processed}/${cases.length} records indexed...`);
  }
}

console.log(`\r  → ${processed} records indexed          `);

// Write the index to disk
console.log(`  Writing index to ${OUTPUT_PATH}...`);
const { errors } = await index.writeFiles({ outputPath: OUTPUT_PATH });

if (errors.length > 0) {
  console.error('  ⚠️  Errors:', errors);
} else {
  console.log('  ✅ Pagefind index built successfully!');
}

// Report index size
let totalSize = 0;
function measureDir(dir) {
  if (!fs.existsSync(dir)) return;
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) measureDir(full);
    else totalSize += fs.statSync(full).size;
  }
}
measureDir(OUTPUT_PATH);
console.log(`  Index size: ${(totalSize / 1024 / 1024).toFixed(1)} MB`);
console.log('\n✅ Search index build complete!');
