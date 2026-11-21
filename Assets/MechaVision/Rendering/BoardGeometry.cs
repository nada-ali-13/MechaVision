using System.Collections.Generic;
using System.Globalization;
using MechaVision.Catalog;
using UnityEngine;
using UnityEngine.Rendering;

namespace MechaVision.Rendering
{
    internal sealed class BoardGeometry
    {
        private static readonly Color Dark = new Color(0.15f, 0.20f, 0.27f);
        private static readonly Color Metal = new Color(0.68f, 0.76f, 0.83f);
        private static readonly Color Blue = new Color(0.10f, 0.39f, 0.63f);
        private static readonly Color Teal = new Color(0.12f, 0.48f, 0.42f);
        private static readonly int Tint = Shader.PropertyToID("_Color");

        private readonly Material surface;
        private readonly int layer;
        private Mesh holes;

        internal BoardGeometry(Material surface, int layer)
        {
            this.surface = surface;
            this.layer = layer;
        }

        internal Transform Node(string name, Transform parent, Vector3 offset)
        {
            var node = new GameObject(name) { layer = layer };
            node.transform.SetParent(parent, false);
            node.transform.localPosition = offset;
            return node.transform;
        }

        internal void Paint(Renderer renderer, Color tint)
        {
            renderer.sharedMaterial = surface;
            var properties = new MaterialPropertyBlock();
            properties.SetColor(Tint, tint);
            renderer.SetPropertyBlock(properties);
        }

        internal void ReleaseMeshes()
        {
            BoardAssembly.Release(holes);
            holes = null;
        }

        internal void Part(Transform root, PartData part, PinData[] pins, bool sitsOnBoard)
        {
            Vector3 size = part.size_m;
            switch (part.geometry)
            {
                case "led":
                    Led(root, size, pins, part.id);
                    return;
                case "resistor":
                    Resistor(root, size, pins, part.id);
                    return;
                case "uno":
                    Uno(root, size);
                    break;
                case "ultrasonic":
                    Ultrasonic(root, size);
                    break;
                case "servo":
                    Servo(root, size);
                    break;
                case "button":
                    Box(root, "Switch housing", AtHeight(size.y * 0.25f),
                        new Vector3(size.x, size.y * 0.50f, size.z), Metal);
                    Round(root, "Pushbutton", AtHeight(size.y * 0.68f),
                        new Vector3(size.x * 0.60f, size.y * 0.64f, size.z * 0.60f), Dark);
                    break;
                case "potentiometer":
                    Round(root, "Potentiometer housing", AtHeight(size.y * 0.26f),
                        new Vector3(size.x, size.y * 0.52f, size.z), Blue);
                    Round(root, "Adjustment knob", AtHeight(size.y * 0.66f),
                        new Vector3(size.x * 0.53f, size.y * 0.68f, size.z * 0.53f), Metal);
                    break;
                case "buzzer":
                    Round(root, "Buzzer body", AtHeight(size.y * 0.50f), size, Dark);
                    Round(root, "Sound aperture", AtHeight(size.y), size * 0.20f, Metal);
                    break;
                case "motor":
                    Round(root, "Motor body", AtHeight(size.y * 0.5f), size, Metal);
                    Round(root, "Motor shaft", AtHeight(size.y),
                        new Vector3(size.x * 0.15f, size.y * 0.40f, size.z * 0.15f), Dark);
                    break;
                case "display":
                case "oled":
                case "lcd":
                    Module(root, size);
                    Box(root, "Display", AtHeight(size.y * 0.77f),
                        new Vector3(size.x * 0.78f, size.y * 0.46f, size.z * 0.68f), Dark);
                    break;
                case "power":
                    Box(root, "Supply enclosure", AtHeight(size.y * 0.5f), size, Dark);
                    Box(root, "Supply panel", new Vector3(0, size.y * 0.65f, -size.z * 0.51f),
                        new Vector3(size.x * 0.9f, size.y * 0.40f, 0.001f), Metal);
                    break;
                default:
                    Module(root, size);
                    break;
            }

            foreach (PinData pin in pins)
            {
                if (sitsOnBoard)
                    Lead(root, pin.position_m, pin.position_m + AtHeight(size.y * 0.35f), 0.00055f);
                else
                    Round(root, "Terminal " + pin.id, pin.position_m,
                        new Vector3(0.00145f, 0.00125f, 0.00145f), Metal);
            }
        }

        internal void Junction(Transform root, Vector3 size, PinData[] ports)
        {
            var shell = new Color(0.63f, 0.66f, 0.68f);
            var lever = new Color(0.94f, 0.36f, 0.09f);
            Box(root, "Splice housing", AtHeight(size.y * 0.45f), size, shell);
            foreach (PinData port in ports)
            {
                Vector3 socket = port.position_m;
                Round(root, "Splice terminal " + port.id, socket,
                    new Vector3(0.0020f, 0.0014f, 0.0020f), Metal);
                Box(root, "Lever " + port.id, new Vector3(socket.x, size.y * 0.99f, size.z * 0.08f),
                    new Vector3(size.x * 0.22f, size.y * 0.12f, size.z * 0.62f), lever);
            }
        }

        internal void Breadboard(Transform parent, PhysicalBoardProfile profile)
        {
            Transform root = Node("Virtual 830-point breadboard", parent, Vector3.zero);
            Vector3 size = profile.dimensions_m;
            Box(root, "Breadboard body", AtHeight(-size.y * 0.5f), size,
                new Color(0.88f, 0.89f, 0.88f));
            if (profile.TryGetHole("E1", out Vector3 nearestUpper) &&
                profile.TryGetHole("F1", out Vector3 nearestLower))
            {
                float slotCenter = (nearestLower.z + nearestUpper.z) * 0.5f;
                float slotWidth = Mathf.Max(profile.pitch_m, nearestLower.z - nearestUpper.z - profile.pitch_m);
                Box(root, "Center trench", new Vector3(0, 0.00006f, slotCenter),
                    new Vector3(size.x * 0.97f, 0.00016f, slotWidth), new Color(0.68f, 0.72f, 0.74f));
            }

            var vertices = new List<Vector3>();
            var faces = new List<int>();
            foreach (Vector3 hole in profile.HolePositions)
                AddHole(vertices, faces, hole.x, hole.z);

            holes = new Mesh { name = "Breadboard perforations" };
            holes.SetVertices(vertices);
            holes.SetTriangles(faces, 0);
            holes.RecalculateNormals();
            Transform holesNode = Node("Terminal and rail holes", root, Vector3.zero);
            holesNode.gameObject.AddComponent<MeshFilter>().sharedMesh = holes;
            MeshRenderer renderer = holesNode.gameObject.AddComponent<MeshRenderer>();
            renderer.shadowCastingMode = ShadowCastingMode.Off;
            renderer.receiveShadows = false;
            Paint(renderer, Dark);

            foreach (BoardRailData rail in profile.rails)
                DrawRailStripes(root, profile, rail);
        }

        private void DrawRailStripes(Transform root, PhysicalBoardProfile profile, BoardRailData rail)
        {
            int first = 1;
            int last = rail.holes_per_group * rail.group_count;
            if (rail.cut_after != null)
            {
                foreach (int cut in rail.cut_after)
                {
                    AddRailStripe(root, profile, rail, first, cut);
                    first = cut + 1;
                }
            }
            AddRailStripe(root, profile, rail, first, last);
        }

        private void AddRailStripe(Transform root, PhysicalBoardProfile profile, BoardRailData rail,
            int first, int last)
        {
            if (!profile.TryGetHole(rail.id + first.ToString(CultureInfo.InvariantCulture), out Vector3 from) ||
                !profile.TryGetHole(rail.id + last.ToString(CultureInfo.InvariantCulture), out Vector3 to))
                return;

            Color tint = rail.id.EndsWith("P", System.StringComparison.Ordinal)
                ? new Color(0.83f, 0.22f, 0.20f)
                : Blue;
            float offset = Mathf.Sign(rail.z_m) * (rail.id == "TP" || rail.id == "BN" ? 0.00135f : -0.00135f);
            Vector3 center = new Vector3((from.x + to.x) * 0.5f, 0.00008f, rail.z_m + offset);
            Box(root, $"Rail segment {rail.id}{first}–{rail.id}{last}", center,
                new Vector3(to.x - from.x + 0.0012f, 0.00016f, 0.00055f), tint);
        }

        private static void AddHole(List<Vector3> vertices, List<int> faces, float x, float z)
        {
            const int sides = 8;
            const float radius = 0.00053f;
            const float y = 0.00022f;
            int center = vertices.Count;
            vertices.Add(new Vector3(x, y, z));
            for (int index = 0; index < sides; index++)
            {
                float angle = (Mathf.PI * 2 * index) / sides;
                vertices.Add(new Vector3(x + radius * Mathf.Cos(angle), y, z + radius * Mathf.Sin(angle)));
                faces.Add(center);
                faces.Add(center + 1 + (index + 1) % sides);
                faces.Add(center + 1 + index);
            }
        }

        private void Led(Transform root, Vector3 size, PinData[] pins, string id)
        {
            Color lens = id switch
            {
                "led_green" => new Color(0.14f, 0.72f, 0.34f),
                "led_yellow" => new Color(1f, 0.76f, 0.12f),
                _ => new Color(0.93f, 0.13f, 0.16f)
            };
            Round(root, "LED lens base", AtHeight(size.y * 0.52f),
                new Vector3(size.x, size.y * 0.31f, size.z), lens);
            Shape(root, "LED lens dome", PrimitiveType.Sphere, AtHeight(size.y * 0.70f),
                new Vector3(size.x * 0.90f, size.y * 0.60f, size.z * 0.90f), lens);
            foreach (PinData pin in pins)
                Lead(root, pin.position_m, pin.position_m + AtHeight(size.y * 0.4f), 0.00055f);
        }

        private void Resistor(Transform root, Vector3 size, PinData[] pins, string id)
        {
            float centerY = size.y * 0.70f;
            Transform body = Round(root, "Resistor body", AtHeight(centerY),
                new Vector3(size.y, size.x, size.z), new Color(0.85f, 0.70f, 0.48f));
            body.localRotation = Quaternion.Euler(0, 0, 90);
            var black = new Color(0.06f, 0.06f, 0.06f);
            var brown = new Color(0.30f, 0.17f, 0.12f);
            var red = new Color(0.85f, 0.17f, 0.15f);
            var orange = new Color(0.98f, 0.43f, 0.10f);
            var yellow = new Color(0.99f, 0.76f, 0.10f);
            var gold = new Color(0.77f, 0.59f, 0.19f);
            Color[] bands = id switch
            {
                "resistor" or "resistor_220" => new[] { red, red, brown, gold },
                "resistor_1k" => new[] { brown, black, red, gold },
                "resistor_2k" => new[] { red, black, red, gold },
                "resistor_10k" => new[] { brown, black, orange, gold },
                "resistor_100k" => new[] { brown, black, yellow, gold },
                _ => System.Array.Empty<Color>()
            };
            for (int index = 0; index < bands.Length; index++)
            {
                Transform band = Round(root, "Resistance color band",
                    new Vector3(size.x * (-0.32f + 0.21f * index), centerY, 0),
                    new Vector3(size.y * 1.03f, size.x * 0.07f, size.z * 1.03f), bands[index]);
                band.localRotation = body.localRotation;
            }
            foreach (PinData pin in pins)
            {
                Vector3 elbow = pin.position_m + AtHeight(centerY);
                Vector3 bodyEdge = new Vector3(Mathf.Sign(elbow.x) * size.x * 0.5f, centerY, 0);
                Lead(root, pin.position_m, elbow, 0.00052f);
                Lead(root, elbow, bodyEdge, 0.00052f);
            }
        }

        private void Uno(Transform root, Vector3 size)
        {
            Box(root, "Arduino PCB", AtHeight(0.0009f),
                new Vector3(size.x, 0.0018f, size.z), Teal);
            Box(root, "Microcontroller", AtHeight(0.0035f),
                new Vector3(size.x * 0.42f, 0.004f, size.z * 0.18f), Dark);
            Box(root, "USB connector", new Vector3(-size.x * 0.35f, 0.0075f, -0.010f),
                new Vector3(0.016f, 0.014f, 0.013f), Metal);
            Box(root, "Power connector", new Vector3(-size.x * 0.36f, 0.0065f, 0.017f),
                new Vector3(0.014f, 0.012f, 0.010f), Dark);
            foreach (float z in new[] { -0.024f, 0.024f })
            {
                Box(root, "Pin header", new Vector3(size.x * 0.11f, 0.0027f, z),
                    new Vector3(size.x * 0.78f, 0.0027f, 0.0032f), Dark);
            }
        }

        private void Ultrasonic(Transform root, Vector3 size)
        {
            Box(root, "Ultrasonic PCB", AtHeight(0.001f),
                new Vector3(size.x, 0.002f, size.z), Blue);
            foreach (float direction in new[] { -1f, 1f })
            {
                Vector3 offset = new Vector3(direction * size.x * 0.25f, size.y * 0.48f, 0);
                Round(root, "Transducer can", offset,
                    new Vector3(size.z, size.y * 0.85f, size.z), Metal);
                Round(root, "Transducer grille", offset + AtHeight(size.y * 0.45f),
                    new Vector3(size.z * 0.64f, 0.0012f, size.z * 0.64f), Dark);
            }
        }

        private void Servo(Transform root, Vector3 size)
        {
            Box(root, "Servo housing", AtHeight(size.y * 0.37f),
                new Vector3(size.x, size.y * 0.74f, size.z), Blue);
            Vector3 hornOffset = new Vector3(size.x * 0.21f, size.y * 0.81f, 0);
            Round(root, "Servo spline", hornOffset,
                new Vector3(size.z * 0.58f, size.y * 0.24f, size.z * 0.58f), Metal);
            Box(root, "Servo horn", hornOffset + AtHeight(size.y * 0.15f),
                new Vector3(size.x * 0.95f, 0.0018f, size.z * 0.38f), Color.white);
        }

        private void Module(Transform root, Vector3 size)
        {
            Box(root, "Module PCB", AtHeight(size.y * 0.12f),
                new Vector3(size.x, size.y * 0.24f, size.z), Teal);
            Box(root, "Module package", AtHeight(size.y * 0.62f),
                new Vector3(size.x * 0.70f, size.y * 0.76f, size.z * 0.62f), Dark);
        }

        private void Lead(Transform root, Vector3 start, Vector3 end, float thickness)
        {
            Vector3 direction = end - start;
            if (direction.sqrMagnitude < 0.0000000001f)
                return;

            Transform lead = Round(root, "Metal lead", (start + end) * 0.5f,
                new Vector3(thickness, direction.magnitude, thickness), Metal);
            lead.localRotation = Quaternion.FromToRotation(Vector3.up, direction);
        }

        private static Vector3 AtHeight(float y)
        {
            return new Vector3(0, y, 0);
        }

        private Transform Box(Transform parent, string name, Vector3 center, Vector3 size, Color color)
        {
            return Shape(parent, name, PrimitiveType.Cube, center, size, color);
        }

        private Transform Round(Transform parent, string name, Vector3 center, Vector3 size, Color color)
        {
            // Unity's cylinder mesh is two units tall.
            size.y *= 0.5f;
            return Shape(parent, name, PrimitiveType.Cylinder, center, size, color);
        }

        private Transform Shape(Transform parent, string name, PrimitiveType kind, Vector3 center,
            Vector3 scale, Color color)
        {
            GameObject model = GameObject.CreatePrimitive(kind);
            model.name = name;
            model.layer = layer;
            model.transform.SetParent(parent, false);
            model.transform.localPosition = center;
            model.transform.localScale = scale;

            // The explicit collider types preserve CreatePrimitive dependencies in player builds.
            Collider collider;
            switch (kind)
            {
                case PrimitiveType.Cube:
                    collider = model.GetComponent<BoxCollider>();
                    break;
                case PrimitiveType.Sphere:
                    collider = model.GetComponent<SphereCollider>();
                    break;
                default:
                    collider = model.GetComponent<CapsuleCollider>();
                    break;
            }
            if (collider != null)
            {
                collider.enabled = false;
                BoardAssembly.Release(collider);
            }

            var renderer = model.GetComponent<MeshRenderer>();
            renderer.shadowCastingMode = ShadowCastingMode.Off;
            renderer.receiveShadows = false;
            Paint(renderer, color);
            return model.transform;
        }
    }
}
