# Deployment Guide

## Build Stats
- **7 static HTML pages** + client-side case viewer
- **10,807 case JSON files** served as static assets (~151MB)
- **Pagefind search index** (~36MB compressed, chunked and lazy-loaded)
- **Total dist size**: ~223MB
- **Total files**: ~22,000

## Free Hosting Options

### Option 1: Netlify (Recommended ✅)
**Best choice** — no file count limit, 100GB/month bandwidth, free tier.

```bash
# Install Netlify CLI
npm install -g netlify-cli

# Build and deploy
npm run build
netlify deploy --prod --dir dist
```

Or connect your GitHub repo to Netlify and it auto-builds on push.

### Option 2: Cloudflare Pages
**Note**: Free tier has a 20,000 file limit. Our deploy is ~22,000 files, so you'd need the Pro plan ($25/month) OR reduce file count by removing individual case JSONs and loading text inline.

```bash
# Install Wrangler
npm install -g wrangler

# Deploy
wrangler pages deploy dist --project-name blue-book-archive
```

### Option 3: Vercel
Free tier supports static sites. File count shouldn't be an issue.

```bash
npm install -g vercel
npm run build
vercel --prod
```

## Build Commands

```bash
# Install dependencies
npm install

# Prepare data (run once, or when casefiles change)
npm run prepare-data

# Build everything (prepare + astro build + pagefind index)
npm run build

# Preview locally
npm run preview
```

## Architecture

```
casefiles/
├── txt/          # 10,807 OCR'd document transcripts
└── json/         # 10,807 AI-extracted metadata files

blue-book-astro/
├── scripts/
│   ├── prepare-data.mjs        # Reads casefiles → generates src/data/ and public/data/
│   └── build-search-index.mjs  # Runs after astro build → generates dist/pagefind/
├── src/
│   ├── data/
│   │   ├── cases-index.json    # Slim metadata (no text) — used at build time
│   │   └── stats.json          # Pre-computed stats
│   ├── pages/
│   │   ├── index.astro         # Home page
│   │   ├── search.astro        # Pagefind search interface
│   │   ├── case.astro          # Client-side case viewer (/case?id=<slug>)
│   │   ├── browse.astro        # Browse by year/state
│   │   ├── stats.astro         # Statistical analysis
│   │   └── about.astro         # About page
│   └── layouts/
│       └── BaseLayout.astro
└── public/
    └── data/
        └── cases/              # 10,807 individual case JSON files
                                # Each file: ~14KB, contains full text + metadata
```

## How Search Works

1. **Pagefind index** (`dist/pagefind/`) is built once during `npm run build`
2. The search page loads Pagefind's JS lazily on first keypress
3. Pagefind performs full-text search entirely client-side — no server needed
4. Filters: year, state, witness count, photographic evidence
5. Each search result links to `/case?id=<slug>`
6. The case viewer page (`/case`) fetches `/data/cases/<slug>.json` to display the case

## Updating Cases

If the casefiles directory is updated with new records:

```bash
npm run prepare-data  # Re-generates data files (skips existing case JSONs)
npm run build         # Rebuilds everything
```

To force re-generation of all case JSON files, delete `public/data/cases/` first.
