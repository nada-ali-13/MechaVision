using System;
using System.Collections.Generic;
using MechaVision.Catalog;
using UnityEngine;
using UnityEngine.Rendering;

namespace MechaVision.Rendering
{
    public sealed class BoardAssembly : MonoBehaviour
    {
        private const int WireSegments = 24;
        private const float HolePitch = 0.00254f;
        private const float FirstRowOffset = 0.00381f;
        private const int HoleColumns = 63;
        private const string BoardShader = "MechaVision/BoardSurface";

        private readonly Dictionary<string, PartData> parts =
            new Dictionary<string, PartData>(StringComparer.Ordinal);
        private readonly Dictionary<string, Transform> anchors =
            new Dictionary<string, Transform>(StringComparer.Ordinal);
        private readonly Dictionary<string, LineRenderer> wires =
            new Dictionary<string, LineRenderer>(StringComparer.Ordinal);
        private readonly HashSet<string> visibleWires = new HashSet<string>(StringComparer.Ordinal);

        private Transform boardRoot;
        private Transform contents;
        private Material surface;
        private BoardGeometry geometry;
        private AssemblyStepData[] steps = Array.Empty<AssemblyStepData>();
        private bool virtualBreadboard;
        private int objectLayer;

        public void Configure(Transform root, CatalogData catalog, bool showVirtualBreadboard = false)
        {
            if (root == null)
                throw new ArgumentNullException(nameof(root));

            Clear();
            boardRoot = root;
            objectLayer = root.gameObject.layer;
            virtualBreadboard = showVirtualBreadboard;
            parts.Clear();
            if (catalog?.parts == null)
                return;
            foreach (PartData part in catalog.parts)
                parts.Add(part.id, part);
        }

        public void ShowProject(ProjectData project)
        {
            if (project == null)
                throw new ArgumentNullException(nameof(project));

            ShowAssembly(project.id, project.components, project.connections, project.assembly_steps, parts);
        }

        public void ShowStep(int step)
        {
            if (step < 0 || step > steps.Length)
                throw new ArgumentOutOfRangeException(nameof(step));

            visibleWires.Clear();
            for (int index = 0; index < step; index++)
            {
                foreach (string id in steps[index].connection_ids)
                    visibleWires.Add(id);
            }

            foreach (KeyValuePair<string, LineRenderer> wire in wires)
                wire.Value.gameObject.SetActive(step == 0 || visibleWires.Contains(wire.Key));
        }

        public void SetAssemblyVisible(bool visible)
        {
            if (contents != null)
                contents.gameObject.SetActive(visible);
        }

        public bool TryGetAnchor(string endpoint, out Transform anchor)
        {
            return anchors.TryGetValue(endpoint, out anchor);
        }

        public bool TryGetWire(string connectionId, out LineRenderer wire)
        {
            return wires.TryGetValue(connectionId, out wire);
        }

        public void Clear()
        {
            if (contents != null)
            {
                contents.gameObject.SetActive(false);
                Release(contents.gameObject);
            }

            contents = null;
            geometry?.ReleaseMeshes();
            anchors.Clear();
            wires.Clear();
            visibleWires.Clear();
            steps = Array.Empty<AssemblyStepData>();
        }

        public void ShowTrackingProof()
        {
            var proofParts = new Dictionary<string, PartData>(StringComparer.Ordinal)
            {
                ["led"] = new PartData
                {
                    id = "led", geometry = "led", size_m = new Vector3(0.005f, 0.009f, 0.005f),
                    pins = new[] { Pin("ANODE", -0.00127f), Pin("CATHODE", 0.00127f) }
                },
                ["resistor"] = new PartData
                {
                    id = "resistor", geometry = "resistor", size_m = new Vector3(0.005f, 0.0025f, 0.0025f),
                    pins = new[] { Pin("A", -0.00381f), Pin("B", 0.00381f) }
                }
            };
            ComponentData[] components =
            {
                new ComponentData
                {
                    id = "led1", part_id = "led", qty = 1, placement = "breadboard",
                    position_m = new Vector3(-5.5f * HolePitch, 0, FirstRowOffset)
                },
                new ComponentData
                {
                    id = "r1", part_id = "resistor", qty = 1, placement = "breadboard",
                    position_m = new Vector3(5.5f * HolePitch, 0, -FirstRowOffset)
                }
            };
            ConnectionData[] connections =
            {
                new ConnectionData
                {
                    id = "proof_signal", from = "led1.ANODE", to = "r1.A", kind = "signal", color = "yellow"
                },
                new ConnectionData
                {
                    id = "proof_ground", from = "led1.CATHODE", to = "breadboard.F35", kind = "ground", color = "black"
                },
                new ConnectionData
                {
                    id = "proof_power", from = "r1.B", to = "breadboard.D45", kind = "power", color = "red"
                }
            };
            ShowAssembly("TrackingProof", components, connections, Array.Empty<AssemblyStepData>(), proofParts);
        }

        private void ShowAssembly(
            string name, ComponentData[] components, ConnectionData[] connections,
            AssemblyStepData[] assemblySteps, Dictionary<string, PartData> registry)
        {
            if (boardRoot == null)
                throw new InvalidOperationException("Configure BoardAssembly with a board root first.");

            Clear();
            EnsureMaterial();
            contents = geometry.Node(name, boardRoot, Vector3.zero);
            contents.gameObject.SetActive(false);
            try
            {
                if (virtualBreadboard)
                    geometry.Breadboard(contents, HolePitch, FirstRowOffset, HoleColumns);
                foreach (ComponentData component in components)
                    AddComponent(component, registry[component.part_id]);
                foreach (ConnectionData connection in connections)
                    AddWire(connection);
                steps = assemblySteps ?? Array.Empty<AssemblyStepData>();
                contents.gameObject.SetActive(true);
            }
            catch
            {
                Clear();
                throw;
            }
        }

        private static PinData Pin(string id, float x)
        {
            return new PinData { id = id, position_m = new Vector3(x, 0, 0) };
        }

        private void EnsureMaterial()
        {
            if (surface == null)
            {
                Shader shader = Resources.Load<Shader>(BoardShader);
                if (shader == null)
                    throw new InvalidOperationException($"Missing renderer shader {BoardShader}.");
                surface = new Material(shader) { name = "MechaVision Board Surface" };
            }
            geometry = new BoardGeometry(surface, objectLayer);
        }

        private void AddComponent(ComponentData component, PartData part)
        {
            Transform partRoot = geometry.Node(component.id, contents, component.position_m);

            foreach (PinData pin in part.pins)
            {
                Transform anchor = geometry.Node(pin.id, partRoot, pin.position_m);
                anchors.Add($"{component.id}.{pin.id}", anchor);
            }

            geometry.Part(partRoot, part, component.placement == "breadboard");
        }

        private Transform ResolveAnchor(string endpoint)
        {
            if (anchors.TryGetValue(endpoint, out Transform anchor))
                return anchor;

            const string holePrefix = "breadboard.";
            if (endpoint.StartsWith(holePrefix, StringComparison.Ordinal) &&
                endpoint.Length > holePrefix.Length + 1)
            {
                char row = endpoint[holePrefix.Length];
                if (row >= 'A' && row <= 'J' &&
                    int.TryParse(endpoint.Substring(holePrefix.Length + 1), out int column) &&
                    column >= 1 && column <= HoleColumns)
                {
                    float x = (column - (HoleColumns + 1) / 2) * HolePitch;
                    float z = row >= 'F'
                        ? FirstRowOffset + (row - 'F') * HolePitch
                        : -FirstRowOffset - ('E' - row) * HolePitch;
                    anchor = geometry.Node(endpoint, contents, new Vector3(x, 0, z));
                    anchors.Add(endpoint, anchor);
                    return anchor;
                }
            }

            throw new InvalidOperationException($"Unknown wire endpoint {endpoint}.");
        }

        private void AddWire(ConnectionData connection)
        {
            Transform start = ResolveAnchor(connection.from);
            Transform end = ResolveAnchor(connection.to);
            Transform wire = geometry.Node(connection.id, contents, Vector3.zero);
            var line = wire.gameObject.AddComponent<LineRenderer>();
            line.useWorldSpace = false;
            line.widthMultiplier = 0.0016f;
            line.positionCount = WireSegments + 1;
            line.numCapVertices = 4;
            line.alignment = LineAlignment.View;
            line.generateLightingData = true;
            line.shadowCastingMode = ShadowCastingMode.Off;
            line.receiveShadows = false;
            geometry.Paint(line, WireColor(connection.color));

            Vector3 from = wire.InverseTransformPoint(start.position);
            Vector3 to = wire.InverseTransformPoint(end.position);
            float lift = Mathf.Clamp(Vector3.Distance(from, to) * 0.20f, 0.006f, 0.031f);

            line.SetPosition(0, from);
            for (int i = 1; i < WireSegments; i++)
            {
                float t = i / (float)WireSegments;
                Vector3 position = Vector3.Lerp(from, to, t);
                position.y += 4f * lift * t * (1f - t);
                line.SetPosition(i, position);
            }
            line.SetPosition(WireSegments, to);
            wires.Add(connection.id, line);
        }

        private static Color WireColor(string name)
        {
            switch (name)
            {
                case "red": return new Color(0.97f, 0.24f, 0.18f);
                case "black": return new Color(0.10f, 0.15f, 0.22f);
                case "yellow": return new Color(1f, 0.79f, 0.15f);
                case "green": return new Color(0.2f, 0.79f, 0.42f);
                case "blue": return new Color(0.19f, 0.53f, 1f);
                default: return Color.white;
            }
        }

        private void OnDestroy()
        {
            Clear();
            Release(surface);
        }

        internal static void Release(UnityEngine.Object target)
        {
            if (target == null)
                return;
            if (Application.isPlaying)
                Destroy(target);
            else
                DestroyImmediate(target);
        }
    }
}
