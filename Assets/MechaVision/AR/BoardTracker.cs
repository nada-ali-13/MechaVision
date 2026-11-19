using UnityEngine;
using UnityEngine.XR.ARFoundation;
using UnityEngine.XR.ARSubsystems;

namespace MechaVision.AR
{
    [DisallowMultipleComponent]
    public sealed class BoardTracker : MonoBehaviour
    {
        public const string MarkerName = "MechaVisionMarker";
        private const double MaxFrameAgeSeconds = 0.25;

        [SerializeField] private BoardCalibration calibration = new();
        [SerializeField] private ARSession session;
        [SerializeField] private ARCameraManager cameraManager;
        [SerializeField] private ARTrackedImageManager imageManager;
        [SerializeField] private Transform boardRoot;

        private readonly ArCoreImageVisibility visibility = new();
        private long lastFrameTimestamp;
        private double lastFrameTime = double.NegativeInfinity;
        private bool paused;

        public Transform BoardRoot => boardRoot;
        public BoardCalibration Calibration => calibration;
        public bool IsTracking { get; private set; }
        public string StatusArabic { get; private set; } = "وجّهي الكاميرا نحو علامة البورد";

        public void Configure(ARSession arSession, ARCameraManager arCamera, ARTrackedImageManager images, Transform root)
        {
            session = arSession;
            cameraManager = arCamera;
            imageManager = images;
            boardRoot = root;
        }

        public void SetCalibration(Vector3 offsetMillimetres, Vector3 rotationDegrees) =>
            calibration.Set(offsetMillimetres, rotationDegrees);

        public void ResetTracking()
        {
            InvalidateFrame();
            Hide("وجّهي الكاميرا نحو علامة البورد");
            if (session != null)
                session.Reset();
        }

        private void OnEnable()
        {
            if (cameraManager != null)
                cameraManager.frameReceived += OnFrameReceived;
            Hide("وجّهي الكاميرا نحو علامة البورد");
        }

        private void OnDisable()
        {
            if (cameraManager != null)
                cameraManager.frameReceived -= OnFrameReceived;
            InvalidateFrame();
            Hide("توقّف التتبّع");
        }

        private void OnDestroy() => visibility.Dispose();

        private void OnApplicationPause(bool isPaused)
        {
            paused = isPaused;
            InvalidateFrame();
            if (isPaused)
                Hide("توقّف التتبّع مؤقتًا");
        }

        private void OnFrameReceived(ARCameraFrameEventArgs frame)
        {
            if (!paused && frame.timestampNs is long timestamp && timestamp > 0 && timestamp != lastFrameTimestamp)
            {
                lastFrameTimestamp = timestamp;
                lastFrameTime = Time.realtimeSinceStartupAsDouble;
            }
        }

        private void LateUpdate()
        {
            if (paused)
                return;

            if (ARSession.state == ARSessionState.Unsupported)
            {
                Hide(Application.isEditor ? "التتبّع الفعلي متاح على هاتف Android يدعم ARCore" : "تعذّر تشغيل ARCore على هذا الجهاز");
                return;
            }

            if (ARSession.state != ARSessionState.SessionTracking || imageManager == null)
            {
                Hide("انتظري بدء الكاميرا واسمحي بالوصول إليها");
                return;
            }

            if (Time.realtimeSinceStartupAsDouble - lastFrameTime > MaxFrameAgeSeconds ||
                !TryGetTrackedMarker(out ARTrackedImage marker) || !visibility.IsObserved(session))
            {
                Hide(visibility.IsUnavailable ? "تعذّر التحقق من رؤية العلامة عبر ARCore" : "وجّهي الكاميرا نحو علامة البورد");
                return;
            }

            Pose markerPose = new(marker.transform.position, marker.transform.rotation);
            Pose boardPose = calibration.Resolve(markerPose);
            if (!IsFinite(boardPose))
            {
                Hide("تعذّر تحديث موضع البورد. أعيدي توجيه الكاميرا نحو العلامة");
                return;
            }

            boardRoot.SetPositionAndRotation(boardPose.position, boardPose.rotation);
            boardRoot.gameObject.SetActive(true);
            IsTracking = true;
            StatusArabic = "تم تتبّع علامة البورد";
        }

        private bool TryGetTrackedMarker(out ARTrackedImage marker)
        {
            marker = null;
            foreach (ARTrackedImage image in imageManager.trackables)
            {
                if (image.trackingState != TrackingState.Tracking || image.referenceImage.name != MarkerName)
                    continue;

                // Do not jump between two copies of the same reference.
                if (marker != null)
                    return false;
                marker = image;
            }
            return marker != null;
        }

        private void InvalidateFrame()
        {
            lastFrameTimestamp = 0;
            lastFrameTime = double.NegativeInfinity;
        }

        private static bool IsFinite(Pose pose) =>
            float.IsFinite(pose.position.x) && float.IsFinite(pose.position.y) && float.IsFinite(pose.position.z) &&
            float.IsFinite(pose.rotation.x) && float.IsFinite(pose.rotation.y) &&
            float.IsFinite(pose.rotation.z) && float.IsFinite(pose.rotation.w);

        private void Hide(string message)
        {
            if (boardRoot != null)
                boardRoot.gameObject.SetActive(false);
            IsTracking = false;
            StatusArabic = message;
        }
    }
}
