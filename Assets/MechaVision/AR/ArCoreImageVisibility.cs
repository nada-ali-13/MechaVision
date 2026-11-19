using System;
using UnityEngine.XR.ARFoundation;

#if UNITY_ANDROID && !UNITY_EDITOR
using System.Runtime.InteropServices;
using UnityEngine.XR.ARCore;
#endif

namespace MechaVision.AR
{
    /// <summary>Checks the ARCore mode that distinguishes direct observation from a last-known pose.</summary>
    internal sealed class ArCoreImageVisibility : IDisposable
    {
        public bool IsUnavailable { get; private set; }

#if UNITY_ANDROID && !UNITY_EDITOR
        private const string Library = "arcore_sdk_c";
        private const int AugmentedImage = 0x41520104;
        private const int FullTracking = 1;
        private IntPtr trackables;
        private IntPtr listSession;

        public bool IsObserved(ARSession arSession)
        {
            if (IsUnavailable || arSession.subsystem is not ARCoreSessionSubsystem subsystem)
                return false;

            IntPtr session = subsystem.session.AsIntPtr();
            if (session == IntPtr.Zero)
                return false;

            try
            {
                if (session != listSession)
                {
                    Dispose();
                    listSession = session;
                }
                if (trackables == IntPtr.Zero)
                    ArTrackableList_create(session, out trackables);
                if (trackables == IntPtr.Zero)
                    return false;

                ArSession_getAllTrackables(session, AugmentedImage, trackables);
                ArTrackableList_getSize(session, trackables, out int count);
                int observedImages = 0;
                for (int index = 0; index < count; index++)
                {
                    ArTrackableList_acquireItem(session, trackables, index, out IntPtr image);
                    if (image == IntPtr.Zero)
                        continue;

                    try
                    {
                        ArAugmentedImage_getTrackingMethod(session, image, out int method);
                        if (method == FullTracking)
                            observedImages++;
                    }
                    finally
                    {
                        ArTrackable_release(image);
                    }
                }

                // The project's reference library contains one image. Refuse an ambiguous observation.
                return observedImages == 1;
            }
            catch (Exception exception) when (exception is DllNotFoundException or EntryPointNotFoundException)
            {
                IsUnavailable = true;
                UnityEngine.Debug.LogWarning(exception.Message);
                return false;
            }
        }

        public void Dispose()
        {
            if (trackables != IntPtr.Zero)
                ArTrackableList_destroy(trackables);
            trackables = IntPtr.Zero;
            listSession = IntPtr.Zero;
        }

        [DllImport(Library)] private static extern void ArTrackableList_create(IntPtr session, out IntPtr list);
        [DllImport(Library)] private static extern void ArTrackableList_destroy(IntPtr list);
        [DllImport(Library)] private static extern void ArSession_getAllTrackables(IntPtr session, int filter, IntPtr list);
        [DllImport(Library)] private static extern void ArTrackableList_getSize(IntPtr session, IntPtr list, out int size);
        [DllImport(Library)] private static extern void ArTrackableList_acquireItem(IntPtr session, IntPtr list, int index, out IntPtr item);
        [DllImport(Library)] private static extern void ArAugmentedImage_getTrackingMethod(IntPtr session, IntPtr image, out int method);
        [DllImport(Library)] private static extern void ArTrackable_release(IntPtr trackable);
#else
        public bool IsObserved(ARSession arSession) => false;
        public void Dispose() { }
#endif
    }
}
