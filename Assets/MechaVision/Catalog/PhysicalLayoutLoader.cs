using System;
using System.Collections.Generic;
using System.Security.Cryptography;
using System.Text;
using UnityEngine;

namespace MechaVision.Catalog
{
    public static class PhysicalLayoutLoader
    {
        public const string TrackingProofProjectId = "led_resistor_demo";
        public const string PlansResourcePath = "MechaVision/physical_plans";
        public const string BoardResourcePath = "MechaVision/breadboard_830";

        private static Dictionary<string, PhysicalLayoutPlan> plans;
        private static PhysicalBoardProfile profile;
        private static string measurementStatus;
        private static string profileHash;

        public static string MeasurementStatus
        {
            get
            {
                EnsurePlansLoaded();
                return measurementStatus;
            }
        }

        public static PhysicalBoardProfile BoardProfile
        {
            get
            {
                if (profile != null)
                    return profile;

                TextAsset asset = Resources.Load<TextAsset>(BoardResourcePath);
                if (asset == null)
                    throw new InvalidOperationException($"Missing board profile {BoardResourcePath}.");
                string text = asset.text.Replace("\r\n", "\n").Replace('\r', '\n');
                PhysicalBoardProfile parsed = JsonUtility.FromJson<PhysicalBoardProfile>(text);
                if (parsed == null || parsed.profile_version != 1 || string.IsNullOrEmpty(parsed.id))
                    throw new InvalidOperationException($"Invalid board profile {BoardResourcePath}.");
                using (SHA256 sha256 = SHA256.Create())
                {
                    byte[] hash = sha256.ComputeHash(Encoding.UTF8.GetBytes(text));
                    profileHash = BitConverter.ToString(hash).Replace("-", "").ToLowerInvariant();
                }
                profile = parsed;
                return profile;
            }
        }

        public static PhysicalLayoutPlan Find(string projectId)
        {
            if (string.IsNullOrWhiteSpace(projectId))
                return null;

            EnsurePlansLoaded();
            return plans != null && plans.TryGetValue(projectId, out PhysicalLayoutPlan result) ? result : null;
        }

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]
        private static void ResetCache()
        {
            plans = null;
            profile = null;
            measurementStatus = null;
            profileHash = null;
        }

        private static void EnsurePlansLoaded()
        {
            if (plans != null)
                return;

            TextAsset asset = Resources.Load<TextAsset>(PlansResourcePath);
            if (asset == null)
                return;

            PhysicalLayoutCatalog catalog = JsonUtility.FromJson<PhysicalLayoutCatalog>(asset.text);
            if (catalog == null || catalog.schema_version != 1 || catalog.plans == null)
                throw new InvalidOperationException($"Invalid physical plans {PlansResourcePath}.");
            if (catalog.board_profile_id != BoardProfile.id || catalog.board_profile_sha256 != profileHash)
                throw new InvalidOperationException("Physical plans must be regenerated for the loaded board profile.");

            var byId = new Dictionary<string, PhysicalLayoutPlan>(StringComparer.Ordinal);
            foreach (PhysicalLayoutPlan plan in catalog.plans)
                byId.Add(plan.project_id, plan);
            measurementStatus = catalog.measurement_status;
            plans = byId;
        }
    }
}
