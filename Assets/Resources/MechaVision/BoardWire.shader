Shader "MechaVision/BoardWire"
{
    Properties
    {
        [HideInInspector] _WriteDepth ("Write Depth", Float) = 0
    }
    SubShader
    {
        Tags { "RenderType" = "Transparent" "Queue" = "Transparent" }
        Pass
        {
            Cull Off
            ZWrite [_WriteDepth]
            Blend SrcAlpha OneMinusSrcAlpha
            CGPROGRAM
            #pragma vertex Vertex
            #pragma fragment Fragment
            #include "UnityCG.cginc"

            struct VertexInput
            {
                float4 vertex : POSITION;
                fixed4 color : COLOR;
            };

            struct Interpolators
            {
                float4 vertex : SV_POSITION;
                fixed4 color : COLOR;
            };

            Interpolators Vertex(VertexInput input)
            {
                Interpolators output;
                output.vertex = UnityObjectToClipPos(input.vertex);
                output.color = input.color;
                return output;
            }

            fixed4 Fragment(Interpolators input) : SV_Target
            {
                return input.color;
            }
            ENDCG
        }
    }
}
