import { Background, ReactFlow } from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import type { Run, Stage } from '../types';
import { labels, stages } from '../types';

export default function WorkflowGraph({
  run,
  onSelect,
}: {
  run: Run | null;
  onSelect: (stage: Stage) => void;
}) {
  const nodes = stages.map((stage, index) => ({
    id: stage,
    position: { x: index * 175, y: 30 },
    data: { label: `${String(index + 1).padStart(2, '0')}  ${labels[stage]}` },
    style: {
      borderRadius: 10,
      padding: '15px 8px',
      width: 153,
      fontSize: 12,
      background: run?.artifacts[stage] ? '#e3efe7' : '#fff',
      color: '#24483c',
      border: `1px solid ${run?.artifacts[stage] ? '#98b9a5' : '#d8ded7'}`,
    },
  }));
  const edges = stages.slice(1).map((stage, i) => ({
    id: `edge-${stage}`,
    source: stages[i],
    target: stage,
    animated: run?.status === 'running',
    style: { stroke: '#a8b8ae' },
  }));
  return (
    <div className="graph" aria-label="Interactive seven-stage engineering workflow">
      <ReactFlow
        nodes={nodes}
        edges={run?.strategy === 'single_prompt' ? [] : edges}
        fitView
        nodesDraggable={false}
        nodesConnectable={false}
        panOnDrag={false}
        zoomOnScroll={false}
        zoomOnDoubleClick={false}
        minZoom={0.25}
        maxZoom={1.1}
        onNodeClick={(_, node) => onSelect(node.id as (typeof stages)[number])}
      >
        <Background color="#d7ded6" gap={18} size={1} />
      </ReactFlow>
    </div>
  );
}
