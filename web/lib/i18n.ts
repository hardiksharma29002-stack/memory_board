import enStrings from '../locales/en.json';
import hiLatnStrings from '../locales/hi-Latn.json';

export type Locale = 'en' | 'hi-Latn';

const LOCALES: Record<Locale, Record<string, unknown>> = {
  en: enStrings as Record<string, unknown>,
  'hi-Latn': hiLatnStrings as Record<string, unknown>,
};

export function getTranslation(
  key: string,
  locale: Locale = 'en',
  params: Record<string, string | number> = {}
): string {
  const parts = key.split('.');
  let current: unknown = LOCALES[locale] || LOCALES.en;

  for (const part of parts) {
    if (current && typeof current === 'object' && part in (current as Record<string, unknown>)) {
      current = (current as Record<string, unknown>)[part];
    } else {
      // Fallback to English
      current = LOCALES.en;
      for (const p of parts) {
        if (current && typeof current === 'object' && p in (current as Record<string, unknown>)) {
          current = (current as Record<string, unknown>)[p];
        } else {
          return key;
        }
      }
      break;
    }
  }

  let text = typeof current === 'string' ? current : key;
  for (const [paramKey, paramVal] of Object.entries(params)) {
    text = text.replace(new RegExp(`\\{${paramKey}\\}`, 'g'), String(paramVal));
  }

  return text;
}
