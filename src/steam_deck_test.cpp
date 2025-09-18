#include <QApplication>
#include <QTimer>
#include <QDebug>
#include <iostream>
#include <iomanip>
#include <chrono>
#include <thread>

#include "paint_controller/steam_deck_handler.hpp"

class SteamDeckTester : public QObject {
    Q_OBJECT

public:
    SteamDeckTester(QObject* parent = nullptr) : QObject(parent) {
        // Create Steam Deck handler
        handler_ = std::make_unique<paint_controller::SteamDeckHandler>(0.1f, 0.1f, 0.15f, this);
        
        // Connect signals
        connect(handler_.get(), &paint_controller::SteamDeckHandler::connection_status_changed,
                this, &SteamDeckTester::on_connection_status_changed);
        connect(handler_.get(), &paint_controller::SteamDeckHandler::input_state_changed,
                this, &SteamDeckTester::on_input_state_changed);
        connect(handler_.get(), &paint_controller::SteamDeckHandler::button_held,
                this, &SteamDeckTester::on_button_held);
        
        // Register some button callbacks
        handler_->register_button_callback("a", [this]() {
            std::cout << "Button A pressed!" << std::endl;
        });
        
        handler_->register_button_callback("b", [this]() {
            std::cout << "Button B pressed!" << std::endl;
        });
        
        handler_->register_button_callback("x", [this]() {
            std::cout << "Button X pressed!" << std::endl;
        });
        
        handler_->register_button_callback("y", [this]() {
            std::cout << "Button Y pressed!" << std::endl;
        });
        
        // Register hold callback for menu button (hold for 2 seconds)
        handler_->register_button_hold_callback("menu", 2.0f, [this](float duration) {
            std::cout << "Menu button held for " << duration << " seconds!" << std::endl;
        });
        
        // Setup status display timer
        status_timer_ = new QTimer(this);
        connect(status_timer_, &QTimer::timeout, this, &SteamDeckTester::display_status);
        status_timer_->start(100);  // Update every 100ms
        
        // Try to start the handler
        if (handler_->start()) {
            std::cout << "Steam Deck handler started successfully!" << std::endl;
        } else {
            std::cout << "Failed to start Steam Deck handler. Make sure Steam Deck is connected." << std::endl;
        }
    }
    
    ~SteamDeckTester() {
        if (handler_) {
            handler_->stop();
        }
    }

private slots:
    void on_connection_status_changed(bool connected) {
        std::cout << "Steam Deck connection status: " << (connected ? "CONNECTED" : "DISCONNECTED") << std::endl;
    }
    
    void on_input_state_changed(const paint_controller::SteamDeckInputState& state) {
        // Store latest state for display
        latest_state_ = state;
        
        // Check for any pressed buttons and print them
        auto pressed_buttons = handler_->get_all_pressed_buttons();
        for (const auto& [button, pressed] : pressed_buttons) {
            if (pressed) {
                std::cout << "Button pressed: " << button << std::endl;
            }
        }
    }
    
    void on_button_held(const QString& button, float duration) {
        std::cout << "Button " << button.toStdString() << " held for " << duration << " seconds" << std::endl;
    }
    
    void display_status() {
        if (!handler_->is_available()) {
            return;
        }
        
        auto state = handler_->get_current_state();
        
        // Clear screen and display status
        std::cout << "\033[2J\033[H";  // Clear screen and move cursor to top-left
        std::cout << "=== Steam Deck Controller Status ===" << std::endl;
        std::cout << "Connection: " << (handler_->is_available() ? "CONNECTED" : "DISCONNECTED") << std::endl;
        std::cout << std::endl;
        
        // Display stick values
        std::cout << "Left Stick:  X=" << std::setw(8) << std::fixed << std::setprecision(1) 
                  << state.left_stick.x << " Y=" << std::setw(8) << state.left_stick.y << std::endl;
        std::cout << "Right Stick: X=" << std::setw(8) << std::fixed << std::setprecision(1) 
                  << state.right_stick.x << " Y=" << std::setw(8) << state.right_stick.y << std::endl;
        std::cout << std::endl;
        
        // Display trigger values
        std::cout << "Left Trigger:  " << std::setw(8) << std::fixed << std::setprecision(1) 
                  << state.triggers.left << std::endl;
        std::cout << "Right Trigger: " << std::setw(8) << std::fixed << std::setprecision(1) 
                  << state.triggers.right << std::endl;
        std::cout << std::endl;
        
        // Display D-pad
        std::cout << "D-Pad: ";
        if (state.buttons.up) std::cout << "UP ";
        if (state.buttons.down) std::cout << "DOWN ";
        if (state.buttons.left) std::cout << "LEFT ";
        if (state.buttons.right) std::cout << "RIGHT ";
        std::cout << std::endl;
        
        // Display face buttons
        std::cout << "Face Buttons: ";
        if (state.buttons.a) std::cout << "A ";
        if (state.buttons.b) std::cout << "B ";
        if (state.buttons.x) std::cout << "X ";
        if (state.buttons.y) std::cout << "Y ";
        std::cout << std::endl;
        
        // Display shoulder buttons
        std::cout << "Shoulder: ";
        if (state.buttons.l1) std::cout << "L1 ";
        if (state.buttons.r1) std::cout << "R1 ";
        if (state.buttons.l4) std::cout << "L4 ";
        if (state.buttons.r4) std::cout << "R4 ";
        if (state.buttons.l5) std::cout << "L5 ";
        if (state.buttons.r5) std::cout << "R5 ";
        std::cout << std::endl;
        
        // Display other buttons
        std::cout << "Other: ";
        if (state.buttons.l3) std::cout << "L3 ";
        if (state.buttons.menu) std::cout << "MENU ";
        if (state.buttons.switch_btn) std::cout << "SWITCH ";
        if (state.buttons.steam) std::cout << "STEAM ";
        if (state.buttons.dot) std::cout << "DOT ";
        std::cout << std::endl;
        
        // Display IMU values
        std::cout << std::endl;
        std::cout << "IMU: Pitch=" << std::setw(8) << std::fixed << std::setprecision(1) 
                  << state.imu.pitch << " Roll=" << std::setw(8) << state.imu.roll 
                  << " Yaw=" << std::setw(8) << state.imu.yaw << std::endl;
        
        std::cout << std::endl;
        std::cout << "Press Ctrl+C to exit" << std::endl;
        std::cout.flush();
    }

private:
    std::unique_ptr<paint_controller::SteamDeckHandler> handler_;
    QTimer* status_timer_;
    paint_controller::SteamDeckInputState latest_state_;
};

int main(int argc, char* argv[]) {
    QApplication app(argc, argv);
    
    std::cout << "Steam Deck Controller Test Program" << std::endl;
    std::cout << "===================================" << std::endl;
    std::cout << "Make sure your Steam Deck is connected via USB and in desktop mode." << std::endl;
    std::cout << "You may need to run this with sudo if permissions are required." << std::endl;
    std::cout << std::endl;
    
    SteamDeckTester tester;
    
    // Setup signal handler for clean exit
    QTimer::singleShot(0, [&]() {
        std::cout << "Test program started. Monitoring Steam Deck input..." << std::endl;
    });
    
    return app.exec();
}

#include "steam_deck_test.moc"
