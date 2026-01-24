/**
 * Breadcrumbs Component
 *
 * Shows the path from root to the currently selected node.
 */

import { useCallback } from 'react';
import { useTreeStore, NODE_COLORS } from '@/stores/treeStore';

export function Breadcrumbs() {
    const breadcrumbPath = useTreeStore((state) => state.breadcrumbPath);
    const selectNode = useTreeStore((state) => state.selectNode);
    const expandNode = useTreeStore((state) => state.expandNode);
    
    const handleClick = useCallback(async (nodeId: string) => {
        // Expand the node to show its children, then select it
        await expandNode(nodeId);
        selectNode(nodeId);
    }, [expandNode, selectNode]);
    
    if (breadcrumbPath.length === 0) {
        return (
            <nav className="breadcrumbs">
                <button 
                    className="breadcrumb-item breadcrumb-root"
                    onClick={() => selectNode(null)}
                >
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
                        <polyline points="9 22 9 12 15 12 15 22" />
                    </svg>
                    <span>Root</span>
                </button>
            </nav>
        );
    }
    
    return (
        <nav className="breadcrumbs">
            <button 
                className="breadcrumb-item breadcrumb-root"
                onClick={() => selectNode(null)}
            >
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
                    <polyline points="9 22 9 12 15 12 15 22" />
                </svg>
            </button>
            
            {breadcrumbPath.map((node, index) => {
                const isLast = index === breadcrumbPath.length - 1;
                const color = NODE_COLORS[node.type] || NODE_COLORS.unknown;
                
                return (
                    <div key={node.id} style={{ display: 'flex', alignItems: 'center' }}>
                        <span className="breadcrumb-separator">›</span>
                        <button
                            className={`breadcrumb-item ${isLast ? 'breadcrumb-current' : ''}`}
                            onClick={() => !isLast && handleClick(node.id)}
                            disabled={isLast}
                        >
                            <span 
                                className="breadcrumb-type"
                                style={{ backgroundColor: color }}
                            />
                            <span>{node.name}</span>
                        </button>
                    </div>
                );
            })}
        </nav>
    );
}

export default Breadcrumbs;
