#include <rclcpp/rclcpp.hpp>
#include <sensor_msgs/msg/image.hpp>
#include <cv_bridge/cv_bridge.h>
#include "image2depth/depth_estimator.hpp"

class DepthEstimationNode : public rclcpp::Node
{
public:
    DepthEstimationNode()
        : Node("depth_estimation_node")
    {
        // Declare parameters
        this->declare_parameter<std::string>("model_path", 
            std::string(getenv("HOME") ? getenv("HOME") : ".") + 
            "/.local/share/image2depth/models/midas_small.onnx");
        this->declare_parameter<int>("input_width", 384);
        this->declare_parameter<int>("input_height", 384);
        this->declare_parameter<bool>("normalize_output", true);
        this->declare_parameter<bool>("use_gpu", false);
        this->declare_parameter<bool>("apply_bilateral_filter", false);
        this->declare_parameter<bool>("verbose", true);
        this->declare_parameter<std::string>("input_topic", "/camera/image_raw");
        this->declare_parameter<std::string>("output_topic", "/depth/image");
        
        // Get parameters
        std::string model_path = this->get_parameter("model_path").as_string();
        int input_width = this->get_parameter("input_width").as_int();
        int input_height = this->get_parameter("input_height").as_int();
        bool normalize_output = this->get_parameter("normalize_output").as_bool();
        bool use_gpu = this->get_parameter("use_gpu").as_bool();
        bool apply_bilateral_filter = this->get_parameter("apply_bilateral_filter").as_bool();
        bool verbose = this->get_parameter("verbose").as_bool();
        std::string input_topic = this->get_parameter("input_topic").as_string();
        std::string output_topic = this->get_parameter("output_topic").as_string();
        
        // Configure depth estimator
        image2depth::DepthEstimatorConfig config;
        config.model_path = model_path;
        config.input_width = input_width;
        config.input_height = input_height;
        config.normalize_output = normalize_output;
        config.use_gpu = use_gpu;
        config.apply_bilateral_filter = apply_bilateral_filter;
        config.verbose = verbose;
        
        // Initialize depth estimator
        depth_estimator_ = std::make_unique<image2depth::DepthEstimator>(config);
        
        if (!depth_estimator_->initialize()) {
            RCLCPP_ERROR(this->get_logger(), "Failed to initialize depth estimator");
            rclcpp::shutdown();
            return;
        }
        
        RCLCPP_INFO(this->get_logger(), "Depth estimator initialized successfully");
        
        // Create subscriber
        image_subscription_ = this->create_subscription<sensor_msgs::msg::Image>(
            input_topic, 10,
            std::bind(&DepthEstimationNode::imageCallback, this, std::placeholders::_1));
        
        // Create publisher
        depth_publisher_ = this->create_publisher<sensor_msgs::msg::Image>(output_topic, 10);
        
        RCLCPP_INFO(this->get_logger(), "Depth estimation node started");
        RCLCPP_INFO(this->get_logger(), "  Input topic: %s", input_topic.c_str());
        RCLCPP_INFO(this->get_logger(), "  Output topic: %s", output_topic.c_str());
    }

private:
    void imageCallback(const sensor_msgs::msg::Image::SharedPtr msg)
    {
        try {
            // Convert ROS image to OpenCV
            cv_bridge::CvImagePtr cv_ptr = cv_bridge::toCvCopy(msg, sensor_msgs::image_encodings::BGR8);
            
            // Estimate depth
            cv::Mat depth_map;
            if (!depth_estimator_->estimateDepth(cv_ptr->image, depth_map)) {
                RCLCPP_ERROR(this->get_logger(), "Failed to estimate depth");
                return;
            }
            
            // Convert depth map to ROS message
            cv_bridge::CvImage depth_msg;
            depth_msg.header = msg->header;
            depth_msg.encoding = depth_map.type() == CV_8U ? 
                sensor_msgs::image_encodings::MONO8 : 
                sensor_msgs::image_encodings::TYPE_32FC1;
            depth_msg.image = depth_map;
            
            // Publish depth map
            depth_publisher_->publish(*depth_msg.toImageMsg());
            
            // Log performance occasionally
            static int count = 0;
            if (++count % 30 == 0) {
                RCLCPP_INFO(this->get_logger(), 
                    "FPS: %.2f, Inference time: %.2f ms",
                    depth_estimator_->getCurrentFPS(),
                    depth_estimator_->getLastInferenceTime());
            }
            
        } catch (cv_bridge::Exception& e) {
            RCLCPP_ERROR(this->get_logger(), "cv_bridge exception: %s", e.what());
        } catch (const std::exception& e) {
            RCLCPP_ERROR(this->get_logger(), "Exception: %s", e.what());
        }
    }
    
    std::unique_ptr<image2depth::DepthEstimator> depth_estimator_;
    rclcpp::Subscription<sensor_msgs::msg::Image>::SharedPtr image_subscription_;
    rclcpp::Publisher<sensor_msgs::msg::Image>::SharedPtr depth_publisher_;
};

int main(int argc, char** argv)
{
    rclcpp::init(argc, argv);
    auto node = std::make_shared<DepthEstimationNode>();
    rclcpp::spin(node);
    rclcpp::shutdown();
    return 0;
}
