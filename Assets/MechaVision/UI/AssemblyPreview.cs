using MechaVision.Catalog;
using MechaVision.Rendering;
using UnityEngine;

namespace MechaVision.UI
{
    internal sealed class AssemblyPreview
    {
        internal const int Layer = 30;

        private readonly GameObject stage;
        private readonly Camera camera;
        private readonly RenderTexture texture;
        private readonly Transform board;
        private readonly BoardAssembly assembly;

        internal AssemblyPreview(Transform parent, CatalogData catalog)
        {
            stage = new GameObject("Assembly preview");
            stage.transform.SetParent(parent, false);
            stage.transform.position = new Vector3(90f, -90f, 90f);

            board = new GameObject("Preview board").transform;
            board.SetParent(stage.transform, false);
            board.gameObject.layer = Layer;
            assembly = stage.AddComponent<BoardAssembly>();
            assembly.Configure(board, catalog, true);

            texture = new RenderTexture(800, 800, 24) { name = "Circuit preview", antiAliasing = 2 };
            camera = new GameObject("Board preview camera").AddComponent<Camera>();
            camera.transform.SetParent(stage.transform, false);
            camera.targetTexture = texture;
            camera.cullingMask = 1 << Layer;
            camera.clearFlags = CameraClearFlags.SolidColor;
            camera.backgroundColor = AppView.Background;
            camera.orthographic = true;
            camera.nearClipPlane = 0.01f;
            camera.farClipPlane = 5f;

            Light key = new GameObject("Board preview light").AddComponent<Light>();
            key.transform.SetParent(stage.transform, false);
            key.transform.rotation = Quaternion.Euler(58f, -30f, 0f);
            key.type = LightType.Directional;
            key.intensity = 1.7f;
            key.cullingMask = 1 << Layer;
        }

        internal Texture Image => texture;

        internal void Show(ProjectData project)
        {
            stage.SetActive(true);
            if (project == null)
                assembly.ShowTrackingProof();
            else
                assembly.ShowProject(project);

            SetLayer(board);
            FrameBoard();
        }

        internal void ShowStep(int step)
        {
            assembly.ShowStep(step, fadeCompleted: true);
        }

        internal void ShowAll() => assembly.ShowAll();

        internal void SetAssemblyVisible(bool visible) => assembly.SetAssemblyVisible(visible);

        internal void Hide()
        {
            stage.SetActive(false);
        }

        internal void Dispose()
        {
            camera.targetTexture = null;
            texture.Release();
            Object.Destroy(texture);
            Object.Destroy(stage);
        }

        private void FrameBoard()
        {
            Bounds bounds = new Bounds(board.position, new Vector3(0.18f, 0.03f, 0.07f));
            foreach (Renderer item in board.GetComponentsInChildren<Renderer>())
                bounds.Encapsulate(item.bounds);
            Vector3 direction = new Vector3(0.04f, 0.83f, -0.55f);
            camera.transform.position = bounds.center + direction * 0.5f;
            camera.transform.LookAt(bounds.center);
            camera.orthographicSize = Mathf.Max(0.105f, bounds.extents.magnitude * 1.17f);
        }

        private static void SetLayer(Transform root)
        {
            root.gameObject.layer = Layer;
            foreach (Transform child in root)
                SetLayer(child);
        }
    }
}
