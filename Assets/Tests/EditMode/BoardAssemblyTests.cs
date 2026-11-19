using MechaVision.Catalog;
using MechaVision.Rendering;
using NUnit.Framework;
using UnityEngine;

namespace MechaVision.Tests
{
    public sealed class BoardAssemblyTests
    {
        private GameObject board;

        [SetUp]
        public void CreateBoard()
        {
            board = new GameObject("BoardRoot");
        }

        [TearDown]
        public void RemoveBoard()
        {
            Object.DestroyImmediate(board);
        }

        [Test]
        public void MovingBoardMovesWireEndpointsAndPartAnchorsTogether()
        {
            var assembly = board.AddComponent<BoardAssembly>();
            assembly.Configure(board.transform, null);
            assembly.ShowTrackingProof();

            AssertWireEndpoints(assembly);
            board.transform.SetPositionAndRotation(new Vector3(1, 2, 3), Quaternion.Euler(23, 75, -14));
            AssertWireEndpoints(assembly);
        }

        [Test]
        public void CatalogStepControlsWireVisibility()
        {
            var catalog = CatalogLoader.Load();
            var project = catalog.projects[0];
            var connection = project.connections[0];
            var assembly = board.AddComponent<BoardAssembly>();
            assembly.Configure(board.transform, catalog);
            assembly.ShowProject(project);
            Assert.That(assembly.TryGetWire(connection.id, out var wire), Is.True);
            assembly.ShowStep(1);
            Assert.That(wire.gameObject.activeSelf, Is.False);
            assembly.ShowStep(project.assembly_steps.Length);
            Assert.That(wire.gameObject.activeSelf, Is.True);
            assembly.ShowStep(0);
            Assert.That(wire.gameObject.activeSelf, Is.True);
        }

        private static void AssertWireEndpoints(BoardAssembly assembly)
        {
            Assert.That(assembly.TryGetAnchor("led1.ANODE", out var led), Is.True);
            Assert.That(assembly.TryGetAnchor("r1.A", out var resistor), Is.True);
            Assert.That(assembly.TryGetWire("proof_signal", out var wire), Is.True);
            Assert.That(wire.useWorldSpace, Is.False);
            Vector3 start = wire.transform.TransformPoint(wire.GetPosition(0));
            Vector3 end = wire.transform.TransformPoint(wire.GetPosition(wire.positionCount - 1));
            Assert.That(Vector3.Distance(start, led.position), Is.LessThan(0.0001f));
            Assert.That(Vector3.Distance(end, resistor.position), Is.LessThan(0.0001f));
        }
    }
}
