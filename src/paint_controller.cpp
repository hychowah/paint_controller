#include "paint_controller/paint_controller.hpp"

#include <iostream>
#include <fstream>
#include <csignal>
#include <QDir>
#include <QQmlContext>
#include <QMetaObject>
#include <QQmlProperty>
#include <QMutexLocker>

namespace paint_controller {

// ConfigLoader implementation
RobotConfig ConfigLoader::load_config(const std::string& config_path) {
    RobotConfig config;
    // For now, return default config. You can implement YAML parsing later
    std::cout << "Loading config from: " << config_path << std::endl;
    std::cout << "Using default configuration for now" << std::endl;
    return config;
}

// ImageProvider implementation
ImageProvider::ImageProvider() 
    : QQuickImageProvider(QQuickImageProvider::Image)
    , image_(640, 480, QImage::Format_RGB888) {
    image_.fill(Qt::black);
}

QImage ImageProvider::requestImage(const QString& id, QSize* size, const QSize& requestedSize) {
    Q_UNUSED(id)
    Q_UNUSED(requestedSize)
    
    QMutexLocker lock(&image_mutex_);
    if (size) {
        *size = image_.size();
    }
    return image_;
}

void ImageProvider::updateImage(const QImage& new_image) {
    QMutexLocker lock(&image_mutex_);
    image_ = new_image.copy();
}

// VideoStream implementation
VideoStream::VideoStream(int port) : pipeline_(nullptr), sink_(nullptr) {
    gst_init(nullptr, nullptr);
    
    std::string pipeline_str = 
        "udpsrc port=" + std::to_string(port) + 
        " caps=\"application/x-rtp, media=(string)video, "
        "clock-rate=(int)90000, encoding-name=(string)H264, payload=(int)96\" "
        "! rtph264depay ! avdec_h264 ! videoconvert ! video/x-raw,format=RGB ! appsink name=sink";
    
    pipeline_ = gst_parse_launch(pipeline_str.c_str(), nullptr);
    if (!pipeline_) {
        std::cerr << "Failed to create GStreamer pipeline" << std::endl;
        return;
    }
    
    sink_ = gst_bin_get_by_name(GST_BIN(pipeline_), "sink");
    if (!sink_) {
        std::cerr << "Failed to get sink element" << std::endl;
        return;
    }
    
    g_object_set(sink_, "emit-signals", TRUE, nullptr);
}

VideoStream::~VideoStream() {
    stop();
    if (pipeline_) {
        gst_object_unref(pipeline_);
    }
    if (sink_) {
        gst_object_unref(sink_);
    }
}

void VideoStream::start() {
    if (pipeline_) {
        gst_element_set_state(pipeline_, GST_STATE_PLAYING);
    }
}

void VideoStream::stop() {
    if (pipeline_) {
        gst_element_set_state(pipeline_, GST_STATE_NULL);
    }
}

void VideoStream::connect_new_sample_callback(std::function<void(GstSample*)> callback) {
    callback_ = callback;
    if (sink_) {
        g_signal_connect(sink_, "new-sample", G_CALLBACK(on_new_sample_static), this);
    }
}

GstFlowReturn VideoStream::on_new_sample_static(GstElement* sink, gpointer user_data) {
    auto* video_stream = static_cast<VideoStream*>(user_data);
    return video_stream->on_new_sample(sink);
}

GstFlowReturn VideoStream::on_new_sample(GstElement* sink) {
    GstSample* sample = nullptr;
    g_signal_emit_by_name(sink, "pull-sample", &sample);
    
    if (sample && callback_) {
        callback_(sample);
        gst_sample_unref(sample);
    }
    
    return GST_FLOW_OK;
}

// NetworkMonitor implementation
NetworkMonitor::NetworkMonitor() 
    : ef_signal_strength_(0), base_signal_strength_(0) {
}

void NetworkMonitor::ef_ip_callback(const std_msgs::msg::String::SharedPtr msg) {
    ef_ip_ = msg->data;
}

void NetworkMonitor::ef_signal_strength_callback(const std_msgs::msg::Int32::SharedPtr msg) {
    ef_signal_strength_ = msg->data;
}

void NetworkMonitor::base_ip_callback(const std_msgs::msg::String::SharedPtr msg) {
    base_ip_ = msg->data;
}

void NetworkMonitor::base_signal_strength_callback(const std_msgs::msg::Int32::SharedPtr msg) {
    base_signal_strength_ = msg->data;
}

// RosThread implementation
RosThread::RosThread(std::shared_ptr<rclcpp::Node> node) 
    : node_(node), shutdown_requested_(false), running_(false) {
}

RosThread::~RosThread() {
    request_shutdown();
    wait();
}

void RosThread::request_shutdown() {
    shutdown_requested_ = true;
}

void RosThread::run() {
    try {
        running_ = true;
        emit node_started();
        
        while (!shutdown_requested_ && rclcpp::ok()) {
            rclcpp::spin_some(node_);
            QThread::msleep(10);  // 10ms sleep to prevent excessive CPU usage
        }
        
        running_ = false;
        emit node_stopped();
        
    } catch (const std::exception& e) {
        emit error_occurred(QString::fromStdString(e.what()));
        running_ = false;
    }
}

// RobotController implementation
RobotController::RobotController(const RobotConfig& config) 
    : rclcpp::Node("robot_controller")
    , config_(config)
    , current_status_(HeartbeatStatus::IDLE)
    , control_mode_("base")
    , status_timer_(new QTimer(this))
    , heartbeat_timer_(new QTimer(this))
    , engine_(nullptr) {
    
    // Initialize GStreamer
    gst_init(nullptr, nullptr);
    
    // Setup image provider
    ef_image_provider_ = std::make_unique<ImageProvider>();
    
    // Setup GStreamer pipeline for end-effector video
    setup_gstreamer();
    
    // Setup ROS publishers and subscribers
    setup_subscribers();
    heartbeat_pub_ = this->create_publisher<std_msgs::msg::UInt8>("/controller/heartbeat", 10);
    
    // Setup timers
    connect(status_timer_, &QTimer::timeout, this, &RobotController::timer_callback);
    connect(heartbeat_timer_, &QTimer::timeout, this, &RobotController::publish_heartbeat);
    
    status_timer_->start(static_cast<int>(1000 / config_.update_rate));
    heartbeat_timer_->start(500);  // 0.5 seconds
    
    RCLCPP_INFO(this->get_logger(), "RobotController initialized");
}

RobotController::~RobotController() {
    cleanup();
}

void RobotController::cleanup() {
    if (status_timer_) {
        status_timer_->stop();
    }
    if (heartbeat_timer_) {
        heartbeat_timer_->stop();
    }
    
    if (ef_pipeline_) {
        gst_element_set_state(ef_pipeline_, GST_STATE_NULL);
        gst_object_unref(ef_pipeline_);
        ef_pipeline_ = nullptr;
    }
    
    if (ef_sink_) {
        gst_object_unref(ef_sink_);
        ef_sink_ = nullptr;
    }
}

void RobotController::set_control_mode(const QString& mode) {
    if (control_mode_ != mode.toStdString()) {
        control_mode_ = mode.toStdString();
        emit control_mode_changed(mode);
        RCLCPP_INFO(this->get_logger(), "Control mode changed to: %s", control_mode_.c_str());
    }
}

void RobotController::setup_subscribers() {
    auto ef_ip_sub = this->create_subscription<std_msgs::msg::String>(
        "connection/ef/ip",
        1,
        [this](const std_msgs::msg::String::SharedPtr msg) {
            network_monitor_.ef_ip_callback(msg);
        }
    );
    
    auto ef_signal_sub = this->create_subscription<std_msgs::msg::Int32>(
        "connection/ef/signal_strength",
        1,
        [this](const std_msgs::msg::Int32::SharedPtr msg) {
            network_monitor_.ef_signal_strength_callback(msg);
        }
    );
    
    auto base_ip_sub = this->create_subscription<std_msgs::msg::String>(
        "connection/base/ip",
        1,
        [this](const std_msgs::msg::String::SharedPtr msg) {
            network_monitor_.base_ip_callback(msg);
        }
    );
    
    auto base_signal_sub = this->create_subscription<std_msgs::msg::Int32>(
        "connection/base/signal_strength",
        1,
        [this](const std_msgs::msg::Int32::SharedPtr msg) {
            network_monitor_.base_signal_strength_callback(msg);
        }
    );
}

void RobotController::setup_gstreamer() {
    std::string pipeline_str = 
        "udpsrc port=5001 caps=\"application/x-rtp, media=(string)video, "
        "clock-rate=(int)90000, encoding-name=(string)H264, payload=(int)96\" "
        "! rtph264depay ! avdec_h264 ! videoconvert ! video/x-raw,format=RGB ! appsink name=sink";
    
    ef_pipeline_ = gst_parse_launch(pipeline_str.c_str(), nullptr);
    if (!ef_pipeline_) {
        RCLCPP_ERROR(this->get_logger(), "Failed to create GStreamer pipeline");
        return;
    }
    
    ef_sink_ = gst_bin_get_by_name(GST_BIN(ef_pipeline_), "sink");
    if (!ef_sink_) {
        RCLCPP_ERROR(this->get_logger(), "Failed to get sink element");
        return;
    }
    
    g_object_set(ef_sink_, "emit-signals", TRUE, nullptr);
    g_signal_connect(ef_sink_, "new-sample", G_CALLBACK(on_new_ef_sample_static), this);
    
    gst_element_set_state(ef_pipeline_, GST_STATE_PLAYING);
}

GstFlowReturn RobotController::on_new_ef_sample_static(GstElement* sink, gpointer user_data) {
    auto* controller = static_cast<RobotController*>(user_data);
    GstSample* sample = nullptr;
    g_signal_emit_by_name(sink, "pull-sample", &sample);
    
    if (sample) {
        auto flow = controller->on_new_ef_sample(sample);
        gst_sample_unref(sample);
        return flow;
    }
    return GST_FLOW_OK;
}

GstFlowReturn RobotController::on_new_ef_sample(GstSample* sample) {
    GstBuffer* buffer = gst_sample_get_buffer(sample);
    GstCaps* caps = gst_sample_get_caps(sample);
    
    if (!buffer || !caps) {
        return GST_FLOW_OK;
    }
    
    GstStructure* structure = gst_caps_get_structure(caps, 0);
    gint width, height;
    
    if (!gst_structure_get_int(structure, "width", &width) ||
        !gst_structure_get_int(structure, "height", &height)) {
        return GST_FLOW_OK;
    }
    
    GstMapInfo map_info;
    if (!gst_buffer_map(buffer, &map_info, GST_MAP_READ)) {
        return GST_FLOW_OK;
    }
    
    // Create QImage from buffer data
    QImage ef_image(map_info.data, width, height, width * 3, QImage::Format_RGB888);
    ef_image_provider_->updateImage(ef_image);
    
    gst_buffer_unmap(buffer, &map_info);
    
    emit frame_ready();
    
    return GST_FLOW_OK;
}

void RobotController::timer_callback() {
    // Update network monitor data and emit status update
    emit status_updated();
    
    RCLCPP_DEBUG(this->get_logger(), "Status updated - EF IP: %s, Base IP: %s", 
                network_monitor_.get_ef_ip().c_str(),
                network_monitor_.get_base_ip().c_str());
}

void RobotController::publish_heartbeat() {
    auto msg = std_msgs::msg::UInt8();
    msg.data = static_cast<uint8_t>(current_status_);
    heartbeat_pub_->publish(msg);
}

// Qt Slots implementation
void RobotController::set_left_joystick_control(const QString& control) {
    RCLCPP_INFO(this->get_logger(), "Left joystick control set to: %s", control.toStdString().c_str());
}

void RobotController::set_right_joystick_control(const QString& control) {
    RCLCPP_INFO(this->get_logger(), "Right joystick control set to: %s", control.toStdString().c_str());
}

void RobotController::terminate_nodes() {
    RCLCPP_INFO(this->get_logger(), "Terminating nodes requested");
}

void RobotController::toggle_switch_changed(bool checked) {
    RCLCPP_INFO(this->get_logger(), "Toggle switch changed to: %s", checked ? "true" : "false");
}

void RobotController::toggle_sidebar() {
    if (!engine_) {
        RCLCPP_ERROR(this->get_logger(), "QML engine not available");
        return;
    }
    
    auto root_objects = engine_->rootObjects();
    if (root_objects.empty()) {
        RCLCPP_ERROR(this->get_logger(), "No root QML objects found");
        return;
    }
    
    QObject* root = root_objects[0];
    QObject* select_bar = root->findChild<QObject*>("selectBar");
    
    if (select_bar) {
        QMetaObject::invokeMethod(select_bar, "toggleSidebar");
        RCLCPP_INFO(this->get_logger(), "Toggled sidebar state");
    } else {
        RCLCPP_ERROR(this->get_logger(), "SelectBar not found in QML");
    }
}

void RobotController::show_popup(const QString& title, const QString& message, 
                                const QString& popup_type, int dismiss_delay) {
    if (!engine_) {
        RCLCPP_ERROR(this->get_logger(), "QML engine not available");
        return;
    }
    
    auto root_objects = engine_->rootObjects();
    if (root_objects.empty()) {
        RCLCPP_ERROR(this->get_logger(), "No root QML objects found");
        return;
    }
    
    QObject* root = root_objects[0];
    QObject* popup = root->findChild<QObject*>("messagePopup");
    
    if (popup) {
        QQmlProperty::write(popup, "messageTitle", title);
        QQmlProperty::write(popup, "messageText", message);
        QQmlProperty::write(popup, "messageType", popup_type);
        QQmlProperty::write(popup, "dismissDelay", dismiss_delay);
        QMetaObject::invokeMethod(popup, "open");
        RCLCPP_INFO(this->get_logger(), "Showing %s popup: %s - %s", 
                   popup_type.toStdString().c_str(),
                   title.toStdString().c_str(),
                   message.toStdString().c_str());
    } else {
        RCLCPP_ERROR(this->get_logger(), "Popup not found in QML");
    }
}

} // namespace paint_controller

// Signal handler for Ctrl+C
QApplication* global_app = nullptr;
void handle_sigint(int signum) {
    Q_UNUSED(signum)
    std::cout << "\nCaught Ctrl+C. Quitting application..." << std::endl;
    if (global_app) {
        global_app->quit();
    }
}

int main(int argc, char** argv) {
    // Initialize ROS
    rclcpp::init(argc, argv);
    
    // Load configuration
    auto config = paint_controller::ConfigLoader::load_config("robot_config.yaml");
    
    // Create Qt application
    QApplication app(argc, argv);
    global_app = &app;
    
    // Setup signal handler
    std::signal(SIGINT, handle_sigint);
    
    // Create robot controller
    auto controller = std::make_shared<paint_controller::RobotController>(config);
    
    // Start ROS thread
    paint_controller::RosThread ros_thread(controller);
    ros_thread.start();
    
    // Setup QML engine
    QQmlApplicationEngine engine;
    controller->set_engine(&engine);  // Store engine reference for popup access
    
    // Add image providers
    engine.addImageProvider("ef_live", controller->get_ef_image_provider());
    
    // Load QML interface
    QString qml_path;
    
    // Try to find QML file in installed location first
    QString install_qml_path = "/home/c3spray_deck/ros2_ws/install/paint_controller_ros2/share/paint_controller_ros2/qml/core/MainWindow.qml";
    QString source_qml_path = "/home/c3spray_deck/ros2_ws/src/paint_controller_ros2/paint_controller/qml/core/MainWindow.qml";
    
    if (QFile::exists(install_qml_path)) {
        qml_path = install_qml_path;
    } else if (QFile::exists(source_qml_path)) {
        qml_path = source_qml_path;
    } else {
        // Fallback to relative paths
        QString rel_path1 = QDir::currentPath() + "/paint_controller/qml/core/MainWindow.qml";
        QString rel_path2 = "../../src/paint_controller_ros2/paint_controller/qml/core/MainWindow.qml";
        
        if (QFile::exists(rel_path1)) {
            qml_path = rel_path1;
        } else if (QFile::exists(rel_path2)) {
            qml_path = rel_path2;
        } else {
            std::cerr << "QML file not found in any expected location" << std::endl;
            std::cerr << "Tried: " << install_qml_path.toStdString() << std::endl;
            std::cerr << "Tried: " << source_qml_path.toStdString() << std::endl;
            std::cerr << "Tried: " << rel_path1.toStdString() << std::endl;
            std::cerr << "Tried: " << rel_path2.toStdString() << std::endl;
            return -1;
        }
    }
    
    engine.load(QUrl::fromLocalFile(qml_path));
    
    if (engine.rootObjects().isEmpty()) {
        std::cerr << "Failed to load QML file: " << qml_path.toStdString() << std::endl;
        return -1;
    }
    
    // Set context properties
    engine.rootContext()->setContextProperty("backend", controller.get());
    engine.rootContext()->setContextProperty("baseStreamer", controller.get());
    
    std::cout << "Paint Controller C++ started successfully!" << std::endl;
    std::cout << "Control mode: " << controller->control_mode().toStdString() << std::endl;
    
    // Run application
    int result = 0;
    try {
        result = app.exec();
    } catch (const std::exception& e) {
        std::cerr << "Application error: " << e.what() << std::endl;
        result = -1;
    }
    
    // Cleanup
    controller->cleanup();
    ros_thread.request_shutdown();
    ros_thread.wait();
    rclcpp::shutdown();
    
    return result;
}
