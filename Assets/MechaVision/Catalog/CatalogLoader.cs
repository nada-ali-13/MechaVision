using System;
using UnityEngine;

namespace MechaVision.Catalog
{
    public static class CatalogLoader
    {
        public const string ResourcePath = "MechaVision/catalog";

        public static CatalogData Load()
        {
            TextAsset asset = Resources.Load<TextAsset>(ResourcePath);
            if (asset == null)
                throw new InvalidOperationException($"Missing catalog resource {ResourcePath}.");

            CatalogData catalog = JsonUtility.FromJson<CatalogData>(asset.text);
            if (catalog == null || catalog.schema_version != 1 ||
                catalog.parts == null || catalog.parts.Length == 0 ||
                catalog.projects == null || catalog.projects.Length == 0)
                throw new InvalidOperationException($"Invalid catalog resource {ResourcePath}.");

            return catalog;
        }

        public static string LoadSketch(ProjectData project)
        {
            if (project == null)
                throw new ArgumentNullException(nameof(project));
            if (string.IsNullOrWhiteSpace(project.sketch_resource))
                throw new InvalidOperationException($"Project {project.id} has no sketch resource.");

            TextAsset asset = Resources.Load<TextAsset>(project.sketch_resource);
            if (asset == null)
                throw new InvalidOperationException($"Missing sketch resource {project.sketch_resource}.");

            return asset.text;
        }
    }
}
