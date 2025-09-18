#ifndef STEAM_DECK_HANDLER_HPP
#define STEAM_DECK_HANDLER_HPP

#include <memory>
#include <string>
#include <chrono>
#include <thread>
#include <atomic>
#include <mutex>
#include <map>
#include <vector>
#include <functional>
#include <cmath>

#include <QObject>
#include <QTimer>
#include <QThread>
#include <QMutex>
#include <QMutexLocker>

// HID library for Linux
#include <hidapi/hidapi.h>

namespace paint_controller {

struct StickData {
    float x = 0.0f;
    float y = 0.0f;
};

struct TriggerData {
    float left = 0.0f;
    float right = 0.0f;
};

struct ButtonData {
    bool up = false;
    bool down = false;
    bool left = false;
    bool right = false;
    bool a = false;
    bool b = false;
    bool x = false;
    bool y = false;
    bool l1 = false;
    bool r1 = false;
    bool l4 = false;
    bool r4 = false;
    bool l5 = false;
    bool r5 = false;
    bool l3 = false;
    bool menu = false;
    bool switch_btn = false;  // 'switch' is a C++ keyword, so using switch_btn
    bool steam = false;
    bool dot = false;
};

struct ImuData {
    float pitch = 0.0f;
    float roll = 0.0f;
    float yaw = 0.0f;
};

struct SteamDeckInputState {
    StickData left_stick;
    StickData right_stick;
    TriggerData triggers;
    ButtonData buttons;
    ImuData imu;
};

struct ButtonTiming {
    std::chrono::steady_clock::time_point start_time;
    std::chrono::steady_clock::time_point last_trigger_time;
};

struct HoldCallback {
    std::function<void(float)> callback;
    float duration;
    bool update_during_hold;
    float update_interval;
    std::chrono::steady_clock::time_point last_update_time;
    int callback_id;
};

class SteamDeckReaderThread : public QThread {
    Q_OBJECT

public:
    explicit SteamDeckReaderThread(QObject* parent = nullptr);
    ~SteamDeckReaderThread();
    
    void set_device(hid_device* device);
    void stop();

protected:
    void run() override;

signals:
    void data_read(const QByteArray& data);

private:
    std::atomic<bool> stop_requested_;
    hid_device* device_;
    QMutex mutex_;
};

class SteamDeckHandler : public QObject {
    Q_OBJECT

public:
    explicit SteamDeckHandler(float deadzone = 0.1f, 
                            float smoothing_factor = 0.1f, 
                            float default_debounce_time = 0.15f,
                            QObject* parent = nullptr);
    ~SteamDeckHandler();

    // Control methods
    bool start();
    void stop();
    
    // State access methods
    SteamDeckInputState get_current_state() const;
    bool has_new_input() const;
    bool is_available() const { return available_; }
    
    // Individual component getters
    StickData get_left_stick() const;
    StickData get_right_stick() const;
    TriggerData get_triggers() const;
    ButtonData get_buttons() const;
    ImuData get_imu() const;
    
    // Button press detection (edge detection with debouncing)
    bool get_button_pressed(const std::string& button) const;
    std::map<std::string, bool> get_all_pressed_buttons() const;
    float get_button_hold_duration(const std::string& button) const;
    
    // Configuration methods
    void set_debounce_time(const std::string& button, float debounce_time);
    void set_default_debounce_time(float debounce_time);
    void set_all_debounce_times(float debounce_time);
    float get_debounce_time(const std::string& button) const;
    float get_default_debounce_time() const;
    std::map<std::string, float> get_all_debounce_times() const;
    
    // Callback registration
    bool register_button_callback(const std::string& button, std::function<void()> callback);
    bool unregister_button_callback(const std::string& button, std::function<void()> callback);
    bool register_button_hold_callback(const std::string& button, 
                                     float hold_duration, 
                                     std::function<void(float)> callback,
                                     bool update_during_hold = false,
                                     float update_interval = 0.1f);
    bool unregister_button_hold_callback(const std::string& button, std::function<void(float)> callback);

signals:
    void input_state_changed(const SteamDeckInputState& state);
    void left_stick_changed();
    void right_stick_changed();
    void triggers_changed();
    void buttons_changed();
    void imu_changed();
    void connection_status_changed(bool connected);
    void button_held(const QString& button, float duration);
    void button_hold_progress(const QString& button, float current_duration, float target_duration);

private slots:
    void process_input(const QByteArray& data);
    void check_availability();

private:
    // Configuration
    float deadzone_;
    float smoothing_factor_;
    float default_debounce_time_;
    
    // Device management
    hid_device* device_;
    std::unique_ptr<SteamDeckReaderThread> reader_thread_;
    
    // State management
    mutable QMutex state_mutex_;
    SteamDeckInputState input_state_;
    SteamDeckInputState prev_input_state_;
    StickData prev_stick_values_[2];  // 0=left, 1=right
    
    // Connection status
    std::atomic<bool> available_;
    std::chrono::steady_clock::time_point last_input_time_;
    float connection_timeout_;
    QTimer* availability_timer_;
    
    // Button processing
    std::map<std::string, bool> button_pressed_;
    std::map<std::string, ButtonTiming> button_state_timing_;
    std::map<std::string, float> debounce_times_;
    
    // Callback system
    std::map<std::string, std::vector<std::function<void()>>> button_callbacks_;
    std::map<std::string, std::vector<HoldCallback>> button_hold_callbacks_;
    std::map<std::string, std::map<int, bool>> button_hold_triggered_;
    
    // Internal processing methods
    StickData process_stick(float x, float y, int stick_id);
    float scale_deadzone(float magnitude) const;
    float apply_smoothing(float current, float previous) const;
    void update_button_states_and_timing();
    void emit_change_signals();
    
    // Button name validation
    bool is_valid_button(const std::string& button) const;
    
    // Constants
    static constexpr uint16_t VALVE_VID = 0x28DE;
    static constexpr uint16_t STEAM_DECK_PID = 0x1205;
    static constexpr int INTERFACE_NUMBER = 2;
    
public:
    static constexpr int HID_BUFFER_SIZE = 64;
};

} // namespace paint_controller

#endif // STEAM_DECK_HANDLER_HPP
