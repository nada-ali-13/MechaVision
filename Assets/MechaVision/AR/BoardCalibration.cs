using System;
using UnityEngine;

namespace MechaVision.AR
{
    /// <summary>Transforms the centre of the printed image into the top centre of the physical board.</summary>
    [Serializable]
    public sealed class BoardCalibration
    {
        [SerializeField] private Vector3 offsetMillimetres = new(140f, 0f, 0f);
        [SerializeField] private Vector3 rotationDegrees;

        public Vector3 OffsetMillimetres => offsetMillimetres;
        public Vector3 RotationDegrees => rotationDegrees;

        public void Set(Vector3 offsetMm, Vector3 eulerDegrees)
        {
            if (!IsFinite(offsetMm) || !IsFinite(eulerDegrees))
                throw new ArgumentException("Board calibration must contain finite measurements.");

            offsetMillimetres = offsetMm;
            rotationDegrees = eulerDegrees;
        }

        public Pose Resolve(Pose markerWorldPose)
        {
            Vector3 localOffset = offsetMillimetres * 0.001f;
            return new Pose(
                markerWorldPose.position + markerWorldPose.rotation * localOffset,
                markerWorldPose.rotation * Quaternion.Euler(rotationDegrees));
        }

        private static bool IsFinite(Vector3 vector) =>
            float.IsFinite(vector.x) && float.IsFinite(vector.y) && float.IsFinite(vector.z);
    }
}
