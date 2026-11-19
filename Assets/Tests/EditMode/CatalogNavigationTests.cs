using MechaVision.Catalog;
using MechaVision.UI;
using NUnit.Framework;

namespace MechaVision.Tests
{
    public sealed class CatalogNavigationTests
    {
        [Test]
        public void SearchesArabicEnglishAndAliasesAndAppliesFilters()
        {
            var project = new ProjectData
            {
                name_ar = "سَلَّة مهملات ذكية",
                name_en = "Smart Dustbin",
                aliases = new[] { "automatic trash bin", "حاوية ذكية" },
                category = "automation",
                level = "beginner"
            };

            Assert.That(CatalogNavigation.Matches(project, "سلة"), Is.True);
            Assert.That(CatalogNavigation.Matches(project, "SMART"), Is.True);
            Assert.That(CatalogNavigation.Matches(project, "حاوية"), Is.True);
            Assert.That(CatalogNavigation.Matches(project, "trash"), Is.True);
            Assert.That(CatalogNavigation.Matches(project, "trash", "sensors"), Is.False);
            Assert.That(CatalogNavigation.Matches(project, "", "automation", "advanced"), Is.False);
        }

        [TestCase(0, 1, 3, 1)]
        [TestCase(0, -1, 3, 3)]
        [TestCase(1, -1, 3, 1)]
        [TestCase(2, 1, 3, 3)]
        [TestCase(3, 1, 3, 3)]
        [TestCase(0, 1, 0, 0)]
        public void StepSelectionHandlesAllModeAndBoundaries(int step, int delta, int count, int expected)
        {
            Assert.That(CatalogNavigation.MoveStep(step, delta, count), Is.EqualTo(expected));
        }
    }
}
