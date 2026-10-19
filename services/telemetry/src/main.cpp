#include "crow.h"

#include <curl/curl.h>
#include <iostream>
#include <string>

bool forwardToAnalytics(const std::string& json) {
    CURL* curl = curl_easy_init();

    if (!curl) {
        return false;
    }

    curl_slist* headers = nullptr;
    headers = curl_slist_append(headers, "Content-Type: application/json");

    curl_easy_setopt(curl, CURLOPT_URL, "http://analytics:8001/measurements");

    curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);
    curl_easy_setopt(curl, CURLOPT_POSTFIELDS, json.c_str());
    curl_easy_setopt(curl, CURLOPT_POSTFIELDSIZE,
                     static_cast<long>(json.size()));
    curl_easy_setopt(curl, CURLOPT_TIMEOUT, 5L);

    CURLcode result = curl_easy_perform(curl);

    long statusCode = 0;
    if (result == CURLE_OK) {
        curl_easy_getinfo(curl, CURLINFO_RESPONSE_CODE, &statusCode);
    }

    curl_slist_free_all(headers);
    curl_easy_cleanup(curl);

    return result == CURLE_OK && statusCode >= 200 && statusCode < 300;
}

int main() {
    if (curl_global_init(CURL_GLOBAL_DEFAULT) != CURLE_OK) {
       std::cerr << "Failed to initialize libcurl\n";
        return 1;
    }
    crow::SimpleApp app;

    CROW_ROUTE(app, "/measurements")
        .methods(crow::HTTPMethod::POST)

            ([](const crow::request& req) {
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

                    std::cout << "Received measurement:\n"
                              << "  Device: " << deviceId << '\n'
                              << "  Temperature: " << temperature << '\n'
                              << "  Timestamp: " << timestamp << '\n'
                              << std::endl;

                    if (!forwardToAnalytics(req.body)) {
                        std::cerr << "Failed to forward measurement to Analytics\n";
                        return crow::response(502, "Analytics service unavailable");
                    }

                    return crow::response(200, "Measurement forwarded");
                } catch (const std::exception& e) {
                    std::cerr << "Invalid measurement: " << e.what() << '\n';

                    return crow::response(400, "Invalid measurement fields");
                }
            });

    std::cout << "Starting telemetry service on port 8000...\n";

    app.bindaddr("0.0.0.0").port(8000).multithreaded().run();
    
    curl_global_cleanup();
    return 0;
}
