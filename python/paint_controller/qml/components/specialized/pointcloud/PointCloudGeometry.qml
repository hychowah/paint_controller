import Qt3D.Core
import Qt3D.Render

Geometry {
    property var points: []

    AttributeValue {
        name: "vertexPosition"
        vertexBaseType: AttributeValue.Float
        vertexSize: 3
        count: points.length
        byteOffset: 0
        byteStride: 4 * 4
        buffer: Buffer {
            type: Buffer.VertexBuffer
            data: {
                var array = new Float32Array(points.length * 4);
                for (var i = 0; i < points.length; i++) {
                    array[i * 4 + 0] = points[i].x;
                    array[i * 4 + 1] = points[i].y;
                    array[i * 4 + 2] = points[i].z || 0;
                    array[i * 4 + 3] = points[i].intensity || 0;
                }
                return array;
            }
        }
    }

    AttributeValue {
        name: "intensity"
        vertexBaseType: AttributeValue.Float
        vertexSize: 1
        count: points.length
        byteOffset: 3 * 4
        byteStride: 4 * 4
        buffer: Buffer {
            type: Buffer.VertexBuffer
            data: {
                var array = new Float32Array(points.length * 4);
                for (var i = 0; i < points.length; i++) {
                    array[i * 4 + 3] = points[i].intensity || 0;
                }
                return array;
            }
        }
    }
}