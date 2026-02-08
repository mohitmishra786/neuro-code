/**
 * NeuroCode Graph Types
 *
 * Type definitions for the code visualization graph.
 *
 * Naming Convention:
 * - API Response types (ApiNode, SearchResponse, etc.) use snake_case to match
 *   the backend API responses (qualified_name, line_number, child_count, etc.)
 * - Internal types (GraphNode, TreeNode, etc.) use camelCase for consistency
 *   with frontend conventions (qualifiedName, lineNumber, childCount, etc.)
 * - Transformation functions (apiNodeToGraphNode) handle the conversion.
 */

// Branded types for ID type safety
// Using opaque types prevents accidentally passing a FileId where a NodeId is expected
type Brand<T, B> = T & { __brand: B };

export type NodeId = Brand<string, 'NodeId'>;
export type EdgeId = Brand<string, 'EdgeId'>;
export type FileId = Brand<string, 'FileId'>;

/**
 * Type guard to check if a string is a valid NodeId
 */
export function isNodeId(value: unknown): value is NodeId {
    return typeof value === 'string' && value.length > 0;
}

/**
 * Type guard to check if a string is a valid EdgeId
 */
export function isEdgeId(value: unknown): value is EdgeId {
    return typeof value === 'string' && value.length > 0 && value.includes('->');
}

/**
 * Type guard to check if a string is a valid FileId
 */
export function isFileId(value: unknown): value is FileId {
    return typeof value === 'string' && value.length > 0;
}

/**
 * Create a NodeId from a string
 */
export function createNodeId(id: string): NodeId {
    return id as NodeId;
}

/**
 * Create an EdgeId from source and target node IDs
 */
export function createEdgeId(sourceId: NodeId, targetId: NodeId): EdgeId {
    return `${sourceId}->${targetId}` as EdgeId;
}

/**
 * Create a FileId from a string path
 */
export function createFileId(path: string): FileId {
    return path as FileId;
}

export type NodeType = 'package' | 'module' | 'class' | 'function' | 'variable' | 'unknown';

const NODE_TYPE_VALUES = ['package', 'module', 'class', 'function', 'variable', 'unknown'] as const;

export function isValidNodeType(value: unknown): value is NodeType {
    return typeof value === 'string' && NODE_TYPE_VALUES.includes(value as NodeType);
}

export type ValidNodeType = typeof NODE_TYPE_VALUES[number];

export type RelationshipType =
    | 'CONTAINS'
    | 'IMPORTS'
    | 'CALLS'
    | 'INSTANTIATES'
    | 'INHERITS'
    | 'DECORATES'
    | 'DEFINES'
    | 'USES';

export const RELATIONSHIP_TYPE_VALUES = [
    'CONTAINS',
    'IMPORTS',
    'CALLS',
    'INSTANTIATES',
    'INHERITS',
    'DECORATES',
    'DEFINES',
    'USES',
] as const satisfies ReadonlyArray<RelationshipType>;

export interface GraphNode {
    id: string;
    name: string;
    type: NodeType;
    qualifiedName?: string;
    lineNumber?: number;
    docstring?: string;
    childCount: number;
    isExpanded: boolean;
    isAsync?: boolean;
    isMethod?: boolean;
    isAbstract?: boolean;
    complexity?: number;
    returnType?: string;
    typeHint?: string;
    // Visual properties
    x?: number;
    y?: number;
    size?: number;
    color?: string;
    label?: string;
}

export interface GraphEdge {
    id: string;
    source: string;
    target: string;
    type: RelationshipType;
    weight?: number;
    callCount?: number;
}

export function isValidRelationshipType(value: unknown): value is RelationshipType {
    return (
        typeof value === 'string' &&
        RELATIONSHIP_TYPE_VALUES.includes(value as RelationshipType)
    );
}

export type EdgeType = 'contains' | 'calls' | 'imports' | 'inherits';

export const EDGE_TYPE_VALUES = ['contains', 'calls', 'imports', 'inherits'] as const satisfies ReadonlyArray<EdgeType>;

export type NodeType = typeof NODE_TYPE_VALUES[number];

export const NODE_TYPE_CIRCLE = 'circleNode' as const;

export function isValidEdgeType(value: unknown): value is EdgeType {
    return typeof value === 'string' && EDGE_TYPE_VALUES.includes(value as EdgeType);
}

export interface Viewport {
    x: number;
    y: number;
    zoom: number;
    width: number;
    height: number;
}

export interface SearchResult {
    id: string;
    name: string;
    type: NodeType;
    qualifiedName?: string;
    lineNumber?: number;
    docstring?: string;
    score: number;
}

export interface BreadcrumbItem {
    id: string;
    name: string;
    type: NodeType;
}

export interface ReferenceNode {
    id: string;
    name: string;
    type: NodeType;
    qualifiedName?: string;
    relationshipType: string;
    direction: 'incoming' | 'outgoing';
    lineNumber?: number;
}

// API Response types
export interface RootNodesResponse {
    readonly nodes: readonly ApiNode[];
    readonly total: number;
}

export interface ChildrenResponse {
    readonly parent_id: string;
    readonly children: readonly ApiNode[];
    readonly total: number;
}

export interface AncestorsResponse {
    readonly node_id: string;
    readonly ancestors: readonly ApiNode[];
}

export interface SearchResponse {
    readonly query: string;
    readonly results: readonly SearchResult[];
    readonly total: number;
}

export interface ReferencesResponse {
    readonly node_id: string;
    readonly references: readonly ReferenceNode[];
    readonly total: number;
}

export interface ApiNode {
    readonly id: string;
    readonly name: string;
    readonly type: NodeType;
    readonly qualified_name?: string;
    readonly line_number?: number;
    readonly docstring?: string;
    readonly child_count: number;
    readonly is_async?: boolean;
    readonly is_method?: boolean;
    readonly is_abstract?: boolean;
    readonly complexity?: number;
    readonly return_type?: string;
    readonly type_hint?: string;
}

// WebSocket message types with index signature for dynamic properties
export interface WebSocketMessage {
    /** Message type discriminator */
    type: string;
    /** Dynamic properties for message data */
    [key: string]: unknown;
}

export interface FileChangedMessage extends WebSocketMessage {
    type: 'file_changed';
    path: string;
    change_type: 'created' | 'modified' | 'deleted';
}

export interface GraphUpdatedMessage extends WebSocketMessage {
    type: 'graph_updated';
    added_count: number;
    modified_count: number;
    removed_count: number;
    affected_modules: string[];
}

export interface HeartbeatMessage extends WebSocketMessage {
    type: 'heartbeat';
    timestamp: number;
}

export interface ProjectTreeNode {
    readonly id: string;
    readonly type: NodeType | 'root' | 'package';
    readonly label?: string;
    readonly data?: Readonly<Record<string, unknown>>;
    readonly children?: readonly ProjectTreeNode[];
}

// Validation helper types - REMOVED: StringOrUndefined, NumberOrUndefined, BooleanOrUndefined
// These were unused helper types that added no value

// Validation functions for runtime type checking
export function isValidApiNode(value: unknown): value is ApiNode {
    if (typeof value !== 'object' || value === null) return false;
    const node = value as Record<string, unknown>;
    return (
        typeof node.id === 'string' &&
        typeof node.name === 'string' &&
        isValidNodeType(node.type) &&
        (node.qualified_name === undefined || typeof node.qualified_name === 'string') &&
        (node.line_number === undefined || typeof node.line_number === 'number') &&
        (node.docstring === undefined || typeof node.docstring === 'string') &&
        typeof node.child_count === 'number' &&
        (node.is_async === undefined || typeof node.is_async === 'boolean') &&
        (node.is_method === undefined || typeof node.is_method === 'boolean') &&
        (node.is_abstract === undefined || typeof node.is_abstract === 'boolean') &&
        (node.complexity === undefined || typeof node.complexity === 'number') &&
        (node.return_type === undefined || typeof node.return_type === 'string') &&
        (node.type_hint === undefined || typeof node.type_hint === 'string')
    );
}

export function isValidSearchResult(value: unknown): value is SearchResult {
    if (typeof value !== 'object' || value === null) return false;
    const result = value as Record<string, unknown>;
    return (
        typeof result.id === 'string' &&
        typeof result.name === 'string' &&
        isValidNodeType(result.type) &&
        (result.qualified_name === undefined || typeof result.qualified_name === 'string') &&
        (result.line_number === undefined || typeof result.line_number === 'number') &&
        (result.docstring === undefined || typeof result.docstring === 'string') &&
        typeof result.score === 'number'
    );
}

export function isValidSearchResponse(value: unknown): value is SearchResponse {
    if (typeof value !== 'object' || value === null) return false;
    const response = value as Record<string, unknown>;
    return (
        typeof response.query === 'string' &&
        Array.isArray(response.results) &&
        response.results.every(isValidSearchResult) &&
        typeof response.total === 'number'
    );
}

export function isValidRootNodesResponse(value: unknown): value is RootNodesResponse {
    if (typeof value !== 'object' || value === null) return false;
    const response = value as Record<string, unknown>;
    return (
        Array.isArray(response.nodes) &&
        response.nodes.every(isValidApiNode) &&
        typeof response.total === 'number'
    );
}

export function isValidChildrenResponse(value: unknown): value is ChildrenResponse {
    if (typeof value !== 'object' || value === null) return false;
    const response = value as Record<string, unknown>;
    return (
        typeof response.parent_id === 'string' &&
        Array.isArray(response.children) &&
        response.children.every(isValidApiNode) &&
        typeof response.total === 'number'
    );
}

export function isValidAncestorsResponse(value: unknown): value is AncestorsResponse {
    if (typeof value !== 'object' || value === null) return false;
    const response = value as Record<string, unknown>;
    return (
        typeof response.node_id === 'string' &&
        Array.isArray(response.ancestors) &&
        response.ancestors.every(isValidApiNode)
    );
}

// Safe parsing functions that return null on failure
export function parseApiNode(data: unknown): ApiNode | null {
    return isValidApiNode(data) ? data : null;
}

export function parseSearchResponse(data: unknown): SearchResponse | null {
    return isValidSearchResponse(data) ? data : null;
}

export function parseRootNodesResponse(data: unknown): RootNodesResponse | null {
    return isValidRootNodesResponse(data) ? data : null;
}

export function parseChildrenResponse(data: unknown): ChildrenResponse | null {
    return isValidChildrenResponse(data) ? data : null;
}

export function parseAncestorsResponse(data: unknown): AncestorsResponse | null {
    return isValidAncestorsResponse(data) ? data : null;
}
