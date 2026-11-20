using MechaVision.Catalog;
using NUnit.Framework;

namespace MechaVision.Tests
{
    public sealed class CatalogResourceTests
    {
        [Test]
        public void ImportsOfflineCatalogAndAllSketchTextAssets()
        {
            var catalog = CatalogLoader.Load();
            Assert.That(catalog.projects, Has.Length.EqualTo(50));
            foreach (var project in catalog.projects)
            {
                string sketch = CatalogLoader.LoadSketch(project);
                Assert.That(sketch, Does.Contain("void setup"), project.id);
                Assert.That(sketch, Does.Contain("void loop"), project.id);
            }
        }
    }
}
