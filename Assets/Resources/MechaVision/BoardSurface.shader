Shader "MechaVision/BoardSurface"
{
    Properties
    {
        _Color ("Color", Color) = (1, 1, 1, 1)
    }
    SubShader
    {
        Tags { "RenderType" = "Opaque" "Queue" = "Geometry" }
        Pass
        {
            CGPROGRAM
            #pragma vertex Vertex
            #pragma fragment Fragment
            #include "UnityCG.cginc"

            fixed4 _Color;

            struct VertexInput
            {
                float4 vertex : POSITION;
                float3 normal : NORMAL;
            };

            struct Interpolators
            {
                float4 vertex : SV_POSITION;
                float3 normal : TEXCOORD0;
            };

            Interpolators Vertex(VertexInput input)
            {
                Interpolators output;
                output.vertex = UnityObjectToClipPos(input.vertex);
                output.normal = UnityObjectToWorldNormal(input.normal);
                return output;
            }

            fixed4 Fragment(Interpolators input) : SV_Target
            {
                float luminance = 0.67 + 0.33 * abs(dot(
                    normalize(input.normal + float3(0, 0.001, 0)),
                    normalize(float3(-0.4, 1, -0.25))));
                return fixed4(_Color.rgb * luminance, 1);
            }
            ENDCG
        }
    }
}
