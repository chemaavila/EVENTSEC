import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import ReactFlow, {
  addEdge,
  Background,
  Controls,
  MiniMap,
  type Connection,
  type Edge,
  type Node,
  type ReactFlowInstance,
  useEdgesState,
  useNodesState,
} from "reactflow";
import "reactflow/dist/style.css";

import {
  createWorkplanItem,
  deleteWorkplanItem,
  getWorkplan,
  getWorkplanFlow,
  listWorkplanItems,
  updateWorkplanFlow,
  updateWorkplanItem,
  type Workplan,
  type WorkplanFlowPayload,
  type WorkplanItem,
} from "../services/api";
import type { ApiError } from "../services/http";
import { useToast } from "../components/common/ToastProvider";
import { LoadingState } from "../components/common/LoadingState";
import { ErrorState } from "../components/common/ErrorState";

const defaultNode = (): Node => ({
  id: "start",
  position: { x: 100, y: 100 },
  data: { label: "Start" },
  type: "default",
});

const WorkplanDetailPage = () => {
  const { workplanId } = useParams();
  const id = Number(workplanId);
  const { pushToast } = useToast();
  const [activeTab, setActiveTab] = useState<"details" | "items" | "flow">("details");
  const [workplan, setWorkplan] = useState<Workplan | null>(null);
  const [items, setItems] = useState<WorkplanItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [nodes, setNodes, onNodesChange] = useNodesState<Node[]>([defaultNode()]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge[]>([]);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [savingFlow, setSavingFlow] = useState(false);
  const [reactFlowInstance, setReactFlowInstance] = useState<ReactFlowInstance | null>(
    null
  );
  const [flowViewport, setFlowViewport] = useState<{ x: number; y: number; zoom: number } | null>(
    null
  );
  const [newItemTitle, setNewItemTitle] = useState("");

  const selectedNode = useMemo(
    () => nodes.find((node) => node.id === selectedNodeId) ?? null,
    [nodes, selectedNodeId]
  );

  const loadData = async () => {
    try {
      setLoading(true);
      const [workplanData, itemData] = await Promise.all([
        getWorkplan(id),
        listWorkplanItems(id),
      ]);
      setWorkplan(workplanData);
      setItems(itemData);
      setError(null);
      try {
        const flow = await getWorkplanFlow(id);
        setNodes(flow.nodes as Node[]);
        setEdges(flow.edges as Edge[]);
        if (flow.viewport) {
          setFlowViewport(flow.viewport as { x: number; y: number; zoom: number });
        }
      } catch (err) {
        const apiError = err as ApiError;
        if (apiError?.status !== 404) {
          throw err;
        }
        setNodes([defaultNode()]);
        setEdges([]);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load workplan");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!Number.isFinite(id)) {
      setError("Invalid workplan id");
      setLoading(false);
      return;
    }
    loadData().catch((err) => console.error(err));
  }, [id]);

  useEffect(() => {
    if (reactFlowInstance && flowViewport) {
      reactFlowInstance.setViewport(flowViewport);
    }
  }, [reactFlowInstance, flowViewport]);

  const handleAddNode = () => {
    const nextIndex = nodes.length + 1;
    const newNode: Node = {
      id: `node-${Date.now()}`,
      position: { x: 100 + nextIndex * 20, y: 100 + nextIndex * 20 },
      data: { label: `Task ${nextIndex}` },
      type: "default",
    };
    setNodes((prev) => [...prev, newNode]);
  };

  const handleSaveFlow = async () => {
    try {
      setSavingFlow(true);
      const viewport = reactFlowInstance?.getViewport();
      const payload: WorkplanFlowPayload = {
        format: "reactflow",
        nodes,
        edges,
        viewport,
      };
      await updateWorkplanFlow(id, payload);
      pushToast({
        title: "Diagram saved",
        message: "Flow diagram saved to workplan.",
        variant: "success",
      });
    } catch (err) {
      const details = err instanceof Error ? err.message : "Unknown error";
      pushToast({
        title: "Failed to save diagram",
        message: "Please try again.",
        details,
        variant: "error",
      });
    } finally {
      setSavingFlow(false);
    }
  };

  const handleCreateItem = async () => {
    if (!newItemTitle.trim()) return;
    try {
      const item = await createWorkplanItem(id, { title: newItemTitle.trim() });
      setItems((prev) => [...prev, item]);
      setNewItemTitle("");
    } catch (err) {
      pushToast({
        title: "Failed to add item",
        message: "Please try again.",
        details: err instanceof Error ? err.message : "Unknown error",
        variant: "error",
      });
    }
  };

  const handleUpdateItemStatus = async (item: WorkplanItem, status: string) => {
    try {
      const updated = await updateWorkplanItem(id, item.id, { status });
      setItems((prev) => prev.map((entry) => (entry.id === item.id ? updated : entry)));
    } catch (err) {
      pushToast({
        title: "Failed to update item",
        message: "Please try again.",
        details: err instanceof Error ? err.message : "Unknown error",
        variant: "error",
      });
    }
  };

  const handleDeleteItem = async (itemId: number) => {
    try {
      await deleteWorkplanItem(id, itemId);
      setItems((prev) => prev.filter((entry) => entry.id !== itemId));
    } catch (err) {
      pushToast({
        title: "Failed to remove item",
        message: "Please try again.",
        details: err instanceof Error ? err.message : "Unknown error",
        variant: "error",
      });
    }
  };

  if (loading) {
    return <LoadingState message="Loading workplan..." />;
  }

  if (error || !workplan) {
    return (
      <ErrorState
        message="Workplan not available."
        details={error ?? "Unknown error"}
        onRetry={() => loadData()}
      />
    );
  }

  return (
    <div className="page-root">
      <div className="page-header">
        <div className="page-title-group">
          <div className="page-title">{workplan.title}</div>
          <div className="page-subtitle">{workplan.description}</div>
        </div>
        <div className="stack-horizontal">
          <Link to="/workplans" className="btn btn-ghost">
            Back to workplans
          </Link>
        </div>
      </div>

      <div className="card">
        <div className="stack-horizontal" style={{ gap: "1rem" }}>
          <button
            type="button"
            className={`btn btn-sm ${activeTab === "details" ? "" : "btn-ghost"}`}
            onClick={() => setActiveTab("details")}
          >
            Details
          </button>
          <button
            type="button"
            className={`btn btn-sm ${activeTab === "items" ? "" : "btn-ghost"}`}
            onClick={() => setActiveTab("items")}
          >
            Tasks
          </button>
          <button
            type="button"
            className={`btn btn-sm ${activeTab === "flow" ? "" : "btn-ghost"}`}
            onClick={() => setActiveTab("flow")}
          >
            Flow Diagram
          </button>
        </div>
      </div>

      {activeTab === "details" && (
        <div className="card">
          <div className="stack-vertical">
            <div className="muted">Status: {workplan.status}</div>
            <div className="muted">Priority: {workplan.priority ?? "N/A"}</div>
            <div className="muted">
              Due at: {workplan.due_at ? new Date(workplan.due_at).toLocaleString() : "—"}
            </div>
            <div className="muted">
              Context:{" "}
              {workplan.context_type === "alert"
                ? `Alert #${workplan.context_id ?? "—"}`
                : workplan.context_type ?? "—"}
            </div>
          </div>
        </div>
      )}

      {activeTab === "items" && (
        <div className="card stack-vertical">
          <div className="stack-horizontal">
            <input
              className="field-control"
              placeholder="New task"
              value={newItemTitle}
              onChange={(event) => setNewItemTitle(event.target.value)}
            />
            <button type="button" className="btn btn-sm" onClick={handleCreateItem}>
              Add item
            </button>
          </div>
          {items.length === 0 ? (
            <div className="muted">No tasks yet.</div>
          ) : (
            items.map((item) => (
              <div key={item.id} className="stack-horizontal" style={{ gap: "1rem" }}>
                <div style={{ flex: 1 }}>{item.title}</div>
                <select
                  className="field-control"
                  value={item.status}
                  onChange={(event) => handleUpdateItemStatus(item, event.target.value)}
                >
                  <option value="open">Open</option>
                  <option value="in_progress">In progress</option>
                  <option value="blocked">Blocked</option>
                  <option value="done">Done</option>
                </select>
                <button
                  type="button"
                  className="btn btn-ghost"
                  onClick={() => handleDeleteItem(item.id)}
                >
                  Remove
                </button>
              </div>
            ))
          )}
        </div>
      )}

      {activeTab === "flow" && (
        <div className="card">
          <div className="stack-horizontal" style={{ marginBottom: "0.75rem" }}>
            <button type="button" className="btn btn-sm" onClick={handleAddNode}>
              Add node
            </button>
            <button
              type="button"
              className="btn btn-sm"
              onClick={handleSaveFlow}
              disabled={savingFlow}
            >
              {savingFlow ? "Saving..." : "Save diagram"}
            </button>
            <button
              type="button"
              className="btn btn-ghost"
              onClick={() => reactFlowInstance?.setViewport({ x: 0, y: 0, zoom: 1 })}
            >
              Reset view
            </button>
          </div>
          <div style={{ height: "480px" }}>
            <ReactFlow
              nodes={nodes}
              edges={edges}
              onNodesChange={onNodesChange}
              onEdgesChange={onEdgesChange}
              onNodeClick={(_, node) => setSelectedNodeId(node.id)}
              onConnect={(connection: Connection) =>
                setEdges((eds) => addEdge(connection, eds))
              }
              onInit={setReactFlowInstance}
              fitView
            >
              <Background gap={16} />
              <Controls />
              <MiniMap />
            </ReactFlow>
          </div>
          {selectedNode && (
            <div className="field-group" style={{ marginTop: "1rem" }}>
              <label className="field-label">Selected node label</label>
              <input
                className="field-control"
                value={(selectedNode.data as { label?: string })?.label ?? ""}
                onChange={(event) => {
                  const label = event.target.value;
                  setNodes((prev) =>
                    prev.map((node) =>
                      node.id === selectedNode.id
                        ? { ...node, data: { ...node.data, label } }
                        : node
                    )
                  );
                }}
              />
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default WorkplanDetailPage;
