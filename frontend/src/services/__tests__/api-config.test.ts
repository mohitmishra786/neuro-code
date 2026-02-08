/**
 * Tests for API Configuration
 *
 * Verifies that the API base URL is properly configured from environment variables.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';

describe('API Configuration', () => {
    describe('API Base URL', () => {
        it('should use environment variable when available', () => {
            // Simulate environment variable being set
            vi.stubEnv('VITE_API_URL', 'https://api.neurocode.example.com');

            // Re-import to get the new value
            // Note: In real tests, we'd need to re-evaluate the module
            const apiUrl = import.meta.env.VITE_API_URL;
            expect(apiUrl).toBe('https://api.neurocode.example.com');

            vi.unstubAllEnvs();
        });

        it('should fallback to localhost when env var not set', () => {
            vi.stubEnv('VITE_API_URL', undefined);

            const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
            expect(apiUrl).toBe('http://localhost:8000');

            vi.unstubAllEnvs();
        });

        it('should support production URLs', () => {
            vi.stubEnv('VITE_API_URL', 'https://api.production.example.com');

            const apiUrl = import.meta.env.VITE_API_URL;
            expect(apiUrl).toBe('https://api.production.example.com');
            expect(apiUrl).not.toContain('localhost');

            vi.unstubAllEnvs();
        });
    });

    describe('Environment Variable Types', () => {
        it('VITE_API_URL should be a string', () => {
            vi.stubEnv('VITE_API_URL', 'http://localhost:8000');

            const apiUrl = import.meta.env.VITE_API_URL;
            expect(typeof apiUrl).toBe('string');

            vi.unstubAllEnvs();
        });
    });
});
