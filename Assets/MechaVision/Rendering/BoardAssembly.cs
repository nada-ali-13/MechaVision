using System;
using System.Collections.Generic;
using MechaVision.Catalog;
using UnityEngine;
using UnityEngine.Rendering;

namespace MechaVision.Rendering
{
    public sealed class BoardAssembly : MonoBehaviour
    {
        private const float ActiveWidth = 0.0018f;
        private const float FadedWidth = 0.0011f;

        private readonly Dictionary<string, PartData> parts = new(StringComparer.Ordinal);
        private readonly Dictionary<string, Transform> anchors = new(StringComparer.Ordinal);
        private readonly Dictionary<string, Vector3> externalTerminals = new(StringComparer.Ordinal);
        private readonly Dictionary<string, WireDisplay> wires = new(StringComparer.Ordinal);
        private readonly HashSet<string> completedWires = new(StringComparer.Ordinal);
        private readonly HashSet<string> currentWires = new(StringComparer.Ordinal);

        private Transform boardRoot;
        private Transform contents;
        private Material surface;
        private Material wireMaterial;
        private Material fadedWireMaterial;
        private BoardGeometry geometry;
        private PhysicalBoardProfile boardProfile;
        private AssemblyStepData[] steps = Array.Empty<AssemblyStepData>();
        private bool virtualBreadboard;

        public void Configure(Transform root, CatalogData catalog, bool showVirtualBreadboard = false)
        {
            if (root == null)
                throw new ArgumentNullException(nameof(root));

            Clear();
            boardRoot = root;
            virtualBreadboard = showVirtualBreadboard;
            parts.Clear();
            if (catalog?.parts == null)
                return;
            foreach (PartData part in catalog.parts)
                parts.Add(part.id, part);
        }

        public PhysicalLayoutPlan GetLayout(ProjectData project)
        {
            return PhysicalLayoutLoader.Find(project?.id);
        }

        public bool CanShowProject(ProjectData project)
        {
            return GetLayout(project)?.IsPlanned == true;
        }

        public void ShowProject(ProjectData project)
        {
            if (project == null)
                throw new ArgumentNullException(nameof(project));
            ShowAssembly(GetLayout(project), project.id);
        }

        public void ShowTrackingProof()
        {
            string projectId = PhysicalLayoutLoader.TrackingProofProjectId;
            ShowAssembly(PhysicalLayoutLoader.Find(projectId), projectId);
        }

        public void ShowStep(int step, bool fadeCompleted = false)
        {
            if (step < 0 || step > steps.Length)
                throw new ArgumentOutOfRangeException(nameof(step));

            completedWires.Clear();
            currentWires.Clear();

            if (step > 0)
            {
                currentWires.UnionWith(steps[step - 1].connection_ids);
                if (fadeCompleted)
                {
                    for (int index = 0; index < step - 1; index++)
                        completedWires.UnionWith(steps[index].connection_ids);
                }
            }

            foreach (KeyValuePair<string, WireDisplay> entry in wires)
            {
                bool current = currentWires.Contains(entry.Key);
                bool faded = !current && completedWires.Contains(entry.Key);
                UpdateWire(entry.Value, current || faded, faded);
            }
        }

        public void ShowAll()
        {
            foreach (WireDisplay wire in wires.Values)
                UpdateWire(wire, true, false);
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
            bool exists = wires.TryGetValue(connectionId, out WireDisplay display);
            wire = exists ? display.Line : null;
            return exists;
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
            externalTerminals.Clear();
            wires.Clear();
            completedWires.Clear();
            currentWires.Clear();
            steps = Array.Empty<AssemblyStepData>();
        }

        private void ShowAssembly(PhysicalLayoutPlan plan, string projectId)
        {
            Clear();
            if (boardRoot == null)
                throw new InvalidOperationException("Configure BoardAssembly with a board root first.");
            if (plan?.IsPlanned != true)
                throw new InvalidOperationException($"Physical layout is unavailable for {projectId}.");

            if (parts.Count == 0)
            {
                foreach (PartData part in CatalogLoader.Load().parts)
                    parts.Add(part.id, part);
            }

            boardProfile = PhysicalLayoutLoader.BoardProfile;
            surface ??= LoadMaterial("BoardSurface");
            if (wireMaterial == null)
            {
                wireMaterial = LoadMaterial("BoardWire");
                wireMaterial.SetFloat("_WriteDepth", 1f);
                wireMaterial.renderQueue = (int)RenderQueue.Geometry;
                fadedWireMaterial = new Material(wireMaterial) { name = "MechaVision BoardWire Faded" };
                fadedWireMaterial.SetFloat("_WriteDepth", 0f);
                fadedWireMaterial.renderQueue = (int)RenderQueue.Transparent;
            }
            geometry = new BoardGeometry(surface, boardRoot.gameObject.layer);
            contents = geometry.Node(projectId, boardRoot, Vector3.zero);
            contents.gameObject.SetActive(false);

            try
            {
                if (virtualBreadboard)
                    geometry.Breadboard(contents, boardProfile);
                foreach (PhysicalComponentData component in plan.components)
                    AddComponent(component, parts[component.part_id]);
                foreach (PhysicalJunctionData junction in plan.junctions ?? Array.Empty<PhysicalJunctionData>())
                    AddJunction(junction);
                foreach (PhysicalConnectionData connection in plan.connections)
                    AddWire(connection);
                steps = plan.assembly_steps;
                ShowStep(0);
                contents.gameObject.SetActive(true);
            }
            catch
            {
                Clear();
                throw;
            }
        }

        private static Material LoadMaterial(string resourceName)
        {
            Shader shader = Resources.Load<Shader>($"MechaVision/{resourceName}");
            if (shader == null)
                throw new InvalidOperationException($"Missing renderer shader {resourceName}.");
            return new Material(shader) { name = $"MechaVision {resourceName}" };
        }

        private void AddComponent(PhysicalComponentData component, PartData part)
        {
            Transform partRoot = geometry.Node(component.instance_id, contents, component.position_m);
            bool mounted = component.placement == "breadboard";
            var pins = new PinData[component.pins.Length];

            for (int index = 0; index < pins.Length; index++)
            {
                PhysicalPinData pin = component.pins[index];
                string name = $"{component.instance_id}.{pin.id}";
                Vector3 position;
                if (mounted)
                {
                    if (!boardProfile.TryGetHole(pin.terminal, out position) ||
                        (position - pin.position_m).sqrMagnitude > 0.0000000001f)
                        throw new InvalidOperationException($"Pin {name} does not match hole {pin.terminal}.");
                }
                else
                {
                    if (!StringComparer.Ordinal.Equals(name, pin.terminal))
                        throw new InvalidOperationException($"Invalid external terminal {pin.terminal}.");
                    position = pin.position_m;
                    externalTerminals.Add(name, position);
                }

                Vector3 localPosition = position - component.position_m;
                Transform terminal = geometry.Node(pin.id, partRoot, localPosition);
                anchors.Add(name, terminal);
                pins[index] = new PinData { id = pin.id, position_m = localPosition };
            }

            geometry.Part(partRoot, part, pins, mounted);
        }

        private void AddJunction(PhysicalJunctionData junction)
        {
            Transform root = geometry.Node(junction.id, contents, junction.position_m);
            var ports = new PinData[junction.ports.Length];
            for (int index = 0; index < ports.Length; index++)
            {
                PhysicalPinData port = junction.ports[index];
                string name = $"{junction.id}.{port.id}";
                if (!StringComparer.Ordinal.Equals(name, port.terminal))
                    throw new InvalidOperationException($"Invalid junction terminal {port.terminal}.");

                externalTerminals.Add(name, port.position_m);
                Vector3 localPosition = port.position_m - junction.position_m;
                anchors.Add(name, geometry.Node(port.id, root, localPosition));
                ports[index] = new PinData { id = port.id, position_m = localPosition };
            }
            geometry.Junction(root, junction.size_m, ports);
        }

        private Vector3 ResolveTerminal(string endpoint)
        {
            if (externalTerminals.TryGetValue(endpoint, out Vector3 position))
                return position;

            if (!boardProfile.TryGetHole(endpoint, out position))
                throw new InvalidOperationException($"Unknown wire terminal {endpoint}.");

            if (!anchors.ContainsKey(endpoint))
                anchors.Add(endpoint, geometry.Node(endpoint, contents, position));
            return position;
        }

        private void AddWire(PhysicalConnectionData connection)
        {
            Vector3 start = ResolveTerminal(connection.from);
            Vector3 end = ResolveTerminal(connection.to);
            Vector3[] waypoints = connection.via ?? Array.Empty<Vector3>();
            Transform wire = geometry.Node(connection.id, contents, Vector3.zero);
            LineRenderer line = wire.gameObject.AddComponent<LineRenderer>();
            line.useWorldSpace = false;
            line.positionCount = waypoints.Length + 2;
            line.numCornerVertices = 2;
            line.numCapVertices = 4;
            line.alignment = LineAlignment.View;
            line.shadowCastingMode = ShadowCastingMode.Off;
            line.receiveShadows = false;
            line.SetPosition(0, start);
            for (int index = 0; index < waypoints.Length; index++)
                line.SetPosition(index + 1, waypoints[index]);
            line.SetPosition(line.positionCount - 1, end);
            line.sharedMaterial = wireMaterial;
            wires.Add(connection.id, new WireDisplay(line, WireColor(connection.color)));
        }

        private void UpdateWire(WireDisplay wire, bool active, bool faded)
        {
            wire.Line.gameObject.SetActive(active);
            if (!active)
                return;

            wire.Line.sharedMaterial = faded ? fadedWireMaterial : wireMaterial;
            wire.Line.widthMultiplier = faded ? FadedWidth : ActiveWidth;
            Color color = wire.Color;
            color.a = faded ? 0.27f : 1f;
            wire.Line.startColor = color;
            wire.Line.endColor = color;
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
                case "orange": return new Color(1f, 0.45f, 0.08f);
                case "purple": return new Color(0.69f, 0.32f, 0.88f);
                default: return Color.white;
            }
        }

        private void OnDestroy()
        {
            Clear();
            Release(surface);
            Release(wireMaterial);
            Release(fadedWireMaterial);
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

        private sealed class WireDisplay
        {
            public WireDisplay(LineRenderer line, Color color)
            {
                Line = line;
                Color = color;
            }

            public LineRenderer Line { get; }
            public Color Color { get; }
        }
    }
}
