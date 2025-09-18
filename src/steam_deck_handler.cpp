#include "paint_controller/steam_deck_handler.hpp"
#include <iostream>
#include <cstring>
#include <algorithm>

namespace paint_controller {

// SteamDeckReaderThread implementation
SteamDeckReaderThread::SteamDeckReaderThread(QObject* parent)
    : QThread(parent), stop_requested_(false), device_(nullptr) {
}

SteamDeckReaderThread::~SteamDeckReaderThread() {
    stop();
}

void SteamDeckReaderThread::set_device(hid_device* device) {
    QMutexLocker lock(&mutex_);
    device_ = device;
}

void SteamDeckReaderThread::stop() {
    stop_requested_ = true;
    wait();
}

void SteamDeckReaderThread::run() {
    stop_requested_ = false;
    

    if (!device_) {
        std::cerr << "Error: No HID device set for reader thread" << std::endl;
        return;
    }
    
    unsigned char buffer[SteamDeckHandler::HID_BUFFER_SIZE];
    
    while (!stop_requested_) {
        QMutexLocker lock(&mutex_);
        if (device_) {
            int bytes_read = hid_read_timeout(device_, buffer, SteamDeckHandler::HID_BUFFER_SIZE, 1);
            if (bytes_read > 0) {
                QByteArray data(reinterpret_cast<const char*>(buffer), bytes_read);
                emit data_read(data);
            } else if (bytes_read < 0) {
                std::cerr << "Error reading from Steam Deck HID device" << std::endl;
                QThread::msleep(10);
            }
        }
        lock.unlock();
        
        // Short sleep to prevent tight loop
        QThread::msleep(1);
    }
}

// SteamDeckHandler implementation
SteamDeckHandler::SteamDeckHandler(float deadzone, float smoothing_factor, float default_debounce_time, QObject* parent)
    : QObject(parent)
    , deadzone_(deadzone)
    , smoothing_factor_(std::max(0.0f, std::min(1.0f, smoothing_factor)))
    , default_debounce_time_(default_debounce_time)
    , device_(nullptr)
    , available_(false)
    , connection_timeout_(1.0f)
    , availability_timer_(new QTimer(this)) {
    
    // Initialize HID library
    if (hid_init()) {
        std::cerr << "Failed to initialize HID library" << std::endl;
    }
    
    // Initialize stick values
    prev_stick_values_[0] = {0.0f, 0.0f};
    prev_stick_values_[1] = {0.0f, 0.0f};
    
    // Initialize button names and debounce times
    std::vector<std::string> button_names = {
        "up", "down", "left", "right",
        "a", "b", "x", "y",
        "l1", "r1", "l4", "r4",
        "l5", "r5", "l3",
        "menu", "switch", "steam", "dot"
    };
    
    for (const auto& button : button_names) {
        button_pressed_[button] = false;
        button_state_timing_[button] = {std::chrono::steady_clock::now(), std::chrono::steady_clock::now()};
        debounce_times_[button] = default_debounce_time_;
        button_callbacks_[button] = {};
        button_hold_callbacks_[button] = {};
        button_hold_triggered_[button] = {};
    }
    
    // Initialize reader thread
    reader_thread_ = std::make_unique<SteamDeckReaderThread>(this);
    connect(reader_thread_.get(), &SteamDeckReaderThread::data_read,
            this, &SteamDeckHandler::process_input);
    
    // Setup availability timer
    connect(availability_timer_, &QTimer::timeout, this, &SteamDeckHandler::check_availability);
    availability_timer_->start(200);  // Check every 200ms
    
    last_input_time_ = std::chrono::steady_clock::now();
}

SteamDeckHandler::~SteamDeckHandler() {
    stop();
    hid_exit();
}

bool SteamDeckHandler::start() {
    // Find Steam Deck device
    struct hid_device_info* device_info = hid_enumerate(VALVE_VID, STEAM_DECK_PID);
    struct hid_device_info* target_device = nullptr;
    
    // Look for interface 2 (controller interface)
    for (struct hid_device_info* current = device_info; current != nullptr; current = current->next) {
        if (current->interface_number == INTERFACE_NUMBER) {
            target_device = current;
            break;
        }
    }
    
    if (!target_device) {
        std::cerr << "Error: Steam Deck interface " << INTERFACE_NUMBER << " not found!" << std::endl;
        hid_free_enumeration(device_info);
        return false;
    }
    
    // Open the device
    device_ = hid_open_path(target_device->path);
    hid_free_enumeration(device_info);
    
    if (!device_) {
        std::cerr << "Error: Failed to open Steam Deck HID device" << std::endl;
        return false;
    }
    
    // Set non-blocking mode
    if (hid_set_nonblocking(device_, 1) != 0) {
        std::cerr << "Warning: Failed to set non-blocking mode" << std::endl;
    }
    
    // Start reader thread
    reader_thread_->set_device(device_);
    reader_thread_->start();
    
    available_ = true;
    last_input_time_ = std::chrono::steady_clock::now();
    emit connection_status_changed(true);
    
    std::cout << "Steam Deck HID connection started successfully" << std::endl;
    return true;
}

void SteamDeckHandler::stop() {
    if (reader_thread_ && reader_thread_->isRunning()) {
        reader_thread_->stop();
    }
    
    if (device_) {
        hid_close(device_);
        device_ = nullptr;
    }
    
    available_ = false;
    emit connection_status_changed(false);
    std::cout << "Steam Deck HID connection stopped" << std::endl;
}

bool SteamDeckHandler::is_valid_button(const std::string& button) const {
    return button_pressed_.find(button) != button_pressed_.end();
}

bool SteamDeckHandler::register_button_callback(const std::string& button, std::function<void()> callback) {
    if (!is_valid_button(button)) {
        std::cerr << "Warning: Button '" << button << "' is not a valid button name" << std::endl;
        return false;
    }
    
    QMutexLocker lock(&state_mutex_);
    button_callbacks_[button].push_back(callback);
    return true;
}

bool SteamDeckHandler::unregister_button_callback(const std::string& button, std::function<void()> /* callback */) {
    if (!is_valid_button(button)) {
        std::cerr << "Warning: Button '" << button << "' is not a valid button name" << std::endl;
        return false;
    }
    
    QMutexLocker lock(&state_mutex_);
    // Note: This is simplified - in practice, comparing std::function objects is complex
    // For a production implementation, you might want to use a different approach like IDs
    std::cerr << "Warning: Function comparison for removal not implemented - use clear callbacks instead" << std::endl;
    return false;
}

bool SteamDeckHandler::register_button_hold_callback(const std::string& button, 
                                                   float hold_duration, 
                                                   std::function<void(float)> callback,
                                                   bool update_during_hold,
                                                   float update_interval) {
    if (!is_valid_button(button)) {
        std::cerr << "Warning: Button '" << button << "' is not a valid button name" << std::endl;
        return false;
    }
    
    QMutexLocker lock(&state_mutex_);
    int callback_id = static_cast<int>(button_hold_callbacks_[button].size());
    button_hold_callbacks_[button].push_back({
        callback, hold_duration, update_during_hold, update_interval,
        std::chrono::steady_clock::now(), callback_id
    });
    button_hold_triggered_[button][callback_id] = false;
    
    return true;
}

bool SteamDeckHandler::unregister_button_hold_callback(const std::string& button, std::function<void(float)> /* callback */) {
    if (!is_valid_button(button)) {
        std::cerr << "Warning: Button '" << button << "' is not a valid button name" << std::endl;
        return false;
    }
    
    // Note: Same issue as regular callback removal - function comparison is complex
    std::cerr << "Warning: Function comparison for removal not implemented - use clear callbacks instead" << std::endl;
    return false;
}

void SteamDeckHandler::check_availability() {
    auto current_time = std::chrono::steady_clock::now();
    auto time_since_last_input = std::chrono::duration_cast<std::chrono::milliseconds>(
        current_time - last_input_time_).count() / 1000.0f;
    
    if (time_since_last_input > connection_timeout_) {
        if (available_) {
            available_ = false;
            std::cout << "Steam Deck considered disconnected: " << time_since_last_input << "s since last message" << std::endl;
            emit connection_status_changed(false);
        }
    }
}

void SteamDeckHandler::process_input(const QByteArray& data) {
    if (data.size() < HID_BUFFER_SIZE) {
        return;
    }
    
    // Update the last input time
    last_input_time_ = std::chrono::steady_clock::now();
    
    // Set available status if it wasn't already
    if (!available_) {
        available_ = true;
        emit connection_status_changed(true);
        std::cout << "Steam Deck reconnected" << std::endl;
    }
    
    QMutexLocker lock(&state_mutex_);
    
    // Store previous state for change detection
    prev_input_state_ = input_state_;
    
    const unsigned char* raw_data = reinterpret_cast<const unsigned char*>(data.constData());
    
    // Process byte 8 (first button byte)
    uint8_t button_byte1 = raw_data[8];
    // bool r2_click = (button_byte1 & (1 << 0)) != 0;  // Not used in current implementation
    // bool l2_click = (button_byte1 & (1 << 1)) != 0;  // Not used in current implementation
    bool r1 = (button_byte1 & (1 << 2)) != 0;
    bool l1 = (button_byte1 & (1 << 3)) != 0;
    bool y = (button_byte1 & (1 << 4)) != 0;
    bool b = (button_byte1 & (1 << 5)) != 0;
    bool x = (button_byte1 & (1 << 6)) != 0;
    bool a = (button_byte1 & (1 << 7)) != 0;
    
    // Process byte 9 (second button byte)
    uint8_t button_byte2 = raw_data[9];
    bool dpad_up = (button_byte2 & (1 << 0)) != 0;
    bool dpad_right = (button_byte2 & (1 << 1)) != 0;
    bool dpad_left = (button_byte2 & (1 << 2)) != 0;
    bool dpad_down = (button_byte2 & (1 << 3)) != 0;
    bool switch_btn = (button_byte2 & (1 << 4)) != 0;
    bool steam = (button_byte2 & (1 << 5)) != 0;
    bool menu = (button_byte2 & (1 << 6)) != 0;
    bool l5 = (button_byte2 & (1 << 7)) != 0;
    
    // Process byte 10 (third button byte)
    uint8_t button_byte3 = raw_data[10];
    bool r5 = (button_byte3 & (1 << 0)) != 0;
    // bool left_touchpad_touch = (button_byte3 & (1 << 3)) != 0;  // Not used in current implementation
    // bool right_touchpad_touch = (button_byte3 & (1 << 4)) != 0; // Not used in current implementation
    bool l3 = (button_byte3 & (1 << 6)) != 0;
    
    // Process byte 13 (fourth button byte)
    uint8_t button_byte4 = raw_data[13];
    bool l4 = (button_byte4 & (1 << 1)) != 0;
    bool r4 = (button_byte4 & (1 << 2)) != 0;
    
    // Process byte 14 (fifth button byte)
    uint8_t button_byte5 = raw_data[14];
    bool dot_button = (button_byte5 & (1 << 2)) != 0;
    
    // Process analog inputs (little endian 16-bit signed integers)
    int16_t imu_pitch_raw = static_cast<int16_t>(raw_data[38] | (raw_data[39] << 8));
    int16_t imu_roll_raw = static_cast<int16_t>(raw_data[40] | (raw_data[41] << 8));
    int16_t imu_yaw_raw = static_cast<int16_t>(raw_data[42] | (raw_data[43] << 8));
    int16_t left_trigger_raw = static_cast<int16_t>(raw_data[44] | (raw_data[45] << 8));
    int16_t right_trigger_raw = static_cast<int16_t>(raw_data[46] | (raw_data[47] << 8));
    int16_t left_stick_x_raw = static_cast<int16_t>(raw_data[48] | (raw_data[49] << 8));
    int16_t left_stick_y_raw = static_cast<int16_t>(raw_data[50] | (raw_data[51] << 8));
    int16_t right_stick_x_raw = static_cast<int16_t>(raw_data[52] | (raw_data[53] << 8));
    int16_t right_stick_y_raw = static_cast<int16_t>(raw_data[54] | (raw_data[55] << 8));
    
    // Update the input state
    input_state_.left_stick = process_stick(static_cast<float>(left_stick_x_raw), static_cast<float>(left_stick_y_raw), 0);
    input_state_.right_stick = process_stick(static_cast<float>(right_stick_x_raw), static_cast<float>(right_stick_y_raw), 1);
    
    input_state_.triggers.left = static_cast<float>(left_trigger_raw);
    input_state_.triggers.right = static_cast<float>(right_trigger_raw);
    
    input_state_.buttons.up = dpad_up;
    input_state_.buttons.down = dpad_down;
    input_state_.buttons.left = dpad_left;
    input_state_.buttons.right = dpad_right;
    input_state_.buttons.a = a;
    input_state_.buttons.b = b;
    input_state_.buttons.x = x;
    input_state_.buttons.y = y;
    input_state_.buttons.l1 = l1;
    input_state_.buttons.r1 = r1;
    input_state_.buttons.l4 = l4;
    input_state_.buttons.r4 = r4;
    input_state_.buttons.l5 = l5;
    input_state_.buttons.r5 = r5;
    input_state_.buttons.l3 = l3;
    input_state_.buttons.menu = menu;
    input_state_.buttons.switch_btn = switch_btn;
    input_state_.buttons.steam = steam;
    input_state_.buttons.dot = dot_button;
    
    input_state_.imu.pitch = static_cast<float>(imu_pitch_raw);
    input_state_.imu.roll = static_cast<float>(imu_roll_raw);
    input_state_.imu.yaw = static_cast<float>(imu_yaw_raw);
    
    // Update button timing and states
    update_button_states_and_timing();
    
    // Collect callbacks to execute (to avoid holding mutex during execution)
    std::vector<std::function<void()>> callbacks_to_execute;
    std::vector<std::pair<std::string, HoldCallback*>> hold_callbacks_to_execute;
    std::vector<std::tuple<QString, float, float>> progress_signals_to_emit;
    
    for (const auto& [button, pressed] : button_pressed_) {
        if (pressed) {
            for (const auto& callback : button_callbacks_[button]) {
                callbacks_to_execute.push_back(callback);
            }
        }
    }
    
    // Check hold callbacks
    auto current_time = std::chrono::steady_clock::now();
    for (auto& [button, timing] : button_state_timing_) {
        bool current_state = false;
        
        // Get button states (this is a bit ugly but works for the mapping)
        if (button == "up") { current_state = input_state_.buttons.up; }
        else if (button == "down") { current_state = input_state_.buttons.down; }
        else if (button == "left") { current_state = input_state_.buttons.left; }
        else if (button == "right") { current_state = input_state_.buttons.right; }
        else if (button == "a") { current_state = input_state_.buttons.a; }
        else if (button == "b") { current_state = input_state_.buttons.b; }
        else if (button == "x") { current_state = input_state_.buttons.x; }
        else if (button == "y") { current_state = input_state_.buttons.y; }
        else if (button == "l1") { current_state = input_state_.buttons.l1; }
        else if (button == "r1") { current_state = input_state_.buttons.r1; }
        else if (button == "l4") { current_state = input_state_.buttons.l4; }
        else if (button == "r4") { current_state = input_state_.buttons.r4; }
        else if (button == "l5") { current_state = input_state_.buttons.l5; }
        else if (button == "r5") { current_state = input_state_.buttons.r5; }
        else if (button == "l3") { current_state = input_state_.buttons.l3; }
        else if (button == "menu") { current_state = input_state_.buttons.menu; }
        else if (button == "switch") { current_state = input_state_.buttons.switch_btn; }
        else if (button == "steam") { current_state = input_state_.buttons.steam; }
        else if (button == "dot") { current_state = input_state_.buttons.dot; }
        
        if (current_state) {
            // Button is currently pressed
            auto hold_duration_ms = std::chrono::duration_cast<std::chrono::milliseconds>(current_time - timing.start_time);
            float hold_duration = hold_duration_ms.count() / 1000.0f;
            
            // Check all hold callbacks for this button
            for (auto& hold_callback : button_hold_callbacks_[button]) {
                if (hold_duration >= hold_callback.duration) {
                    // Check if this callback hasn't been triggered yet for this hold session
                    if (!button_hold_triggered_[button][hold_callback.callback_id]) {
                        hold_callbacks_to_execute.push_back({button, &hold_callback});
                        button_hold_triggered_[button][hold_callback.callback_id] = true;
                        // Emit held signal (will be done outside mutex)
                    }
                    
                    // Check for progress updates
                    if (hold_callback.update_during_hold) {
                        auto time_since_last_update_ms = std::chrono::duration_cast<std::chrono::milliseconds>(
                            current_time - hold_callback.last_update_time);
                        float time_since_last_update = time_since_last_update_ms.count() / 1000.0f;
                        
                        if (time_since_last_update >= hold_callback.update_interval) {
                            hold_callbacks_to_execute.push_back({button, &hold_callback});
                            hold_callback.last_update_time = current_time;
                        }
                    }
                }
                
                // Emit progress signal for UI updates
                if (hold_callback.update_during_hold || !button_hold_triggered_[button][hold_callback.callback_id]) {
                    progress_signals_to_emit.push_back({QString::fromStdString(button), hold_duration, hold_callback.duration});
                }
            }
        }
    }
    
    lock.unlock();
    
    // Execute callbacks outside the mutex lock
    for (const auto& callback : callbacks_to_execute) {
        try {
            callback();
        } catch (const std::exception& e) {
            std::cerr << "Error in button callback: " << e.what() << std::endl;
        }
    }
    
    for (const auto& [button, hold_callback] : hold_callbacks_to_execute) {
        try {
            auto current_time_for_callback = std::chrono::steady_clock::now();
            auto hold_duration_ms = std::chrono::duration_cast<std::chrono::milliseconds>(
                current_time_for_callback - button_state_timing_[button].start_time);
            float duration = hold_duration_ms.count() / 1000.0f;
            hold_callback->callback(duration);
        } catch (const std::exception& e) {
            std::cerr << "Error in hold callback for " << button << ": " << e.what() << std::endl;
        }
    }
    
    // Emit progress signals
    for (const auto& [button, current_duration, target_duration] : progress_signals_to_emit) {
        emit button_hold_progress(button, current_duration, target_duration);
    }
    
    // Emit held signals
    for (const auto& [button, hold_callback] : hold_callbacks_to_execute) {
        auto current_time_for_signal = std::chrono::steady_clock::now();
        auto hold_duration_ms = std::chrono::duration_cast<std::chrono::milliseconds>(
            current_time_for_signal - button_state_timing_[button].start_time);
        float duration = hold_duration_ms.count() / 1000.0f;
        emit button_held(QString::fromStdString(button), duration);
    }
    
    // Emit signals
    emit_change_signals();
}

void SteamDeckHandler::update_button_states_and_timing() {
    auto current_time = std::chrono::steady_clock::now();
    
    for (auto& [button, pressed] : button_pressed_) {
        bool prev_state = false;
        bool current_state = false;
        
        // Get button states (mapping from string to actual button state)
        if (button == "up") { prev_state = prev_input_state_.buttons.up; current_state = input_state_.buttons.up; }
        else if (button == "down") { prev_state = prev_input_state_.buttons.down; current_state = input_state_.buttons.down; }
        else if (button == "left") { prev_state = prev_input_state_.buttons.left; current_state = input_state_.buttons.left; }
        else if (button == "right") { prev_state = prev_input_state_.buttons.right; current_state = input_state_.buttons.right; }
        else if (button == "a") { prev_state = prev_input_state_.buttons.a; current_state = input_state_.buttons.a; }
        else if (button == "b") { prev_state = prev_input_state_.buttons.b; current_state = input_state_.buttons.b; }
        else if (button == "x") { prev_state = prev_input_state_.buttons.x; current_state = input_state_.buttons.x; }
        else if (button == "y") { prev_state = prev_input_state_.buttons.y; current_state = input_state_.buttons.y; }
        else if (button == "l1") { prev_state = prev_input_state_.buttons.l1; current_state = input_state_.buttons.l1; }
        else if (button == "r1") { prev_state = prev_input_state_.buttons.r1; current_state = input_state_.buttons.r1; }
        else if (button == "l4") { prev_state = prev_input_state_.buttons.l4; current_state = input_state_.buttons.l4; }
        else if (button == "r4") { prev_state = prev_input_state_.buttons.r4; current_state = input_state_.buttons.r4; }
        else if (button == "l5") { prev_state = prev_input_state_.buttons.l5; current_state = input_state_.buttons.l5; }
        else if (button == "r5") { prev_state = prev_input_state_.buttons.r5; current_state = input_state_.buttons.r5; }
        else if (button == "l3") { prev_state = prev_input_state_.buttons.l3; current_state = input_state_.buttons.l3; }
        else if (button == "menu") { prev_state = prev_input_state_.buttons.menu; current_state = input_state_.buttons.menu; }
        else if (button == "switch") { prev_state = prev_input_state_.buttons.switch_btn; current_state = input_state_.buttons.switch_btn; }
        else if (button == "steam") { prev_state = prev_input_state_.buttons.steam; current_state = input_state_.buttons.steam; }
        else if (button == "dot") { prev_state = prev_input_state_.buttons.dot; current_state = input_state_.buttons.dot; }
        
        auto& timing = button_state_timing_[button];
        
        if (!prev_state && current_state) {
            // Button just pressed (rising edge)
            // Check debounce
            auto time_since_last_trigger_ms = std::chrono::duration_cast<std::chrono::milliseconds>(
                current_time - timing.last_trigger_time);
            float time_since_last_trigger = time_since_last_trigger_ms.count() / 1000.0f;
            
            if (time_since_last_trigger >= debounce_times_[button]) {
                // Valid press - update all timings
                timing.start_time = current_time;
                timing.last_trigger_time = current_time;
                pressed = true;
                
                // Reset hold triggered states for this button
                for (auto& [callback_id, triggered] : button_hold_triggered_[button]) {
                    triggered = false;
                }
            } else {
                // Debounce - ignore this press
                pressed = false;
            }
        } else if (prev_state && !current_state) {
            // Button just released
            pressed = false;
        } else {
            // No state change
            pressed = false;
        }
    }
}

void SteamDeckHandler::emit_change_signals() {
    emit left_stick_changed();
    emit right_stick_changed();
    emit triggers_changed();
    emit buttons_changed();
    emit imu_changed();
    emit input_state_changed(input_state_);
}

StickData SteamDeckHandler::process_stick(float x, float y, int stick_id) {
    // Normalize inputs to -1.0 to 1.0 range
    x = x / 32768.0f;
    y = y / 32768.0f;
    
    // Calculate magnitude and direction
    float magnitude = std::sqrt(x*x + y*y);
    if (magnitude < deadzone_) {
        prev_stick_values_[stick_id] = {0.0f, 0.0f};
        return {0.0f, 0.0f};
    }
    
    // Calculate normalized direction
    float normalized_x = 0.0f, normalized_y = 0.0f;
    if (magnitude > 0) {
        normalized_x = x / magnitude;
        normalized_y = y / magnitude;
    }
    
    // Apply deadzone scaling
    float scaled_magnitude = scale_deadzone(magnitude);
    
    // Apply the scaled magnitude back to the normalized direction
    float processed_x = normalized_x * scaled_magnitude;
    float processed_y = normalized_y * scaled_magnitude;
    
    // Apply smoothing
    float smoothed_x = apply_smoothing(processed_x, prev_stick_values_[stick_id].x);
    float smoothed_y = apply_smoothing(processed_y, prev_stick_values_[stick_id].y);
    
    // Store current values for next frame
    prev_stick_values_[stick_id] = {smoothed_x, smoothed_y};
    
    return {smoothed_x * 32768.0f, smoothed_y * 32768.0f};
}

float SteamDeckHandler::scale_deadzone(float magnitude) const {
    if (magnitude < deadzone_) {
        return 0.0f;
    }
    
    // Rescale the input from [deadzone, 1.0] to [0.0, 1.0]
    float scaled = (magnitude - deadzone_) / (1.0f - deadzone_);
    return std::min(scaled, 1.0f);  // Clamp to maximum of 1.0
}

float SteamDeckHandler::apply_smoothing(float current, float previous) const {
    return current * smoothing_factor_ + previous * (1.0f - smoothing_factor_);
}

// Getter implementations
SteamDeckInputState SteamDeckHandler::get_current_state() const {
    QMutexLocker lock(&state_mutex_);
    return input_state_;
}

bool SteamDeckHandler::has_new_input() const {
    QMutexLocker lock(&state_mutex_);
    // This is a simplified comparison - in practice you might want to compare specific fields
    return true;  // For now, always assume new input when called
}

StickData SteamDeckHandler::get_left_stick() const {
    QMutexLocker lock(&state_mutex_);
    return input_state_.left_stick;
}

StickData SteamDeckHandler::get_right_stick() const {
    QMutexLocker lock(&state_mutex_);
    return input_state_.right_stick;
}

TriggerData SteamDeckHandler::get_triggers() const {
    QMutexLocker lock(&state_mutex_);
    return input_state_.triggers;
}

ButtonData SteamDeckHandler::get_buttons() const {
    QMutexLocker lock(&state_mutex_);
    return input_state_.buttons;
}

ImuData SteamDeckHandler::get_imu() const {
    QMutexLocker lock(&state_mutex_);
    return input_state_.imu;
}

bool SteamDeckHandler::get_button_pressed(const std::string& button) const {
    QMutexLocker lock(&state_mutex_);
    auto it = button_pressed_.find(button);
    return (it != button_pressed_.end()) ? it->second : false;
}

std::map<std::string, bool> SteamDeckHandler::get_all_pressed_buttons() const {
    QMutexLocker lock(&state_mutex_);
    return button_pressed_;
}

float SteamDeckHandler::get_button_hold_duration(const std::string& button) const {
    QMutexLocker lock(&state_mutex_);
    
    // Get current button state
    bool current_state = false;
    if (button == "up") current_state = input_state_.buttons.up;
    else if (button == "down") current_state = input_state_.buttons.down;
    else if (button == "left") current_state = input_state_.buttons.left;
    else if (button == "right") current_state = input_state_.buttons.right;
    else if (button == "a") current_state = input_state_.buttons.a;
    else if (button == "b") current_state = input_state_.buttons.b;
    else if (button == "x") current_state = input_state_.buttons.x;
    else if (button == "y") current_state = input_state_.buttons.y;
    else if (button == "l1") current_state = input_state_.buttons.l1;
    else if (button == "r1") current_state = input_state_.buttons.r1;
    else if (button == "l4") current_state = input_state_.buttons.l4;
    else if (button == "r4") current_state = input_state_.buttons.r4;
    else if (button == "l5") current_state = input_state_.buttons.l5;
    else if (button == "r5") current_state = input_state_.buttons.r5;
    else if (button == "l3") current_state = input_state_.buttons.l3;
    else if (button == "menu") current_state = input_state_.buttons.menu;
    else if (button == "switch") current_state = input_state_.buttons.switch_btn;
    else if (button == "steam") current_state = input_state_.buttons.steam;
    else if (button == "dot") current_state = input_state_.buttons.dot;
    
    if (current_state) {
        auto current_time = std::chrono::steady_clock::now();
        auto it = button_state_timing_.find(button);
        if (it != button_state_timing_.end()) {
            auto duration_ms = std::chrono::duration_cast<std::chrono::milliseconds>(
                current_time - it->second.start_time);
            return duration_ms.count() / 1000.0f;
        }
    }
    return 0.0f;
}

// Configuration method implementations
void SteamDeckHandler::set_debounce_time(const std::string& button, float debounce_time) {
    QMutexLocker lock(&state_mutex_);
    if (is_valid_button(button)) {
        debounce_times_[button] = std::max(0.0f, debounce_time);
    } else {
        std::cerr << "Warning: Button '" << button << "' not found when setting debounce time" << std::endl;
    }
}

void SteamDeckHandler::set_default_debounce_time(float debounce_time) {
    QMutexLocker lock(&state_mutex_);
    default_debounce_time_ = std::max(0.0f, debounce_time);
}

void SteamDeckHandler::set_all_debounce_times(float debounce_time) {
    float safe_debounce_time = std::max(0.0f, debounce_time);
    QMutexLocker lock(&state_mutex_);
    for (auto& [button, time] : debounce_times_) {
        time = safe_debounce_time;
    }
}

float SteamDeckHandler::get_debounce_time(const std::string& button) const {
    QMutexLocker lock(&state_mutex_);
    if (is_valid_button(button)) {
        auto it = debounce_times_.find(button);
        return (it != debounce_times_.end()) ? it->second : default_debounce_time_;
    } else {
        std::cerr << "Warning: Button '" << button << "' not found when getting debounce time" << std::endl;
        return default_debounce_time_;
    }
}

float SteamDeckHandler::get_default_debounce_time() const {
    QMutexLocker lock(&state_mutex_);
    return default_debounce_time_;
}

std::map<std::string, float> SteamDeckHandler::get_all_debounce_times() const {
    QMutexLocker lock(&state_mutex_);
    return debounce_times_;
}

} // namespace paint_controller
