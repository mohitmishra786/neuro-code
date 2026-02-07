/**
 * Graph Types Validation Tests
 */

import { describe, it, expect } from 'vitest';
import {
    isValidNodeType,
    isValidRelationshipType,
    isValidApiNode,
    isValidSearchResponse,
    isValidRootNodesResponse,
    isValidChildrenResponse,
    isValidAncestorsResponse,
    isValidSearchResult,
    parseApiNode,
    parseSearchResponse,
    parseRootNodesResponse,
} from '../graph.types';
import { ApiNode, SearchResponse, RootNodesResponse } from '../graph.types';

describe('isValidNodeType', () => {
    it('should return true for valid node types', () => {
        expect(isValidNodeType('package')).toBe(true);
        expect(isValidNodeType('module')).toBe(true);
        expect(isValidNodeType('class')).toBe(true);
        expect(isValidNodeType('function')).toBe(true);
        expect(isValidNodeType('variable')).toBe(true);
        expect(isValidNodeType('unknown')).toBe(true);
    });

    it('should return false for invalid node types', () => {
        expect(isValidNodeType('invalid')).toBe(false);
        expect(isValidNodeType('')).toBe(false);
        expect(isValidNodeType('PACKAGE')).toBe(false);
        expect(isValidNodeType(123 as unknown)).toBe(false);
        expect(isValidNodeType(null)).toBe(false);
        expect(isValidNodeType(undefined)).toBe(false);
        expect(isValidNodeType({}) as unknown).toBe(false);
        expect(isValidNodeType([]) as unknown).toBe(false);
    });
});

describe('isValidRelationshipType', () => {
    it('should return true for valid relationship types', () => {
        expect(isValidRelationshipType('CONTAINS')).toBe(true);
        expect(isValidRelationshipType('IMPORTS')).toBe(true);
        expect(isValidRelationshipType('CALLS')).toBe(true);
        expect(isValidRelationshipType('INSTANTIATES')).toBe(true);
        expect(isValidRelationshipType('INHERITS')).toBe(true);
        expect(isValidRelationshipType('DECORATES')).toBe(true);
        expect(isValidRelationshipType('DEFINES')).toBe(true);
        expect(isValidRelationshipType('USES')).toBe(true);
    });

    it('should return false for invalid relationship types', () => {
        expect(isValidRelationshipType('contains')).toBe(false);
        expect(isValidRelationshipType('invalid')).toBe(false);
        expect(isValidRelationshipType('')).toBe(false);
        expect(isValidRelationshipType(123 as unknown)).toBe(false);
    });
});

describe('isValidApiNode', () => {
    it('should return true for valid ApiNode', () => {
        const validNode: unknown = {
            id: 'test-id',
            name: 'TestNode',
            type: 'class',
            qualified_name: 'pkg.TestNode',
            line_number: 42,
            docstring: 'A test node',
            child_count: 5,
            is_async: true,
            is_method: false,
            is_abstract: true,
            complexity: 10,
            return_type: 'string',
            type_hint: 'str',
        };
        expect(isValidApiNode(validNode)).toBe(true);
    });

    it('should return true for minimal valid ApiNode', () => {
        const minimalNode: unknown = {
            id: 'test-id',
            name: 'TestNode',
            type: 'function',
            child_count: 0,
        };
        expect(isValidApiNode(minimalNode)).toBe(true);
    });

    it('should return false for invalid ApiNode', () => {
        expect(isValidApiNode(null)).toBe(false);
        expect(isValidApiNode(undefined)).toBe(false);
        expect(isValidApiNode('string' as unknown)).toBe(false);
        expect(isValidApiNode(123 as unknown)).toBe(false);
        expect(isValidApiNode({})).toBe(false);
        expect(isValidApiNode({ id: 123 })).toBe(false);
        expect(isValidApiNode({ id: 'test', name: 123 })).toBe(false);
        expect(isValidApiNode({ id: 'test', name: 'test', type: 'invalid' })).toBe(false);
        expect(isValidApiNode({ id: 'test', name: 'test', type: 'class', child_count: 'five' })).toBe(false);
    });
});

describe('isValidSearchResult', () => {
    it('should return true for valid SearchResult', () => {
        const validResult: unknown = {
            id: 'test-id',
            name: 'TestSearch',
            type: 'function',
            qualified_name: 'pkg.TestSearch',
            line_number: 10,
            docstring: 'Search result',
            score: 0.95,
        };
        expect(isValidSearchResult(validResult)).toBe(true);
    });

    it('should return false for invalid SearchResult', () => {
        expect(isValidSearchResult(null)).toBe(false);
        expect(isValidSearchResult({ id: 'test', name: 'test', type: 'invalid' })).toBe(false);
        expect(isValidSearchResult({ id: 'test', name: 'test', type: 'class', score: 'high' })).toBe(false);
    });
});

describe('isValidSearchResponse', () => {
    it('should return true for valid SearchResponse', () => {
        const validResponse: unknown = {
            query: 'test',
            results: [
                { id: 'r1', name: 'Result1', type: 'class', score: 0.9 },
                { id: 'r2', name: 'Result2', type: 'function', score: 0.8 },
            ],
            total: 2,
        };
        expect(isValidSearchResponse(validResponse)).toBe(true);
    });

    it('should return false for invalid SearchResponse', () => {
        expect(isValidSearchResponse(null)).toBe(false);
        expect(isValidSearchResponse({ query: 'test', results: [], total: 0 })).toBe(true);
        expect(isValidSearchResponse({ query: 123, results: [], total: 0 })).toBe(false);
        expect(isValidSearchResponse({ query: 'test', results: [{ id: 1 }], total: 1 })).toBe(false);
    });
});

describe('isValidRootNodesResponse', () => {
    it('should return true for valid RootNodesResponse', () => {
        const validResponse: unknown = {
            nodes: [
                { id: 'n1', name: 'Node1', type: 'package', child_count: 5 },
                { id: 'n2', name: 'Node2', type: 'module', child_count: 10 },
            ],
            total: 2,
        };
        expect(isValidRootNodesResponse(validResponse)).toBe(true);
    });

    it('should return false for invalid RootNodesResponse', () => {
        expect(isValidRootNodesResponse(null)).toBe(false);
        expect(isValidRootNodesResponse({ nodes: [], total: 0 })).toBe(true);
        expect(isValidRootNodesResponse({ nodes: 'invalid', total: 0 })).toBe(false);
        expect(isValidRootNodesResponse({ nodes: [], total: 'zero' })).toBe(false);
    });
});

describe('isValidChildrenResponse', () => {
    it('should return true for valid ChildrenResponse', () => {
        const validResponse: unknown = {
            parent_id: 'parent-1',
            children: [
                { id: 'c1', name: 'Child1', type: 'class', child_count: 2 },
            ],
            total: 1,
        };
        expect(isValidChildrenResponse(validResponse)).toBe(true);
    });

    it('should return false for invalid ChildrenResponse', () => {
        expect(isValidChildrenResponse(null)).toBe(false);
        expect(isValidChildrenResponse({ parent_id: 'p1', children: [], total: 0 })).toBe(true);
        expect(isValidChildrenResponse({ parent_id: 123, children: [], total: 0 })).toBe(false);
    });
});

describe('isValidAncestorsResponse', () => {
    it('should return true for valid AncestorsResponse', () => {
        const validResponse: unknown = {
            node_id: 'node-1',
            ancestors: [
                { id: 'a1', name: 'Ancestor1', type: 'package', child_count: 5 },
            ],
        };
        expect(isValidAncestorsResponse(validResponse)).toBe(true);
    });

    it('should return false for invalid AncestorsResponse', () => {
        expect(isValidAncestorsResponse(null)).toBe(false);
        expect(isValidAncestorsResponse({ node_id: 'n1', ancestors: [] })).toBe(true);
        expect(isValidAncestorsResponse({ node_id: 123, ancestors: [] })).toBe(false);
    });
});

describe('parseApiNode', () => {
    it('should return parsed node for valid input', () => {
        const validNode = {
            id: 'test',
            name: 'Test',
            type: 'class' as const,
            child_count: 5,
        };
        const result = parseApiNode(validNode);
        expect(result).not.toBeNull();
        expect(result?.id).toBe('test');
    });

    it('should return null for invalid input', () => {
        expect(parseApiNode(null)).toBeNull();
        expect(parseApiNode({})).toBeNull();
        expect(parseApiNode({ id: 123 })).toBeNull();
    });
});

describe('parseSearchResponse', () => {
    it('should return parsed response for valid input', () => {
        const validResponse = {
            query: 'test',
            results: [{ id: 'r1', name: 'Result', type: 'class' as const, score: 0.9 }],
            total: 1,
        };
        const result = parseSearchResponse(validResponse);
        expect(result).not.toBeNull();
        expect(result?.query).toBe('test');
    });

    it('should return null for invalid input', () => {
        expect(parseSearchResponse(null)).toBeNull();
        expect(parseSearchResponse({ query: 123 })).toBeNull();
    });
});

describe('parseRootNodesResponse', () => {
    it('should return parsed response for valid input', () => {
        const validResponse = {
            nodes: [{ id: 'n1', name: 'Node', type: 'module' as const, child_count: 0 }],
            total: 1,
        };
        const result = parseRootNodesResponse(validResponse);
        expect(result).not.toBeNull();
        expect(result?.total).toBe(1);
    });

    it('should return null for invalid input', () => {
        expect(parseRootNodesResponse(null)).toBeNull();
        expect(parseRootNodesResponse({ nodes: 'invalid' })).toBeNull();
    });
});
