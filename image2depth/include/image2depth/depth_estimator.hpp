#ifndef IMAGE2DEPTH_DEPTH_ESTIMATOR_HPP
#define IMAGE2DEPTH_DEPTH_ESTIMATOR_HPP

#include <opencv2/opencv.hpp>
#include <opencv2/dnn.hpp>
#include <string>
#include <memory>
#include <chrono>

namespace image2depth
{

/**
 * @brief Configuration for depth estimation
 */
struct DepthEstimatorConfig
{
    // Model file path (ONNX format)
    std::string model_path;
    
    // Input image size for the model
    int input_width = 384;
    int input_height = 384;
    
    // Whether to normalize depth output to 0-255 range
    bool normalize_output = true;
    
    // Backend for inference (OpenCV DNN or ONNX Runtime)
    enum class Backend {
        OPENCV_DNN,
        ONNXRUNTIME
    } backend = Backend::OPENCV_DNN;
    
    // Use GPU if available
    bool use_gpu = false;
    
    // Apply bilateral filter for smoother results
    bool apply_bilateral_filter = false;
    
    // Print performance metrics
    bool verbose = true;
    
    // Auto-scale large input images/videos before processing
    // Set to 0 to disable, or specify max dimension (e.g., 1280)
    // This improves performance for high-resolution inputs
    int max_input_dimension = 1280;
};

/**
 * @brief Depth estimation class using MiDaS or similar monocular depth models
 * 
 * This class provides real-time depth estimation from RGB images, optimized
 * for running on Steam Deck hardware (~10 FPS target).
 */
class DepthEstimator
{
public:
    /**
     * @brief Constructor
     * @param config Configuration parameters
     */
    explicit DepthEstimator(const DepthEstimatorConfig& config);
    
    /**
     * @brief Destructor
     */
    ~DepthEstimator();
    
    /**
     * @brief Initialize the depth estimator and load model
     * @return true if initialization successful, false otherwise
     */
    bool initialize();
    
    /**
     * @brief Estimate depth from an input image
     * @param input_image Input BGR image
     * @param depth_map Output depth map (single channel, float or uint8)
     * @return true if estimation successful, false otherwise
     */
    bool estimateDepth(const cv::Mat& input_image, cv::Mat& depth_map);
    
    /**
     * @brief Get the last inference time in milliseconds
     * @return Inference time in ms
     */
    double getLastInferenceTime() const { return last_inference_time_ms_; }
    
    /**
     * @brief Get the current FPS
     * @return Frames per second
     */
    double getCurrentFPS() const { return current_fps_; }
    
    /**
     * @brief Check if the estimator is initialized
     * @return true if initialized
     */
    bool isInitialized() const { return initialized_; }

private:
    /**
     * @brief Preprocess input image for model inference
     */
    cv::Mat preprocessImage(const cv::Mat& input_image);
    
    /**
     * @brief Postprocess model output to create depth map
     */
    cv::Mat postprocessOutput(const cv::Mat& model_output, 
                              const cv::Size& original_size);
    
    /**
     * @brief Update FPS calculation
     */
    void updateFPS();

    // Configuration
    DepthEstimatorConfig config_;
    
    // Model (using OpenCV DNN backend)
    cv::dnn::Net net_;
    
    // Note: ONNX Runtime backend is not yet implemented
    // When implemented, it will provide 20-30% performance improvement
    
    // State
    bool initialized_;
    double last_inference_time_ms_;
    double current_fps_;
    
    // FPS calculation
    std::chrono::steady_clock::time_point last_time_;
    int frame_count_;
    double fps_update_interval_;
};

/**
 * @brief Helper function to download MiDaS small model if not present
 * @param model_path Path where model should be stored
 * @return true if model is available, false otherwise
 */
bool ensureModelAvailable(const std::string& model_path);

/**
 * @brief Get default model path
 * @return Default path for MiDaS small ONNX model
 */
std::string getDefaultModelPath();

} // namespace image2depth

#endif // IMAGE2DEPTH_DEPTH_ESTIMATOR_HPP
