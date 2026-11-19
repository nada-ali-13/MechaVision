using MechaVision.Rendering;
using MechaVision.UI;
using Unity.XR.CoreUtils;
using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.InputSystem.XR;
using UnityEngine.XR.ARFoundation;
using UnityEngine.XR.ARSubsystems;

namespace MechaVision.AR
{
    /// <summary>Creates the single-camera mobile AR rig for the TrackingProof scene.</summary>
    public sealed class TrackingProofRig : MonoBehaviour
    {
        [SerializeField] private XRReferenceImageLibrary markerLibrary;

        private void Awake()
        {
            if (markerLibrary == null || markerLibrary.count != 1 || markerLibrary[0].name != BoardTracker.MarkerName)
            {
                Debug.LogError("TrackingProof requires its one-image reference library.", this);
                return;
            }

            GameObject sessionObject = new("AR Session");
            sessionObject.SetActive(false);
            sessionObject.transform.SetParent(transform, false);
            ARSession session = sessionObject.AddComponent<ARSession>();
            session.attemptUpdate = true;
            sessionObject.AddComponent<ARInputManager>();

            GameObject originObject = new("XR Origin");
            originObject.SetActive(false);
            originObject.transform.SetParent(transform, false);
            XROrigin origin = originObject.AddComponent<XROrigin>();
            origin.Origin = originObject;
            origin.CameraYOffset = 0f;

            GameObject cameraOffset = new("Camera Offset");
            cameraOffset.transform.SetParent(originObject.transform, false);
            origin.CameraFloorOffsetObject = cameraOffset;
            GameObject cameraObject = new("AR Camera");
            cameraObject.tag = "MainCamera";
            cameraObject.transform.SetParent(cameraOffset.transform, false);

            Camera arCamera = cameraObject.AddComponent<Camera>();
            arCamera.clearFlags = CameraClearFlags.SolidColor;
            arCamera.backgroundColor = Color.black;
            arCamera.nearClipPlane = 0.05f;
            arCamera.farClipPlane = 10f;
            arCamera.cullingMask &= ~(1 << 30);
            origin.Camera = arCamera;

            cameraObject.AddComponent<AudioListener>();
            ARCameraManager cameraManager = cameraObject.AddComponent<ARCameraManager>();
            cameraManager.requestedFacingDirection = CameraFacingDirection.World;
            cameraObject.AddComponent<ARCameraBackground>();
            TrackedPoseDriver driver = cameraObject.AddComponent<TrackedPoseDriver>();
            driver.positionInput = new InputActionProperty(new InputAction(
                "AR position", binding: "<HandheldARInputDevice>/devicePosition", expectedControlType: "Vector3"));
            driver.rotationInput = new InputActionProperty(new InputAction(
                "AR rotation", binding: "<HandheldARInputDevice>/deviceRotation", expectedControlType: "Quaternion"));

            ARTrackedImageManager images = originObject.AddComponent<ARTrackedImageManager>();
            images.referenceLibrary = markerLibrary;
            images.requestedMaxNumberOfMovingImages = 1;

            GameObject board = new("BoardRoot");
            board.transform.SetParent(originObject.transform, false);
            board.SetActive(false);

            GameObject application = new("MechaVision App");
            application.SetActive(false);
            application.transform.SetParent(transform, false);
            BoardTracker tracker = application.AddComponent<BoardTracker>();
            tracker.Configure(session, cameraManager, images, board.transform);
            MechaVisionApp app = application.AddComponent<MechaVisionApp>();
            app.tracker = tracker;
            app.assembly = application.AddComponent<BoardAssembly>();

            sessionObject.SetActive(true);
            originObject.SetActive(true);
            application.SetActive(true);
        }
    }
}
