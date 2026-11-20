using System;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.Build;
using UnityEditor.Build.Reporting;
using UnityEditor.XR.Management;
using UnityEngine.XR.ARCore;

namespace MechaVision.Editor
{
    public static class TrackingProofBuild
    {
        private const string ScenePath = "Assets/Scenes/TrackingProof.unity";

        [MenuItem("MechaVision/Build Android APK")]
        public static void BuildAndroid()
        {
            if (EditorUserBuildSettings.activeBuildTarget != BuildTarget.Android)
                throw new BuildFailedException("Switch the active build target to Android or pass -buildTarget Android.");

            var android = XRGeneralSettingsPerBuildTarget.XRGeneralSettingsForBuildTarget(BuildTargetGroup.Android);
            if (android == null || !android.InitManagerOnStart || android.Manager == null ||
                !android.Manager.activeLoaders.Any(loader => loader is ARCoreLoader))
                throw new BuildFailedException("Enable Google ARCore and Initialize XR on Startup for Android.");

            string output = "Builds/MechaVision.apk";
            string[] arguments = Environment.GetCommandLineArgs();
            int outputArgument = Array.IndexOf(arguments, "-mechaApk");
            if (outputArgument >= 0)
            {
                if (outputArgument + 1 >= arguments.Length || !arguments[outputArgument + 1].EndsWith(".apk", StringComparison.OrdinalIgnoreCase))
                    throw new BuildFailedException("-mechaApk requires a path ending in .apk.");
                output = arguments[outputArgument + 1];
            }

            Directory.CreateDirectory(Path.GetDirectoryName(Path.GetFullPath(output)));
            EditorUserBuildSettings.buildAppBundle = false;
            BuildReport result = BuildPipeline.BuildPlayer(new BuildPlayerOptions
            {
                scenes = new[] { ScenePath },
                locationPathName = output,
                target = BuildTarget.Android,
                options = BuildOptions.None
            });
            if (result.summary.result != BuildResult.Succeeded)
                throw new BuildFailedException($"MechaVision Android build result: {result.summary.result}");
        }
    }
}
