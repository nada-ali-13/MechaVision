using System;
using System.Collections.Generic;
using System.Globalization;
using UnityEngine;

namespace MechaVision.Catalog
{
    [Serializable]
    internal sealed class PhysicalLayoutCatalog
    {
        public int schema_version;
        public string board_profile_id;
        public string board_profile_sha256;
        public string measurement_status;
        public PhysicalLayoutPlan[] plans;
    }

    [Serializable]
    public sealed class PhysicalLayoutPlan
    {
        public string project_id;
        public string status;
        public string reason_ar;
        public string[] warnings_ar;
        public bool net_equivalent;
        public PhysicalComponentData[] components;
        public PhysicalJunctionData[] junctions;
        public PhysicalConnectionData[] connections;
        public AssemblyStepData[] assembly_steps;

        public bool IsPlanned => status == "planned" && net_equivalent;
    }

    [Serializable]
    public sealed class PhysicalComponentData
    {
        public string instance_id;
        public string part_id;
        public string placement;
        public Vector3 position_m;
        public PhysicalPinData[] pins;
    }

    [Serializable]
    public sealed class PhysicalJunctionData
    {
        public string id;
        public string name_ar;
        public string part_number;
        public string source_url;
        public Vector3 position_m;
        public Vector3 size_m;
        public PhysicalPinData[] ports;
    }

    [Serializable]
    public sealed class PhysicalPinData
    {
        public string id;
        public string terminal;
        public Vector3 position_m;
    }

    [Serializable]
    public sealed class PhysicalConnectionData
    {
        public string id;
        public string from;
        public string to;
        public string kind;
        public string color;
        public Vector3[] via;
    }

    [Serializable]
    public sealed class PhysicalBoardProfile
    {
        public int profile_version;
        public string id;
        public string measurement_status;
        public string measurement_notes_ar;
        public float pitch_m;
        public Vector3 dimensions_m;
        public int column_count;
        public float column_first_x_m;
        public BoardRowData[] rows;
        public BoardRailData[] rails;

        private Dictionary<string, Vector3> holes;

        public IEnumerable<Vector3> HolePositions => GetHoles().Values;

        public bool TryGetHole(string name, out Vector3 position)
        {
            position = Vector3.zero;
            return name != null && GetHoles().TryGetValue(name, out position);
        }

        private Dictionary<string, Vector3> GetHoles()
        {
            if (holes != null)
                return holes;

            if (pitch_m <= 0 || column_count < 1 || rows == null || rails == null ||
                dimensions_m.x <= 0 || dimensions_m.y <= 0 || dimensions_m.z <= 0)
                throw new InvalidOperationException("Invalid physical breadboard profile.");

            var result = new Dictionary<string, Vector3>(StringComparer.Ordinal);
            foreach (BoardRowData row in rows)
            {
                for (int index = 0; index < column_count; index++)
                {
                    string key = row.name + (index + 1).ToString(CultureInfo.InvariantCulture);
                    result.Add(key, new Vector3(column_first_x_m + index * pitch_m, 0, row.z_m));
                }
            }

            foreach (BoardRailData rail in rails)
            {
                float railPitch = rail.pitch_m > 0 ? rail.pitch_m : pitch_m;
                for (int group = 0; group < rail.group_count; group++)
                {
                    for (int withinGroup = 0; withinGroup < rail.holes_per_group; withinGroup++)
                    {
                        int index = group * rail.holes_per_group + withinGroup;
                        string key = rail.id + (index + 1).ToString(CultureInfo.InvariantCulture);
                        float x = rail.first_x_m + (index + group * rail.gap_after_group_pitches) * railPitch;
                        result.Add(key, new Vector3(x, 0, rail.z_m));
                    }
                }
            }

            holes = result;
            return holes;
        }
    }

    [Serializable]
    public sealed class BoardRowData
    {
        public string name;
        public float z_m;
    }

    [Serializable]
    public sealed class BoardRailData
    {
        public string id;
        public float z_m;
        public float first_x_m;
        public float pitch_m;
        public int holes_per_group;
        public int group_count;
        public float gap_after_group_pitches;
        public int[] cut_after;
    }
}
