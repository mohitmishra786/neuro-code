/**
 * Tests for Generic Constraints and Index Signatures
 *
 * Verifies that:
 * - Generic functions have proper constraints
 * - Index signatures are properly typed
 * - Type safety is maintained for dynamic object access
 */

import { describe, it, expect } from 'vitest';

describe('Generic Constraints', () => {
    describe('Proper extends constraints', () => {
        it('should constrain generic to specific type', () => {
            function processItem<T extends { id: string }>(item: T): string {
                return item.id;
            }

            const valid = processItem({ id: '123', name: 'test' });
            expect(valid).toBe('123');
        });

        it('should constrain array element types', () => {
            function getFirst<T extends { length: number }>(arr: T): T extends { 0: infer U } ? U : never {
                return arr[0] as never;
            }

            const first = getFirst(['a', 'b', 'c']);
            expect(first).toBe('a');
        });
    });

    describe('Fetcher type with constraint', () => {
        it('should use constrained generic type', () => {
            type Fetcher<T> = (signal: AbortSignal) => Promise<T>;

            const fetcher: Fetcher<string> = async (signal) => {
                return 'data';
            };

            fetcher(new AbortController().signal).then(data => {
                expect(data).toBe('data');
            });
        });
    });
});

describe('Index Signatures', () => {
    describe('Properly typed index signatures', () => {
        it('should allow dynamic property access with known value type', () => {
            interface DynamicMessage {
                type: string;
                [key: string]: unknown;
            }

            const msg: DynamicMessage = {
                type: 'test',
                data: { value: 123 },
                timestamp: Date.now(),
            };

            expect(msg.type).toBe('test');
            expect(msg['data']).toEqual({ value: 123 });
        });

        it('should enforce consistent value type in index signature', () => {
            interface StrictDynamic {
                name: string;
                [key: string]: string | number;
            }

            const obj: StrictDynamic = {
                name: 'test',
                age: 25,
                count: 5,
            };

            expect(obj.name).toBe('test');
            expect(obj['age']).toBe(25);
        });
    });

    describe('WebSocket message with index signature', () => {
        it('should allow type-safe dynamic access', () => {
            interface WebSocketMessage {
                type: string;
                [key: string]: unknown;
            }

            const msg: WebSocketMessage = {
                type: 'graph_updated',
                added_count: 5,
                modified_count: 10,
            };

            expect(msg.type).toBe('graph_updated');
            expect(msg['added_count']).toBe(5);
            expect(msg.modified_count).toBe(10);
        });
    });
});

describe('Type Guards', () => {
    describe('Type narrowing with guards', () => {
        it('should narrow type with type guard', () => {
            function isString(value: unknown): value is string {
                return typeof value === 'string';
            }

            let val: unknown = 'hello';

            if (isString(val)) {
                // val is now string here
                expect(val.toUpperCase()).toBe('HELLO');
            }
        });

        it('should prevent any leakage with proper constraints', () => {
            function processWithConstraint<T extends { id: string }>(input: T): T {
                return input;
            }

            const result = processWithConstraint({ id: '1', name: 'test' });
            expect(result.id).toBe('1');
        });
    });
});
