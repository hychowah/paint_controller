import Qt3D.Core 2.15
import Qt3D.Render 2.15

Effect {
    property real pointSize: 5.0
    property color baseColor: "#00FF00"

    techniques: [
        Technique {
            graphicsApiFilter {
                api: GraphicsApiFilter.OpenGL
                profile: GraphicsApiFilter.CoreProfile
                majorVersion: 3
                minorVersion: 2
            }

            renderPasses: [
                RenderPass {
                    shaderProgram: ShaderProgram {
                        vertexShaderCode: "
                            #version 330
                            in vec3 vertexPosition;
                            in float intensity;
                            uniform mat4 modelViewProjection;
                            uniform float pointSize;
                            out float vs_intensity;

                            void main() {
                                gl_Position = modelViewProjection * vec4(vertexPosition, 1.0);
                                gl_PointSize = pointSize;
                                vs_intensity = intensity;
                            }
                        "

                        fragmentShaderCode: "
                            #version 330
                            in float vs_intensity;
                            uniform vec3 baseColor;
                            out vec4 fragColor;

                            void main() {
                                vec2 coords = gl_PointCoord * 2.0 - 1.0;
                                float r = dot(coords, coords);
                                if (r > 1.0) discard;
                                
                                // Modify color based on intensity
                                vec3 color = mix(baseColor, vec3(1.0), vs_intensity);
                                fragColor = vec4(color, 1.0);
                            }
                        "
                    }

                    parameters: [
                        Parameter { name: "pointSize"; value: pointSize },
                        Parameter { name: "baseColor"; value: Qt.vector3d(baseColor.r, baseColor.g, baseColor.b) }
                    ]
                }
            ]
        }
    ]
}