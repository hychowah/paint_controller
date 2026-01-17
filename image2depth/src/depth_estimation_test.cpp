#include "image2depth/depth_estimator.hpp"
#include <iostream>
#include <opencv2/highgui.hpp>

void printUsage(const char* program_name)
{
    std::cout << "Usage: " << program_name << " --model <path> [--image|--video|--camera] [options]\n"
              << "\nRequired:\n"
              << "  --model <path>        Path to ONNX model file\n"
              << "\nInput Source (choose one):\n"
              << "  --image <path>        Process a single image file\n"
              << "  --video <path>        Process a video file\n"
              << "  --camera <id>         Process camera stream (device ID, e.g., 0)\n"
              << "\nOptional Parameters:\n"
              << "  --width <pixels>      Model input width (default: 384)\n"
              << "  --height <pixels>     Model input height (default: 384)\n"
              << "  --gpu                 Use GPU acceleration if available\n"
              << "  --filter              Apply bilateral filter to output\n"
              << "  --output <path>       Save output to file (image or video)\n"
              << "  --help                Show this help message\n"
              << "\nExamples:\n"
              << "  # Process an image\n"
              << "  " << program_name << " --model midas_small.onnx --image input.jpg\n"
              << "\n  # Process an image and save output\n"
              << "  " << program_name << " --model midas_small.onnx --image input.jpg --output depth.jpg\n"
              << "\n  # Process a video\n"
              << "  " << program_name << " --model midas_small.onnx --video input.mp4 --output depth_output.avi\n"
              << "\n  # Process camera stream\n"
              << "  " << program_name << " --model midas_small.onnx --camera 0\n"
              << "\n  # Use GPU and filtering\n"
              << "  " << program_name << " --model midas_small.onnx --image input.jpg --gpu --filter\n";
}

int main(int argc, char** argv)
{
    // Parse command line arguments
    std::string model_path;
    std::string image_path;
    std::string video_path;
    std::string output_path;
    int camera_id = -1;
    int input_width = 384;
    int input_height = 384;
    bool use_gpu = false;
    bool apply_filter = false;
    
    for (int i = 1; i < argc; ++i) {
        std::string arg = argv[i];
        
        if (arg == "--help" || arg == "-h") {
            printUsage(argv[0]);
            return 0;
        } else if (arg == "--model" && i + 1 < argc) {
            model_path = argv[++i];
        } else if (arg == "--image" && i + 1 < argc) {
            image_path = argv[++i];
        } else if (arg == "--video" && i + 1 < argc) {
            video_path = argv[++i];
        } else if (arg == "--camera" && i + 1 < argc) {
            camera_id = std::stoi(argv[++i]);
        } else if (arg == "--width" && i + 1 < argc) {
            input_width = std::stoi(argv[++i]);
        } else if (arg == "--height" && i + 1 < argc) {
            input_height = std::stoi(argv[++i]);
        } else if (arg == "--gpu") {
            use_gpu = true;
        } else if (arg == "--filter") {
            apply_filter = true;
        } else if (arg == "--output" && i + 1 < argc) {
            output_path = argv[++i];
        }
    }
    
    // Validate arguments
    if (model_path.empty()) {
        std::cerr << "Error: Model path is required\n" << std::endl;
        printUsage(argv[0]);
        return 1;
    }
    
    if (image_path.empty() && video_path.empty() && camera_id < 0) {
        std::cerr << "Error: You must specify one input source:\n"
                  << "       --image <path>   for image files\n"
                  << "       --video <path>   for video files\n"
                  << "       --camera <id>    for camera stream\n" << std::endl;
        printUsage(argv[0]);
        return 1;
    }
    
    // Configure depth estimator
    image2depth::DepthEstimatorConfig config;
    config.model_path = model_path;
    config.input_width = input_width;
    config.input_height = input_height;
    config.normalize_output = true;
    config.use_gpu = use_gpu;
    config.apply_bilateral_filter = apply_filter;
    config.verbose = true;
    
    // Initialize depth estimator
    image2depth::DepthEstimator estimator(config);
    
    if (!estimator.initialize()) {
        std::cerr << "Failed to initialize depth estimator" << std::endl;
        return 1;
    }
    
    std::cout << "Depth estimator initialized successfully" << std::endl;
    
    // Process single image
    if (!image_path.empty()) {
        cv::Mat image = cv::imread(image_path);
        if (image.empty()) {
            std::cerr << "Failed to load image: " << image_path << std::endl;
            return 1;
        }
        
        cv::Mat depth_map;
        if (!estimator.estimateDepth(image, depth_map)) {
            std::cerr << "Failed to estimate depth" << std::endl;
            return 1;
        }
        
        std::cout << "Depth estimation completed in " 
                  << estimator.getLastInferenceTime() << " ms" << std::endl;
        
        // Display results
        cv::imshow("Input Image", image);
        cv::imshow("Depth Map", depth_map);
        
        // Save if output path specified
        if (!output_path.empty()) {
            cv::imwrite(output_path, depth_map);
            std::cout << "Depth map saved to: " << output_path << std::endl;
        }
        
        std::cout << "Press any key to exit..." << std::endl;
        cv::waitKey(0);
    }
    // Process video or camera stream
    else {
        cv::VideoCapture cap;
        
        if (!video_path.empty()) {
            cap.open(video_path);
            if (!cap.isOpened()) {
                std::cerr << "Failed to open video: " << video_path << std::endl;
                return 1;
            }
            std::cout << "Processing video: " << video_path << std::endl;
        } else {
            cap.open(camera_id);
            if (!cap.isOpened()) {
                std::cerr << "Failed to open camera: " << camera_id << std::endl;
                return 1;
            }
            std::cout << "Processing camera stream: " << camera_id << std::endl;
        }
        
        // Setup video writer if output path specified
        cv::VideoWriter writer;
        if (!output_path.empty()) {
            int fourcc = cv::VideoWriter::fourcc('M', 'J', 'P', 'G');
            double fps = cap.get(cv::CAP_PROP_FPS);
            if (fps <= 0) fps = 30.0;
            int width = cap.get(cv::CAP_PROP_FRAME_WIDTH);
            int height = cap.get(cv::CAP_PROP_FRAME_HEIGHT);
            writer.open(output_path, fourcc, fps, cv::Size(width, height), false);
        }
        
        cv::Mat frame, depth_map;
        std::cout << "Press 'q' to quit" << std::endl;
        
        while (true) {
            cap >> frame;
            if (frame.empty()) {
                std::cout << "End of video stream" << std::endl;
                break;
            }
            
            if (!estimator.estimateDepth(frame, depth_map)) {
                std::cerr << "Failed to estimate depth" << std::endl;
                continue;
            }
            
            // Display results
            cv::imshow("Input Frame", frame);
            cv::imshow("Depth Map", depth_map);
            
            // Write to output video if specified
            if (writer.isOpened()) {
                writer.write(depth_map);
            }
            
            // Check for quit key
            int key = cv::waitKey(1);
            if (key == 'q' || key == 'Q' || key == 27) {  // 'q' or ESC
                break;
            }
        }
        
        if (writer.isOpened()) {
            writer.release();
            std::cout << "Output video saved to: " << output_path << std::endl;
        }
    }
    
    cv::destroyAllWindows();
    return 0;
}
