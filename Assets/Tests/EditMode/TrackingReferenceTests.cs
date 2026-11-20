using MechaVision.AR;
using NUnit.Framework;
using UnityEditor;
using UnityEngine.XR.ARSubsystems;

namespace MechaVision.Tests
{
    public sealed class TrackingReferenceTests
    {
        [Test]
        public void ReferenceLibraryContainsThePrintedMarkerAtItsMeasuredSize()
        {
            var library = AssetDatabase.LoadAssetAtPath<XRReferenceImageLibrary>(
                "Assets/MechaVision/AR/TrackingProofImageLibrary.asset");

            Assert.That(library, Is.Not.Null);
            Assert.That(library.count, Is.EqualTo(1));
            var marker = library[0];
            Assert.That(marker.name, Is.EqualTo(BoardTracker.MarkerName));
            Assert.That(marker.specifySize, Is.True);
            Assert.That(marker.size.x, Is.EqualTo(0.075f).Within(0.00001f));
            Assert.That(marker.size.y, Is.EqualTo(0.060f).Within(0.00001f));
            Assert.That(AssetDatabase.GUIDToAssetPath(marker.textureGuid.ToString("N")),
                Is.EqualTo("Assets/MechaVision/AR/MechaVisionMarker.png"));
        }
    }
}
