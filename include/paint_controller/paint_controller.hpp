#ifndef PAINT_CONTROLLER_HPP
#define PAINT_CONTROLLER_HPP

#include <memory>
#include <string>
#include <chrono>

#include <rclcpp/rclcpp.hpp>
#include <std_msgs/msg/float64.hpp>
#include <std_msgs/msg/bool.hpp>
#include <std_msgs/msg/float32.hpp>
#include <std_msgs/msg/int32.hpp>
#include <std_msgs/msg/string.hpp>
#include <std_msgs/msg/u_int8.hpp>
#include <sensor_msgs/msg/laser_scan.hpp>

#include <QApplication>
#include <QObject>
#include <QTimer>
#include <QUrl>
#include <QQmlApplicationEngine>
#include <QQuickImageProvider>
#include <QImage>
#include <QPixmap>
#include <QThread>
#include <QMutex>

#include <gst/gst.h>
#include <gst/app/gstappsink.h>

namespace paint_controller {

enum class HeartbeatStatus : uint8_t {
    IDLE = 0x00,      // System is off or not initialized
    ONTASK = 0x01,    // Normal operation
    WARNING = 0x02,   // Minor issue detected
    ERROR = 0x03      // Critical error
};

struct RobotConfig {
    int video_port = 5000;
    double update_rate = 60.0;  // Hz
    double watchdog_timeout = 1.0;  // seconds
    double joystick_deadzone = 0.1;
    double max_winch_speed = 1500.0;
    int video_width = 640;
    int video_height = 480;
};

class ConfigLoader {
public:
    static RobotConfig load_config(const std::string& config_path);
};

class ImageProvider : public QQuickImageProvider {
public:
    ImageProvider();
    QImage requestImage(const QString& id, QSize* size, const QSize& requestedSize) override;
    void updateImage(const QImage& new_image);

private:
    QImage image_;
    QMutex image_mutex_;
};

class VideoStream {
public:
    VideoStream(int port);
    ~VideoStream();
    
    void start();
    void stop();
    void connect_new_sample_callback(std::function<void(GstSample*)> callback);

private:
    GstElement* pipeline_;
    GstElement* sink_;
    std::function<void(GstSample*)> callback_;
    
    static GstFlowReturn on_new_sample_static(GstElement* sink, gpointer user_data);
    GstFlowReturn on_new_sample(GstElement* sink);
};

class NetworkMonitor {
public:
    NetworkMonitor();
    
    void ef_ip_callback(const std_msgs::msg::String::SharedPtr msg);
    void ef_signal_strength_callback(const std_msgs::msg::Int32::SharedPtr msg);
    void base_ip_callback(const std_msgs::msg::String::SharedPtr msg);
    void base_signal_strength_callback(const std_msgs::msg::Int32::SharedPtr msg);
    
    std::string get_ef_ip() const { return ef_ip_; }
    int get_ef_signal_strength() const { return ef_signal_strength_; }
    std::string get_base_ip() const { return base_ip_; }
    int get_base_signal_strength() const { return base_signal_strength_; }

private:
    std::string ef_ip_;
    int ef_signal_strength_;
    std::string base_ip_;
    int base_signal_strength_;
};

class RosThread : public QThread {
    Q_OBJECT

public:
    RosThread(std::shared_ptr<rclcpp::Node> node);
    ~RosThread();
    
    void request_shutdown();

protected:
    void run() override;

signals:
    void error_occurred(const QString& error);
    void node_started();
    void node_stopped();

private:
    std::shared_ptr<rclcpp::Node> node_;
    std::atomic<bool> shutdown_requested_;
    std::atomic<bool> running_;
};

class RobotController : public QObject, public rclcpp::Node {
    Q_OBJECT
    Q_PROPERTY(QString control_mode READ control_mode WRITE set_control_mode NOTIFY control_mode_changed)

public:
    RobotController(const RobotConfig& config);
    ~RobotController();
    
    void cleanup();
    
    // Public accessors for main function
    void set_engine(QQmlApplicationEngine* engine) { engine_ = engine; }
    ImageProvider* get_ef_image_provider() const { return ef_image_provider_.get(); }
    
    // Property getters/setters
    QString control_mode() const { return QString::fromStdString(control_mode_); }
    void set_control_mode(const QString& mode);

public slots:
    void set_left_joystick_control(const QString& control);
    void set_right_joystick_control(const QString& control);
    void terminate_nodes();
    void toggle_switch_changed(bool checked);
    void toggle_sidebar();
    void show_popup(const QString& title, const QString& message, 
                   const QString& popup_type = "info", int dismiss_delay = 500);

signals:
    void frame_ready();
    void emergency_overlay_changed(bool visible, float current_duration, float target_duration);
    void emergency_triggered();
    void new_scan_data(const QVariantList& ranges, float angle_min, float angle_max, 
                      float angle_increment, float range_max);
    void status_updated();
    void control_mode_changed(const QString& mode);

private slots:
    void timer_callback();
    void publish_heartbeat();

private:
    void setup_subscribers();
    void setup_gstreamer();
    GstFlowReturn on_new_ef_sample(GstSample* sample);
    static GstFlowReturn on_new_ef_sample_static(GstElement* sink, gpointer user_data);
    
    // Configuration
    RobotConfig config_;
    
    // ROS2 components
    rclcpp::Publisher<std_msgs::msg::UInt8>::SharedPtr heartbeat_pub_;
    NetworkMonitor network_monitor_;
    
    // Qt/GStreamer components
    std::unique_ptr<ImageProvider> ef_image_provider_;
    GstElement* ef_pipeline_;
    GstElement* ef_sink_;
    
    // State
    HeartbeatStatus current_status_;
    std::string control_mode_;
    
    // Timers
    QTimer* status_timer_;
    QTimer* heartbeat_timer_;
    
    // Engine reference for QML interaction
    QQmlApplicationEngine* engine_;
};

} // namespace paint_controller

#endif // PAINT_CONTROLLER_HPP
