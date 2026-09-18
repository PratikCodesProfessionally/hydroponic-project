/**
 * Hilfsfunktionen fuer Messwerte und CSV-Export.
 *
 * sanitizeNumericValue: Zahl aus dem Pi-Payload pruefen. Unplausible Werte
 * (Exponentialdarstellung wie 8.45e15, ausserhalb des erwarteten Bereichs)
 * werden zu null, damit das Dashboard "--" zeigt statt eines Fantasiewerts.
 * Null ist ein gueltiger Messwert (z. B. 0 Dosierungen) und bleibt erhalten.
 *
 * formatCsvValue: Zelle fuer den CSV-Export. Zahlen werden geprueft,
 * Zeitstempel und Wahrheitswerte unveraendert uebernommen.
 */

function parseNumericValue(value) {
    if (value === null || value === undefined || value === '') {
        return null;
    }

    if (typeof value === 'string') {
        const trimmed = value.trim();
        if (!trimmed) {
            return null;
        }
        value = trimmed;
    }

    const parsed = typeof value === 'number' ? value : Number(value);
    if (!Number.isFinite(parsed)) {
        return null;
    }

    return parsed;
}

function sanitizeNumericValue(value, {
    min = Number.MIN_SAFE_INTEGER,
    max = Number.MAX_SAFE_INTEGER,
    absMax = 1e12,
    absMin = 1e-6
} = {}) {
    const parsed = parseNumericValue(value);
    if (parsed === null) {
        return null;
    }

    if (Math.abs(parsed) > absMax) {
        return null;
    }

    // Exakt 0 ist ein echter Wert; nur winzige Restwerte aus
    // Exponentialdarstellung (8.45e-15) sind unplausibel.
    if (parsed !== 0 && Math.abs(parsed) < absMin) {
        return null;
    }

    if (parsed < min || parsed > max) {
        return null;
    }

    return parsed;
}

function formatCsvValue(value, options = {}) {
    if (value === null || value === undefined) {
        return '';
    }
    if (typeof value === 'boolean') {
        return value ? 'true' : 'false';
    }
    if (typeof value === 'string' && !Number.isFinite(Number(value.trim()))) {
        // Zeitstempel und andere Texte unveraendert durchreichen.
        return value;
    }
    const parsed = sanitizeNumericValue(value, options);
    return parsed === null ? '' : String(parsed);
}

module.exports = { formatCsvValue, sanitizeNumericValue };
