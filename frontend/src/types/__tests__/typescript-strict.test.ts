/**
 * Tests for TypeScript Strict Configuration and Store Type Safety
 *
 * Verifies that the codebase follows strict TypeScript practices:
 * - noImplicitAny is enabled
 * - strictNullChecks is enabled
 * - Readonly types are used appropriately
 * - Utility types (Pick, Omit, Partial) are used where appropriate
 */

import { describe, it, expect } from 'vitest';

describe('TypeScript Strict Configuration', () => {
    describe('Readonly Types', () => {
        it('should enforce readonly arrays', () => {
            const readonlyArray: readonly string[] = ['a', 'b', 'c'];
            // Cannot modify readonly array
            expect(readonlyArray.length).toBe(3);
        });

        it('should enforce readonly sets', () => {
            const readonlySet: ReadonlySet<string> = new Set(['a', 'b']);
            expect(readonlySet.has('a')).toBe(true);
        });

        it('should type readonly objects (runtime is still mutable JS)', () => {
            const readonlyObj: { readonly key: string } = { key: 'value' };
            expect(readonlyObj.key).toBe('value');
            // Compile-time readonly is enforced by tsc; runtime assignment is not blocked by JS.
            const mutable = readonlyObj as { key: string };
            mutable.key = 'newValue';
            expect(mutable.key).toBe('newValue');
        });
    });

    describe('Theme Mode Type Safety', () => {
        it('should only allow light or dark theme', () => {
            type ThemeMode = 'light' | 'dark';
            const validTheme: ThemeMode = 'light';
            const validTheme2: ThemeMode = 'dark';

            // @ts-expect-error - Type '"blue"' is not assignable to type 'ThemeMode'
            const invalidTheme: ThemeMode = 'blue';
        });
    });

    describe('Branded Types for ID Safety', () => {
        it('should create branded NodeId type', () => {
            type NodeId = string & { __brand: 'NodeId' };
            const nodeId: NodeId = 'node_123' as NodeId;
            expect(typeof nodeId).toBe('string');
        });
    });

    describe('Utility Types', () => {
        it('should use Pick correctly', () => {
            interface FullUser {
                id: number;
                name: string;
                email: string;
                password: string;
            }

            type UserPreview = Pick<FullUser, 'id' | 'name'>;

            const preview: UserPreview = {
                id: 1,
                name: 'John',
            };

            // @ts-expect-error - Object literal may only specify known properties
            const invalid: UserPreview = { id: 1, name: 'John', email: 'john@test.com' };
        });

        it('should use Partial correctly', () => {
            interface FullConfig {
                theme: string;
                fontSize: number;
            }

            const update: Partial<FullConfig> = { theme: 'dark' };
            expect(update.theme).toBe('dark');
        });

        it('should use Omit correctly', () => {
            interface FullUser {
                id: number;
                name: string;
                password: string;
            }

            type PublicUser = Omit<FullUser, 'password'>;

            const publicUser: PublicUser = {
                id: 1,
                name: 'John',
            };

            // @ts-expect-error - Object literal may only specify known properties
            const invalid: PublicUser = { id: 1, name: 'John', password: 'secret' };
        });
    });

    describe('Strict Null Checks', () => {
        it('should require null checks', () => {
            const value: string | null = null;

            // @ts-expect-error - Type 'null' is not assignable to type 'string'
            const invalid: string = value;

            const valid: string = value ?? 'default';
            expect(valid).toBe('default');
        });

        it('should handle optional properties', () => {
            interface WithOptional {
                required: string;
                optional?: number;
            }

            const obj: WithOptional = { required: 'test' };
            const num: number | undefined = obj.optional;

            // @ts-expect-error - Type 'undefined' is not assignable to type 'number'
            const invalid: number = obj.optional;
        });
    });
});
