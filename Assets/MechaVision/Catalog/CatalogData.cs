using System;
using UnityEngine;

namespace MechaVision.Catalog
{
    [Serializable]
    public sealed class CatalogData
    {
        public int schema_version;
        public PartData[] parts;
        public ProjectData[] projects;
    }

    [Serializable]
    public sealed class PartData
    {
        public string id;
        public string name_ar;
        public string name_en;
        public string geometry;
        public Vector3 size_m;
        public PinData[] pins;
        public SourceData[] sources;
    }

    [Serializable]
    public sealed class PinData
    {
        public string id;
        public Vector3 position_m;
    }

    [Serializable]
    public sealed class ProjectData
    {
        public string id;
        public string name_ar;
        public string name_en;
        public string[] aliases;
        public string category;
        public string level;
        public string description_ar;
        public string[] learning_objectives;
        public string board;
        public ComponentData[] components;
        public ConnectionData[] connections;
        public AssemblyStepData[] assembly_steps;
        public string sketch_path;
        public string sketch_resource;
        public LibraryData[] required_libraries;
        public ElectricalData electrical_constraints;
        public SourceData[] sources;
        public VerificationData verification;
    }

    [Serializable]
    public sealed class ComponentData
    {
        public string id;
        public string part_id;
        public int qty;
        public string placement;
        public Vector3 position_m;
    }

    [Serializable]
    public sealed class ConnectionData
    {
        public string id;
        public string from;
        public string to;
        public string kind;
        public string color;
    }

    [Serializable]
    public sealed class AssemblyStepData
    {
        public int step;
        public string[] connection_ids;
        public string instruction_ar;
    }

    [Serializable]
    public sealed class LibraryData
    {
        public string name;
        public string version;
    }

    [Serializable]
    public sealed class ElectricalData
    {
        public string supply_notes_ar;
        public string[] warnings_ar;
    }

    [Serializable]
    public sealed class SourceData
    {
        public string url;
        public string purpose;
        public string accessed_on;
    }

    [Serializable]
    public sealed class VerificationData
    {
        public string status;
        public bool schema_valid;
        public bool pin_reviewed;
        public bool power_reviewed;
        public bool code_compiled;
        public bool hardware_tested;
        public bool ar_layout_reviewed;
    }
}
