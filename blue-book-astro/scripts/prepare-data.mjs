/**
 * Prepare Blue Book data for Astro build.
 * Reads the master cases.json and:
 *  1. Writes public/data/cases/<id>.json  (individual case files, served to browser)
 *  2. Writes src/data/cases-index.json    (slim metadata, used at build time)
 *  3. Writes src/data/stats.json          (pre-computed statistics)
 */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, '..');
// cases.json lives at the repo root (../.. from this script = blue_book_searcher/)
const CASES_JSON = path.resolve(__dirname, '../../cases.json');
const PUBLIC_CASES_DIR = path.join(ROOT, 'public', 'data', 'cases');
const SRC_DATA_DIR = path.join(ROOT, 'src', 'data');

// If cases.json doesn't exist, tell user to run parse-cases.py first
if (!fs.existsSync(CASES_JSON)) {
  console.error(`❌ cases.json not found at ${CASES_JSON}`);
  console.error('   Run: python3 scripts/parse-cases.py first');
  process.exit(1);
}

console.log('📂 Reading cases.json...');
const cases = JSON.parse(fs.readFileSync(CASES_JSON, 'utf8'));
console.log(`  → ${cases.length} cases loaded`);

// Create output directories
fs.mkdirSync(PUBLIC_CASES_DIR, { recursive: true });
fs.mkdirSync(SRC_DATA_DIR, { recursive: true });

// 1. Write individual case JSON files (include text_content for full-text display)
console.log('📄 Writing individual case files...');
let written = 0;
for (const c of cases) {
  const outPath = path.join(PUBLIC_CASES_DIR, `${c.id}.json`);
  // Only write if not exists (speed up re-runs)
  if (!fs.existsSync(outPath)) {
    fs.writeFileSync(outPath, JSON.stringify({
      id: c.id,
      filename: c.filename,
      case_id: c.case_id,
      date: c.date,
      year: c.year,
      month: c.month,
      location: c.location,
      state: c.state,
      summary: c.summary,
      interesting_points: c.interesting_points,
      sighted_object: c.sighted_object,
      witnesses: c.witnesses,
      witness_description: c.witness_description,
      contains_photographs: c.contains_photographs,
      conclusion: c.conclusion,
      text_content: c.text_content,
      has_json: c.has_json,
    }));
    written++;
  }
}
console.log(`  → ${written} new files written (${cases.length - written} already existed)`);

// 2. Write slim index (no text_content) for build-time use
console.log('📋 Writing cases-index.json...');
const index = cases.map(c => ({
  id: c.id,
  filename: c.filename,
  case_id: c.case_id,
  date: c.date,
  year: c.year,
  month: c.month,
  location: c.location,
  state: c.state,
  summary: c.summary,
  interesting_points: c.interesting_points,
  sighted_object: c.sighted_object,
  witnesses: c.witnesses,
  witness_description: c.witness_description,
  contains_photographs: c.contains_photographs,
  conclusion: c.conclusion,
  has_json: c.has_json,
}));
// Write to src/data/ for build-time import (stats page, home page)
fs.writeFileSync(path.join(SRC_DATA_DIR, 'cases-index.json'), JSON.stringify(index));
console.log(`  → src/data: ${(fs.statSync(path.join(SRC_DATA_DIR, 'cases-index.json')).size / 1024 / 1024).toFixed(1)} MB`);

// Also write a SLIM browse index (just id, date, year, location, state, summary, witnesses, photos)
// This is fetched client-side by the browse page — much smaller than the full index
const browseIndex = cases.map(c => ({
  id: c.id,
  date: c.date,
  year: c.year,
  location: c.location,
  state: c.state,
  summary: c.summary ? c.summary.slice(0, 120) : '',
  witnesses: c.witnesses,
  contains_photographs: c.contains_photographs,
  conclusion_category: c.conclusion && c.conclusion.trim() ? normalizeConclusion(c.conclusion) : '',
}));
const PUBLIC_DATA_DIR = path.join(ROOT, 'public', 'data');
fs.mkdirSync(PUBLIC_DATA_DIR, { recursive: true });
fs.writeFileSync(path.join(PUBLIC_DATA_DIR, 'browse-index.json'), JSON.stringify(browseIndex));
console.log(`  → public/data/browse-index.json: ${(fs.statSync(path.join(PUBLIC_DATA_DIR, 'browse-index.json')).size / 1024 / 1024).toFixed(1)} MB`);

// Map index — slim records with lat/lng for the map page
// Only written if locations-geocoded.json exists (run geocode-locations.py first)
const GEOCODED_FILE = path.join(__dirname, '../src/data/locations-geocoded.json');
if (fs.existsSync(GEOCODED_FILE)) {
  console.log('🗺️  Writing map-index.json...');
  const geocoded = JSON.parse(fs.readFileSync(GEOCODED_FILE, 'utf8'));
  const mapIndex = cases
    .map(c => {
      const coords = geocoded[c.location];
      if (!coords) return null;
      return {
        id: c.id,
        date: c.date,
        year: c.year,
        location: c.location,
        summary: c.summary ? c.summary.slice(0, 100) : '',
        witnesses: c.witnesses,
        contains_photographs: c.contains_photographs,
        lat: coords[0],
        lng: coords[1],
      };
    })
    .filter(Boolean);
  fs.writeFileSync(path.join(PUBLIC_DATA_DIR, 'map-index.json'), JSON.stringify(mapIndex));
  console.log(`  → ${mapIndex.length.toLocaleString()} mapped cases`);
  console.log(`  → public/data/map-index.json: ${(fs.statSync(path.join(PUBLIC_DATA_DIR, 'map-index.json')).size / 1024 / 1024).toFixed(1)} MB`);
} else {
  console.log('🗺️  Skipping map-index.json (run geocode-locations.py to enable the map page)');
}

// 3. Compute statistics
console.log('📊 Computing statistics...');

// Cases per year
const casesByYear = {};
for (const c of cases) {
  if (c.year) {
    casesByYear[c.year] = (casesByYear[c.year] || 0) + 1;
  }
}

// Cases by state (top 20)
const casesByState = {};
for (const c of cases) {
  if (c.state && c.state !== 'US' && c.state.length > 1) {
    casesByState[c.state] = (casesByState[c.state] || 0) + 1;
  }
}
const topStates = Object.entries(casesByState)
  .sort((a, b) => b[1] - a[1])
  .slice(0, 20)
  .map(([state, count]) => ({ state, count }));
// Distinct countries — raw `state` values mix US states, countries, oceans, regions,
// abbreviations, and misspellings; map known values to a canonical country, skip the rest
const US_STATES = ['Alabama','Alaska','Arizona','Arkansas','California','Colorado','Connecticut','Delaware','Florida','Georgia','Hawaii','Idaho','Illinois','Indiana','Iowa','Kansas','Kentucky','Louisiana','Maine','Maryland','Massachusetts','Michigan','Minnesota','Mississippi','Missouri','Montana','Nebraska','Nevada','New Hampshire','New Jersey','New Mexico','New York','North Carolina','North Dakota','Ohio','Oklahoma','Oregon','Pennsylvania','Rhode Island','South Carolina','South Dakota','Tennessee','Texas','Utah','Vermont','Virginia','Washington','West Virginia','Wisconsin','Wyoming'];
const US_STATE_SET = new Set(US_STATES.map(s => s.toLowerCase()));
const US_ALIASES = [
  // country names, DC, abbreviations, misspellings
  'us', 'usa', 'united states', 'united states of america', 'district of columbia', 'dc', 'd c',
  'ca', 'ny', 'md', 'va', 'pa', 'la', 'ky', 'nj', 'nc', 'wa', 'nv', 'il', 'pr', 'gu',
  'colo', 'minn', 'wisc', 'mass', 'mo', 'ga', 'calif', 'utan',
  // territories (era-appropriate: counted as US)
  'puerto rico', 'guam', 'virgin islands', 'midway islands', 'johnston island', 'canal zone',
  'trust territory of the pacific islands', 'marshall islands',
  // cities, sub-state regions, multi-state values
  'long island', 'new york city', 'new york state', 'washington and oregon states',
  'central pennsylvania', 'new orleans', 'indianapolis', 'montgomery', 'east baton rouge parish',
  'florida keys', 'west coast us', 'carolina', 'maine area', 'medicine bow', 'hawaiian islands',
  'virginia and new york', 'near puerto rico', 'rocky mountain area',
];
const COUNTRY_ALIASES = {
  ...Object.fromEntries(US_ALIASES.map(k => [k, 'United States'])),
  'canada': 'Canada', 'newfoundland': 'Canada', 'labrador': 'Canada',
  'japan': 'Japan', 'okinawa': 'Japan', 'kadena': 'Japan', 'ryuku island': 'Japan', 'northern japan': 'Japan', 'japanese area': 'Japan',
  'germany': 'Germany', 'west germany': 'Germany',
  'england': 'United Kingdom', 'uk': 'United Kingdom', 'scotland': 'United Kingdom', 'northern ireland': 'United Kingdom', 'bermuda': 'United Kingdom', 'british west indies': 'United Kingdom', 'bwi': 'United Kingdom',
  'korea': 'South Korea', 'south korea': 'South Korea', 'north korea': 'North Korea',
  'denmark': 'Denmark', 'greenland': 'Denmark',
  'italy': 'Italy', 'southern italy': 'Italy',
  'philippines': 'Philippines', 'republic philippines': 'Philippines', 'usaf philippines': 'Philippines',
  'france': 'France', 'martinique': 'France',
  'portugal': 'Portugal', 'azores': 'Portugal',
  'australia': 'Australia', 'south australia': 'Australia', 'au': 'Australia',
  'ussr': 'Soviet Union', 'russia': 'Soviet Union', 'northeastern siberia': 'Soviet Union',
  'morocco': 'Morocco', 'french morocco': 'Morocco',
  'libya': 'Libya', 'lybia': 'Libya',
  'netherlands': 'Netherlands', 'holland': 'Netherlands',
  'colombia': 'Colombia', 'columbia': 'Colombia',
  'taiwan': 'Taiwan', 'formosa': 'Taiwan',
  'india': 'India', 'northeast india': 'India',
  'panama': 'Panama', 'panama canal': 'Panama',
  'viet nam': 'Vietnam', 'south viet nam': 'Vietnam', 'republic vietnam': 'Vietnam',
  'new guinea': 'Papua New Guinea', 'papua new guinea': 'Papua New Guinea',
  'fiji islands': 'Fiji',
  'mexico': 'Mexico', 'iceland': 'Iceland', 'turkey': 'Turkey', 'brazil': 'Brazil',
  'venezuela': 'Venezuela', 'iran': 'Iran', 'uruguay': 'Uruguay', 'spain': 'Spain',
  'finland': 'Finland', 'south africa': 'South Africa', 'sweden': 'Sweden',
  'argentina': 'Argentina', 'chile': 'Chile', 'saudi arabia': 'Saudi Arabia', 'peru': 'Peru',
  'china': 'China', 'norway': 'Norway', 'greece': 'Greece', 'new zealand': 'New Zealand',
  'indonesia': 'Indonesia', 'switzerland': 'Switzerland', 'guatemala': 'Guatemala',
  'cyprus': 'Cyprus', 'pakistan': 'Pakistan', 'burma': 'Burma', 'thailand': 'Thailand',
  'cuba': 'Cuba', 'hungary': 'Hungary', 'algeria': 'Algeria', 'egypt': 'Egypt',
  'afghanistan': 'Afghanistan', 'paraguay': 'Paraguay', 'singapore': 'Singapore',
  'yugoslavia': 'Yugoslavia', 'bulgaria': 'Bulgaria', 'poland': 'Poland',
  'czechoslovakia': 'Czechoslovakia', 'jamaica': 'Jamaica', 'iraq': 'Iraq',
  'bahamas': 'Bahamas', 'austria': 'Austria', 'israel': 'Israel', 'bolivia': 'Bolivia',
  'nicaragua': 'Nicaragua', 'haiti': 'Haiti', 'lebanon': 'Lebanon', 'belgium': 'Belgium',
};
function countryForState(raw) {
  const s = String(raw || '').trim().toLowerCase();
  if (!s) return null;
  if (US_STATE_SET.has(s)) return 'United States';
  return COUNTRY_ALIASES[s] || null;
}
const countrySet = new Set(cases.map(c => countryForState(c.state)).filter(Boolean));
const distinctCountries = countrySet.size;

// Witness distribution
const witnessGroups = { '0': 0, '1': 0, '2': 0, '3-5': 0, '6-10': 0, '10+': 0, 'unknown': 0 };
for (const c of cases) {
  if (c.witnesses === null || c.witnesses === undefined) {
    witnessGroups['unknown']++;
  } else if (c.witnesses === 0) {
    witnessGroups['0']++;
  } else if (c.witnesses === 1) {
    witnessGroups['1']++;
  } else if (c.witnesses === 2) {
    witnessGroups['2']++;
  } else if (c.witnesses <= 5) {
    witnessGroups['3-5']++;
  } else if (c.witnesses <= 10) {
    witnessGroups['6-10']++;
  } else {
    witnessGroups['10+']++;
  }
}

// AF Conclusion categories
function normalizeConclusion(raw) {
  const c = raw.toUpperCase();
  if (/\bBALLOON\b/.test(c)) return 'Balloon';
  if (/\bA\/C\b/.test(c) || c.includes('AIRCRAFT')) return 'Aircraft';
  if (['ASTRO', 'STAR', 'PLANET', 'METEOR', 'SATELLITE', 'SUN DOG', 'SUNDOG'].some(x => c.includes(x))) return 'Astronomical';
  if (c.includes('UNIDENTIFIED')) return 'Unidentified';
  if (c.includes('INSUFF')) return 'Insufficient Data';
  if (c.includes('HOAX')) return 'Hoax';
  if (['CONTRAIL', 'CLOUD', 'WEATHER', 'ATMOSPHERIC'].some(x => c.includes(x))) return 'Natural / Atmospheric';
  if (c.includes('BIRD')) return 'Birds';
  if (c.includes('MISSILE') || c.includes('ROCKET')) return 'Missile / Rocket';
  return 'Other / Unknown';
}
const conclusionCounts = {};
for (const c of cases) {
  if (c.conclusion && c.conclusion.trim()) {
    const cat = normalizeConclusion(c.conclusion);
    conclusionCounts[cat] = (conclusionCounts[cat] || 0) + 1;
  }
}
const afConclusions = Object.entries(conclusionCounts)
  .sort((a, b) => b[1] - a[1])
  .map(([category, count]) => ({ category, count }));
const afConclusionsTotal = afConclusions.reduce((s, x) => s + x.count, 0);

// Cases by month (Jan–Dec)
const monthNames = ['January','February','March','April','May','June','July','August','September','October','November','December'];
const monthCounts = {};
for (const c of cases) {
  if (c.month && /^\d{2}$/.test(c.month)) {
    const idx = parseInt(c.month, 10) - 1;
    if (idx >= 0 && idx < 12) monthCounts[idx] = (monthCounts[idx] || 0) + 1;
  }
}
const casesByMonth = monthNames.map((month, i) => ({ month, count: monthCounts[i] || 0 }));

// Top mass sightings (100+ witnesses)
const massSightings = cases
  .filter(c => c.witnesses && c.witnesses >= 100)
  .sort((a, b) => b.witnesses - a.witnesses)
  .slice(0, 10)
  .map(c => ({ witnesses: c.witnesses, date: c.date, location: c.location, id: c.id }));

// Photo cases
const withPhotos = cases.filter(c => c.contains_photographs).length;

const stats = {
  total: cases.length,
  yearRange: { min: Math.min(...Object.keys(casesByYear).map(Number)), max: Math.max(...Object.keys(casesByYear).map(Number)) },
  casesByYear: Object.entries(casesByYear).sort((a, b) => Number(a[0]) - Number(b[0])).map(([year, count]) => ({ year: Number(year), count })),
  topStates,
  distinctCountries,
  witnessGroups: Object.entries(witnessGroups).map(([range, count]) => ({ range, count })),
  afConclusions,
  afConclusionsTotal,
  casesByMonth,
  massSightings,
  withPhotos,
  withoutPhotos: cases.length - withPhotos,
};

fs.writeFileSync(path.join(SRC_DATA_DIR, 'stats.json'), JSON.stringify(stats));
console.log('  → stats.json written');

console.log('\n✅ Data preparation complete!');
console.log(`   ${cases.length} cases ready for Astro build`);
