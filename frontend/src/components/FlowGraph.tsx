import { useEffect } from 'react';
import ReactFlow, {
    Background,
    Controls,
    MiniMap,
    NodeTypes,
    Panel
} from 'reactflow';
import 'reactflow/dist/style.css';
import { useGraphStore } from '@/stores/graphStore';
import { useThemeStore } from '@/stores/themeStore';

// Placeholder for custom node (will implement properly later)
const ModuleNode = ({ id, data }: any) => {
    const expandNode = useGraphStore(state => state.expandNode);

    return (
        <div
            onClick={(e) => {
                e.stopPropagation();
                expandNode(id);
            }}
            style={{
                padding: '10px',
                border: '1px solid #777',
                borderRadius: '5px',
                background: '#1a1a1a',
                color: '#fff',
                minWidth: '150px',
                cursor: 'pointer'
            }}>
            <div style={{ borderBottom: '1px solid #555', paddingBottom: '5px', marginBottom: '5px', fontWeight: 'bold' }}>
                {data.label}
            </div>
            <div style={{ fontSize: '10px', color: '#aaa' }}>
                {data.original?.type}
            </div>
        </div>
    );
};

const nodeTypes: NodeTypes = {
    module: ModuleNode,
    package: ModuleNode,
};

export function FlowGraph() {
    const {
        nodes,
        edges,
        onNodesChange,
        onEdgesChange,
        loadProjectTree,
        loading,
        error
    } = useGraphStore();

    const mode = useThemeStore((state) => state.mode);

    useEffect(() => {
        // Load the current project tree (using '.' for current dir relative to backend)
        loadProjectTree('.');
    }, [loadProjectTree]);

    if (loading) return <div style={{ padding: 20 }}>Loading tree...</div>;
    if (error) return <div style={{ padding: 20, color: 'red' }}>Error: {error}</div>;

    return (
        <div style={{ width: '100%', height: '100%' }}>
            <ReactFlow
                nodes={nodes}
                edges={edges}
                onNodesChange={onNodesChange}
                onEdgesChange={onEdgesChange}
                nodeTypes={nodeTypes}
                fitView
                className={mode === 'dark' ? 'dark' : ''}
                style={{ background: mode === 'dark' ? '#0a0a0f' : '#ffffff' }}
            >
                <Background color={mode === 'dark' ? '#aaa' : '#555'} gap={16} />
                <Controls />
                <MiniMap style={mode === 'dark' ? { background: '#333' } : undefined} />
                <Panel position="top-right">
                    <div>Nodes: {nodes.length}</div>
                </Panel>
            </ReactFlow>
        </div>
    );
}

export default FlowGraph;
