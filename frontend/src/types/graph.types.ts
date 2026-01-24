/**
 * NeuroCode Graph Types
 *
 * Type definitions for the code visualization graph.
 */

export type NodeType = 'package' | 'module' | 'class' | 'function' | 'variable' | 'unknown';

export type RelationshipType =
    | 'CONTAINS'
    | 'IMPORTS'
    | 'CALLS'
    | 'INSTANTIATES'
    | 'INHERITS'
    | 'DECORATES'
    | 'DEFINES'
    | 'USES';

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
    nodes: ApiNode[];
    total: number;
}

export interface ChildrenResponse {
    parent_id: string;
    children: ApiNode[];
    total: number;
}

export interface AncestorsResponse {
    node_id: string;
    ancestors: ApiNode[];
}

export interface SearchResponse {
    query: string;
    results: SearchResult[];
    total: number;
}

export interface ReferencesResponse {
    node_id: string;
    references: ReferenceNode[];
    total: number;
}

export interface ApiNode {
    id: string;
    name: string;
    type: NodeType;
    qualified_name?: string;
    line_number?: number;
    docstring?: string;
    child_count: number;
    is_async?: boolean;
    is_method?: boolean;
    is_abstract?: boolean;
    complexity?: number;
    return_type?: string;
    type_hint?: string;
}

// WebSocket message types
export interface WebSocketMessage {
    type: string;
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
    id: string;
    type: NodeType | 'root' | 'package';
    label?: string;
    data?: Record<string, unknown>;
    children?: ProjectTreeNode[];
}
