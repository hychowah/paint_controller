#include "image2depth/depth_estimator.hpp"
#include <iostream>
#include <fstream>
#include <sys/stat.h>

namespace image2depth
{

DepthEstimator::DepthEstimator(const DepthEstimatorConfig& config)
    : config_(config)
    , initialized_(false)
    , last_inference_time_ms_(0.0)
    , current_fps_(0.0)
    , frame_count_(0)
    , fps_update_interval_(1.0)
#ifdef USE_ONNXRUNTIME
    , ort_session_(nullptr)
    , ort_env_(nullptr)
#endif
{
}

DepthEstimator::~DepthEstimator()
{
#ifdef USE_ONNXRUNTIME
    // Clean up ONNX Runtime resources if used
    // TODO: Implement ONNX Runtime cleanup
#endif
}

bool DepthEstimator::initialize()
{
    if (initialized_) {
        std::cerr << "DepthEstimator already initialized" << std::endl;
        return true;
    }
    
    // Check if model file exists
    struct stat buffer;
    if (stat(config_.model_path.c_str(), &buffer) != 0) {
        std::cerr << "Model file not found: " << config_.model_path << std::endl;
        std::cerr << "Please download a depth estimation model (e.g., MiDaS small)" << std::endl;
        return false;
    }
    
    try {
        // Load model using OpenCV DNN (works with ONNX models)
        if (config_.backend == DepthEstimatorConfig::Backend::OPENCV_DNN) {
            net_ = cv::dnn::readNetFromONNX(config_.model_path);
            
            if (net_.empty()) {
                std::cerr << "Failed to load model from: " << config_.model_path << std::endl;
                return false;
            }
            
            // Set backend and target
            if (config_.use_gpu) {
                net_.setPreferableBackend(cv::dnn::DNN_BACKEND_CUDA);
                net_.setPreferableTarget(cv::dnn::DNN_TARGET_CUDA);
                if (config_.verbose) {
                    std::cout << "Using CUDA backend for inference" << std::endl;
                }
            } else {
                net_.setPreferableBackend(cv::dnn::DNN_BACKEND_OPENCV);
                net_.setPreferableTarget(cv::dnn::DNN_TARGET_CPU);
                if (config_.verbose) {
                    std::cout << "Using CPU backend for inference" << std::endl;
                }
            }
            
            if (config_.verbose) {
                std::cout << "Model loaded successfully from: " << config_.model_path << std::endl;
                std::cout << "Input size: " << config_.input_width << "x" << config_.input_height << std::endl;
            }
        }
#ifdef USE_ONNXRUNTIME
        else if (config_.backend == DepthEstimatorConfig::Backend::ONNXRUNTIME) {
            // TODO: Initialize ONNX Runtime
            // This would provide better performance on Steam Deck
            std::cerr << "ONNX Runtime backend not yet implemented" << std::endl;
            return false;
        }
#endif
        
        initialized_ = true;
        last_time_ = std::chrono::steady_clock::now();
        
        return true;
        
    } catch (const cv::Exception& e) {
        std::cerr << "OpenCV exception during initialization: " << e.what() << std::endl;
        return false;
    } catch (const std::exception& e) {
        std::cerr << "Exception during initialization: " << e.what() << std::endl;
        return false;
    }
}

cv::Mat DepthEstimator::preprocessImage(const cv::Mat& input_image)
{
    cv::Mat preprocessed;
    
    // Resize to model input size
    cv::resize(input_image, preprocessed, 
               cv::Size(config_.input_width, config_.input_height));
    
    // Convert BGR to RGB (most models expect RGB)
    cv::cvtColor(preprocessed, preprocessed, cv::COLOR_BGR2RGB);
    
    // Convert to float and normalize to [0, 1]
    preprocessed.convertTo(preprocessed, CV_32F, 1.0 / 255.0);
    
    // Create blob (OpenCV DNN format: NCHW)
    cv::Mat blob = cv::dnn::blobFromImage(preprocessed);
    
    return blob;
}

cv::Mat DepthEstimator::postprocessOutput(const cv::Mat& model_output,
                                          const cv::Size& original_size)
{
    cv::Mat depth_map;
    
    // Model output is typically [1, 1, H, W] or [H, W]
    // Extract the 2D depth map
    if (model_output.dims == 4) {
        // Format: [N, C, H, W] - extract [H, W]
        std::vector<cv::Range> ranges = {
            cv::Range(0, 1),  // batch
            cv::Range(0, 1),  // channel
            cv::Range::all(), // height
            cv::Range::all()  // width
        };
        depth_map = model_output(ranges).clone();
        depth_map = depth_map.reshape(1, model_output.size[2]);
    } else if (model_output.dims == 2) {
        depth_map = model_output.clone();
    } else {
        std::cerr << "Unexpected model output dimensions: " << model_output.dims << std::endl;
        return cv::Mat();
    }
    
    // Resize to original image size
    cv::resize(depth_map, depth_map, original_size);
    
    // Apply bilateral filter if configured (smooths depth while preserving edges)
    if (config_.apply_bilateral_filter) {
        cv::Mat filtered;
        cv::bilateralFilter(depth_map, filtered, 5, 50, 50);
        depth_map = filtered;
    }
    
    // Normalize to 0-255 range if configured
    if (config_.normalize_output) {
        double min_val, max_val;
        cv::minMaxLoc(depth_map, &min_val, &max_val);
        
        if (max_val > min_val) {
            depth_map = (depth_map - min_val) / (max_val - min_val) * 255.0;
        }
        
        depth_map.convertTo(depth_map, CV_8U);
    }
    
    return depth_map;
}

bool DepthEstimator::estimateDepth(const cv::Mat& input_image, cv::Mat& depth_map)
{
    if (!initialized_) {
        std::cerr << "DepthEstimator not initialized" << std::endl;
        return false;
    }
    
    if (input_image.empty()) {
        std::cerr << "Input image is empty" << std::endl;
        return false;
    }
    
    auto start_time = std::chrono::steady_clock::now();
    
    try {
        // Preprocess input image
        cv::Mat blob = preprocessImage(input_image);
        
        // Run inference
        if (config_.backend == DepthEstimatorConfig::Backend::OPENCV_DNN) {
            net_.setInput(blob);
            cv::Mat output = net_.forward();
            
            // Postprocess output
            depth_map = postprocessOutput(output, input_image.size());
        }
#ifdef USE_ONNXRUNTIME
        else if (config_.backend == DepthEstimatorConfig::Backend::ONNXRUNTIME) {
            // TODO: ONNX Runtime inference
            std::cerr << "ONNX Runtime inference not yet implemented" << std::endl;
            return false;
        }
#endif
        
        // Calculate inference time
        auto end_time = std::chrono::steady_clock::now();
        last_inference_time_ms_ = 
            std::chrono::duration<double, std::milli>(end_time - start_time).count();
        
        // Update FPS
        updateFPS();
        
        if (config_.verbose && frame_count_ % 30 == 0) {
            std::cout << "Inference time: " << last_inference_time_ms_ << " ms, "
                      << "FPS: " << current_fps_ << std::endl;
        }
        
        return !depth_map.empty();
        
    } catch (const cv::Exception& e) {
        std::cerr << "OpenCV exception during depth estimation: " << e.what() << std::endl;
        return false;
    } catch (const std::exception& e) {
        std::cerr << "Exception during depth estimation: " << e.what() << std::endl;
        return false;
    }
}

void DepthEstimator::updateFPS()
{
    frame_count_++;
    
    auto current_time = std::chrono::steady_clock::now();
    double elapsed = std::chrono::duration<double>(current_time - last_time_).count();
    
    if (elapsed >= fps_update_interval_) {
        current_fps_ = frame_count_ / elapsed;
        frame_count_ = 0;
        last_time_ = current_time;
    }
}

bool ensureModelAvailable(const std::string& model_path)
{
    struct stat buffer;
    return (stat(model_path.c_str(), &buffer) == 0);
}

std::string getDefaultModelPath()
{
    // Default path relative to the package
    return "/tmp/midas_small.onnx";
}

} // namespace image2depth
