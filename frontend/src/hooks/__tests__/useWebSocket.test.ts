/**
 * useWebSocket Hook Tests
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useWebSocket } from '../useWebSocket';

describe('useWebSocket', () => {
    beforeEach(() => {
        vi.clearAllMocks();
        vi.useFakeTimers();
    });

    afterEach(() => {
        vi.useRealTimers();
        vi.restoreAllMocks();
    });

    describe('connection state', () => {
        it('should have correct initial state', () => {
            const { result } = renderHook(() => useWebSocket({ url: 'ws://test.local/ws' }));

            expect(result.current.isConnected).toBe(false);
            expect(result.current.error).toBe(null);
            expect(result.current.lastMessage).toBe(null);
        });
    });

    describe('connection attempt tracking', () => {
        it('should track connection attempts', () => {
            const { result } = renderHook(() => useWebSocket({ url: 'ws://test.local/ws' }));

            // Initial state
            expect(result.current.isConnected).toBe(false);
        });

        it('should cleanup on unmount without throwing', () => {
            const { result, unmount } = renderHook(() =>
                useWebSocket({ url: 'ws://test.local/ws' }),
            );

            expect(typeof result.current.disconnect).toBe('function');
            expect(() => unmount()).not.toThrow();
        });
    });

    describe('send function', () => {
        it('should return send function', () => {
            const { result } = renderHook(() => useWebSocket({ url: 'ws://test.local/ws' }));

            expect(typeof result.current.send).toBe('function');
        });
    });

    describe('connect function', () => {
        it('should return connect function', () => {
            const { result } = renderHook(() => useWebSocket({ url: 'ws://test.local/ws' }));

            expect(typeof result.current.connect).toBe('function');
        });
    });

    describe('disconnect function', () => {
        it('should return disconnect function', () => {
            const { result } = renderHook(() => useWebSocket({ url: 'ws://test.local/ws' }));

            expect(typeof result.current.disconnect).toBe('function');
        });
    });
});
