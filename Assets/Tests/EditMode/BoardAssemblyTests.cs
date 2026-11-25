using System.Linq;
using MechaVision.Catalog;
using MechaVision.Rendering;
using NUnit.Framework;
using UnityEngine;

namespace MechaVision.Tests
{
    public sealed class BoardAssemblyTests
    {
        private GameObject board;
        private BoardAssembly assembly;
        private PhysicalLayoutPlan proof;

        [SetUp]
        public void CreateBoard()
        {
            board = new GameObject("BoardRoot");
            assembly = board.AddComponent<BoardAssembly>();
            assembly.Configure(board.transform, CatalogLoader.Load());
            proof = PhysicalLayoutLoader.Find(PhysicalLayoutLoader.TrackingProofProjectId);
            Assert.That(proof?.IsPlanned, Is.True);
        }

        [TearDown]
        public void RemoveBoard()
        {
            Object.DestroyImmediate(board);
        }

        [Test]
        public void PhysicalProfileResolvesTheNamedHolesAndRailGaps()
        {
            PhysicalBoardProfile profile = PhysicalLayoutLoader.BoardProfile;
            Assert.That(profile.HolePositions.Count(), Is.EqualTo(830));
            Assert.That(profile.TryGetHole("A1", out Vector3 a1), Is.True);
            Assert.That(a1, Is.EqualTo(new Vector3(-0.07874f, 0, -0.01397f)));
            Assert.That(profile.TryGetHole("J63", out Vector3 j63), Is.True);
            Assert.That(j63.x, Is.EqualTo(0.07874f).Within(0.000001f));
            Assert.That(profile.TryGetHole("TP5", out Vector3 end), Is.True);
            Assert.That(profile.TryGetHole("TP6", out Vector3 start), Is.True);
            Assert.That(start.x - end.x, Is.EqualTo(2 * profile.pitch_m).Within(0.000001f));
            Assert.That(profile.TryGetHole("TP51", out _), Is.False);
            Assert.That(profile.TryGetHole("K1", out _), Is.False);
        }

        [Test]
        public void PerRailPitchOverridesCommonPitch()
        {
            var profile = new PhysicalBoardProfile
            {
                pitch_m = 0.00254f,
                dimensions_m = new Vector3(0.165f, 0.009f, 0.055f),
                column_count = 1,
                rows = new[] { new BoardRowData { name = "A" } },
                rails = new[]
                {
                    new BoardRailData
                    {
                        id = "TP", z_m = -0.02286f, first_x_m = -0.012f, pitch_m = 0.003f,
                        holes_per_group = 2, group_count = 2, gap_after_group_pitches = 1
                    }
                }
            };
            Assert.That(profile.TryGetHole("TP3", out Vector3 third), Is.True);
            Assert.That(third.x, Is.EqualTo(-0.003f).Within(0.000001f));
        }

        [Test]
        public void MovingBoardMovesPhysicalWireEndpointsAndPinAnchorsTogether()
        {
            assembly.ShowTrackingProof();
            AssertRoutePositions();
            AssertInsertedPins();

            board.transform.SetPositionAndRotation(new Vector3(1, 2, 3), Quaternion.Euler(23, 75, -14));
            AssertRoutePositions();
            AssertInsertedPins();
        }

        [Test]
        public void StepDisplaysCurrentWiresAndOptionallyFadesCompletedWires()
        {
            assembly.ShowTrackingProof();
            AssemblyStepData[] wireSteps = proof.assembly_steps.Where(step => step.connection_ids.Length > 0).ToArray();
            Assert.That(wireSteps.Length, Is.GreaterThanOrEqualTo(2));
            AssertActiveWires(Enumerable.Empty<string>());

            assembly.ShowStep(wireSteps[0].step);
            AssertActiveWires(wireSteps[0].connection_ids);

            assembly.ShowStep(wireSteps[1].step);
            AssertActiveWires(wireSteps[1].connection_ids);

            assembly.ShowStep(wireSteps[1].step, fadeCompleted: true);
            AssertActiveWires(wireSteps[0].connection_ids.Concat(wireSteps[1].connection_ids));
            Assert.That(assembly.TryGetWire(wireSteps[0].connection_ids[0], out LineRenderer completed), Is.True);
            Assert.That(assembly.TryGetWire(wireSteps[1].connection_ids[0], out LineRenderer current), Is.True);
            Assert.That(completed.startColor.a, Is.LessThan(current.startColor.a));

            assembly.ShowAll();
            AssertActiveWires(proof.connections.Select(connection => connection.id));
            Assert.That(completed.startColor.a, Is.EqualTo(current.startColor.a));

            assembly.ShowStep(0);
            AssertActiveWires(Enumerable.Empty<string>());
        }

        [Test]
        public void UnknownProjectCannotFallBackToIllustrativeWires()
        {
            assembly.ShowTrackingProof();
            var unknown = new ProjectData { id = "unknown_physical_fixture" };

            Assert.That(assembly.CanShowProject(unknown), Is.False);
            Assert.Throws<System.InvalidOperationException>(() => assembly.ShowProject(unknown));
            Assert.That(assembly.TryGetWire(proof.connections[0].id, out _), Is.False);
        }

        private void AssertRoutePositions()
        {
            foreach (PhysicalConnectionData connection in proof.connections)
            {
                Assert.That(assembly.TryGetAnchor(connection.from, out Transform start), Is.True);
                Assert.That(assembly.TryGetAnchor(connection.to, out Transform end), Is.True);
                Assert.That(assembly.TryGetWire(connection.id, out LineRenderer wire), Is.True);
                Assert.That(wire.useWorldSpace, Is.False);
                Assert.That(wire.positionCount, Is.EqualTo(connection.via.Length + 2));
                Assert.That(Vector3.Distance(wire.transform.TransformPoint(wire.GetPosition(0)), start.position),
                    Is.LessThan(0.00001f));
                Assert.That(Vector3.Distance(wire.transform.TransformPoint(wire.GetPosition(wire.positionCount - 1)),
                    end.position), Is.LessThan(0.00001f));
                for (int index = 0; index < connection.via.Length; index++)
                    Assert.That(wire.GetPosition(index + 1), Is.EqualTo(connection.via[index]));
            }
        }

        private void AssertInsertedPins()
        {
            var profile = PhysicalLayoutLoader.BoardProfile;
            var inserted = proof.components.Where(component => component.placement == "breadboard").ToArray();
            Assert.That(inserted.Length, Is.GreaterThan(0));
            foreach (PhysicalComponentData component in inserted)
            {
                foreach (PhysicalPinData pin in component.pins)
                {
                    Assert.That(profile.TryGetHole(pin.terminal, out Vector3 hole), Is.True);
                    Assert.That(assembly.TryGetAnchor($"{component.instance_id}.{pin.id}", out Transform anchor), Is.True);
                    Vector3 expected = board.transform.TransformPoint(hole);
                    Assert.That(Vector3.Distance(anchor.position, expected), Is.LessThan(0.00001f));
                }
            }
        }

        private void AssertActiveWires(System.Collections.Generic.IEnumerable<string> expected)
        {
            var active = proof.connections.Where(connection =>
                assembly.TryGetWire(connection.id, out LineRenderer line) && line.gameObject.activeSelf);
            Assert.That(active.Select(connection => connection.id), Is.EquivalentTo(expected));
        }
    }
}
