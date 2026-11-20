using MechaVision.AR;
using NUnit.Framework;
using UnityEngine;

namespace MechaVision.Tests
{
    public sealed class BoardCalibrationTests
    {
        [Test]
        public void ResolvesMillimetresAndRotationInMarkerCoordinates()
        {
            var calibration = new BoardCalibration();
            calibration.Set(new Vector3(100, 20, -50), new Vector3(0, 15, 0));
            var marker = new Pose(new Vector3(2, 1, 4), Quaternion.Euler(0, 90, 0));

            var board = calibration.Resolve(marker);

            Assert.That(Vector3.Distance(board.position, new Vector3(1.95f, 1.02f, 3.9f)), Is.LessThan(0.0001f));
            Assert.That(Quaternion.Angle(board.rotation, Quaternion.Euler(0, 105, 0)), Is.LessThan(0.01f));
        }
    }
}
