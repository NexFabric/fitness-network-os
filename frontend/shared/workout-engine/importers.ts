/**
 * Workout Tracker CSV Parser & Importer Engine
 *
 * Supports importing workout history from popular consumer apps:
 * - Strong App
 * - Hevy
 * - FitNotes (Android & iOS)
 *
 * Attribution / Origin:
 * Adapted and re-engineered from openGym (DuarteSantos8 / TechLionDev) for GymClubNex.
 */

export interface ParsedWorkoutRow {
  date: string;
  exerciseName: string;
  weightKg?: number;
  weightLb?: number;
  reps?: number;
  rpe?: number;
  rir?: number;
  seconds?: number;
  notes?: string;
  category?: string;
}

export type SupportedSourceApp = 'Strong' | 'Hevy' | 'FitNotes' | 'FitNotes (iOS)' | 'Generic CSV';

/**
 * Standard CSV Parser handling quotes, commas, newlines, and BOM.
 */
export function parseCsvRows(text: string): string[][] {
  const rows: string[][] = [];
  let row: string[] = [];
  let field = '';
  let insideQuotes = false;
  const cleanText = text.replace(/^\uFEFF/, ''); // Strip BOM if present

  for (let i = 0; i < cleanText.length; i++) {
    const char = cleanText[i];
    if (insideQuotes) {
      if (char === '"') {
        if (cleanText[i + 1] === '"') {
          field += '"';
          i++;
        } else {
          insideQuotes = false;
        }
      } else {
        field += char;
      }
    } else if (char === '"') {
      insideQuotes = true;
    } else if (char === ',') {
      row.push(field);
      field = '';
    } else if (char === '\n' || char === '\r') {
      if (char === '\r' && cleanText[i + 1] === '\n') {
        i++;
      }
      row.push(field);
      field = '';
      if (row.some((cell) => cell.trim() !== '')) {
        rows.push(row);
      }
      row = [];
    } else {
      field += char;
    }
  }

  row.push(field);
  if (row.some((cell) => cell.trim() !== '')) {
    rows.push(row);
  }

  return rows;
}

const normalizeHeader = (header: string): string =>
  header.toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim();

/**
 * Detect source application from CSV header row.
 */
export function detectSourceApp(headerRow: string[]): SupportedSourceApp {
  const headers = headerRow.map(normalizeHeader);
  if (headers.includes('exercise title') && headers.includes('set index')) return 'Hevy';
  if (headers.includes('exercise name') && headers.includes('set order')) return 'Strong';
  if (headers.includes('exercise') && headers.includes('kind')) return 'FitNotes (iOS)';
  if (headers.includes('exercise') && (headers.includes('weight unit') || headers.includes('category'))) return 'FitNotes';
  return 'Generic CSV';
}
