#include "crow.h"

#include "KafkaProducer.h"

#include <cstdlib>
#include <iostream>
#include <string>

int main() {
    const char* env = std::getenv("KAFKA_BOOTSTRAP_SERVERS");
    std::string brokers = env ? env : "kafka:29092";

    KafkaProducer producer(brokers);

    crow::SimpleApp app;

    CROW_ROUTE(app, "/measurements")
        .methods(crow::HTTPMethod::POST)(
            [&producer](const crow::request& req) {
            auto body = crow::json::load(req.body);

            if (!body) {
                return crow::response(400, "Invalid JSON");
            }

            if (!body.has("device_id") || !body.has("temperature") ||
                !body.has("timestamp")) {
                return crow::response(400, "Missing required fields");
            }

            try {
                int deviceId = body["device_id"].i();
                double temperature = body["temperature"].d();
                std::string timestamp = body["timestamp"].s();

                std::cout << "Received measurement: " << deviceId << ", "
                          << temperature << ", " << timestamp << '\n';

                if (!producer.publish(req.body)) {
                    return crow::response(503, "Kafka publishing failed");
                }

                return crow::response(200, "Measurement published to Kafka");

            } catch (const std::exception& e) {
                std::cerr << "Invalid measurement: " << e.what() << '\n';

                return crow::response(400, "Invalid measurement fields");
            }
        });

    std::cout << "Starting telemetry on port 8000...\n";

    app.bindaddr("0.0.0.0").port(8000).multithreaded().run();

    return 0;
}
