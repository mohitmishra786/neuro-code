/**
 * Error Types Tests
 */

import { describe, it, expect } from 'vitest';
import {
    NeuroCodeError,
    ApiValidationError,
    ParseError,
    GraphError,
    CacheError,
    WebSocketError,
    ErrorCodes,
    handleError,
    isNeuroCodeError,
} from '../errors';

describe('NeuroCodeError', () => {
    it('should create error with code and context', () => {
        const error = new NeuroCodeError('Test error', ErrorCodes.UNKNOWN, { key: 'value' });
        expect(error.message).toBe('Test error');
        expect(error.code).toBe('UNKNOWN');
        expect(error.context).toEqual({ key: 'value' });
        expect(error.name).toBe('NeuroCodeError');
    });
});

describe('ApiValidationError', () => {
    it('should create validation error', () => {
        const error = new ApiValidationError('Invalid field', 'email', 'bad-email');
        expect(error.message).toBe('Invalid field');
        expect(error.code).toBe('API_VALIDATION_ERROR');
        expect(error.field).toBe('email');
        expect(error.receivedValue).toBe('bad-email');
        expect(error.name).toBe('ApiValidationError');
    });
});

describe('ParseError', () => {
    it('should create parse error', () => {
        const error = new ParseError('Parse failed', '/path/to/file.ts', 42);
        expect(error.message).toBe('Parse failed');
        expect(error.code).toBe('PARSE_ERROR');
        expect(error.filePath).toBe('/path/to/file.ts');
        expect(error.lineNumber).toBe(42);
    });
});

describe('GraphError', () => {
    it('should create graph error', () => {
        const error = new GraphError('Node not found', 'node-123', 'lookup');
        expect(error.message).toBe('Node not found');
        expect(error.code).toBe('GRAPH_ERROR');
        expect(error.nodeId).toBe('node-123');
        expect(error.operation).toBe('lookup');
    });
});

describe('CacheError', () => {
    it('should create cache error', () => {
        const error = new CacheError('Cache miss', 'node-cache-key');
        expect(error.message).toBe('Cache miss');
        expect(error.code).toBe('CACHE_ERROR');
        expect(error.cacheKey).toBe('node-cache-key');
    });
});

describe('WebSocketError', () => {
    it('should create websocket error', () => {
        const error = new WebSocketError('Connection failed', 'ws://localhost', 3);
        expect(error.message).toBe('Connection failed');
        expect(error.code).toBe('WEBSOCKET_ERROR');
        expect(error.url).toBe('ws://localhost');
        expect(error.readyState).toBe(3);
    });
});

describe('ErrorCodes', () => {
    it('should have all expected error codes', () => {
        expect(ErrorCodes.UNKNOWN).toBe('UNKNOWN');
        expect(ErrorCodes.API_VALIDATION_ERROR).toBe('API_VALIDATION_ERROR');
        expect(ErrorCodes.PARSE_ERROR).toBe('PARSE_ERROR');
        expect(ErrorCodes.GRAPH_ERROR).toBe('GRAPH_ERROR');
        expect(ErrorCodes.CACHE_ERROR).toBe('CACHE_ERROR');
        expect(ErrorCodes.WEBSOCKET_ERROR).toBe('WEBSOCKET_ERROR');
        expect(ErrorCodes.NETWORK_ERROR).toBe('NETWORK_ERROR');
        expect(ErrorCodes.TIMEOUT_ERROR).toBe('TIMEOUT_ERROR');
        expect(ErrorCodes.PERMISSION_DENIED).toBe('PERMISSION_DENIED');
        expect(ErrorCodes.NOT_FOUND).toBe('NOT_FOUND');
        expect(ErrorCodes.CONFLICT).toBe('CONFLICT');
    });
});

describe('handleError', () => {
    it('should return NeuroCodeError as-is', () => {
        const originalError = new NeuroCodeError('Test', ErrorCodes.UNKNOWN);
        const result = handleError(originalError);
        expect(result).toBe(originalError);
    });

    it('should convert Error to NeuroCodeError', () => {
        const originalError = new Error('Original error');
        const result = handleError(originalError);
        expect(result).toBeInstanceOf(NeuroCodeError);
        expect(result.message).toBe('Original error');
        expect((result as NeuroCodeError).code).toBe(ErrorCodes.UNKNOWN);
    });

    it('should convert unknown values to NeuroCodeError', () => {
        expect(handleError('string error')).toBeInstanceOf(NeuroCodeError);
        expect(handleError(123 as unknown)).toBeInstanceOf(NeuroCodeError);
        expect(handleError(null)).toBeInstanceOf(NeuroCodeError);
        expect(handleError(undefined)).toBeInstanceOf(NeuroCodeError);
    });
});

describe('isNeuroCodeError', () => {
    it('should return true for NeuroCodeError', () => {
        const error = new NeuroCodeError('Test', ErrorCodes.UNKNOWN);
        expect(isNeuroCodeError(error)).toBe(true);
    });

    it('should return true for subclasses', () => {
        expect(isNeuroCodeError(new ApiValidationError('Test', 'field'))).toBe(true);
        expect(isNeuroCodeError(new ParseError('Test', 'path'))).toBe(true);
        expect(isNeuroCodeError(new GraphError('Test'))).toBe(true);
    });

    it('should return false for regular Error', () => {
        expect(isNeuroCodeError(new Error('Regular error'))).toBe(false);
    });

    it('should return false for non-Error values', () => {
        expect(isNeuroCodeError('string')).toBe(false);
        expect(isNeuroCodeError(123)).toBe(false);
        expect(isNeuroCodeError(null)).toBe(false);
        expect(isNeuroCodeError(undefined)).toBe(false);
        expect(isNeuroCodeError({})).toBe(false);
    });
});
