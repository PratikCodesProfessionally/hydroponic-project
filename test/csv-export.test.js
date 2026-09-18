const test = require('node:test');
const assert = require('node:assert/strict');
const { formatCsvValue, sanitizeNumericValue } = require('../server/csv-utils');

test('formatCsvValue rejects implausible scientific-notation values', () => {
    assert.equal(formatCsvValue(8.45e15), '');
    assert.equal(formatCsvValue(8.45e-15), '');
    assert.equal(formatCsvValue(7.8), '7.8');
    assert.equal(formatCsvValue('7.8'), '7.8');
    assert.equal(formatCsvValue(null), '');
    assert.equal(formatCsvValue(undefined), '');
});

test('formatCsvValue keeps timestamps, booleans and zero', () => {
    assert.equal(formatCsvValue('2026-08-06 21:18:04'), '2026-08-06 21:18:04');
    assert.equal(formatCsvValue(false), 'false');
    assert.equal(formatCsvValue(true), 'true');
    assert.equal(formatCsvValue(0), '0');
});

test('sanitizeNumericValue applies plausibility limits but keeps zero', () => {
    assert.equal(sanitizeNumericValue(0, { min: 0, max: 100000 }), 0);
    assert.equal(sanitizeNumericValue(5.8, { min: 0, max: 14 }), 5.8);
    assert.equal(sanitizeNumericValue(15, { min: 0, max: 14 }), null);
    assert.equal(sanitizeNumericValue('1.5234', { min: 0, max: 5 }), 1.5234);
    assert.equal(sanitizeNumericValue(1523.4, { min: 0, max: 5 }), null);
    assert.equal(sanitizeNumericValue('', { min: 0, max: 14 }), null);
});

test('export row matches the Pi log column format', () => {
    const punkt = {
        timestamp: '2026-09-18 10:00:00', ph: 5.83, phVoltage: 1.5234,
        waterTemp: 24.19, airTemp: null, airHumidity: null, pumpActive: false
    };
    const zeile = [punkt.timestamp, punkt.ph, punkt.phVoltage, punkt.waterTemp,
        punkt.airTemp, punkt.airHumidity, punkt.pumpActive]
        .map(formatCsvValue).join(',');
    assert.equal(zeile, '2026-09-18 10:00:00,5.83,1.5234,24.19,,,false');
});
